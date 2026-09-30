"""Bundled theme packs with durable rollback and native static wallpaper playback."""
from __future__ import annotations
import ctypes
from ctypes import wintypes
from datetime import datetime
import json
from pathlib import Path
import re
import sys
import uuid
import zipfile

from backend import Assignment, atomic_json, canonical
from cursor_adapter import ROLE_KEYS, snapshot, read_json
from theme_packages import PackageLibrary, checked_asset, DATA_TYPES

USER32 = ctypes.WinDLL('user32', use_last_error=True)
USER32.SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT]
USER32.SystemParametersInfoW.restype = wintypes.BOOL


def current_wallpaper():
    value = ctypes.create_unicode_buffer(32768)
    if not USER32.SystemParametersInfoW(0x73, len(value), value, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return value.value


def set_wallpaper(path):
    if path and not Path(path).is_file():
        raise FileNotFoundError('壁纸文件不存在，已保留当前桌面。')
    value = ctypes.create_unicode_buffer(str(path))
    if not USER32.SystemParametersInfoW(20, 0, value, 3):
        raise ctypes.WinError(ctypes.get_last_error())
    if canonical(current_wallpaper()) != canonical(str(path)):
        raise RuntimeError('Windows 没有确认壁纸变更。')


class StaticWallpaper:
    def __init__(self, directory):
        self.data = Path(directory)
        self.path = self.data / 'wallpaper' / 'static.json'

    def status(self):
        record = read_json(self.path, {})
        active = record.get('status') == 'applied' and canonical(current_wallpaper()) == canonical(record.get('after', ''))
        return {'active': active, 'mode': 'static', 'paused': False, 'mediaId': record.get('mediaId'), 'settings': record.get('settings'), 'record': record.get('id')}

    def apply(self, media_id, settings):
        if not isinstance(media_id, str) or not re.fullmatch(r'[a-f0-9]{64}\.(jpg|jpeg|png|bmp|webp|gif)', media_id):
            raise ValueError('静态壁纸资源无效。')
        source = self.data / 'wallpapers' / media_id
        if not source.is_file():
            raise FileNotFoundError('壁纸素材不存在。')
        from PIL import Image
        with Image.open(source) as image:
            if getattr(image, 'is_animated', False):
                raise ValueError('动图需通过动态壁纸播放器应用。')
        # Windows does not natively support WebP. Decode once, never keep a renderer alive.
        if source.suffix.lower() in {'.webp', '.gif'}:
            target = source.with_suffix('.static.bmp')
            if not target.exists():
                with Image.open(source) as image:
                    image.convert('RGB').save(target, format='BMP')
            source = target
        previous = read_json(self.path, None)
        record = {'id': uuid.uuid4().hex, 'status': 'prepared', 'before': current_wallpaper(),
                  'previous': previous.get('id') if previous and previous.get('status') == 'applied' else None,
                  'after': str(source), 'mediaId': media_id, 'settings': settings}
        history = self.data / 'wallpaper' / 'static-history' / (record['id'] + '.json')
        atomic_json(history, record)
        try:
            set_wallpaper(source)
            record['status'] = 'applied'
            atomic_json(history, record); atomic_json(self.path, record)
        except Exception:
            set_wallpaper(record['before'])
            record['status'] = 'rolled_back'; atomic_json(history, record)
            raise
        return self.status()

    def restore(self, expected_id=None):
        record = read_json(self.path, {})
        if record.get('status') != 'applied':
            return {'active': False, 'mode': 'static'}
        if expected_id is not None and record.get('id') != expected_id:
            raise ValueError('壁纸已被其他操作修改，请先恢复最近一次壁纸。')
        if canonical(current_wallpaper()) != canonical(record['after']):
            raise ValueError('壁纸已在其他程序中修改，已保留当前桌面。')
        set_wallpaper(record['before'])
        record['status'] = 'restored'
        atomic_json(self.data / 'wallpaper' / 'static-history' / (record['id'] + '.json'), record)
        previous = read_json(self.data / 'wallpaper' / 'static-history' / (record['previous'] + '.json'), {}) if record.get('previous') else {}
        atomic_json(self.path, previous or {'status': 'restored'})
        return self.status()


class TemplateAdapter:
    def __init__(self, bridge, root=None):
        self.bridge = bridge
        self.root = Path(root) if root else (Path(sys.executable).parent.parent / 'wwwroot' / 'templates' if getattr(sys, 'frozen', False)
                                           else Path(__file__).resolve().parents[2] / 'assets' / 'templates')
        self.data = bridge.store.directory
        self.history = self.data / 'template-history'
        self.wallpaper = StaticWallpaper(self.data)
        self.packages = PackageLibrary(self.data)

    def catalog(self):
        items = []
        for original in read_json(self.root / 'catalog.json', []):
            item = dict(original)
            prefix = item['id'] + '/'
            item.update(source='builtin', version=item.get('version', '1.0.0'), assetBase='/templates/',
                        cursors={role: prefix + 'cursors/' + role + '.cur' for role in ROLE_KEYS},
                        icons={key: {'file': prefix + 'icons/' + key + '.ico', 'matches': words} for key, words in item['iconMatches'].items()},
                        cursorPreview=prefix + 'cursor-preview.png')
            items.append(item)
        return items + self.packages.catalog()

    def asset(self, item, value):
        root = self.packages.assets / item['assetFolder'] if item['source'] == 'imported' else self.root
        return checked_asset(root, value, DATA_TYPES)

    def list(self):
        return {'packs': [{key: value for key, value in item.items() if key != 'assetFolder'} for item in self.catalog()]}

    def media(self, ident):
        item = self.theme(ident)
        return {'wallpaper': str(self.asset(item, item['wallpaper'])),
                'animatedWallpaper': str(self.asset(item, item['animatedWallpaper'])) if item.get('animatedWallpaper') else None}

    def export(self, ident):
        item = self.theme(ident)
        manifest = {key: value for key, value in item.items() if key in {
            'name', 'subtitle', 'version', 'accent', 'pale', 'wallpaper', 'thumbnail', 'animatedWallpaper',
            'motionLabel', 'author', 'artwork', 'cursorSize', 'cursors', 'icons', 'cursorPreview'}}
        manifest.update(schemaVersion=1, id=item.get('packageId', item['id']))
        paths = {manifest[key] for key in ('wallpaper', 'thumbnail', 'animatedWallpaper', 'cursorPreview') if manifest.get(key)}
        paths.update(manifest['cursors'].values())
        paths.update(icon['file'] for icon in manifest['icons'].values())
        folder = self.data / 'exports'
        folder.mkdir(exist_ok=True)
        output = folder / (manifest['id'] + '-' + manifest['version'] + '-' + uuid.uuid4().hex[:8] + '.tspack')
        temporary = output.with_suffix('.partial')
        try:
            with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('theme.json', json.dumps(manifest, ensure_ascii=False, indent=2))
                for value in sorted(paths):
                    archive.write(self.asset(item, value), value)
            temporary.rename(output)
        finally:
            temporary.unlink(missing_ok=True)
        return {'path': str(output), 'name': item['name']}

    def theme(self, ident):
        if not isinstance(ident, str) or not re.fullmatch(r'[a-z0-9-]{1,64}', ident):
            raise ValueError('模板编号无效。')
        item = next((item for item in self.catalog() if item['id'] == ident), None)
        if item is None:
            raise ValueError('找不到该套装，请刷新列表或重新导入数据包。')
        return item

    def plan(self, ident):
        item = self.theme(ident)
        rows, errors = self.bridge.rows()
        matches=[]
        for row in rows:
            name=row['name'].casefold()
            symbol=next((key for key, words in item['iconMatches'].items() if any(word.casefold() in name for word in words)), None)
            if symbol: matches.append({'name':row['name'], 'path':row['path'], 'sha256':row['sha256'], 'symbol':symbol})
        return item, matches

    def current(self):
        for path in sorted(self.history.glob('*.json'), key=lambda value:value.stat().st_mtime_ns, reverse=True):
            record = read_json(path, {})
            if record.get('status') in {'applied', 'restoring', 'needs_attention'}:
                return record
        return {}

    def apply(self, ident, media_id, use_icons=False, use_cursors=False, wallpaper_mode='static', motion_media_id=None):
        if wallpaper_mode not in {'static', 'animated'}:
            raise ValueError('壁纸模式无效。')
        if wallpaper_mode == 'animated':
            if not isinstance(motion_media_id, str) or not re.fullmatch(r'[a-f0-9]{64}\.mp4', motion_media_id):
                raise ValueError('动态壁纸资源无效。')
            if not (self.data / 'wallpapers' / motion_media_id).is_file():
                raise FileNotFoundError('动态壁纸素材不存在。')
        item, matches = self.plan(ident)
        self.asset(item, item['wallpaper'])
        use_cursors = use_cursors is True and bool(item.get('cursors'))
        use_icons = use_icons is True and bool(item.get('icons'))
        # Preflight every cursor and icon before touching the desktop.
        roles = {role: self.bridge.cursors.import_file(self.asset(item, value)) for role, value in item['cursors'].items()} if use_cursors else {}
        icons = {key:self.bridge.store.import_icon(self.asset(item, value['file'])) for key, value in item['icons'].items()} if use_icons else {}
        record={'id':uuid.uuid4().hex,'templateId':ident,'name':item['name'],'status':'prepared','created':datetime.now().isoformat(),
                'icons':None,'cursors':False,'wallpaper':None,'beforeCursors':snapshot() if use_cursors else None,
                'mode':wallpaper_mode,'motionMediaId':motion_media_id}
        path=self.history/(record['id']+'.json');atomic_json(path,record)
        try:
            if icons:
                settings=self.bridge.store.read_settings()
                known={value.get('sha256'):value for value in settings.get('icons',[])}
                for symbol,value in icons.items():known[value['sha256']]={**value,'name':item['name']+' · '+symbol}
                settings['icons']=list(known.values());self.bridge.store.save_settings(settings)
            if use_icons and matches:
                result=self.bridge.store.apply([Assignment(row['path'],icons[row['symbol']]['path'],row['sha256']) for row in matches])
                record['icons']=result['id'];atomic_json(path,record)
                if any(entry['status']!='applied' for entry in result['entries']):
                    raise RuntimeError('部分快捷方式未能应用，正在恢复这次修改。')
            if use_cursors:
                self.bridge.cursors.apply(roles,item.get('cursorSize',48),expected_state=record['beforeCursors'])
                record['cursors']=True;record['afterCursors']=snapshot();atomic_json(path,record)
            result=self.wallpaper.apply(media_id,{'enabled':False,'preset':'elegance','strength':1,'perspective':False,'tilt':0,'opposite':True})
            record['wallpaper']=result['record'];record['status']='applied';atomic_json(path,record)
            return {'id':record['id'],'name':item['name'],'iconsApplied':len(matches) if use_icons else 0,'cursorsApplied':17 if use_cursors else 0,'mode':wallpaper_mode}
        except Exception as error:
            issues=[]
            try:
                if record['wallpaper']:self.wallpaper.restore(record['wallpaper'])
                if record['cursors']:self.bridge.cursors.restore()
                if record['icons']:self.bridge.store.restore(record['icons'])
            except Exception as recovery:issues.append(str(recovery))
            record['status']='needs_attention' if issues else 'rolled_back';record['errors']=[str(error),*issues];atomic_json(path,record)
            raise RuntimeError('；'.join(record['errors'])) from error

    def restore(self):
        for path in sorted(self.history.glob('*.json'), key=lambda value:value.stat().st_mtime_ns,reverse=True):
            record=read_json(path,{})
            if record.get('status') not in {'applied','restoring','needs_attention'}:continue
            if record.get('cursors') and snapshot()!=record.get('afterCursors'):
                raise ValueError('指针已在其他操作中修改，请先使用鼠标区域的恢复功能。')
            if record.get('wallpaper'):
                current=read_json(self.wallpaper.path,{})
                if current.get('id')!=record['wallpaper'] or not self.wallpaper.status()['active']:
                    raise ValueError('壁纸已被其他操作修改，已保留当前桌面。')
            record['status']='restoring';atomic_json(path,record)
            if record.get('icons'):
                result=self.bridge.store.restore(record['icons'])
                if any(entry['status'] not in {'restored','skipped'} for entry in result['entries']):
                    raise ValueError('部分快捷方式发生冲突，备份已保留，请到桌面图标区域处理。')
                record['icons']=None;atomic_json(path,record)
            if record.get('cursors'):
                self.bridge.cursors.restore();record['cursors']=False;atomic_json(path,record)
            if record.get('wallpaper'):
                self.wallpaper.restore(record['wallpaper']);record['wallpaper']=None;atomic_json(path,record)
            record['status']='restored';atomic_json(path,record)
            return {'ok':True,'id':record['id'],'name':record['name']}
        raise ValueError('没有可恢复的模板应用记录。')
