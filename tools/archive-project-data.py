"""Archive project profiles and native verification evidence before local cleanup."""
import hashlib
import json
import os
from pathlib import Path
import zipfile

project = Path(__file__).resolve().parents[1]
version = json.loads((project / 'package.json').read_text(encoding='utf-8-sig'))['version']
target = project / 'installers' / f'ThemeStudio-{version}-project-data.zip'
roots = {
    'profiles/ThemeStudio': Path(os.environ['LOCALAPPDATA']) / 'ThemeStudio',
    'profiles/Seelen-Roaming': Path(os.environ['APPDATA']) / 'com.seelen.seelen-ui',
    'profiles/Seelen-Local': Path(os.environ['LOCALAPPDATA']) / 'com.seelen.seelen-ui',
}
manifest = []
with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for prefix, root in roots.items():
        if not root.is_dir():
            continue
        for source in sorted(root.rglob('*')):
            if not source.is_file():
                continue
            if source.is_symlink():
                raise ValueError(f'Project profile contains a symbolic link: {source}')
            relative = source.relative_to(root).as_posix()
            data = source.read_bytes()
            archive.writestr(prefix + '/' + relative, data)
            manifest.append({'root': str(root), 'relative': relative,
                             'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    evidence_root = project / 'qa' / 'runtime'
    for directory in ('wallpaper-native', 'pairing-native', 'admin-native',
                      'windhawk-activation', 'installer-0.2.0'):
        folder = evidence_root / directory
        if folder.is_dir():
            for source in sorted(folder.iterdir()):
                if source.is_file() and source.suffix.lower() in {'.json', '.png', '.log'}:
                    archive.write(source, 'verification/' + directory + '/' + source.name)
    archive.writestr('profile-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
with zipfile.ZipFile(target) as archive:
    if archive.testzip() is not None:
        raise ValueError('Project data archive integrity check failed')
(project / 'installers' / 'profile-manifest.json').write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'archive': str(target), 'files': len(manifest), 'bytes': target.stat().st_size}))
