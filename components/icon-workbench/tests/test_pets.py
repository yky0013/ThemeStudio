from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pet_adapter import PetAdapter, validate_executable


class PetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.exe = self.root/'桌宠 空格.exe'
        shutil.copyfile(sys.executable, self.exe)
        self.adapter = PetAdapter(self.root/'data')

    def test_import_reopen_duplicate_remove_preserve_original_and_never_launch(self):
        original = self.exe.read_bytes()
        with patch('pet_adapter.subprocess.Popen', side_effect=AssertionError('Unexpected launch')):
            item = self.adapter.import_executable(str(self.exe))
            self.assertFalse(item['duplicate'])
            self.assertTrue(self.adapter.import_executable(str(self.exe))['duplicate'])
            reopened = PetAdapter(self.root/'data')
            self.assertEqual(len(reopened.state()['pets']), 1)
            reopened.remove(item['id'])
            self.assertEqual(reopened.state()['pets'], [])
        self.assertEqual(self.exe.read_bytes(), original)

    def test_fresh_state_does_not_create_user_files(self):
        self.assertEqual(self.adapter.state()['pets'], [])
        self.assertFalse(self.adapter.registry.parent.exists())

    def test_fake_exe_and_relative_path_rejected(self):
        for value in ['bad.exe', None, '', str(self.root/'fake.exe')]:
            (self.root/'fake.exe').write_bytes(b'MZ'+b'x'*150)
            with self.assertRaises((ValueError, FileNotFoundError, OSError)):
                validate_executable(value)
        self.assertFalse(self.adapter.registry.exists())

    def test_changed_binary_requires_reimport(self):
        item = self.adapter.import_executable(str(self.exe))
        with self.exe.open('ab') as stream: stream.write(b'updated')
        with patch('pet_adapter.subprocess.Popen') as start:
            with self.assertRaisesRegex(ValueError, '更新'):
                self.adapter.launch(item['id'])
            start.assert_not_called()

    def test_unknown_id_and_missing_binary_never_launch(self):
        item = self.adapter.import_executable(str(self.exe)); self.exe.unlink()
        self.assertFalse(self.adapter.state()['pets'][0]['available'])
        with patch('pet_adapter.subprocess.Popen') as start:
            with self.assertRaises(ValueError): self.adapter.launch('../anything')
            with self.assertRaises(FileNotFoundError): self.adapter.launch(item['id'])
            start.assert_not_called()

    def test_running_pet_not_launched_twice(self):
        item = self.adapter.import_executable(str(self.exe))
        with patch('pet_adapter.process_images', return_value=[(42,str(self.exe))]), patch('pet_adapter.subprocess.Popen') as start:
            self.assertTrue(self.adapter.launch(item['id'])['alreadyRunning'])
            start.assert_not_called()

    def test_launch_uses_explorer_shortcut_without_arguments(self):
        item = self.adapter.import_executable(str(self.exe))
        shell = MagicMock()
        with patch('pet_adapter.process_images', return_value=[]), patch('pet_adapter.win32com.client.Dispatch', return_value=shell), patch('pet_adapter.subprocess.Popen') as start:
            self.assertTrue(self.adapter.launch(item['id'])['requested'])
            shortcut = shell.CreateShortcut.return_value
            self.assertEqual(shortcut.TargetPath, str(self.exe))
            self.assertEqual(shortcut.WorkingDirectory, str(self.exe.parent))
            self.assertEqual(shortcut.Arguments, '')
            self.assertTrue(start.call_args.args[0][0].lower().endswith('explorer.exe'))
            self.assertTrue(start.call_args.args[0][1].endswith('.lnk'))
