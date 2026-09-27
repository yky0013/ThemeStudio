from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pythoncom
from win32com.shell import shell
from PIL import Image
import backend
from backend import Assignment, IconStore, canonical, digest, shortcut_info


def make_link(path: Path, target=None):
    with backend.com_session():
        link = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
        link.SetPath(str(target or Path(os.environ['WINDIR']) / 'System32' / 'notepad.exe'))
        link.SetArguments('"C:\\测试目录\\资料 a.txt" /test')
        link.SetWorkingDirectory(os.environ['WINDIR'])
        link.SetDescription('带有参数的测试快捷方式')
        link.SetShowCmd(3)
        link.SetHotkey(0x0641)
        link.QueryInterface(pythoncom.IID_IPersistFile).Save(str(path), True)
    return path


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='icon-workbench-test-')
        self.folder = Path(self.temp.name) / '中文 路径'
        self.folder.mkdir()
        self.store = IconStore(self.folder / '资源 和 备份')
        self.link = make_link(self.folder / '测试软件.lnk')
        self.icon = self.folder / '测试软件.ico'
        Image.new('RGBA', (256, 256), '#6555DE').save(self.icon, sizes=[(16,16), (32,32), (48,48), (256,256)])
        self.other_icon = self.folder / '另一个图标.ico'
        Image.new('RGBA', (256, 256), '#19A891').save(self.other_icon)

    def tearDown(self):
        for path in self.folder.rglob('*'):
            if path.is_file():
                path.chmod(stat.S_IWRITE | stat.S_IREAD)
        self.temp.cleanup()

    def assignment(self, path=None, icon=None):
        path = path or self.link
        return Assignment(str(path), str(icon or self.icon), digest(path))

    def test_single_apply_preserves_launch_metadata_and_exact_restore(self):
        original = self.link.read_bytes()
        before = shortcut_info(self.link)
        result = self.store.apply([self.assignment()])
        entry = result['entries'][0]
        self.assertEqual(entry['status'], 'applied', entry)
        after = shortcut_info(self.link)
        self.assertEqual(before['details'], after['details'])
        self.assertEqual(after['icon_index'], 0)
        self.assertTrue(Path(after['icon_path']).is_file())
        restored = self.store.restore(result['id'])
        self.assertEqual(restored['entries'][0]['status'], 'restored')
        self.assertEqual(original, self.link.read_bytes())

    def test_batch_different_icons_and_per_item_restore(self):
        second = make_link(self.folder / '第二个软件.lnk')
        originals = [self.link.read_bytes(), second.read_bytes()]
        result = self.store.apply([self.assignment(), self.assignment(second, self.other_icon)])
        self.assertEqual([e['status'] for e in result['entries']], ['applied', 'applied'])
        self.assertNotEqual(shortcut_info(self.link)['icon_path'], shortcut_info(second)['icon_path'])
        self.store.restore(result['id'], [0])
        self.assertEqual(self.link.read_bytes(), originals[0])
        self.assertNotEqual(second.read_bytes(), originals[1])
        self.store.restore(result['id'], [1])
        self.assertEqual(second.read_bytes(), originals[1])

    def test_batch_failure_does_not_block_later_item(self):
        result = self.store.apply([Assignment(str(self.folder/'missing.lnk'), str(self.icon), 'none'), self.assignment()])
        self.assertEqual([e['status'] for e in result['entries']], ['failed', 'applied'])

    def test_stable_library_survives_deleted_source(self):
        metadata = self.store.import_icon(self.icon)
        self.icon.unlink()
        result = self.store.apply([self.assignment(icon=Path(metadata['path']))])
        self.assertEqual(result['entries'][0]['status'], 'applied')
        self.assertTrue(Path(shortcut_info(self.link)['icon_path']).is_file())

    def test_stale_selection_does_not_overwrite(self):
        assignment = self.assignment()
        with backend.com_session():
            link = backend.load_link(self.link)
            link.SetDescription('另一个程序的修改')
            link.QueryInterface(pythoncom.IID_IPersistFile).Save(str(self.link), True)
        current = self.link.read_bytes()
        result = self.store.apply([assignment])
        self.assertEqual(result['entries'][0]['status'], 'failed')
        self.assertEqual(self.link.read_bytes(), current)

    def test_restore_refuses_external_modification(self):
        result = self.store.apply([self.assignment()])
        with backend.com_session():
            link = backend.load_link(self.link)
            link.SetArguments('/new-user-arguments')
            link.QueryInterface(pythoncom.IID_IPersistFile).Save(str(self.link), True)
        changed = self.link.read_bytes()
        restored = self.store.restore(result['id'])
        self.assertEqual(restored['entries'][0]['status'], 'failed')
        self.assertEqual(self.link.read_bytes(), changed)

    def test_restore_history_newest_first(self):
        original = self.link.read_bytes()
        first = self.store.apply([self.assignment()])
        second = self.store.apply([self.assignment(icon=self.other_icon)])
        self.assertEqual(self.store.history()[0]['id'], second['id'])
        self.assertEqual(self.store.restore(first['id'])['entries'][0]['status'], 'failed')
        self.assertEqual(self.store.restore(second['id'])['entries'][0]['status'], 'restored')
        self.assertEqual(self.store.restore(first['id'])['entries'][0]['status'], 'restored')
        self.assertEqual(self.link.read_bytes(), original)

    def test_corrupt_ico_is_rejected_without_changes(self):
        self.icon.write_bytes(b'not an icon')
        original = self.link.read_bytes()
        result = self.store.apply([self.assignment()])
        self.assertEqual(result['entries'][0]['status'], 'failed')
        self.assertEqual(self.link.read_bytes(), original)

    def test_readonly_shortcut_is_untouched(self):
        original = self.link.read_bytes()
        self.link.chmod(stat.S_IREAD)
        result = self.store.apply([self.assignment()])
        self.assertEqual(result['entries'][0]['status'], 'failed')
        self.assertEqual(self.link.read_bytes(), original)

    def test_url_preserves_other_fields_sections_encoding_and_exact_restore(self):
        text = ('; 注释\r\n[InternetShortcut]\r\nURL=steam://rungameid/12345\r\n'
                'IconFile=C:\\Old.ico\r\nIconIndex=4\r\nHotKey=0\r\n; inside\r\n'
                '[Extra]\r\nUnknown=keep-me\r\n')
        for encoding in ['utf-8', 'utf-8-sig', 'utf-16']:
            with self.subTest(encoding=encoding):
                path = self.folder / f'{encoding}.url'
                original = text.encode(encoding)
                path.write_bytes(original)
                result = self.store.apply([self.assignment(path)])
                self.assertEqual(result['entries'][0]['status'], 'applied', result)
                updated = path.read_bytes().decode(encoding)
                self.assertIn('URL=steam://rungameid/12345\r\n', updated)
                self.assertIn('[Extra]\r\nUnknown=keep-me\r\n', updated)
                self.assertIn('; inside\r\n', updated)
                self.assertIn('HotKey=0\r\n', updated)
                self.store.restore(result['id'])
                self.assertEqual(path.read_bytes(), original)

    def test_minimal_url_without_trailing_newline(self):
        path = self.folder/'minimal.url'
        path.write_text('[InternetShortcut]\nURL=https://example.com/?q=100%25', encoding='utf-8')
        result = self.store.apply([self.assignment(path)])
        self.assertEqual(result['entries'][0]['status'], 'applied', result)
        self.assertEqual(shortcut_info(path)['details']['target'], 'https://example.com/?q=100%25')

    def test_staged_verification_failure_keeps_original(self):
        original_stage = self.store._stage_icon
        def bad_stage(src, dst, icon):
            original_stage(src, dst, icon)
            with backend.com_session():
                link = backend.load_link(dst)
                link.SetArguments('/bad')
                link.QueryInterface(pythoncom.IID_IPersistFile).Save(str(dst), True)
        original = self.link.read_bytes()
        with patch.object(self.store, '_stage_icon', side_effect=bad_stage):
            result = self.store.apply([self.assignment()])
        self.assertEqual(result['entries'][0]['status'], 'failed')
        self.assertEqual(self.link.read_bytes(), original)

    def test_prepared_journal_can_recover_after_restart(self):
        original = self.link.read_bytes()
        result = self.store.apply([self.assignment()])
        result['entries'][0]['status'] = 'prepared'
        backend.atomic_json(self.store.history_dir/result['id']/'manifest.json', result)
        reopened = IconStore(self.store.directory)
        restored = reopened.restore(result['id'])
        self.assertEqual(restored['entries'][0]['status'], 'restored')
        self.assertEqual(original, self.link.read_bytes())

    def test_corrupt_backup_blocks_restore(self):
        result = self.store.apply([self.assignment()])
        entry = result['entries'][0]
        backup = self.store.history_dir/result['id']/entry['backup']
        backup.write_bytes(b'corrupt backup')
        current = self.link.read_bytes()
        self.assertEqual(self.store.restore(result['id'])['entries'][0]['status'], 'failed')
        self.assertEqual(self.link.read_bytes(), current)

    def test_exact_match_avoids_ambiguous_name(self):
        shortcuts = [shortcut_info(self.link)]
        first = self.store.import_icon(self.icon)
        self.assertEqual(backend.match_icons(shortcuts, [first])[canonical(self.link)], first['path'])
        second = self.store.import_icon(self.other_icon)
        second['name'] = self.icon.name
        self.assertEqual(backend.match_icons(shortcuts, [first, second]), {})
        first['name'] = '测试软件 候选.ico'
        self.assertEqual(backend.match_icons(shortcuts, [first]), {})

    def test_duplicate_shortcut_batch_rejected(self):
        with self.assertRaises(ValueError):
            self.store.apply([self.assignment(), self.assignment()])

    def test_store_write_lock_blocks_parallel_mutation(self):
        other = IconStore(self.store.directory)
        with self.store.lock():
            with self.assertRaises(RuntimeError):
                other.apply([self.assignment()])

    def test_scan_deduplicates_and_reports_bad_file(self):
        (self.folder/'bad.lnk').write_bytes(b'bad')
        rows, errors = backend.scan_shortcuts([(self.folder, '测试')], [self.link])
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(errors), 1)

    def test_public_desktop_acl_denial_fails_promptly(self):
        with patch('backend.os.open', side_effect=PermissionError('Access denied')) as call:
            with self.assertRaises(PermissionError):
                backend.new_sibling(self.link, '.icon-workbench-')
        self.assertEqual(call.call_count, 1)

    def test_data_directory_is_always_absolute(self):
        with patch('os.getcwd', return_value=str(self.folder)):
            store = IconStore('relative-storage')
        self.assertTrue(store.directory.is_absolute())
        self.assertTrue(Path(store.import_icon(self.icon)['path']).is_absolute())


if __name__ == '__main__':
    unittest.main(verbosity=2)
