"""Current-version verification without PowerShell.

smoke / preserve-theme / recovery do not change desktop appearance.
install requires an elevated terminal and refuses existing registrations.
"""
from __future__ import annotations
import argparse
import ctypes
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import winreg

from studio import ROOT, VENV, audit_payload, build_recovery, compile_host, csc, edition
from studio import installer_path, python, read_json, release_dir, run, sha256, version, write_json


def fresh_directory(label):
    directory = ROOT / "qa/runtime" / (label + "-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    (directory / "desktop").mkdir(parents=True)
    return directory


def native(executable, directory, script=None, timeout=55):
    executable = Path(executable).resolve()
    if not executable.is_relative_to(ROOT):
        raise RuntimeError("QA executable must be inside this checkout.")
    arguments = [executable, "--smoke-dir", directory]
    if script:
        arguments += ["--qa-script", script]
    run(arguments, timeout=timeout)
    report = read_json(directory / ("qa-result.json" if script else "native-runtime.json"))
    if not report.get("passed" if script else "ready"):
        raise RuntimeError("Native verification failed: " + json.dumps(report, ensure_ascii=False))
    return report


def smoke(executable=None):
    directory = fresh_directory("smoke")
    (directory / "desktop/Theme Studio test.url").write_text(
        "[InternetShortcut]\nURL=https://example.org/\n", encoding="utf-8")
    report = native(executable or release_dir() / "ThemeStudio.Diagnostic.exe", directory)
    print(json.dumps({"passed": True, "directory": str(directory), "version": report.get("version")}))


def preserve(executable=None):
    directory = fresh_directory("preserve-theme")
    application = Path(executable) if executable else release_dir() / "ThemeStudio.Diagnostic.exe"
    # Freeze expected edition capabilities from its source, not the displayed DOM.
    expected = {"pets": (ROOT / "src/app/pets.tsx").is_file(),
                "directMediaImport": "导入图片 / 动图 / 视频" in (ROOT / "src/app/templates.tsx").read_text(encoding="utf-8")}
    script = directory / "preserve-theme.js"
    script.write_text("const qaExpectedFeatures = " + json.dumps(expected) + ";\n" +
                      (ROOT / "tools/qa-native-preserve-theme.js").read_text(encoding="utf-8"), encoding="utf-8")
    python("tools/snapshot-appearance.py", directory / "before.json")
    try:
        report = native(application, directory, script)
    finally:
        python("tools/snapshot-appearance.py", directory / "after.json", "--compare", directory / "before.json")
    summary = {"passed": True, "checks": len(report["checks"]), "appearanceUnchanged": True,
               "directory": str(directory),
               "testedFiles": {
                   name: sha256(application.parent / name) for name in [
                       "backend/ThemeStudio.Backend.exe", "wwwroot/app.js",
                       "resources/runtime-distributions.json"
                   ]
               },
               "hostMode": "diagnostic-asInvoker" if "Diagnostic" in application.name else "explicit-executable",
               "hostSha256": sha256(application)}
    write_json(directory / "verification.json", summary)
    print(json.dumps(summary))


def recovery():
    executable = build_recovery()
    directory = fresh_directory("recovery")
    python("tools/snapshot-appearance.py", directory / "before.json")
    try:
        run([executable, "--verify-only", "--quiet", "--json-output", directory / "native.json"])
        result = read_json(directory / "native.json")
        if not result.get("success") or result["settingsChanged"] or result["verifiedFiles"] != 13:
            raise RuntimeError("Native recovery verification failed.")
        # A missing OEM directory must fail before writing any current-user setting.
        failure = subprocess.run([str(executable), "--verify-only", "--quiet", "--cursor-directory",
                                  str(directory / "missing"), "--json-output", str(directory / "missing.json")],
                                 creationflags=subprocess.CREATE_NO_WINDOW)
        if failure.returncode == 0 or read_json(directory / "missing.json")["success"]:
            raise RuntimeError("Missing OEM files were not rejected.")
    finally:
        python("tools/snapshot-appearance.py", directory / "after.json", "--compare", directory / "before.json")
    print(json.dumps({"passed": True, "appearanceUnchanged": True, "directory": str(directory)}))


def registration(app_id):
    key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\{" + app_id + "}_is1"
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, key, 0, winreg.KEY_READ | view) as opened:
                    return {winreg.EnumValue(opened, i)[0]: winreg.EnumValue(opened, i)[1]
                            for i in range(winreg.QueryInfoKey(opened)[1])}
            except FileNotFoundError:
                pass
    return None


def install():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise RuntimeError("Installer lifecycle QA needs an administrator terminal; no installation was attempted.")
    identity = edition()
    if registration(identity["appId"]):
        raise RuntimeError("Existing user installation is registered; refusing to overwrite it for QA.")
    directory = fresh_directory("installer")
    destination = (directory / "安装 位置/ThemeStudio").resolve()
    if not destination.is_relative_to(directory.resolve()):
        raise RuntimeError("QA install directory escaped its root.")
    sentinel = Path(os.environ["LOCALAPPDATA"]) / identity["dataDirectory"] / ("retention-" + directory.name + ".txt")
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text("ThemeStudio installer QA retention marker", encoding="utf-8")
    python("tools/snapshot-appearance.py", directory / "before.json")
    summary = {"passed": False, "installerSha256": sha256(installer_path()), "stages": []}
    try:
        for stage in ("install", "reinstall"):
            run([installer_path(), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-", "/TASKS=",
                 "/DIR=" + str(destination), "/GROUP=ThemeStudio QA " + directory.name,
                 "/LOG=" + str(directory / (stage + ".log"))], timeout=300)
            record = registration(identity["appId"])
            if not record or Path(record["InstallLocation"]).resolve() != destination or record["DisplayVersion"] != version():
                raise RuntimeError("Installer registration does not match the QA copy.")
            python("tools/snapshot-appearance.py", directory / (stage + ".json"), "--compare", directory / "before.json")
            summary["stages"].append(stage)
        for item in release_dir().rglob("*"):
            relative = item.relative_to(release_dir())
            if item.is_file() and "Diagnostic" not in item.name:
                installed = destination / relative
                if not installed.is_file() or sha256(item) != sha256(installed):
                    raise RuntimeError("Installed payload mismatch: " + str(relative))
        audit_payload(destination, "seelen" in read_json(ROOT / "config/runtime-distributions.json"))
        native(destination / "ThemeStudio.exe", fresh_directory("installed-smoke"))
        record = registration(identity["appId"])
        if not record or Path(record["InstallLocation"]).resolve() != destination:
            raise RuntimeError("QA registration changed; refusing uninstall.")
        run([destination / "unins000.exe", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
             "/LOG=" + str(directory / "uninstall.log")], timeout=300)
        if registration(identity["appId"]) or (destination / "ThemeStudio.exe").exists() or not sentinel.is_file():
            raise RuntimeError("Uninstall/retention verification failed.")
        python("tools/snapshot-appearance.py", directory / "uninstall.json", "--compare", directory / "before.json")
        summary.update(passed=True, payloadHashesMatch=True, userDataRetained=True, appearanceUnchanged=True)
        summary["stages"].append("uninstall")
        if sentinel.read_text(encoding="utf-8") == "ThemeStudio installer QA retention marker":
            sentinel.unlink()
    finally:
        write_json(directory / "verification.json", summary)
    print(json.dumps(summary))


def memory(executable=None):
    import win32com.client
    directory = fresh_directory("memory")
    executable = executable or release_dir() / "ThemeStudio.Diagnostic.exe"
    app = subprocess.Popen([str(executable), "--smoke-dir", str(directory), "--qa-script", str(ROOT / "tools/qa-memory.js")],
                           creationflags=subprocess.CREATE_NO_WINDOW)
    wmi = win32com.client.GetObject("winmgmts:")
    samples = []
    for second in range(1, 23):
        time.sleep(1)
        processes = list(wmi.ExecQuery("SELECT ProcessId,ParentProcessId,Name,WorkingSetSize FROM Win32_Process"))
        ids = {app.pid}
        while True:
            children = {int(p.ProcessId) for p in processes if int(p.ParentProcessId) in ids}
            if children.issubset(ids):
                break
            ids |= children
        rows = [{"pid": int(p.ProcessId), "name": p.Name, "working_set_bytes": int(p.WorkingSetSize or 0)}
                for p in processes if int(p.ProcessId) in ids]
        samples.append({"second": second, "working_set_mib": round(sum(p["working_set_bytes"] for p in rows) / 1048576, 2),
                        "processes": rows})
        if app.poll() is not None:
            break
    if app.poll() is None:
        raise RuntimeError("Memory measurement still running; inspect PID " + str(app.pid))
    report = {"metric": "sum of working sets; shared pages may be counted more than once",
              "samples": samples, "exitCode": app.returncode}
    write_json(directory / "memory.json", report)
    print(directory / "memory.json")


def tutorial():
    target = ROOT / "qa/runtime/tutorial-app"
    shutil.copytree(release_dir(), target, dirs_exist_ok=True)
    compile_host(target=target, tutorial=True)
    python("tools/tutorial-fixtures.py")
    print(target / "ThemeStudio.exe")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["smoke", "preserve-theme", "recovery", "install", "memory", "tutorial", "native-mods"])
    parser.add_argument("--executable", type=Path)
    args = parser.parse_args()
    if args.command == "smoke": smoke(args.executable)
    elif args.command == "preserve-theme": preserve(args.executable)
    elif args.command == "recovery": recovery()
    elif args.command == "install": install()
    elif args.command == "memory": memory(args.executable)
    elif args.command == "tutorial": tutorial()
    elif args.command == "native-mods": python("tools/verify-native-mods.py")


if __name__ == "__main__":
    # WMI is optional for memory QA, loaded from this checkout's own dependencies.
    if Path(sys.executable).resolve() != VENV.resolve() and VENV.is_file():
        raise SystemExit(subprocess.call([str(VENV), "-X", "utf8", str(Path(__file__).resolve()), *sys.argv[1:]]))
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        raise SystemExit(1)
