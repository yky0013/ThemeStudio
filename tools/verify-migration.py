"""Bind migration evidence to the final payload; never change system settings."""
import json
from pathlib import Path
import re
import subprocess

from studio import ROOT, audit_payload, edition, installer_path, read_json, release_dir, runtime_lock, sha256, version, write_json


def log(name):
    return (ROOT / name).read_text(encoding="utf-8-sig", errors="replace")


def unittest_counts(text):
    counts = [int(value) for value in re.findall(r"Ran (\d+) tests?", text)]
    if not counts or re.search(r"^FAILED\b", text, re.M) or len(re.findall(r"^OK\s*$", text, re.M)) < len(counts):
        raise RuntimeError("Unit test log is incomplete or contains failures.")
    return counts


def main():
    source_lock = runtime_lock()
    payload = release_dir()
    audit = audit_payload(payload, "seelen" in source_lock)
    audit["stagingFilesIncludingDiagnostics"] = audit.pop("files")
    frontend = log("frontend-final.log")
    tests = re.findall(r"tests (\d+)", frontend)
    passed = re.findall(r"pass (\d+)", frontend)
    if not tests or not passed or tests[-1] != passed[-1] or not re.search(r"fail 0\b", frontend):
        raise RuntimeError("Frontend tests did not all pass.")
    backend_log = ROOT / "backend-final.log"
    backend = unittest_counts(log(backend_log.name) if backend_log.exists() else log("final-build.log"))[-1]
    tools = unittest_counts(log("tools-final.log"))
    if len(tools) != 2 or "PASS: 13 OEM mappings" not in log("tools-final.log"):
        raise RuntimeError("Build/native helper tests or cursor recovery tests are missing.")
    candidates = sorted((ROOT / "qa/runtime").glob("preserve-theme-*/verification.json"))
    if not candidates:
        raise RuntimeError("No successful native UI verification record.")
    ui = read_json(candidates[-1])
    if not ui.get("passed") or not ui.get("appearanceUnchanged") or not ui.get("testedFiles"):
        raise RuntimeError("Native UI verification is incomplete.")
    for name, expected in ui["testedFiles"].items():
        if sha256(payload / name) != expected:
            raise RuntimeError("The payload changed after native UI verification: " + name)
    if not (payload / "docs/asus-cursor-recovery/AsusCursorRecovery.exe").is_file():
        raise RuntimeError("Native cursor recovery executable is missing.")
    actual_lock = read_json(payload / "resources/runtime-distributions.json")
    helper = payload / "runtimes/windhawk/ThemeStudio.NativeActions.exe"
    if sha256(helper) != actual_lock["windhawk"]["nativeActionsSha256"]:
        raise RuntimeError("Native action helper hash mismatch.")
    # Only the explicitly packaged roots/files are included; diagnostic executables are excluded.
    files = [payload / name for name in ("ThemeStudio.exe", "ThemeStudio.exe.config", "LICENSE", "README.md")]
    files += list(payload.glob("*.dll"))
    for directory in ("backend", "wwwroot", "resources", "runtimes", "licenses", "docs"):
        files += [path for path in (payload / directory).rglob("*") if path.is_file()]
    entries = [{"path": path.relative_to(payload).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}
               for path in sorted(files)]
    manifest_path = ROOT / "build/migration-payload-manifest.json"
    write_json(manifest_path, {"kind": "compiler-input-payload", "files": entries})
    native_record = None
    if "seelen" in source_lock:
        native_record = read_json(payload / "runtimes/seelen/native-build.json")
        if native_record["variant"] != actual_lock["seelen"].get("variant"):
            raise RuntimeError("Wrong Seelen variant in payload.")
        for name, expected in native_record["files"].items():
            if sha256(payload / "runtimes/seelen" / name) != expected or actual_lock["seelen"]["files"].get(name) != expected:
                raise RuntimeError("Seelen rebuild hash mismatch: " + name)
        for name, expected in native_record["nativeSourceSha256"].items():
            if sha256(ROOT / source_lock["seelen"]["sourceDirectory"] / name) != expected:
                raise RuntimeError("Native Seelen source differs from the compiled source: " + name)
    installer = installer_path()
    checksum = installer.with_suffix(".exe.sha256").read_text().split()[0]
    if checksum != sha256(installer):
        raise RuntimeError("Installer checksum mismatch.")
    evidence = ROOT / "docs/development/language-migration-validation"
    evidence.mkdir(parents=True, exist_ok=True)
    for name in ("frontend-final.log", "backend-final.log", "tools-final.log"):
        path = ROOT / name
        if path.exists():
            (evidence / (path.stem + ".txt")).write_bytes(path.read_bytes())
    if not backend_log.exists():
        (evidence / "backend-final.txt").write_text(f"Ran {backend} tests; OK. Source log: final-build.log\n", encoding="utf-8")
    summary = {
        "date": "2026-10-20", "version": version(), "build": edition()["build"], "channel": edition()["channel"],
        "localBuildBaseline": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "upstreamBaseCommit": subprocess.check_output(["git", "rev-parse",
            "origin/experiment/no-seelen-20261007" if edition()["channel"] == "no-seelen" else
            "origin/maintenance/0.5" if edition()["channel"] == "maintenance-0.5" else "origin/main"],
            cwd=ROOT, text=True).strip(),
        "installer": {"name": installer.name, "bytes": installer.stat().st_size, "sha256": sha256(installer)},
        "tests": {"frontend": int(tests[-1]), "backend": backend, "buildPipeline": tools[0],
                  "nativeActionsReadOnly": tools[1], "cursorRecovery": "passed",
                  "nativeUiChecks": ui["checks"], "nativeUiMode": ui["hostMode"], "appearanceUnchanged": True},
        "payload": {**audit, "packagedInputFiles": len(entries), "manifestSha256": sha256(manifest_path),
                    "scope": "Exact Inno Setup input roots, not an installed-system observation"},
        "nativeActionHelperSha256": sha256(helper),
        "seelenNativeBuild": native_record,
        "compatibility": "Explicit user-selected PowerShell terminal/script features remain available.",
        "notRun": ["Administrator install/uninstall lifecycle", "Live network enable/disable/reset",
                   "WindowsApps ACL modification", "All optional mods and all Windows versions"],
    }
    write_json(ROOT / "docs/development/no-powershell-verification.json", summary)
    print(json.dumps({"verified": True, "installer": installer.name, "payloadFiles": len(entries)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
