"""Keep the exact fix recoverable inside the single delivered installer.

Only source files and public validation summaries enter this archive. Private
appearance snapshots, user data, caches, and build outputs stay outside it.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

root = Path(__file__).resolve().parents[1]
paths = ['README.md', 'package.json', 'package-lock.json', 'src', 'components', 'installer', 'tests', 'tools', 'assets', 'vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench', 'vendor/Seelen-UI/src/ui/react/settings/i18n/translations/workbench.en.yml', 'vendor/Seelen-UI/src/ui/react/settings/i18n/translations/workbench.zh-CN.yml', 'docs/development/0.4.1-verification.json', 'docs/development/0.5.0-verification.json', 'docs/development/0.5.0-asset-manifest.json', 'docs/guide']
changed = subprocess.check_output(['git', '-c', 'core.safecrlf=false', 'diff', '--name-only', '-z', 'HEAD', '--', *paths], cwd=root)
added = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z', '--', *paths], cwd=root)
names = sorted(set(name for name in (changed + added).decode('utf-8').split('\0') if name))
version = json.loads((root / 'package.json').read_text())['version']
output = root / 'release' / ('ThemeStudio-' + version) / 'docs' / ('source-fix-' + version + '.zip')
base = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root).decode().strip()
manifest = {'baseRepository': 'https://github.com/yky0013/ThemeStudio', 'baseCommit': base, 'version': version, 'files': []}
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name in names:
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('Unsupported source change: ' + name)
        content = path.read_bytes()
        manifest['files'].append({'path': name, 'sha256': hashlib.sha256(content).hexdigest()})
        archive.writestr('updated-source/' + name, content)
    archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    archive.writestr('RESTORE.txt', 'Check out baseCommit from baseRepository in manifest.json, then copy updated-source/ over that checkout.\nThis preserves the complete source changes for this version even when the development checkout is removed.\nBuild with tools/setup.ps1, tools/prepare-runtimes.ps1, tools/fetch-bootstrapper.ps1, and tools/build-installer.ps1.\nNo personal appearance snapshots are included.\n')
with zipfile.ZipFile(output) as archive:
    for item in manifest['files']:
        assert hashlib.sha256(archive.read('updated-source/' + item['path'])).hexdigest() == item['sha256']
print(json.dumps({'sourceFiles': len(names), 'baseCommit': base, 'archiveBytes': output.stat().st_size}))
