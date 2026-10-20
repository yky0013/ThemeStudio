"""Read-only acceptance tests for ThemeStudio.NativeActions.exe.

The tests compile the helper in a temporary directory and exercise only
`--dry-run`/`--report`, plus a mutex-busy call that exits before WMI access.
They never invoke adapter Enable/Disable, ipconfig, takeown, or icacls.
"""
import json
import ctypes
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CSCDIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Microsoft.NET" / "Framework64" / "v4.0.30319"
CSC = CSCDIR / "csc.exe"
SYSTEM_MANAGEMENT = CSCDIR / "System.Management.dll"
SYSTEM_SECURITY = CSCDIR / "System.Security.dll"
SYSTEM_WEB_EXTENSIONS = CSCDIR / "System.Web.Extensions.dll"
SOURCE = ROOT / "src" / "native" / "ThemeStudio.NativeActions.cs"


class NativeActionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="themestudio-native-actions-")
        cls.executable = Path(cls.temp.name) / "ThemeStudio.NativeActions.exe"
        command = [
            str(CSC), "/nologo", "/target:exe", "/platform:x64", "/optimize+",
            "/out:" + str(cls.executable),
            "/r:System.dll", "/r:System.Core.dll",
            "/r:" + str(SYSTEM_MANAGEMENT),
            "/r:" + str(SYSTEM_SECURITY),
            "/r:" + str(SYSTEM_WEB_EXTENSIONS),
            str(SOURCE),
        ]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        if result.returncode:
            raise RuntimeError("csc failed:\n" + result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_helper(self, *args):
        return subprocess.run(
            [str(self.executable), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_network_dry_runs_verify_schema_without_invoking_methods(self):
        for action in ("network-enable", "network-disable", "network-reset"):
            with self.subTest(action=action):
                result = self.run_helper(action, "--dry-run", "--report")
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                self.assertTrue(report["ok"])
                self.assertTrue(report["dryRun"])
                self.assertTrue(report["schemaValid"])
                self.assertTrue(all(not item["invoked"] for item in report["adapters"]))
                self.assertNotIn("completed", " ".join(report["events"]))

    def test_windowsapps_dry_run_does_not_run_security_tools(self):
        result = self.run_helper("windowsapps-access", "--dry-run", "--report")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["ok"])
        self.assertTrue(report["dryRun"])
        events = " ".join(report["events"])
        self.assertIn("would run takeown.exe", events)
        self.assertIn("would run icacls.exe", events)
        self.assertNotIn("takeown.exe completed", events)
        self.assertNotIn("icacls.exe completed", events)

    def test_only_fixed_actions_are_accepted(self):
        result = self.run_helper("invalid-action", "--dry-run", "--report")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unsupported action", result.stderr)

    def test_extra_payload_or_path_is_rejected(self):
        for extra in (r"C:\temp\payload", "arbitrary-command"):
            with self.subTest(extra=extra):
                result = self.run_helper("network-enable", extra, "--dry-run", "--report")
                self.assertEqual(result.returncode, 2)
                self.assertIn("Only one fixed action", result.stderr)

    def test_busy_mutex_returns_without_wmi_or_network_changes(self):
        # Even if the mutex regresses, the helper's non-elevated gate must
        # prevent this acceptance test from ever changing a network adapter.
        if ctypes.windll.shell32.IsUserAnAdmin():
            self.skipTest("Run this busy-guard probe without administrator privileges.")
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_bool
        kernel32.ReleaseMutex.argtypes = [ctypes.c_void_p]
        kernel32.ReleaseMutex.restype = ctypes.c_bool
        mutex_name = r"Local\ThemeStudio.NativeActions.Network"
        handle = kernel32.CreateMutexW(None, True, mutex_name)
        self.assertTrue(handle)
        try:
            result = self.run_helper("network-enable", "--report")
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertFalse(report["ok"])
            self.assertIn("already running", report["error"])
            self.assertIn("network mutex busy", report["events"])
            self.assertEqual(report["adapters"], [])
        finally:
            kernel32.ReleaseMutex(handle)
            kernel32.CloseHandle(handle)

    def test_a_category_sources_have_no_power_shell_or_arbitrary_shell_path(self):
        net_toggle = (ROOT / "vendor" / "windhawk-mods" / "mods" / "net-toggle.wh.cpp").read_text(encoding="utf-8")
        uwp_assets = (ROOT / "vendor" / "windhawk-mods" / "mods" / "uwp-assets-redirect.wh.cpp").read_text(encoding="utf-8")
        helper = SOURCE.read_text(encoding="utf-8")
        for marker in ("powershell", "Get-NetAdapter", "Enable-NetAdapter", "Disable-NetAdapter", "Start-Sleep", "RunPowerShellCommand"):
            self.assertNotIn(marker.lower(), net_toggle.lower())
        for marker in ("powershell", "Start-Process", "g_ownership_command"):
            self.assertNotIn(marker.lower(), uwp_assets.lower())
        self.assertIn("ThemeStudio.NativeActions.exe", net_toggle)
        self.assertIn("ThemeStudio.NativeActions.exe", uwp_assets)
        for interpreter in ('"powershell.exe"', '"pwsh.exe"', '"cmd.exe"'):
            self.assertNotIn(interpreter, helper.lower())


if __name__ == "__main__":
    unittest.main()
