"""Native shortcut round trips and input boundaries; unit tests never alter system cursors."""
import base64
import copy
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from backend import IconStore, digest, shortcut_info
from desktop_bridge import DesktopBridge
from test_backend import make_link
import cursor_adapter as ca


def upload_image(format='PNG', name='小猫.png'):
    stream = io.BytesIO()
    Image.new('RGBA' if format in {'PNG', 'WEBP', 'TIFF', 'ICO'} else 'RGB', (340, 160), '#9675e0').save(stream, format=format)
    return {'name': name, 'data': base64.b64encode(stream.getvalue()).decode()}


class DesktopBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.desktop = self.root / 'Desktop'
        self.desktop.mkdir()
        self.link = make_link(self.desktop / '测试软件.lnk')
        self.url = self.desktop / '测试网页.url'
        self.url.write_text('[InternetShortcut]\nURL=https://example.org/?q=中文\n', encoding='utf-8')
        self.bridge = DesktopBridge(self.root / 'data', [(self.desktop, '测试桌面')])

    def test_png_shortcuts_replace_and_exact_restore(self):
        before = {p: p.read_bytes() for p in (self.link, self.url)}
        details = shortcut_info(self.link)['details']
        icon = self.bridge.dispatch('icons.import', upload_image())
        state = self.bridge.state()
        result = self.bridge.dispatch('icons.apply', {'icon': icon['id'], 'items': state['shortcuts']})
        self.assertEqual([e['status'] for e in result['entries']], ['applied', 'applied'])
        after = shortcut_info(self.link)
        self.assertEqual(details, after['details'])
        with Image.open(after['icon_path']) as image:
            self.assertEqual(image.ico.sizes(), {(n, n) for n in (16, 24, 32, 48, 64, 128, 256)})
            self.assertEqual(image.ico.getimage((256, 256)).getpixel((0, 0))[3], 0)
        self.bridge.dispatch('icons.restore', {'id': result['id']})
        for p, content in before.items():
            self.assertEqual(p.read_bytes(), content)

    def test_common_formats_persist_after_uploaded_source_is_removed(self):
        for format, ext in [('PNG', '.png'), ('JPEG', '.jpg'), ('WEBP', '.webp'), ('BMP', '.bmp'), ('GIF', '.gif'), ('TIFF', '.tiff'), ('ICO', '.ico')]:
            with self.subTest(format=format):
                item = self.bridge.dispatch('icons.import', upload_image(format, '素材' + ext))
                self.assertTrue(item['preview'].startswith('data:image/png;base64,'))
                path = self.bridge.store.icons_dir / (item['id'] + '.ico')
                self.assertTrue(path.is_file())

    def test_stale_shortcut_cannot_be_overwritten(self):
        icon = self.bridge.dispatch('icons.import', upload_image())
        row = next(s for s in self.bridge.state()['shortcuts'] if s['kind'] == '.url')
        self.url.write_text('[InternetShortcut]\nURL=https://example.org/new\n', encoding='utf-8')
        changed = self.url.read_bytes()
        result = self.bridge.dispatch('icons.apply', {'icon': icon['id'], 'items': [row]})
        self.assertEqual(result['entries'][0]['status'], 'failed')
        self.assertEqual(self.url.read_bytes(), changed)

    def test_untrusted_names_and_resource_ids_are_rejected(self):
        for name in ['../escape.png', 'C:\\escape.png', 'file:stream.png', 'file.exe']:
            with self.assertRaises(ValueError):
                self.bridge.dispatch('icons.import', upload_image(name=name))
        with self.assertRaises(ValueError):
            self.bridge.dispatch('cursors.apply', {'roles': {r: 'C:\\escape.cur' for r in ca.ROLE_KEYS}, 'size': 32})
        with self.assertRaises(ValueError):
            self.bridge.dispatch('exec', {'command': 'anything'})

    def test_cursor_upload_and_role_matching_do_not_change_windows(self):
        before = ca.snapshot()
        source = Path(ca.default_scheme()['roles']['Arrow'])
        result = self.bridge.dispatch('cursors.import', {'files': [{'name': 'arrow.cur', 'data': base64.b64encode(source.read_bytes()).decode()}]})
        self.assertEqual(set(result['roles']), {'Arrow'})
        self.assertEqual(before, ca.snapshot())
        self.assertTrue(Path(self.bridge.resources[result['roles']['Arrow']]).is_file())

    def test_stale_cursor_snapshot_blocks_all_registry_writes(self):
        expected = ca.snapshot()
        changed = copy.deepcopy(expected)
        changed['cursors']['Arrow'] = ['changed.cur', 1]
        with patch.object(ca, 'snapshot', return_value=changed), patch.object(ca, 'write_values') as write:
            with self.assertRaisesRegex(ValueError, '重新读取'):
                self.bridge.cursors.apply({}, 32, expected_state=expected)
            write.assert_not_called()

    def test_recipe_export_stays_inside_new_projects_data_directory(self):
        recipe = {'schemaVersion': 1, 'name': '../中文主题', 'seelen': {'activeThemes': [], 'activeIconPacks': []}, 'windhawk': []}
        result = self.bridge.dispatch('recipe.export', recipe)
        target = Path(result['path'])
        self.assertEqual(target.parent, self.bridge.store.directory / 'exports')
        import json
        self.assertEqual(json.loads(target.read_text(encoding='utf-8')), recipe)
        with self.assertRaises(ValueError):
            self.bridge.dispatch('recipe.export', {'schemaVersion': 999})


if __name__ == '__main__':
    unittest.main()
