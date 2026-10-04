"""Dedicated Explorer presets; all changes still use the pinned Windhawk CLI."""
from pathlib import Path
import ctypes
import sys
from backend import atomic_json
from runtime_adapter import read_json, kernel32
from explorer_image import ExplorerImageAdapter, IMAGE_MOD

MOD = 'windows-11-file-explorer-styler'
STORAGE = 'local@' + MOD


class ExplorerAdapter:
    def __init__(self, runtime):
        self.runtime = runtime
        self.record = runtime.data / 'explorer-appearance.json'
        self.images = ExplorerImageAdapter(runtime)

    def observed(self):
        installed = next((m for m in self.runtime._installed_mods_readonly() if m['id'] == STORAGE), None)
        path = self.runtime.windhawk_data / 'Engine' / 'Mods' / (STORAGE + '.ini')
        value = ctypes.create_unicode_buffer(32768)
        kernel32.GetPrivateProfileStringW('Settings', 'theme', '', value, len(value), str(path.resolve()))
        return {'installed': installed is not None, 'enabled': bool(installed and installed['enabled']), 'theme': value.value}

    def state(self):
        build = sys.getwindowsversion().build
        current = self.observed()
        runtime = self.runtime.state()['windhawk']
        mod = next((m for m in runtime['mods'] if m['id'] == STORAGE), {})
        record = read_json(self.record, {})
        image = self.images.state()
        image_mod = next((m for m in runtime['mods'] if m['id'] == 'local@' + IMAGE_MOD), {})
        return {**current, 'supported': build >= 22621, 'build': build,
                'available': runtime['available'] and runtime['compiler'], 'loaded': mod.get('loaded', False),
                'canRestore': image['canRestore'] or record.get('status') in {'prepared', 'applied', 'needs_attention'},
                'image': {**image, 'enabled': image_mod.get('enabled', False), 'loaded': image_mod.get('loaded', False)},
                'choices': self.runtime.catalog[MOD]['themeChoices']}

    def _restore_values(self, previous):
        if not self.observed()['installed']:
            if previous['installed']:
                raise RuntimeError('原资源管理器模组已缺失，无法恢复。')
            return
        self.runtime._wh('mod', 'settings', 'set', STORAGE, 'theme=' + previous['theme'])
        self.runtime._wh('mod', 'enable' if previous['enabled'] else 'disable', STORAGE)

    def apply(self, theme):
        if sys.getwindowsversion().build < 22621:
            raise ValueError('此资源管理器外观功能需要 Windows 11 22H2 或更新版本。')
        mod = self.runtime.catalog[MOD]
        if not isinstance(theme, str) or not theme or theme not in {c['id'] for c in mod['themeChoices']}:
            raise ValueError('请选择资源管理器预设。')
        pending = read_json(self.record, {})
        if pending.get('status') in {'prepared', 'needs_attention'}:
            raise ValueError('上一次操作需要恢复，请先恢复后再应用。')
        before = self.observed()
        record = {'before': before, 'status': 'prepared', 'theme': theme}
        atomic_json(self.record, record)
        try:
            self.runtime.windhawk_apply([{'id': MOD, 'sourceHash': mod['sha256'], 'settings': {'theme': theme}}], preserve_others=True)
            after = self.observed()
            if not after['enabled'] or after['theme'] != theme:
                raise RuntimeError('未能确认资源管理器预设已保存和启用。')
            record.update(status='applied', after=after)
            atomic_json(self.record, record)
        except Exception as failure:
            try:
                self._restore_values(before)
                # Keep any earlier undo record if this attempt was rolled back.
                atomic_json(self.record, pending or {'status': 'rolled_back'})
            except Exception as recovery:
                record.update(status='needs_attention', error=str(failure), recoveryError=str(recovery))
                atomic_json(self.record, record)
                raise RuntimeError(f'{failure}；恢复未完成：{recovery}') from failure
            raise
        return self.state()

    def restore(self):
        if self.images.state()['canRestore']:
            self.images.restore()
            return self.state()
        record = read_json(self.record, {})
        if record.get('status') not in {'prepared', 'applied', 'needs_attention'}:
            raise ValueError('没有可恢复的资源管理器外观记录。')
        if record['status'] == 'applied' and self.observed() != record['after']:
            raise ValueError('资源管理器模组已被其他操作修改，未覆盖该修改。')
        self._restore_values(record['before'])
        current = self.observed()
        if current['enabled'] != record['before']['enabled'] or (current['installed'] and current['theme'] != record['before']['theme']):
            raise RuntimeError('恢复结果尚未确认，请重试。')
        record['status'] = 'restored'
        atomic_json(self.record, record)
        return self.state()
