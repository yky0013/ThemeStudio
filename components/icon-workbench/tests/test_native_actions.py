"""Deployment of the native helper must preserve profiles and reject tampering."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_adapter import RuntimeAdapter


class NativeHelperDeploymentTests(unittest.TestCase):
    def test_verified_helper_is_installed_for_both_module_architectures(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            adapter = RuntimeAdapter(root / "profile", runtime_root=root / "runtimes")
            adapter.windhawk.mkdir(parents=True)
            source = adapter.windhawk / "ThemeStudio.NativeActions.exe"
            source.write_bytes(b"verified fixture")
            adapter.native_actions_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            adapter._install_native_actions()
            for architecture in ("32", "64"):
                output = adapter.windhawk_data / "Engine/Mods" / architecture / source.name
                self.assertEqual(output.read_bytes(), source.read_bytes())
            self.assertFalse(adapter.management.exists())
            self.assertFalse(adapter.windhawk_user.exists())

    def test_modified_helper_is_rejected_before_profile_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            adapter = RuntimeAdapter(root / "profile", runtime_root=root / "runtimes")
            adapter.windhawk.mkdir(parents=True)
            (adapter.windhawk / "ThemeStudio.NativeActions.exe").write_bytes(b"modified")
            adapter.native_actions_hash = "0" * 64
            with self.assertRaises(RuntimeError):
                adapter._install_native_actions()
            self.assertFalse(adapter.windhawk_data.exists())


if __name__ == "__main__":
    unittest.main()
