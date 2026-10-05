"""Theme-linked native Explorer images, with immutable assets and durable undo."""
from __future__ import annotations
import ctypes
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid
from PIL import Image, ImageColor
from backend import atomic_json
from runtime_adapter import read_json, kernel32

IMAGE_MOD = 'themestudio-explorer-background'
FRAME_MOD = 'windows-11-file-explorer-styler'
DEFAULT_APPEARANCE = {'imageOpacity': 35, 'tint': '#081b32'}


def appearance(value=None):
    value = DEFAULT_APPEARANCE if value is None else value
    if not isinstance(value, dict):
        raise ValueError('资源管理器外观参数无效。')
    opacity, tint = value.get('imageOpacity', 35), value.get('tint', '#081b32')
    if type(opacity) is not int or not 10 <= opacity <= 70 or not isinstance(tint, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', tint):
        raise ValueError('图片可见度应为 10–70，底色须为六位颜色。')
    return {'imageOpacity': opacity, 'tint': tint.lower()}


def frame_settings(image_path, tint):
    # The native file list is Win32; Home/Gallery and the command bar are XAML.
    # A local, validated PNG reaches XAML through ImageBrush.
    brush = '<ImageBrush ImageSource="' + image_path.as_uri() + '" Stretch="UniformToFill" />'
    settings = {'theme': '', 'backgroundTranslucentEffect': 'none', 'backgroundTranslucentEffectRegion': '',
                'explorerFrameContainerHeight': 0}
    targets = [
        ('Grid#FileExplorerRoot', ['RequestedTheme=2', 'Background:=' + brush]),
        ('Grid#NavigationBarControlGrid', ['RequestedTheme=2', 'Background=Transparent']),
        ('FileExplorerExtensions.CommandBarControl_Wave1 > Grid, Grid#CommandBarControlRootGrid', ['RequestedTheme=2', 'Background=Transparent']),
        ('CommandBar#FileExplorerCommandBar', ['RequestedTheme=2', 'Background=Transparent']),
        ('Grid#HomeViewRootGrid', ['RequestedTheme=2', 'Background:=' + brush]),
        ('Microsoft.UI.Xaml.Controls.Grid#GalleryRootGrid', ['RequestedTheme=2', 'Background:=' + brush]),
        ('Grid#DetailsViewControlRootGrid', ['RequestedTheme=2', 'Background=Transparent']),
        ('FileExplorerExtensions.FileExplorerTabControl', ['RequestedTheme=2', 'Background=Transparent']),
    ]
    for i, (target, styles) in enumerate(targets):
        settings[f'controlStyles[{i}].target'] = target
        for j, style in enumerate(styles):
            settings[f'controlStyles[{i}].styles[{j}]'] = style
        settings[f'controlStyles[{i}].styles[{len(styles)}]'] = ''
    settings[f'controlStyles[{len(targets)}].target'] = ''
    return settings


class ExplorerImageAdapter:
    def __init__(self, runtime):
        self.runtime = runtime
        self.root = runtime.data / 'explorer-images'
        self.record = self.root / 'current.json'

    def prepare(self, source, value):
        value = appearance(value)
        source = Path(source)
        fingerprint = hashlib.sha256(source.read_bytes() + json.dumps(value, sort_keys=True).encode()).hexdigest()
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / (fingerprint + '.bmp')
        png = target.with_suffix('.png')
        if not target.is_file() or not png.is_file():
            with Image.open(source) as original:
                original.seek(0)
                decoded = original.convert('RGB')
                decoded.thumbnail((2560, 1440), Image.Resampling.LANCZOS)
                # Exactly the same blend as the preview's image over its solid tint.
                composite = Image.blend(Image.new('RGB', decoded.size, ImageColor.getrgb(value['tint'])), decoded, value['imageOpacity'] / 100)
                composite.save(target, format='BMP')
                composite.save(png, format='PNG')
        return target, png, value

    def _read_setting(self, mod, key):
        path = self.runtime.windhawk_data / 'Engine' / 'Mods' / ('local@' + mod + '.ini')
        buffer = ctypes.create_unicode_buffer(32768)
        kernel32.GetPrivateProfileStringW('Settings', key, '', buffer, len(buffer), str(path.resolve()))
        return buffer.value

    def observed(self, settings):
        installed = {mod['id']: mod for mod in self.runtime._installed_mods_readonly()}
        return {mod: {'installed': 'local@' + mod in installed,
                      'enabled': bool(installed.get('local@' + mod, {}).get('enabled')),
                      'settings': {key: self._read_setting(mod, key) for key in values}}
                for mod, values in settings.items()}

    def state(self):
        record = read_json(self.record, {})
        return {'active': record.get('status') == 'applied', 'packId': record.get('packId', ''),
                'appearance': record.get('appearance', DEFAULT_APPEARANCE),
                'canRestore': record.get('status') in {'prepared', 'applied', 'needs_attention'},
                'recordId': record.get('id')}

    def _restore_values(self, before):
        installed = {mod['id'] for mod in self.runtime._installed_mods_readonly()}
        for mod, prior in before.items():
            storage = 'local@' + mod
            if storage not in installed:
                if prior['installed']:
                    raise RuntimeError('原资源管理器组件缺失，无法恢复。')
                continue
            # Disable first, so a half-restored setting cannot render in Explorer.
            self.runtime._wh('mod', 'disable', storage)
            values = [key + '=' + str(value) for key, value in prior['settings'].items()]
            if values:
                self.runtime._wh('mod', 'settings', 'set', storage, *values)
            if prior['enabled']:
                self.runtime._wh('mod', 'enable', storage)

    def _check_restore(self, before):
        after = self.observed({mod: item['settings'] for mod, item in before.items()})
        for mod, prior in before.items():
            if after[mod]['enabled'] != prior['enabled'] or (prior['installed'] and after[mod]['settings'] != prior['settings']):
                raise RuntimeError('资源管理器恢复结果尚未确认，备份已保留。')

    def apply(self, source, pack_id, value=None):
        if sys.getwindowsversion().build < 22621:
            raise ValueError('资源管理器图片外观需要 Windows 11 22H2 或更新版本。')
        previous = read_json(self.record, {})
        if previous.get('status') in {'prepared', 'needs_attention'}:
            raise ValueError('上次资源管理器操作尚未完成，请先恢复。')
        target, png, value = self.prepare(source, value)
        settings = {IMAGE_MOD: {'imagePath': str(target.resolve()), 'textColor': '#e4edfa', 'captionColor': value['tint']}, FRAME_MOD: frame_settings(png.resolve(), value['tint'])}
        selections = [{'id': mod, 'sourceHash': self.runtime.catalog[mod]['sha256'], 'settings': values} for mod, values in settings.items()]
        self.runtime._validate_mods(selections)
        before = self.observed(settings)
        record = {'id': uuid.uuid4().hex, 'status': 'prepared', 'packId': pack_id, 'appearance': value,
                  'before': before, 'settings': settings, 'previous': previous.get('id') if previous.get('status') == 'applied' else None}
        history = self.root / (record['id'] + '.json')
        atomic_json(history, record); atomic_json(self.record, record)
        try:
            self.runtime.windhawk_apply(selections, preserve_others=True)
            after = self.observed(settings)
            for mod, expected in settings.items():
                if not after[mod]['enabled'] or any(after[mod]['settings'][key] != str(value) for key, value in expected.items()):
                    raise RuntimeError('资源管理器外观未能完整保存和启用。')
            record.update(status='applied', after=after)
            atomic_json(history, record); atomic_json(self.record, record)
        except Exception as failure:
            try:
                self._restore_values(before); self._check_restore(before)
                record['status'] = 'rolled_back'; atomic_json(history, record)
                atomic_json(self.record, previous or {'status': 'restored'})
            except Exception as recovery:
                record.update(status='needs_attention', error=str(failure), recoveryError=str(recovery))
                atomic_json(history, record); atomic_json(self.record, record)
                raise RuntimeError(f'{failure}；恢复未完成：{recovery}') from failure
            raise
        return self.state()

    def can_restore(self, expected_id=None):
        record = read_json(self.record, {})
        if record.get('status') not in {'prepared', 'applied', 'needs_attention'}:
            raise ValueError('没有可恢复的资源管理器图片外观。')
        if expected_id is not None and record.get('id') != expected_id:
            raise ValueError('资源管理器已被其他操作修改，请先恢复最近一次外观。')
        if record['status'] == 'applied' and self.observed(record['settings']) != record['after']:
            raise ValueError('资源管理器模组已被其他操作修改，已保留当前外观。')
        return record

    def restore(self, expected_id=None):
        record = self.can_restore(expected_id)
        self._restore_values(record['before']); self._check_restore(record['before'])
        record['status'] = 'restored'; atomic_json(self.root / (record['id'] + '.json'), record)
        previous = read_json(self.root / (record['previous'] + '.json'), {}) if record.get('previous') else {}
        atomic_json(self.record, previous or {'status': 'restored'})
        return self.state()
