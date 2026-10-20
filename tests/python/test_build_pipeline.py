"""Behavioral guards for the replacement build pipeline."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("studio", ROOT / "tools/studio.py")
studio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(studio)


class BuildPipelineTests(unittest.TestCase):
    def test_unicode_archive_path_and_contents(self):
        with tempfile.TemporaryDirectory(prefix="ThemeStudio 测试 ") as folder:
            root = Path(folder)
            archive = root / "输入 文件.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("目录/文件.txt", "content")
            studio.extract_zip(archive, root / "output")
            self.assertEqual((root / "output/目录/文件.txt").read_text(), "content")

    def test_archive_escape_rejected_before_writing_any_entry(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / "unsafe.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("valid.txt", "ok")
                output.writestr("../outside.txt", "bad")
            with self.assertRaises(ValueError):
                studio.extract_zip(archive, root / "output")
            self.assertFalse((root / "output/valid.txt").exists())
            self.assertFalse((root / "outside.txt").exists())

    def test_hash_mismatch_keeps_original_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "payload.exe"
            path.write_bytes(b"original")
            with patch.object(studio.urllib.request, "urlopen", side_effect=AssertionError("network")):
                with self.assertRaises(RuntimeError):
                    studio.pinned_download("https://example.invalid", "0" * 64, path)
            self.assertEqual(path.read_bytes(), b"original")

    def test_verified_cache_is_reused_offline(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "payload.exe"
            path.write_bytes(b"verified")
            with patch.object(studio.urllib.request, "urlopen", side_effect=AssertionError("network")):
                self.assertEqual(studio.pinned_download("unused", hashlib.sha256(b"verified").hexdigest(), path), path)

    def test_stale_powershell_and_seelen_payloads_block_packaging(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "docs").mkdir()
            (root / "docs/restore.PS1").write_text("stale")
            with self.assertRaisesRegex(RuntimeError, "restore.PS1"):
                studio.audit_payload(root)
            (root / "docs/restore.PS1").unlink()
            (root / "slu.exe").write_bytes(b"stale")
            with self.assertRaisesRegex(RuntimeError, "slu.exe"):
                studio.audit_payload(root)

    def test_native_payload_is_allowed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "AsusCursorRecovery.exe").write_bytes(b"native")
            self.assertEqual(studio.audit_payload(root)["files"], 1)

    def test_process_arguments_are_not_interpreted_by_a_shell(self):
        with patch.object(studio.subprocess, "run") as process:
            studio.run(["C:/Program Files/tool.exe", "a & b", "'quoted'", "中文 路径"])
            self.assertEqual(process.call_args.args[0][-3:], ["a & b", "'quoted'", "中文 路径"])
            self.assertNotIn("shell", process.call_args.kwargs)
            self.assertTrue(process.call_args.kwargs["check"])

    def test_json_handles_bom_without_changing_unicode(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "file.json"
            path.write_text('{"value":"中文"}', encoding="utf-8-sig")
            self.assertEqual(studio.read_json(path), {"value": "中文"})

    def test_first_build_and_rebuild_preserve_previous_payload(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(studio, "ROOT", Path(folder)):
            root = Path(folder)
            first = root / "build/first"
            first.mkdir(parents=True)
            (first / "app.exe").write_bytes(b"old")
            destination = root / "release/ThemeStudio"
            studio.promote_payload(first, destination)
            second = root / "build/second"
            second.mkdir()
            (second / "app.exe").write_bytes(b"new")
            studio.promote_payload(second, destination)
            self.assertEqual((destination / "app.exe").read_bytes(), b"new")
            previous = list((root / "release").glob("ThemeStudio-previous-*"))
            self.assertEqual(len(previous), 1)
            self.assertEqual((previous[0] / "app.exe").read_bytes(), b"old")

    def test_payload_move_cannot_escape_checkout(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(studio, "ROOT", Path(folder) / "project"):
            outside = Path(folder) / "outside"
            outside.mkdir()
            with self.assertRaises(RuntimeError):
                studio.promote_payload(outside, Path(folder) / "project/release/app")
            self.assertTrue(outside.is_dir())

    def test_noseelen_edition_rejects_a_regular_engine_manifest(self):
        with patch.object(studio, "edition", return_value={"channel": "no-seelen"}), \
             patch.object(studio, "read_json", return_value={"windhawk": {}, "seelen": {}}):
            with self.assertRaisesRegex(RuntimeError, "NoSeelen"):
                studio.runtime_lock()


if __name__ == "__main__":
    unittest.main()
