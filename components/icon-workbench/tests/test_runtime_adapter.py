"""Regression checks for managed runtime changes; never start a system engine."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_adapter import RuntimeAdapter


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
            self.assertTrue(state['seelen']['removed'])
            self.assertFalse(state['seelen']['available'])
            mods = {item['id']: item for item in state['windhawk']['mods']}
            self.assertEqual(len(mods), 2)
            self.assertTrue(mods['local@mouse-trail']['enabled'])
            self.assertTrue(mods['local@mouse-trail']['loaded'])
            self.assertFalse(mods['local@accent-color-sync']['enabled'])
            self.assertFalse(mods['local@accent-color-sync']['loaded'])
            after = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in Path(folder).rglob('*') if path.is_file()}
            self.assertEqual(before, after)

    def test_removed_seelen_requests_cannot_change_an_external_profile(self):
        with tempfile.TemporaryDirectory() as folder:
            adapter = RuntimeAdapter(folder)
            with patch('runtime_adapter.subprocess.Popen', side_effect=AssertionError('engine started')), \
                    patch('runtime_adapter.atomic_json', side_effect=AssertionError('profile changed')):
                for operation in ('runtime.desktop.apply', 'runtime.seelen.apply', 'runtime.seelen.stop'):
                    with self.assertRaisesRegex(ValueError, '已移除'):
                        adapter.dispatch(operation, {'mode': 'mac', 'seelen': {'activeThemes': ['@default/theme']}})
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_uninstall_leaves_external_seelen_processes_and_files_alone(self):
        with tempfile.TemporaryDirectory() as folder:
            adapter = RuntimeAdapter(folder)
            with patch('runtime_adapter.process_images', return_value=[(42, r'C:\External\seelen-ui.exe')]), \
                    patch.object(adapter, '_run', side_effect=AssertionError('external process changed')), \
                    patch('runtime_adapter.atomic_json', side_effect=AssertionError('profile changed')):
                self.assertTrue(adapter.shutdown()['stopped'])

    def test_applying_an_empty_mod_selection_disables_previous_managed_mods(self):
        with tempfile.TemporaryDirectory() as folder:
            adapter = RuntimeAdapter(folder)
            with patch.object(adapter, 'windhawk_apply', return_value={'mods': []}) as apply_mods:
                result = adapter.dispatch('runtime.apply', {'recipe': {'seelen': {}, 'windhawk': []}})
            apply_mods.assert_called_once_with([])
            self.assertEqual(result['windhawk']['mods'], [])

    def test_other_windhawk_installation_blocks_activation_before_any_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            adapter = RuntimeAdapter(folder)
            with patch('runtime_adapter.process_images', return_value=[(7, r'C:\Mainline\windhawk.exe')]), \
                    patch.object(adapter, '_wh', side_effect=AssertionError('CLI mutated another profile')):
                with self.assertRaisesRegex(ValueError, '另一个 Windhawk'):
                    adapter.windhawk_apply([])
            self.assertEqual(list(Path(folder).iterdir()), [])

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
