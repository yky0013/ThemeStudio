"""One appearance transaction and two independent recovery levels.

The host owns native wallpaper playback. This adapter journals Windows appearance
and returns the corresponding playback target to the host. Baselines are immutable;
undo records are per combined application, not per button or per component.
"""
from __future__ import annotations
import copy
import ctypes
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import uuid

from backend import atomic_json, canonical, digest, new_sibling, notify_shell, shortcut_info
from cursor_adapter import ROLE_KEYS, snapshot, restore_snapshot
from template_adapter import current_wallpaper, set_wallpaper
from runtime_adapter import read_json, process_images

ALLOWED = {'templates.apply','icons.apply','cursors.apply','wallpaper.apply','wallpaper.stop','wallpaper.pause',
           'explorer.apply',
           'runtime.windhawk.apply','runtime.windhawk.stop'}
ALL_DOMAINS = ['cursors','wallpaper','icons','windhawk','explorer']


def cursor_identity(state):
    """Copies of the same CUR/ANI and harmless registry type changes are equivalent."""
    values=state.get('cursors',{})
    roles={}
    for key in ROLE_KEYS:
        value=(values.get(key) or [''])[0]
        path=Path(os.path.expandvars(str(value))) if value else None
        saved=state.get('files',{}).get(key)
        roles[key]=saved['sha256'] if saved else digest(path) if path and path.is_file() else canonical(str(path)) if path else ''
    return {'roles':roles,'size':(values.get('CursorBaseSize') or [32])[0]}


class AppearanceAdapter:
    def __init__(self, bridge):
        self.bridge=bridge; self.data=bridge.store.directory
        self.root=self.data/'appearance'; self.history=self.root/'history'; self.blobs=self.root/'blobs'
        self.baseline=self.root/'initial.json';self.pending=self.root/'pending.json'

    def _records(self):
        return sorted((read_json(p,{}) for p in self.history.glob('*.json')),key=lambda r:r.get('created',''),reverse=True)

    def state(self):
        pending=read_json(self.pending,{})
        recent=next((r for r in self._records() if r.get('status')=='applied'),None)
        legacy=self.bridge.templates.current()
        baseline=read_json(self.baseline,{})
        has_legacy=any((self.data/'cursor-settings/history').glob('*.json')) or bool(legacy) or bool(self.bridge.store.history())
        return {'pending':bool(pending.get('id')),'canUndo':bool(pending.get('id') or recent or legacy),
                'canRestoreInitial':bool(baseline or has_legacy),
                'lastLabel':recent.get('label') if recent else legacy.get('name'),
                'baselineLabel':baseline.get('label') or ('可从旧版备份重建初始外观' if has_legacy else '首次应用前自动保存初始外观')}

    def _blob(self,path):
        path=Path(path);data=path.read_bytes();sha=hashlib.sha256(data).hexdigest()
        name=sha+(path.suffix.lower() or '.bin');target=self.blobs/name
        self.blobs.mkdir(parents=True,exist_ok=True)
        if not target.exists():target.write_bytes(data)
        elif target.read_bytes()!=data:raise ValueError('恢复副本校验失败。')
        return {'blob':name,'sha256':sha}

    def _blob_path(self,item):
        name=item.get('blob','')
        if not re.fullmatch(r'[a-f0-9]{64}\.[a-z0-9]+',name):raise ValueError('恢复副本编号无效。')
        path=self.blobs/name
        if not path.is_file() or digest(path)!=item['sha256']:raise ValueError('恢复副本已缺失或损坏，未修改系统。')
        return path

    def _wallpaper(self,path):
        result={'path':str(path),'staticRecord':read_json(self.data/'wallpaper/static.json')}
        if path and Path(path).is_file():result.update(self._blob(path))
        return result

    def _cursor_backup(self,state):
        result=copy.deepcopy(state);result['files']={}
        for role in ROLE_KEYS:
            value=(result['cursors'].get(role) or [''])[0]
            if value and Path(os.path.expandvars(value)).is_file():result['files'][role]=self._blob(os.path.expandvars(value))
        return result

    def _wallpaper_source(self,item):
        path=Path(item['path']) if item['path'] else None
        if path is None:return ''
        if path.is_file() and (not item.get('sha256') or digest(path)==item['sha256']):return str(path)
        source=self._blob_path(item)
        if source.suffix=='.bin':
            from PIL import Image
            decoded=source.with_suffix('.bmp')
            if not decoded.exists():
                with Image.open(source) as image:image.convert('RGB').save(decoded,format='BMP')
            return str(decoded)
        return str(source)

    def _mod_settings(self,storage):
        if not re.fullmatch(r'local@[a-z0-9-]+',storage):raise ValueError('模组恢复编号无效。')
        path=self.bridge.runtime.windhawk_data/'Engine/Mods'/(storage+'.ini')
        buffer=ctypes.create_unicode_buffer(65536)
        fn=ctypes.windll.kernel32.GetPrivateProfileSectionW
        fn.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint,ctypes.c_wchar_p]
        count=fn('Settings',buffer,len(buffer),str(path.resolve()))
        if count>=len(buffer)-2:raise ValueError('模组设置过长，无法完整备份。')
        return dict(part.split('=',1) for part in buffer[:count].split('\0') if '=' in part)

    def capture(self,domains,paths,native):
        result={};runtime=self.bridge.runtime
        if 'cursors' in domains:result['cursors']=self._cursor_backup(snapshot())
        if 'wallpaper' in domains:result['wallpaper']={**self._wallpaper(current_wallpaper()),'native':copy.deepcopy(native)}
        if 'icons' in domains:
            result['icons']={}
            for value in paths:
                path=Path(value)
                if path.is_file():
                    info=shortcut_info(path)
                    result['icons'][str(path)]={**self._blob(path),'details':info['details']}
        if 'windhawk' in domains:
            result['windhawk']={item['id']:{'enabled':item['enabled'],'settings':self._mod_settings(item['id'])}
                               for item in runtime._installed_mods_readonly()}
            result['windhawkEngine']=any(canonical(image)==canonical(runtime.windhawk_user/'windhawk.exe') for _,image in process_images())
        if 'explorer' in domains:
            result['explorer']={'images':read_json(self.data/'explorer-images/current.json'),
                                'legacy':read_json(self.data/'explorer-appearance.json')}
        return result

    def _scope(self,operations):
        if not isinstance(operations,list) or not 1<=len(operations)<=8:raise ValueError('请选择要统一应用的设置。')
        domains=set();paths=set();seen=set()
        rows,_=self.bridge.rows();known={row['path']:row for row in rows}
        for operation in operations:
            if not isinstance(operation,dict) or operation.get('operation') not in ALLOWED:raise ValueError('不支持的外观操作。')
            op=operation['operation'];payload=operation.get('payload',{})
            if op in seen or not isinstance(payload,dict):raise ValueError('同一设置不能在一次应用中重复提交。')
            seen.add(op)
            if op=='templates.apply':
                _,matches=self.bridge.templates.plan(payload.get('id'));domains.add('wallpaper')
                if payload.get('cursors') is True:domains.add('cursors')
                if payload.get('icons') is True:domains.add('icons');paths.update(row['path'] for row in matches)
                if payload.get('explorer') is True:domains.update(['explorer','windhawk'])
            elif op=='icons.apply':
                domains.add('icons')
                items=payload.get('items')
                if not isinstance(items,list) or not items:raise ValueError('请先选择图标对应关系。')
                by_id={hashlib.sha256(canonical(path).encode('utf-8')).hexdigest():row for path,row in known.items()}
                for item in items:
                    row=by_id.get(item.get('id')) if isinstance(item,dict) else None
                    if not row or row['sha256']!=item.get('sha256'):raise ValueError('桌面项目已变化，请刷新后再应用。')
                    paths.add(row['path'])
            elif op=='cursors.apply':
                self.bridge.resolve_roles(payload.get('roles'));domains.add('cursors')
            elif op.startswith('wallpaper.'):domains.add('wallpaper')
            elif op=='explorer.apply':domains.update(['explorer','windhawk'])
            elif op.startswith('runtime.windhawk.'):domains.add('windhawk')
            else:raise ValueError('此实验分支不支持该外观操作。')
        return sorted(domains),sorted(paths)

    def _all_icon_paths(self):
        rows,_=self.bridge.rows()
        return [row['path'] for row in rows]

    def _legacy_baseline(self,current):
        result=copy.deepcopy(current);sources=[];notes=[];managed=set()
        cursor_records=sorted((read_json(p,{}) for p in (self.data/'cursor-settings/history').glob('*.json')),key=lambda r:r.get('created',''))
        first=next((r for r in cursor_records if r.get('before') and r.get('status')!='prepared'),None)
        if first:result['cursors']=self._cursor_backup(first['before']);sources.append(first.get('created',''))
        histories=sorted((read_json(p,{}) for p in (self.data/'wallpaper/static-history').glob('*.json')),key=lambda r:r.get('id',''))
        roots=[r for r in histories if not r.get('previous') and r.get('status') in {'applied','restored'}]
        if roots:
            # UUID ordering does not describe time; use original filesystem birth time.
            root=min(roots,key=lambda r:(self.data/'wallpaper/static-history'/(r['id']+'.json')).stat().st_birthtime_ns)
            old=root.get('before','')
            if not old or Path(old).is_file():result['wallpaper']={**self._wallpaper(old),'staticRecord':None,'native':None};sources.append('旧版壁纸备份')
            else:notes.append('早期壁纸原文件已不存在，初始恢复会保留这一部分现状。')
        for batch in reversed(self.bridge.store.history()):
            for item in batch.get('entries',[]):
                path=item.get('path');backup=self.bridge.store.history_dir/batch['id']/str(item.get('backup',''))
                if not path or path in managed or not backup.is_file() or digest(backup)!=item.get('before_hash'):continue
                result.setdefault('icons',{})[path]={**self._blob(backup),'details':item.get('before')}
                managed.add(path)
        runtime=self.bridge.runtime;manager=runtime._managed()
        # ThemeStudio's owned Windhawk profile has no enabled mods before its first use.
        # Preserve the prior dedicated Explorer preset when a legacy record proves it existed.
        for key in result.get('windhawk',{}):result['windhawk'][key]['enabled']=False
        result['windhawkEngine']=False
        legacy=read_json(self.data/'explorer-appearance.json',{})
        if legacy.get('before',{}).get('installed'):
            prior=legacy['before'];key='local@windows-11-file-explorer-styler'
            result.setdefault('windhawk',{}).setdefault(key,{'settings':{}}).update(enabled=prior['enabled'])
            result['windhawk'][key]['settings']['theme']=prior['theme']
        result['explorer']={'images':None,'legacy':None}
        if managed:sources.append('旧版图标备份')
        return result,sources,notes,managed

    def ensure_baseline(self,native,paths):
        baseline=read_json(self.baseline)
        if baseline is None:
            current=self.capture(ALL_DOMAINS,self._all_icon_paths(),native)
            original,sources,notes,managed=self._legacy_baseline(current)
            has_legacy=bool(sources)
            baseline={'version':1,'created':datetime.now().isoformat(),'snapshot':original if has_legacy else current,
                      'managedIcons':sorted(managed),'notes':notes,'source':'legacy' if has_legacy else 'first-application',
                      'label':'初始外观来自旧版保留备份；无备份部分按升级时现状保存' if has_legacy else '已保存首次应用前的初始外观'}
        missing=[p for p in paths if p not in baseline['snapshot'].get('icons',{})]
        if missing:baseline['snapshot'].setdefault('icons',{}).update(self.capture(['icons'],missing,None)['icons'])
        baseline['managedIcons']=sorted(set(baseline.get('managedIcons',[]))|set(paths))
        atomic_json(self.baseline,baseline)
        return baseline

    def begin(self,operations,native):
        if read_json(self.pending,{}).get('id'):raise ValueError('上一次操作未完成，请先恢复。')
        domains,paths=self._scope(operations)
        self.ensure_baseline(native,paths)
        before=self.capture(domains,paths,native)
        record={'id':uuid.uuid4().hex,'created':datetime.now().isoformat(),'status':'prepared','kind':'apply',
                'label':'、'.join(str(op.get('label') or op['operation']) for op in operations),
                'domains':domains,'paths':paths,'before':before,'operations':operations}
        self._save(record);atomic_json(self.pending,{'id':record['id']})
        return {'id':record['id'],'wallpaperIncluded':'wallpaper' in domains}

    def _save(self,record):atomic_json(self.history/(record['id']+'.json'),record)
    def _record(self,ident):
        if not isinstance(ident,str) or not re.fullmatch(r'[a-f0-9]{32}',ident):raise ValueError('外观记录无效。')
        record=read_json(self.history/(ident+'.json'))
        if not record:raise ValueError('找不到外观恢复记录。')
        return record

    def commit(self,ident,native):
        record=self._record(ident)
        record['after']=self.capture(record['domains'],record['paths'],native)
        record['status']='applied' if record['kind'] in {'apply','initial'} else 'undone'
        if record.get('undoId'):
            previous=self._record(record['undoId']);previous['status']='undone';self._save(previous)
        if record.get('legacyId'):
            path=self.data/'template-history'/(record['legacyId']+'.json');legacy=read_json(path,{})
            legacy['status']='restored';atomic_json(path,legacy)
        self._save(record);atomic_json(self.pending,{})
        message='整套设置已应用并保存恢复记录。' if record['kind']=='apply' else '已恢复上一次应用前的外观。'
        if record['kind']=='initial':message='已恢复初始外观。'+' '.join(read_json(self.baseline,{}).get('notes',[]))
        return {**self.state(),'message':message}

    def _known_icon_state(self,path,current_hash):
        for batch in self.bridge.store.history():
            for entry in batch.get('entries',[]):
                if canonical(entry.get('path',''))==canonical(path) and current_hash in {entry.get('before_hash'),entry.get('applied_hash')}:
                    return True
        for record in self._records():
            for state in (record.get('before',{}),record.get('after',{})):
                if state.get('icons',{}).get(path,{}).get('sha256')==current_hash:return True
        return False

    def _preflight(self,target,allow_external=False):
        for path,item in target.get('icons',{}).items():
            backup=self._blob_path(item)
            if Path(path).is_file():
                if Path(path).suffix.lower() not in {'.lnk','.url'} or shortcut_info(path)['details']!=shortcut_info(backup)['details']:
                    raise ValueError('快捷方式目标或参数已变化，未覆盖：'+Path(path).name)
                if not allow_external and digest(Path(path))!=item['sha256'] and not self._known_icon_state(path,digest(Path(path))):
                    raise ValueError('快捷方式图标已在其他软件中修改，未覆盖：'+Path(path).name)
        wallpaper=target.get('wallpaper')
        if wallpaper:self._wallpaper_source(wallpaper)
        if target.get('cursors'):
            if set(target['cursors'].get('cursors',{}))!=set(snapshot()['cursors']):raise ValueError('指针备份不完整。')
            for role in ROLE_KEYS:
                value=(target['cursors']['cursors'].get(role) or [''])[0]
                backup=target['cursors'].get('files',{}).get(role)
                if backup:self._blob_path(backup)
                elif value and not Path(os.path.expandvars(value)).is_file():raise ValueError('原指针文件已不存在，未修改系统。')

    def _restore_mods(self,target):
        runtime=self.bridge.runtime;present={m['id']:m for m in runtime._installed_mods_readonly()}
        for ident in sorted(set(present)|set(target)):
            if ident not in present:
                if target[ident]['enabled']:raise ValueError('原模组已缺失，无法恢复：'+ident)
                continue
            runtime._wh('mod','disable',ident)
            if ident in target:
                values=target[ident]['settings']
                if not re.fullmatch(r'local@[a-z0-9-]+',ident) or any('\0' in str(k)+str(v) or '\n' in str(k)+str(v) for k,v in values.items()):raise ValueError('模组备份格式无效。')
                path=runtime.windhawk_data/'Engine/Mods'/(ident+'.ini')
                data=ctypes.create_unicode_buffer('\0'.join(k+'='+str(v) for k,v in values.items())+'\0\0')
                fn=ctypes.windll.kernel32.WritePrivateProfileSectionW
                fn.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p]
                if not fn('Settings',data,str(path.resolve())):raise ctypes.WinError()
                # Bulk restoration keeps exact missing/array keys; the official CLI
                # disables and re-enables the mod around the original INI section.
                if target[ident]['enabled']:runtime._wh('mod','enable',ident)
                if self._mod_settings(ident)!=values:raise RuntimeError('模组设置恢复核对失败。')

    def restore_core(self,target,allow_external=False):
        self._preflight(target,allow_external)
        if 'windhawk' in target:
            self._restore_mods(target['windhawk'])
            runtime=self.bridge.runtime;running=any(canonical(image)==canonical(runtime.windhawk_user/'windhawk.exe') for _,image in process_images())
            expected=target.get('windhawkEngine',any(item['enabled'] for item in target['windhawk'].values()))
            if expected and not running:
                root=runtime._windhawk_root();subprocess.Popen([str(root/'windhawk.exe'),'-tray-only'],cwd=root,creationflags=subprocess.CREATE_NO_WINDOW)
            elif running and not expected:runtime._run([runtime.windhawk_user/'windhawk.exe','-exit','-wait','-timeout','30000'],timeout=40)
            for _ in range(40):
                observed=any(canonical(image)==canonical(runtime.windhawk_user/'windhawk.exe') for _,image in process_images())
                if observed==expected:break
                time.sleep(.1)
            else:raise RuntimeError('运行组件的恢复状态尚未确认，恢复记录已保留。')
        changed=[]
        for value,item in target.get('icons',{}).items():
            path=Path(value)
            if not path.is_file():continue # Never recreate a shortcut the user deleted.
            backup=self._blob_path(item)
            if digest(path)==item['sha256']:continue
            temporary=new_sibling(path,'.appearance-restore-')
            try:
                shutil.copyfile(backup,temporary)
                if digest(temporary)!=item['sha256']:raise ValueError('恢复副本校验失败。')
                os.replace(temporary,path);changed.append(path)
            finally:temporary.unlink(missing_ok=True)
        if changed:notify_shell(changed)
        if 'cursors' in target:
            state=copy.deepcopy(target['cursors'])
            for role,backup in state.get('files',{}).items():
                raw=(state['cursors'].get(role) or [''])[0];path=Path(os.path.expandvars(raw)) if raw else None
                if path and (not path.is_file() or digest(path)!=backup['sha256']):state['cursors'][role][0]=str(self._blob_path(backup))
            restore_snapshot(state)
        if 'wallpaper' in target:
            item=target['wallpaper'];path=self._wallpaper_source(item)
            if canonical(current_wallpaper())!=canonical(path):set_wallpaper(path)
            atomic_json(self.data/'wallpaper/static.json',item.get('staticRecord') or {'status':'restored'})
        if 'explorer' in target:
            atomic_json(self.data/'explorer-images/current.json',target['explorer']['images'] or {'status':'restored'})
            atomic_json(self.data/'explorer-appearance.json',target['explorer']['legacy'] or {'status':'restored'})
        return {'native':target.get('wallpaper',{}).get('native'),'wallpaperIncluded':'wallpaper' in target}

    def rollback(self,ident):
        record=self._record(ident)
        try:result=self.restore_core(record['before'])
        except Exception as error:record.update(status='needs_attention',error=str(error));self._save(record);raise
        return result

    def recovered(self,ident):
        record=self._record(ident);record['status']='rolled_back';self._save(record);atomic_json(self.pending,{})
        return self.state()

    def prepare_restore(self,kind,native):
        if kind not in {'last','initial'}:raise ValueError('请选择恢复上一次或使用前外观。')
        pending=read_json(self.pending,{})
        if pending.get('id'):
            if kind!='last':raise ValueError('请先恢复未完成操作。')
            record=self._record(pending['id']);self._preflight(record['before'])
            return {'id':record['id'],'recover':True,'wallpaperIncluded':'wallpaper' in record['before']}
        undo=next((r for r in self._records() if r.get('status')=='applied'),None)
        legacy_id=None
        if kind=='initial':
            base=self.ensure_baseline(native,[]);target=copy.deepcopy(base['snapshot'])
            target['icons']={p:v for p,v in target.get('icons',{}).items() if p in base['managedIcons']}
        elif undo:target=undo['before']
        else:
            target,legacy_id=self._legacy_target(native)
        self._preflight(target,kind=='initial')
        domains=list(target);paths=list(target.get('icons',{}));before=self.capture(domains,paths,native)
        if kind=='last' and undo:
            if not self._equivalent(before,undo['after']):raise ValueError('外观已被软件外的操作修改；已保留现状。可以选择恢复使用前外观。')
        record={'id':uuid.uuid4().hex,'created':datetime.now().isoformat(),'status':'prepared','kind':kind,
                'label':'恢复使用前外观' if kind=='initial' else '恢复上一次','domains':domains,'paths':paths,
                'before':before,'target':target,'undoId':undo['id'] if kind=='last' and undo else None,'legacyId':legacy_id}
        self._save(record);atomic_json(self.pending,{'id':record['id']})
        return {'id':record['id'],'recover':False,'wallpaperIncluded':'wallpaper' in target}

    def _equivalent(self,current,expected):
        for key,value in expected.items():
            if key=='cursors':
                if cursor_identity(current[key])!=cursor_identity(value):return False
            elif key=='wallpaper':
                if canonical(current[key]['path'])!=canonical(value['path']) or current[key].get('native')!=value.get('native'):return False
            elif key=='icons':
                if {p:i['sha256'] for p,i in current[key].items()}!={p:i['sha256'] for p,i in value.items()}:return False
            elif key=='windhawk':
                visible=lambda items:{k:v['settings'] for k,v in items.items() if v['enabled']}
                if visible(current[key])!=visible(value):return False
            elif key=='explorer':continue
            elif current.get(key)!=value:return False
        return True

    def restore_target(self,ident):
        record=self._record(ident)
        return self.restore_core(record['target'],record['kind']=='initial')

    def _legacy_target(self,native):
        old=self.bridge.templates.current()
        if not old:raise ValueError('还没有可恢复的应用记录。')
        target={}
        if old.get('cursors'):
            now=cursor_identity(snapshot())
            known=[old['beforeCursors'],old.get('afterCursors',{})]
            for p in (self.data/'cursor-settings/history').glob('*.json'):
                item=read_json(p,{})
                known.extend(v for v in (item.get('before'),item.get('after')) if v)
            if not any(now==cursor_identity(state) for state in known):raise ValueError('当前指针不属于已记录的软件操作，已保留。可选择恢复使用前外观。')
            target['cursors']=old['beforeCursors']
        if old.get('icons'):
            manifest=read_json(self.bridge.store._manifest_path(old['icons']),{});target['icons']={}
            for entry in manifest.get('entries',[]):
                backup=self.bridge.store.history_dir/old['icons']/str(entry.get('backup',''))
                if backup.is_file() and digest(backup)==entry.get('before_hash'):
                    target['icons'][entry['path']]={**self._blob(backup),'details':entry.get('before')}
        if old.get('wallpaper'):
            saved=read_json(self.data/'wallpaper/static-history'/(old['wallpaper']+'.json'),{})
            if not saved:raise ValueError('旧版壁纸备份缺失。')
            current=canonical(current_wallpaper())
            owned={canonical(r.get(k,'')) for p in (self.data/'wallpaper/static-history').glob('*.json') for r in [read_json(p,{})] for k in ('before','after')}
            if current not in owned:raise ValueError('壁纸已在其他软件中修改，未覆盖。')
            previous=read_json(self.data/'wallpaper/static-history'/(saved['previous']+'.json')) if saved.get('previous') else None
            playback=read_json(self.data/'template-native-history'/(old['id']+'.json'),{}).get('previous')
            target['wallpaper']={**self._wallpaper(saved.get('before','')),'staticRecord':previous,'native':playback}
        if old.get('explorer'):
            saved=read_json(self.data/'explorer-images'/(old['explorer']+'.json'),{})
            if saved.get('before'):
                mods=self.capture(['windhawk'],[],None)['windhawk']
                for mod,prior in saved['before'].items():
                    ident='local@'+mod
                    if not prior['installed']:mods.pop(ident,None)
                    else:
                        item=mods.setdefault(ident,{'settings':{}});item['enabled']=prior['enabled'];item['settings'].update(prior['settings'])
                target['windhawk']=mods
                target['windhawkEngine']=any(item['enabled'] for item in mods.values())
                previous=read_json(self.data/'explorer-images'/(saved['previous']+'.json')) if saved.get('previous') else None
                target['explorer']={'images':previous,'legacy':read_json(self.data/'explorer-appearance.json')}
        if not target:raise ValueError('这条旧版记录已无可恢复项目。')
        return target,old['id']
