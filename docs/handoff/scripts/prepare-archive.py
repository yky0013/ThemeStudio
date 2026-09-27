from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(r"E:\desktop\windows").resolve()
OUT = ROOT / ".handoff"
REPOSITORIES = ("Seelen-UI", "windhawk", "windhawk-mods", "Cursor-Palette", "Lively-Wallpaper")


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def git(repo: Path, *arguments: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *arguments], check=True, capture_output=True).stdout


def archive(name: str, items: list[tuple[str, Path]], metadata: dict) -> dict:
    destination = OUT / name
    manifest = []
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as output:
        for logical, original in sorted(items):
            before = sha256(original)
            output.write(original, logical)
            after = sha256(original)
            if before != after:
                raise RuntimeError(f"File changed during backup: {original}")
            manifest.append({"path": logical, "bytes": original.stat().st_size, "sha256": before})
        metadata["files"] = manifest
        output.writestr("BACKUP-MANIFEST.json", json.dumps(metadata, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(destination) as saved:
        for entry in manifest:
            value = hashlib.sha256()
            with saved.open(entry["path"]) as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    value.update(chunk)
            if value.hexdigest() != entry["sha256"]:
                raise RuntimeError(f"Archive verification failed: {entry['path']}")
        if saved.testzip() is not None:
            raise RuntimeError("Archive CRC verification failed.")
    result = {"name": name, "bytes": destination.stat().st_size, "sha256": sha256(destination), "files": len(manifest), "verified": True}
    (OUT / (name + ".manifest.json")).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


OUT.mkdir(exist_ok=True)
exclusions = ["!theme-studio/**", "!.handoff/**", "!**/.git/**", "!**/node_modules/**", "!**/.venv/**", "!**/target/**", "!**/__pycache__/**", "!**/.cache/**", "!**/.tools/**", "!**/build/**", "!**/dist/**", "!**/portable/**", "!**/runtime/**", "!**/downloads/**", "!*.pyc", "!*.log", "!*.exe", "!*.dll", "!*.pdb", "!*.zip", "!*.7z", "!*.nupkg", "!*.msi"]
command = ["rg", "--files", "-uu", "-0"]
for exclusion in exclusions:
    command.extend(["-g", exclusion])
listed = subprocess.run(command, cwd=ROOT, check=True, capture_output=True).stdout
paths = {Path(os.fsdecode(raw)) for raw in listed.split(b"\0") if raw}
repositories = []
for name in REPOSITORIES:
    repo = ROOT / name
    tracked = git(repo, "ls-files", "-z")
    paths.update(Path(name) / Path(os.fsdecode(raw)) for raw in tracked.split(b"\0") if raw)
    paths.update(file.relative_to(ROOT) for file in (repo / ".git").rglob("*") if file.is_file())
    repositories.append({"directory": name, "head": git(repo, "rev-parse", "HEAD").decode().strip(), "status": git(repo, "status", "--short").decode("utf-8", errors="replace"), "shallow": git(repo, "rev-parse", "--is-shallow-repository").decode().strip(), "remotes": git(repo, "remote", "-v").decode()})

source_items = []
for relative in paths:
    path = ROOT / relative
    if path.is_file():
        resolved = path.resolve()
        if ROOT not in resolved.parents:
            raise RuntimeError(f"Source path escaped project: {path}")
        source_items.append((relative.as_posix(), path))
results = [archive("windows-legacy-workspace-20260927.zip", source_items, {"originalRoot": str(ROOT), "repositories": repositories, "scope": "Legacy sources, research, evidence, assets and original Git metadata. Current ThemeStudio is preserved in the main GitHub branch. Rebuildable caches, virtual environments, runtime installations and generated binaries are excluded; upstream tracked files are included regardless of extension."})]

app_names = ("ThemeStudio", "DesktopIconWorkbench", "Cursor-Palette", "Lively Wallpaper")
data_items = []
data_roots = []
for name in app_names:
    directory = Path(os.environ["LOCALAPPDATA"]) / name
    if not directory.exists():
        continue
    data_roots.append(str(directory))
    for file in directory.rglob("*"):
        if not file.is_file():
            continue
        relative = file.relative_to(directory)
        if name == "ThemeStudio" and relative.parts[0].lower() == "webview":
            continue
        if any(part.lower() in {"cache", "code cache", "gpucache", "crashpad", "logs"} for part in relative.parts):
            continue
        data_items.append((name + "/" + relative.as_posix(), file))
results.append(archive("windows-project-data-before-cleanup-20260927.zip", data_items, {"dataRoots": data_roots, "scope": "Project settings, imported assets and restore records before clean uninstall. Browser caches and logs are omitted. This is a private release asset."}))
(OUT / "backup-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
