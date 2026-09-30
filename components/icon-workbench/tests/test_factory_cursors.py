"""OEM discovery must be read-only and cannot silently reset unrelated settings."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cursor_adapter as ca
from desktop_bridge import DesktopBridge


class FactoryCursorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.themes = self.root / 'Resources' / 'Themes'
        self.themes.mkdir(parents=True)
        self.theme = self.themes / '0ASUS.theme'
        self.required = set(ca.ROLE_KEYS) - {'Crosshair', 'UpArrow', 'Person', 'Pin'}
        self.mapping = {role: self.themes / (role + '.ani') for role in self.required}
        self.theme.write_text('[Theme]\nDisplayName=TX\n[Control Panel\\Cursors]\n' +
                              '\n'.join(f'{role}={path}' for role, path in self.mapping.items()), encoding='utf-8')

    def test_discovery_is_read_only_and_keeps_optional_system_roles(self):
        before = ca.snapshot()
        with patch.object(ca, 'validate_cursor', side_effect=lambda p: p) as validate, patch.object(ca, 'write_values') as write:
            factory = ca.factory_scheme(self.root)
            self.assertEqual(factory['size'], 32)
            self.assertEqual(set(factory['roles']), set(ca.ROLE_KEYS))
            self.assertEqual(factory['roles']['Crosshair'], '')
            self.assertEqual(factory['roles']['Arrow'], str(self.mapping['Arrow']))
            self.assertEqual(validate.call_count, 13)
            write.assert_not_called()
        self.assertEqual(ca.snapshot(), before)

    def test_missing_oem_is_not_windows_default(self):
        self.theme.unlink()
        self.assertIsNone(ca.factory_scheme(self.root))
        adapter = ca.CursorAdapter(self.root / 'data')
        with patch.object(ca, 'factory_scheme', return_value=None), patch.object(adapter, 'apply') as apply:
            with self.assertRaisesRegex(ValueError, '没有可用'):
                adapter.restore_factory(ca.snapshot())
            apply.assert_not_called()

    def test_incomplete_or_external_theme_is_rejected(self):
        with patch.object(ca, 'validate_cursor', side_effect=lambda p: p):
            self.theme.write_text('[Theme]\nDisplayName=TX\n[Control Panel\\Cursors]\nArrow=' + str(self.mapping['Arrow']), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, '不完整'):
                ca.factory_scheme(self.root)
            self.theme.write_text('[Theme]\nDisplayName=TX\n[Control Panel\\Cursors]\nArrow=' + str(self.root / 'untrusted.ani'), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, '超出'):
                ca.factory_scheme(self.root)

    def test_generic_asus_theme_is_not_offered_as_tianxuan(self):
        self.theme.write_text(self.theme.read_text().replace('DisplayName=TX','DisplayName=ASUS'), encoding='utf-8')
        with patch.object(ca, 'validate_cursor') as validate:
            self.assertIsNone(ca.factory_scheme(self.root))
            validate.assert_not_called()

    def test_utf16_oem_theme_is_supported(self):
        self.theme.write_text(self.theme.read_text(), encoding='utf-16')
        with patch.object(ca, 'validate_cursor', side_effect=lambda p: p):
            self.assertEqual(ca.factory_scheme(self.root)['kind'], 'factory')

    def test_factory_restore_uses_existing_backup_and_conflict_transaction(self):
        adapter = ca.CursorAdapter(self.root / 'data')
        factory = {'roles': {role: str(path) for role, path in self.mapping.items()}, 'size': 32}
        state = ca.snapshot()
        with patch.object(ca, 'factory_scheme', return_value=factory), patch.object(adapter, 'apply', return_value='ok') as apply:
            self.assertEqual(adapter.restore_factory(state), 'ok')
            apply.assert_called_once_with(factory['roles'], 32, expected_state=state)

    def test_bridge_requires_fresh_version_for_factory_restore(self):
        bridge = DesktopBridge(self.root / 'bridge', [])
        with patch.object(bridge.cursors, 'restore_factory') as restore:
            with self.assertRaisesRegex(ValueError, '重新读取'):
                bridge.dispatch('cursors.factory', {'version': 'missing'})
            restore.assert_not_called()
            state = ca.snapshot()
            bridge.cursor_versions['version'] = state
            self.assertEqual(bridge.dispatch('cursors.factory', {'version': 'version'}), {'ok': True})
            restore.assert_called_once_with(state)


if __name__ == '__main__':
    unittest.main()
