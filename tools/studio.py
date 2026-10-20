"""ThemeStudio Windows build CLI. Python + native compilers; no shell scripts.

Examples: python tools/studio.py setup
          python tools/studio.py build-installer
          python tools/studio.py compile-host --diagnostic
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import urllib.parse
import webbrowser
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv/Scripts/python.exe"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def version():
    return read_json(ROOT / "package.json")["version"]


def edition():
    return read_json(ROOT / "config/build-edition.json")


def runtime_lock():
    lock = read_json(ROOT / "config/runtime-distributions.json")
    if edition()["channel"] == "no-seelen" and "seelen" in lock:
        raise RuntimeError("The NoSeelen edition must not contain a Seelen engine.")
    return lock


def release_dir():
    return ROOT / "release" / ("ThemeStudio-" + version())


def installer_path():
    return ROOT / "installers" / edition()["installerName"].format(version=version())


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(arguments, **kwargs):
    # No interpolation, shell=True, execution-policy overrides, or terminal hosts.
    command = [str(item) for item in arguments]
    if not kwargs.get("capture_output"):
        kwargs.setdefault("stdout", sys.stdout)
        kwargs.setdefault("stderr", sys.stderr)
    return subprocess.run(command, cwd=ROOT, check=True,
                          creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                          **kwargs)


def python(*arguments, **kwargs):
    if not VENV.is_file():
        raise RuntimeError("Run python tools/studio.py setup first.")
    return run([VENV, "-X", "utf8", *arguments], **kwargs)


def node(*arguments, **kwargs):
    executable = shutil.which("node.exe")
    if not executable:
        raise RuntimeError("Node.js is required on the build machine.")
    return run([executable, *arguments], **kwargs)


def npm(*arguments):
    executable = shutil.which("node.exe")
    if not executable:
        raise RuntimeError("Install Node.js before setup.")
    # Use npm's JS entrypoint directly, avoiding .cmd quoting and shell dispatch.
    candidates = [Path(executable).parent / "node_modules/npm/bin/npm-cli.js"]
    npm_command = shutil.which("npm.cmd")
    if npm_command:
        candidates.append(Path(npm_command).parent / "node_modules/npm/bin/npm-cli.js")
    entry = next((path for path in candidates if path.is_file()), None)
    if not entry:
        raise RuntimeError("npm-cli.js was not found alongside Node.js/npm.")
    return node(entry, *arguments)


def csc(output, sources, references=(), extra=(), gui=False):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    compiler = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
    return run([compiler, "/nologo", "/target:" + ("winexe" if gui else "exe"),
                "/platform:x64", "/optimize+", "/out:" + str(output),
                *["/r:" + str(item) for item in references], *extra, *sources])


def verify_signature(path, publisher=None):
    source = ROOT / "tools/native/VerifySignature.cs"
    helper = ROOT / "build/native/VerifySignature.exe"
    if not helper.exists() or helper.stat().st_mtime < source.stat().st_mtime:
        csc(helper, [source], ["System.dll", "System.Web.Extensions.dll"])
    result = run([helper, Path(path).resolve(), *([publisher] if publisher else [])],
                 capture_output=True, text=True, encoding="utf-8")
    report = json.loads(result.stdout)
    if not report["valid"]:
        raise RuntimeError("Authenticode validation failed: " + str(path))
    return report


def pinned_download(url, expected_hash, destination, timeout=180):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256(destination) != expected_hash.lower():
            raise RuntimeError(f"Pinned file hash mismatch; retained for inspection: {destination}")
        return destination
    temporary = destination.with_name(destination.name + ".download")
    request = urllib.request.Request(url, headers={"User-Agent": "ThemeStudio-build"})
    with urllib.request.urlopen(request, timeout=timeout) as response, temporary.open("wb") as output:
        shutil.copyfileobj(response, output)
    if sha256(temporary) != expected_hash.lower():
        raise RuntimeError(f"Downloaded hash mismatch; retained for inspection: {temporary}")
    temporary.replace(destination)
    return destination


def extract_zip(archive, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive) as source:
        for entry in source.infolist():
            target = (destination / entry.filename).resolve()
            if not target.is_relative_to(destination):
                raise ValueError("Archive path escapes destination: " + entry.filename)
        source.extractall(destination)


def setup():
    if not VENV.is_file():
        run([sys.executable, "-m", "venv", ROOT / ".venv"])
    python("-m", "pip", "install", "--disable-pip-version-check", "-r",
           "components/icon-workbench/build-requirements.txt")
    npm("ci", "--no-audit", "--no-fund")
    sdk = read_json(ROOT / "config/webview2-sdk.json")
    package = pinned_download(sdk["source"], sdk["sha256"],
                              ROOT / ".cache" / f"microsoft.web.webview2.{sdk['version']}.nupkg")
    extract_zip(package, ROOT / ".cache/webview2")
    print("Project-local dependencies are ready.")


def fetch_runtime(full=False):
    manifest = read_json(ROOT / ("config/webview2-runtime.json" if full else "config/webview2-bootstrapper.json"))
    filename = "MicrosoftEdgeWebView2RuntimeInstallerX64.exe" if full else "MicrosoftEdgeWebview2Setup.exe"
    path = pinned_download(manifest.get("source", manifest.get("url")), manifest["sha256"],
                           ROOT / ".cache/runtime" / filename, timeout=1200 if full else 180)
    verify_signature(path, "Microsoft Corporation")
    print(path)
    return path


def prepare_runtimes(extractor=None):
    locks = runtime_lock()
    cache = ROOT / ".cache/runtimes"
    if "seelen" in locks:
        seelen = locks["seelen"]
        msix = pinned_download(seelen["asset"], seelen["assetSha256"],
                               cache / "Seelen.UI_2.8.6.0_x64.Msix")
        engine = (cache / "seelen-engine").resolve()
        with zipfile.ZipFile(msix) as archive:
            for entry in archive.infolist():
                name = urllib.parse.unquote(entry.filename)
                if not name.startswith("static/") and name not in {
                    "seelen-ui.exe", "slu.exe", "slu-service.exe", "sluhk.dll", "SHA256SUMS", "SHA256SUMS.sig"
                }:
                    continue
                target = (engine / name).resolve()
                if not target.is_relative_to(engine):
                    raise ValueError("MSIX path escapes extraction directory.")
                if entry.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(entry) as source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
        for name, expected in seelen.get("upstreamFiles", seelen["files"]).items():
            if sha256(engine / name) != expected:
                raise RuntimeError("Pinned Seelen binary mismatch: " + name)
        if (engine / "AppxManifest.xml").exists():
            raise RuntimeError("Unpackaged Seelen must not contain package identity metadata.")
    manifest = locks["windhawk"]
    package = pinned_download(manifest["asset"], manifest["assetSha256"], cache / "windhawk_setup_offline.exe")
    verify_signature(package)
    extractor = extractor or shutil.which("7z.exe") or r"C:\Program Files\NVIDIA Corporation\NVIDIA App\7z.exe"
    if not Path(extractor).is_file():
        raise RuntimeError("Pass the full 7-Zip NSIS extractor path with --extractor.")
    destination = cache / "windhawk"
    run([extractor, "x", package, "-o" + str(destination), "-y", "-bso0", "-bsp0"])
    if not (destination / "Engine/2.0").exists():
        shutil.copytree(destination / "Engine/$R1", destination / "Engine/2.0")
    for name, expected in manifest["files"].items():
        if sha256(destination / name) != expected:
            raise RuntimeError("Pinned Windhawk binary mismatch: " + name)
    if not (destination / "Compiler/bin/clang++.exe").is_file():
        raise RuntimeError("Windhawk compiler missing.")
    build_native_actions()
    if locks.get("seelen", {}).get("variant"):
        python("tools/build-seelen-native.py", "all")
    print("Pinned Windhawk payload ready; no engine was started.")


def compile_host(diagnostic=False, target=None, tutorial=False):
    target = Path(target) if target else release_dir()
    name = "ThemeStudio.Diagnostic.exe" if diagnostic else "ThemeStudio.exe"
    extra = ["/win32icon:" + str(ROOT / "assets/brand/theme-studio.ico")]
    manifest = ROOT / "src/host/app.manifest"
    if diagnostic:
        diagnostic_manifest = ROOT / "build/native/diagnostic.manifest"
        diagnostic_manifest.parent.mkdir(parents=True, exist_ok=True)
        diagnostic_manifest.write_text(manifest.read_text(encoding="utf-8").replace(
            "requireAdministrator", "asInvoker"), encoding="utf-8")
        manifest = diagnostic_manifest
    extra.append("/win32manifest:" + str(manifest))
    if tutorial:
        extra.append("/define:TUTORIAL_MODE")
    csc(target / name, sorted((ROOT / "src/host").glob("*.cs")),
        ["System.dll", "System.Core.dll", "System.Drawing.dll", "System.Windows.Forms.dll",
         "System.Web.Extensions.dll", target / "Microsoft.Web.WebView2.Core.dll",
         target / "Microsoft.Web.WebView2.WinForms.dll"], extra, gui=True)
    shutil.copy2(ROOT / "src/host/ThemeStudio.exe.config", target / (name + ".config"))
    return target / name


def build_recovery(target=None):
    target = Path(target) if target else ROOT / "build/cursor-recovery"
    target.mkdir(parents=True, exist_ok=True)
    output = target / "AsusCursorRecovery.exe"
    csc(output, [ROOT / "src/recovery/AsusCursorRecovery.cs"],
        ["System.dll", "System.Core.dll", "System.Windows.Forms.dll", "System.Web.Extensions.dll"],
        gui=True)
    shutil.copy2(ROOT / "src/host/ThemeStudio.exe.config", target / "AsusCursorRecovery.exe.config")
    shutil.copy2(ROOT / "tools/asus-cursor-recovery/使用说明.txt", target / "使用说明.txt")
    for name in ("恢复天选姬指针.bat", "restore_asus_tx_cursor.bat"):
        shutil.copy2(ROOT / "tools/asus-cursor-recovery" / name, target / name)
    return output


def build_native_actions(target=None):
    target = Path(target) if target else ROOT / ".cache/runtimes/windhawk"
    output = target / "ThemeStudio.NativeActions.exe"
    csc(output, [ROOT / "src/native/ThemeStudio.NativeActions.cs"],
        ["System.dll", "System.Core.dll", "System.Management.dll", "System.Web.Extensions.dll"])
    copy(ROOT / "src/host/ThemeStudio.exe.config", target / "ThemeStudio.NativeActions.exe.config")
    write_json(ROOT / "build/native-actions.json", {"sha256": sha256(output)})
    return output


def copy(source, destination):
    source, destination = Path(source), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)


def audit_payload(folder, allow_seelen=False):
    folder = Path(folder)
    forbidden = [p.relative_to(folder).as_posix() for p in folder.rglob("*")
                 if p.is_file() and (p.suffix.lower() in {".ps1", ".psm1", ".psd1"} or
                    p.name.lower() in {"powershell.exe", "pwsh.exe"} or
                    (not allow_seelen and p.name.lower() in {"seelen-ui.exe", "slu.exe", "slu-service.exe", "sluhk.dll"}))]
    if forbidden:
        raise RuntimeError("Unexpected runtime payload: " + ", ".join(forbidden[:20]))
    return {"powershellFiles": 0, "seelenIncluded": (folder / "runtimes/seelen/seelen-ui.exe").exists(),
            "files": sum(1 for p in folder.rglob("*") if p.is_file())}


def promote_payload(stage, destination):
    stage, destination = Path(stage).resolve(), Path(destination).resolve()
    parent = (ROOT / "release").resolve()
    if (not stage.is_relative_to((ROOT / "build").resolve()) or
            not destination.is_relative_to(parent) or destination == parent):
        raise RuntimeError("Payload move escaped the checkout.")
    parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        previous = parent / (destination.name + "-previous-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
        destination.rename(previous)
    stage.rename(destination)


def package(skip_frontend=False):
    if not skip_frontend:
        node("--import", "tsx", "tools/build.ts")
    python("tools/collect-licenses.py")
    python("-m", "unittest", "discover", "-s", "components/icon-workbench/tests", "-q")
    python("-m", "PyInstaller", "--noconfirm", "--onedir", "--console", "--name", "ThemeStudio.Backend",
           "--hidden-import", "win32timezone", "--paths", "components/image-to-ico", "--distpath",
           "build/backend", "--workpath", "build/pyinstaller", "--specpath", "build/spec",
           "components/icon-workbench/desktop_bridge.py")
    # Start with an empty staging folder; old scripts/data cannot leak into the package.
    stage = ROOT / "build" / ("payload-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    stage.mkdir()
    sdk = ROOT / ".cache/webview2"
    copy(ROOT / "build/backend/ThemeStudio.Backend", stage / "backend")
    copy(ROOT / "dist", stage / "wwwroot")
    copy(ROOT / "licenses", stage / "licenses")
    copy(ROOT / "LICENSE", stage / "LICENSE")
    for name in ("Microsoft.Web.WebView2.Core.dll", "Microsoft.Web.WebView2.WinForms.dll"):
        copy(sdk / "lib/net462" / name, stage / name)
    copy(sdk / "runtimes/win-x64/native/WebView2Loader.dll", stage / "WebView2Loader.dll")
    for name in ("LICENSE.txt", "NOTICE.txt"):
        copy(sdk / name, stage / "licenses" / ("Microsoft-WebView2-" + name))
    compile_host(target=stage)
    copy(ROOT / "README.md", stage / "README.md")
    for source in ("docs/theme-pack-format.md", "docs/development/0.6.0-changes.md",
                   "docs/development/explorer-image-update.md", "docs/development/unified-appearance-update.md",
                   "docs/development/transparent-surfaces-update.md", "docs/development/explorer-header-splitter-update.md",
                   "docs/development/no-powershell-migration.md"):
        if (ROOT / source).exists():
            copy(ROOT / source, stage / "docs" / Path(source).name)
    if (ROOT / "docs/research/20261001").exists():
        copy(ROOT / "docs/research/20261001", stage / "docs/research/20261001")
    build_recovery(stage / "docs/asus-cursor-recovery")
    origin = ROOT / ".cache/runtimes/windhawk"
    destination = stage / "runtimes/windhawk"
    if not (origin / "Compiler/bin/clang++.exe").is_file():
        raise RuntimeError("Run prepare-runtimes first.")
    for name in ("windhawk.exe", "windhawk-cli.exe", "windhawk-core.dll", "windhawk-ui.exe", "windhawk-mod.exe",
                 "windhawk-mod-elevated.exe", "windhawk-mod-uiaccess.exe", "ModsRuntime", "Engine/2.0"):
        copy(origin / name, destination / name)
    shutil.copytree(origin / "Compiler", destination / "Compiler", ignore=shutil.ignore_patterns(
        "aarch64-w64-mingw32", "clangd.exe", "aarch64-w64-windows-gnu.cfg"))
    for library in (origin / "AppData/Engine/Mods").rglob("*"):
        if library.is_file() and (library.suffix == ".whl" or library.name == "windhawk-mod-shim.dll"):
            copy(library, destination / "AppData/Engine/Mods" / library.parent.name / library.name)
    helper = build_native_actions()
    copy(helper, destination / helper.name)
    copy(helper.with_suffix(".exe.config"), destination / (helper.name + ".config"))
    resources = stage / "resources"
    write_json(resources / "application.json", {"channel": edition()["channel"], "build": edition()["build"], "version": version()})
    distributions = runtime_lock()
    distributions["windhawk"]["nativeActionsSha256"] = sha256(helper)
    write_json(resources / "runtime-distributions.json", distributions)
    copy(ROOT / "vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/catalog.json", resources / "mod-catalog.json")
    for mod in (ROOT / "vendor/windhawk-mods/mods").iterdir():
        if mod.is_file():
            copy(mod, resources / "windhawk-mods" / mod.name)
    copy(ROOT / "components/explorer-skin/themestudio-explorer-background.wh.cpp",
         resources / "windhawk-mods/themestudio-explorer-background.wh.cpp")
    with_seelen = "seelen" in distributions
    if with_seelen:
        engine = ".cache/runtimes/seelen-native" if distributions["seelen"].get("variant") else ".cache/runtimes/seelen-engine"
        copy(ROOT / engine, stage / "runtimes/seelen")
        copy(ROOT / "vendor/Seelen-UI/src/static/themes", resources / "seelen-themes")
        copy(ROOT / "vendor/runtime-sources/Seelen-UI-2.8.6/LICENSE", stage / "licenses/Seelen-Runtime-2.8.6-AGPL.txt")
    audit = audit_payload(stage, with_seelen)
    destination = release_dir()
    # Preserve the previous build; never recursively delete a populated release.
    promote_payload(stage, destination)
    write_json(ROOT / "build/payload-audit.json", audit)
    print(destination / "ThemeStudio.exe")


def build_installer(skip_package=False):
    if not skip_package:
        package()
    source_lock = runtime_lock()
    audit_payload(release_dir(), "seelen" in source_lock)
    if source_lock.get("seelen", {}).get("variant"):
        native = read_json(release_dir() / "runtimes/seelen/native-build.json")
        shipped = read_json(release_dir() / "resources/runtime-distributions.json")["seelen"]
        if native["variant"] != source_lock["seelen"]["variant"] or shipped.get("variant") != native["variant"]:
            raise RuntimeError("Final installer must contain the requested native Seelen fork.")
        for name, expected in native["files"].items():
            if shipped["files"].get(name) != expected or sha256(release_dir() / "runtimes/seelen" / name) != expected:
                raise RuntimeError("Native Seelen payload differs from its build record: " + name)
    fetch_runtime()
    compiler = ROOT / ".tools/inno-6.7.3/ISCC.exe"
    run([compiler, "/Q", ROOT / "installer/ThemeStudio.iss"])
    installer = installer_path()
    digest = sha256(installer)
    installer.with_suffix(".exe.sha256").write_text(digest + "  " + installer.name + "\n", encoding="utf-8")
    write_json(ROOT / "build/installer-ready.json",
               {"path": str(installer), "sha256": digest, "version": version(), "build": edition()["build"]})
    print(installer)


def start_dev(no_browser=False):
    url = "http://127.0.0.1:4327"
    def health():
        try:
            with urllib.request.urlopen(url + "/health", timeout=2) as response:
                data = json.load(response)
        except (ConnectionError, TimeoutError, urllib.error.URLError):
            return None
        if data.get("app") != "theme-studio":
            raise RuntimeError("Port 4327 belongs to another application.")
        return data
    if not health():
        if not (ROOT / "dist/index.html").is_file():
            raise RuntimeError("Build the frontend first.")
        (ROOT / "build").mkdir(exist_ok=True)
        with (ROOT / "build/dev-stdout.log").open("ab") as stdout, (ROOT / "build/dev-stderr.log").open("ab") as stderr:
            process = subprocess.Popen([shutil.which("node.exe"), "--import", "tsx", "tools/dev-server.ts"],
                                       cwd=ROOT, stdout=stdout, stderr=stderr,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
        write_json(ROOT / "build/dev-process.json", {
            "pid": process.pid, "started": datetime.now(timezone.utc).isoformat(), "url": url})
        for _ in range(30):
            if process.poll() is not None:
                raise RuntimeError("Development server exited; inspect build/dev-stderr.log.")
            if health():
                break
            time.sleep(0.3)
        else:
            raise RuntimeError("Development server did not become ready.")
    if not no_browser:
        webbrowser.open(url)
    print(url)


def test_tools():
    python("-m", "unittest", "discover", "-s", "tests/python", "-v")
    python("tests/native-actions.test.py")
    output = ROOT / "build/native/AsusCursorRecoveryTest.exe"
    csc(output, [ROOT / "src/recovery/AsusCursorRecovery.cs", ROOT / "tests/AsusCursorRecoveryTest.cs"],
        ["System.dll", "System.Core.dll", "System.Windows.Forms.dll", "System.Web.Extensions.dll"],
        ["/main:AsusCursorRecoveryTest"])
    run([output])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup", "prepare-runtimes", "fetch-bootstrapper", "fetch-runtime",
        "package", "build-installer", "compile-host", "build-recovery", "build-native-actions", "start-dev", "check", "test",
        "test-backend", "test-tools", "build", "audit-payload"])
    parser.add_argument("--skip-frontend", action="store_true")
    parser.add_argument("--skip-package", action="store_true")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--extractor", type=Path)
    args = parser.parse_args()
    if args.command == "setup": setup()
    elif args.command == "prepare-runtimes": prepare_runtimes(args.extractor)
    elif args.command == "fetch-bootstrapper": fetch_runtime()
    elif args.command == "fetch-runtime": fetch_runtime(True)
    elif args.command == "package": package(args.skip_frontend)
    elif args.command == "build-installer": build_installer(args.skip_package)
    elif args.command == "compile-host": print(compile_host(args.diagnostic))
    elif args.command == "build-recovery": print(build_recovery())
    elif args.command == "build-native-actions": print(build_native_actions())
    elif args.command == "start-dev": start_dev(args.no_browser)
    elif args.command == "check": node("node_modules/typescript/bin/tsc", "--noEmit")
    elif args.command == "build": node("--import", "tsx", "tools/build.ts")
    elif args.command == "test": node("--import", "tsx", "--test", *sorted((ROOT / "tests").glob("*.test.ts")))
    elif args.command == "test-backend": python("-m", "unittest", "discover", "-s", "components/icon-workbench/tests", "-q")
    elif args.command == "test-tools": test_tools()
    elif args.command == "audit-payload": print(json.dumps(audit_payload(release_dir(), "seelen" in read_json(ROOT / "config/runtime-distributions.json"))))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        raise SystemExit(1)
