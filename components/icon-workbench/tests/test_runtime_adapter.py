"""Regression checks for managed runtime changes; never start a system engine."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_adapter import RuntimeAdapter


class RuntimeAdapterTests(unittest.TestCase):
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
