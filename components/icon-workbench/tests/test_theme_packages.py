"""Archive boundaries, portable export/import and persistence using isolated user data."""
import hashlib
import json
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop_bridge import DesktopBridge
from theme_packages import PackageLibrary

ROOT = Path(__file__).resolve().parents[3]


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.desktop = self.root / 'desktop'
        self.desktop.mkdir()
        self.bridge = DesktopBridge(self.root / 'data', [(self.desktop, 'fixture')])
        self.library = self.bridge.templates.packages
        self.wallpaper = ROOT / 'assets/templates/wuthering-waves/wallpaper.jpg'

    def archive(self, manifest=None, entries=None, name='theme.tspack'):
        value = {'schemaVersion': 1, 'id': 'test-pack', 'name': '测试套装', 'version': '1.0.0', 'wallpaper': '素材/壁纸.jpg'}
        value.update(manifest or {})
        output = self.root / name
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('theme.json', json.dumps(value, ensure_ascii=False))
            archive.write(self.wallpaper, '素材/壁纸.jpg')
            for key, data in (entries or {}).items():
                info = zipfile.ZipInfo(key) if isinstance(key, str) else key
                if isinstance(key, str):
                    info.filename = key  # Keep the malicious raw name; Windows ZipInfo normalizes backslashes.
                archive.writestr(info, data)
        return output

    def test_import_is_durable_without_changing_system_and_duplicate_is_idempotent(self):
        source = self.archive()
        with patch('template_adapter.set_wallpaper') as system, patch.object(self.bridge.cursors, 'apply') as cursors:
            result = self.bridge.dispatch('templates.import', {'path': str(source)})
            self.assertFalse(result['duplicate'])
            system.assert_not_called()
            cursors.assert_not_called()
        duplicate = self.library.import_archive(source)
        self.assertTrue(duplicate['duplicate'])
        source.unlink()
        reopened = DesktopBridge(self.bridge.store.directory, [(self.desktop, 'fixture')])
        packs = reopened.dispatch('templates.list', {})['packs']
        self.assertEqual(len(packs), 8)
        item = next(item for item in packs if item['id'] == result['id'])
        self.assertEqual(item['source'], 'imported')
        self.assertEqual(item['icons'], {})
        self.assertTrue(Path(reopened.templates.media(item['id'])['wallpaper']).is_file())

    def test_export_complete_builtin_imports_all_accessories_without_bundled_motion(self):
        exported = self.bridge.templates.export('wuthering-waves')
        imported = self.library.import_archive(exported['path'])
        item = self.bridge.templates.theme(imported['id'])
        self.assertEqual(len(item['cursors']), 17)
        self.assertEqual(len(item['icons']), 12)
        self.assertEqual(self.bridge.templates.asset(item, item['wallpaper']).read_bytes(), self.wallpaper.read_bytes())
        self.assertIsNone(self.bridge.templates.media(imported['id'])['animatedWallpaper'])
        roundtrip = self.bridge.templates.export(imported['id'])
        with zipfile.ZipFile(roundtrip['path']) as archive:
            manifest = json.loads(archive.read('theme.json'))
        self.assertEqual(manifest['id'], 'wuthering-waves')

    def test_user_imported_animation_survives_export_and_reimport(self):
        video = (ROOT/'vendor/Seelen-UI/src/ui/react/settings/public/fixtures/parallax-motion.mp4').read_bytes()
        imported = self.library.import_archive(self.archive({'animatedWallpaper':'motion.mp4'}, {'motion.mp4':video}))
        exported = self.bridge.templates.export(imported['id'])
        with zipfile.ZipFile(exported['path']) as archive:
            self.assertEqual(archive.read('motion.mp4'), video)
            self.assertEqual(json.loads(archive.read('theme.json'))['animatedWallpaper'], 'motion.mp4')

    def test_new_version_replaces_library_card_and_keeps_previous_assets(self):
        first = self.library.import_archive(self.archive())
        before = self.bridge.templates.media(first['id'])['wallpaper']
        updated = self.library.import_archive(self.archive({'version': '1.1.0'}, name='new.tspack'))
        self.assertTrue(updated['updated'])
        self.assertEqual(first['id'], updated['id'])
        self.assertEqual(len(self.library.catalog()), 1)
        self.assertTrue(Path(before).is_file())
        with self.assertRaisesRegex(ValueError, '更新的套装'):
            self.library.import_archive(self.archive({'subtitle': 'changed'}, name='old.tspack'))
        self.assertEqual(self.library.catalog()[0]['version'], '1.1.0')

    def test_rejects_path_traversal_links_duplicate_names_and_executables(self):
        link = zipfile.ZipInfo('link.jpg')
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        cases = [('../outside.txt', b'bad'), ('C:/outside.txt', b'bad'), ('a\\outside.txt', b'bad'),
                 ('CON.txt', b'bad'), ('file.jpg:payload', b'bad'), ('bad. /x.jpg', b'bad'),
                 ('run.exe', b'MZ'), ('THEME.JSON', b'{}'), (link, b'../other')]
        for key, data in cases:
            with self.subTest(path=str(key)):
                with self.assertRaises(ValueError):
                    self.library.import_archive(self.archive(entries={key: data}))
                self.assertEqual(self.library.catalog(), [])
        self.assertFalse((self.root / 'outside.txt').exists())
        self.assertEqual(list(self.library.root.glob('import-*')), [])

    def test_rejects_missing_assets_bad_schema_and_incomplete_cursor_roles(self):
        for change in ({'schemaVersion': 2}, {'schemaVersion': True}, {'wallpaper': '../bad.jpg'},
                       {'wallpaper': 'absent.jpg'}, {'accent': 'red;display:none'}, {'version': '1.0'},
                       {'cursors': {'Arrow': 'pointer.cur'}}, {'icons': {'browser': {'file': 'missing.ico', 'matches': ['Chrome']}}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.library.import_archive(self.archive(change))
        self.assertEqual(self.library.catalog(), [])

    def test_size_limits_are_checked_before_commit(self):
        source = self.archive()
        for name, limit in (('MAX_ARCHIVE', 10), ('MAX_EXPANDED', 10), ('MAX_ENTRIES', 1)):
            with patch('theme_packages.' + name, limit), self.assertRaises(ValueError):
                self.library.import_archive(source)
        self.assertFalse(self.library.index.exists())

    def test_invalid_archive_preserves_existing_library(self):
        self.library.import_archive(self.archive())
        before = self.library.index.read_bytes()
        with self.assertRaises(ValueError):
            self.library.import_archive(self.archive({'version': '2.0.0', 'wallpaper': 'missing.jpg'}))
        self.assertEqual(before, self.library.index.read_bytes())

    def test_imported_pack_applies_real_shortcut_and_restores_after_restart(self):
        shortcut = self.desktop / 'Chrome.url'
        original = b'[InternetShortcut]\r\nURL=https://example.org\r\n'
        shortcut.write_bytes(original)
        exported = self.bridge.templates.export('wuthering-waves')
        imported = self.library.import_archive(exported['path'])
        current = ['']
        media_id = hashlib.sha256(self.wallpaper.read_bytes()).hexdigest() + '.jpg'
        media = self.bridge.store.directory / 'wallpapers' / media_id
        media.parent.mkdir()
        shutil.copyfile(self.wallpaper, media)
        with patch('template_adapter.current_wallpaper', side_effect=lambda: current[0]), patch('template_adapter.set_wallpaper', side_effect=lambda value: current.__setitem__(0, value)):
            result = self.bridge.templates.apply(imported['id'], media_id, True, False)
            self.assertEqual(result['iconsApplied'], 1)
            self.assertNotEqual(original, shortcut.read_bytes())
            reopened = DesktopBridge(self.bridge.store.directory, [(self.desktop, 'fixture')])
            reopened.templates.restore()
            self.assertEqual(original, shortcut.read_bytes())
            self.assertEqual(current[0], '')


if __name__ == '__main__':
    unittest.main()
