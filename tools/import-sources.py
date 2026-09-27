"""Import fixed local source revisions into the new repository, without nested Git repos."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import zipfile

project = Path(__file__).resolve().parents[1]
original = project.parent
vendor = project / 'vendor'
vendor.mkdir(exist_ok=True)
cache = project / '.cache'
cache.mkdir(exist_ok=True)
sources = []
for name, source_manifest in [('Seelen-UI', 'seelen-source.json'), ('windhawk', 'windhawk-source.json'), ('windhawk-mods', 'windhawk-mods-source.json')]:
    target = vendor / name
    if target.exists():
        raise RuntimeError(f'Imported source already exists: {target}')
    source = original / name
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=source):
        raise RuntimeError(f'Commit or account for source changes before importing: {source}')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    archive = cache / (name + '-' + commit[:12] + '.zip')
    subprocess.run(['git', 'archive', '--format=zip', '--output', str(archive), commit], cwd=source, check=True)
    target.mkdir()
    with zipfile.ZipFile(archive) as package:
        for entry in package.infolist():
            if not (target / entry.filename).resolve().is_relative_to(target.resolve()):
                raise RuntimeError('Archive path is outside vendor directory')
        package.extractall(target)
    provenance = json.loads((original / 'upstream-snapshots' / source_manifest).read_text(encoding='utf-8-sig'))
    sources.append({'directory': 'vendor/' + name, 'localSnapshotCommit': commit, 'archiveSha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'upstream': provenance})
    print(name, commit, flush=True)

for name in ['seelen-source.json', 'windhawk-source.json', 'windhawk-mods-source.json']:
    folder = vendor / 'upstream-snapshots'
    folder.mkdir(exist_ok=True)
    shutil.copy2(original / 'upstream-snapshots' / name, folder / name)

components = project / 'components'
desktop = components / 'icon-workbench'
desktop.mkdir(parents=True)
for name in ['backend.py', 'cursor_adapter.py', 'desktop_bridge.py', 'native_icons.py', 'requirements.txt', 'build-requirements.txt', 'THIRD_PARTY.md']:
    shutil.copy2(original / 'icon-workbench' / name, desktop / name)
shutil.copytree(original / 'icon-workbench/licenses', desktop / 'licenses')
(components / 'image-to-ico').mkdir()
shutil.copy2(original / 'image-to-ico/converter.py', components / 'image-to-ico/converter.py')
tests = desktop / 'tests'
tests.mkdir()
for name in ['test_backend.py', 'test_desktop_bridge.py']:
    shutil.copy2(original / 'icon-workbench/tests' / name, tests / name)
(project / 'config').mkdir(exist_ok=True)
shutil.copy2(original / 'Seelen-UI/documentation/workbench-feature-policy.json', project / 'config/feature-policy.json')
(project / 'licenses').mkdir(exist_ok=True)
for source, destination in [('Seelen-UI/LICENSE', 'LICENSE'), ('Seelen-UI/LICENSE', 'licenses/Seelen-UI-AGPL-3.0.txt'), ('windhawk/LICENSE', 'licenses/Windhawk-GPL-3.0.txt'), ('windhawk-mods/README.md', 'licenses/Windhawk-mods-license-policy.md'), ('icon-workbench/licenses/Cursor-Palette.txt', 'licenses/Cursor-Palette-MIT.txt')]:
    shutil.copy2(original / source, project / destination)
(project / 'docs/source-imports.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
legacy = [{'path': p.relative_to(project).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in components.rglob('*') if p.is_file()]
(project / 'docs/desktop-source-imports.json').write_text(json.dumps(legacy, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
