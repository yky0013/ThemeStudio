"""Copy unmodified dependency notices beside the redistributable application."""
from pathlib import Path
import importlib.metadata as metadata
import json
import re
import shutil
import sys

project = Path(__file__).resolve().parents[1]
destination = project / 'licenses/third-party'
destination.mkdir(parents=True, exist_ok=True)
records = []
name_pattern = re.compile(r'license|copying|notice', re.I)

def collect(name, version, files, origin):
    folder = destination / re.sub(r'[^\w.-]', '_', name + '-' + version)
    folder.mkdir(exist_ok=True)
    copied = []
    for index, source in enumerate(sorted(set(files))):
        target = folder / (str(index + 1) + '-' + source.name)
        shutil.copy2(source, target)
        copied.append(target.relative_to(project).as_posix())
    records.append({'name': name, 'version': version, 'origin': origin, 'notices': copied})

bundle = json.loads((project / 'build/bundle-inputs.json').read_text(encoding='utf-8'))
packages = set()
for filename in bundle['inputs']:
    parts = Path(filename).parts
    if 'node_modules' not in parts:
        continue
    i = max(i for i, part in enumerate(parts) if part == 'node_modules')
    end = i + (3 if parts[i + 1].startswith('@') else 2)
    packages.add(project / Path(*parts[:end]))
for package in sorted(packages):
    info = json.loads((package / 'package.json').read_text(encoding='utf-8'))
    files = [file for file in package.iterdir() if file.is_file() and name_pattern.search(file.name)]
    origin = 'bundled frontend package'
    if not files and info['name'] == 'is-mobile':
        files = [package / 'README.md']
        origin += '; full MIT notice is embedded in README'
    if not files and info['name'] == '@ant-design/icons-svg':
        files = [project / 'node_modules/@ant-design/icons/LICENSE']
        origin += '; shared repository LICENSE, verified against github.com/ant-design/ant-design-icons/blob/master/LICENSE'
    collect(info['name'], info['version'], files, origin)
for name in ['Pillow', 'pywin32', 'pyinstaller', 'altgraph', 'packaging', 'pefile', 'pywin32-ctypes']:
    distribution = metadata.distribution(name)
    files = [Path(distribution.locate_file(file)) for file in distribution.files or [] if name_pattern.search(Path(file).name)]
    collect(name, distribution.version, [f for f in files if f.is_file()], 'Python runtime / packaging component')
collect('Python', '.'.join(map(str, sys.version_info[:3])), [Path(sys.base_prefix) / 'LICENSE.txt'], 'bundled Python runtime')
compiler_license = project / '.tools/inno-6.7.3/license.txt'
if compiler_license.exists():
    collect('Inno-Setup', '6.7.3', [compiler_license], 'installer runtime')
(project / 'licenses/third-party-index.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
missing = [r['name'] for r in records if not r['notices']]
print(json.dumps({'components': len(records), 'missingNotices': missing}, ensure_ascii=False))
if missing:
    raise RuntimeError('Some shipped dependency notices need inspection.')
