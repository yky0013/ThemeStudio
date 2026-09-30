"""Regression checks for managed runtime changes; never start a system engine."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_adapter import RuntimeAdapter, desktop_profile, observed_desktop_mode


class RuntimeAdapterTests(unittest.TestCase):
    def test_fresh_startup_does_not_initialize_engines_or_write_profiles(self):
        with tempfile.TemporaryDirectory() as folder:
            adapter = RuntimeAdapter(folder)
            adapter.seelen_settings = Path(folder) / 'seelen' / 'settings.json'
            with patch.object(adapter, '_wh', side_effect=AssertionError('CLI on startup')), \
                    patch.object(adapter, '_windhawk_root', side_effect=AssertionError('runtime initialized')), \
                    patch('runtime_adapter.subprocess.Popen', side_effect=AssertionError('engine started')), \
                    patch('runtime_adapter.atomic_json', side_effect=AssertionError('profile changed')):
                state = adapter.state()
            self.assertEqual(state['windhawk']['mods'], [])
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_legacy_status_reads_ini_without_rewriting_or_activating_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            adapter = RuntimeAdapter(folder)
            adapter.seelen_settings = Path(folder) / 'seelen-settings.json'
            adapter.seelen_settings.write_text('{"activeThemes":["@user/custom"]}', encoding='utf-8')
            adapter.windhawk_user.mkdir()
            (adapter.windhawk_user / 'windhawk.ini').write_text('[Storage]\nPortable=1\n', encoding='utf-16')
            configs = adapter.windhawk_data / 'Engine' / 'Mods'
            configs.mkdir(parents=True)
            for identifier, disabled in [('local@mouse-trail', 0), ('local@accent-color-sync', 1)]:
                (configs / (identifier + '.ini')).write_text('[Mod]\nLibraryFileName=' + identifier + '.dll\nDisabled=' + str(disabled) + '\nVersion=1.2\n', encoding='utf-16')
            (configs / 'incomplete.ini').write_text('[Mod]\nDisabled=0\n', encoding='utf-16')
            before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in Path(folder).rglob('*') if path.is_file()}
            with patch.object(adapter, '_wh', side_effect=AssertionError('CLI on startup')), \
                    patch.object(adapter, '_windhawk_root', side_effect=AssertionError('runtime initialized')), \
                    patch('runtime_adapter.subprocess.Popen', side_effect=AssertionError('engine started')), \
                    patch('runtime_adapter.atomic_json', side_effect=AssertionError('profile changed')), \
                    patch('runtime_adapter.process_images', return_value=[(1, str(adapter.windhawk_user / 'windhawk.exe'))]), \
                    patch('runtime_adapter.loaded_libraries', return_value={'local@mouse-trail.dll'}):
                state = adapter.state()
                self.assertEqual(state, adapter.state())
            self.assertEqual(state['seelen']['themes'], ['@user/custom'])
            mods = {item['id']: item for item in state['windhawk']['mods']}
            self.assertEqual(len(mods), 2)
            self.assertTrue(mods['local@mouse-trail']['enabled'])
            self.assertTrue(mods['local@mouse-trail']['loaded'])
            self.assertFalse(mods['local@accent-color-sync']['enabled'])
            self.assertFalse(mods['local@accent-color-sync']['loaded'])
            after = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in Path(folder).rglob('*') if path.is_file()}
            self.assertEqual(before, after)

    def test_desktop_modes_preserve_apps_and_unrelated_settings(self):
        before = {'language': 'zh-CN', 'byWidget': {'@seelen/weg': {'position': 'Left', 'size': 32, 'shortcuts': {'x': ['A']}}, 'notes': {'enabled': True}}}
        mac = desktop_profile(before, 'mac')
        self.assertEqual(before['byWidget']['@seelen/weg']['position'], 'Left')
        self.assertEqual(mac['byWidget']['@seelen/weg']['mode'], 'MinContent')
        self.assertEqual(mac['byWidget']['@seelen/weg']['position'], 'Bottom')
        self.assertEqual(mac['byWidget']['@seelen/fancy-toolbar']['position'], 'Top')
        self.assertFalse(mac['byWidget']['@seelen/wallpaper-manager']['enabled'])
        self.assertEqual(observed_desktop_mode(True, mac), 'mac')
        windows = desktop_profile(mac, 'windows')
        self.assertEqual(observed_desktop_mode(False, mac), 'windows')
        self.assertEqual(observed_desktop_mode(True, windows), 'windows')
        self.assertEqual(windows['byWidget']['notes'], before['byWidget']['notes'])
        self.assertEqual(windows['byWidget']['@seelen/weg']['shortcuts'], {'x': ['A']})

    def test_unknown_desktop_mode_is_rejected_before_engine_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            adapter = RuntimeAdapter(folder)
            with patch.object(adapter, 'seelen_apply') as enable, patch.object(adapter, 'seelen_stop') as stop:
                with self.assertRaises(ValueError): adapter.dispatch('runtime.desktop.apply', {'mode': 'unknown'})
                enable.assert_not_called(); stop.assert_not_called()

    def test_saved_windows_choice_survives_applying_other_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            adapter = RuntimeAdapter(folder)
            with patch.object(adapter, '_managed', return_value={'desktopMode': 'windows'}), \
                    patch.object(adapter, 'seelen_apply') as enable, patch.object(adapter, 'seelen_stop', return_value={}) as stop, \
                    patch.object(adapter, 'windhawk_apply', return_value={'mods': []}):
                adapter.dispatch('runtime.apply', {'recipe': {'seelen': {}, 'windhawk': []}})
                enable.assert_not_called(); stop.assert_called_once()

    def test_applying_an_empty_mod_selection_disables_previous_managed_mods(self):
        with tempfile.TemporaryDirectory() as folder:
            adapter = RuntimeAdapter(folder)
            with patch.object(adapter, 'seelen_apply', return_value={'running': True}), \
                    patch.object(adapter, 'windhawk_apply', return_value={'mods': []}) as apply_mods:
                result = adapter.dispatch('runtime.apply', {'recipe': {'seelen': {}, 'windhawk': []}})
            apply_mods.assert_called_once_with([])
            self.assertEqual(result['windhawk']['mods'], [])

    def test_source_integrity_accepts_windows_checkout_line_endings(self):
        with tempfile.TemporaryDirectory() as folder:
            adapter = RuntimeAdapter(folder)
            for identifier in ('mouse-trail', 'accent-color-sync'):
                mod = adapter.catalog[identifier]
                source = (adapter.mod_sources / (identifier + '.wh.cpp')).read_bytes().replace(b'\r\n', b'\n')
                source_directory = Path(folder) / identifier
                source_directory.mkdir()
                target = source_directory / (identifier + '.wh.cpp')
                target.write_bytes(source.replace(b'\n', b'\r\n'))
                original_directory = adapter.mod_sources
                adapter.mod_sources = source_directory
                validated = adapter._validate_mods([{'id': identifier, 'sourceHash': mod['sha256'], 'settings': {}}])
                self.assertEqual(validated[0][1]['id'], identifier)
                target.write_bytes(source + b'\n// changed code\n')
                with self.assertRaisesRegex(ValueError, '源码已变化'):
                    adapter._validate_mods([{'id': identifier, 'sourceHash': mod['sha256'], 'settings': {}}])
                adapter.mod_sources = original_directory


if __name__ == '__main__':
    unittest.main()
