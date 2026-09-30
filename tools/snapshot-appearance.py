"""Read-only Windows appearance snapshots for install/startup acceptance.

Snapshots stay in ignored qa/ storage; only comparison summaries are published.
"""
import argparse
import base64
import ctypes
from ctypes import wintypes as wt
import hashlib
import json
import os
from pathlib import Path
import winreg

advapi = ctypes.WinDLL('advapi32', use_last_error=True)
advapi.RegQueryValueExW.argtypes = [wt.HKEY, wt.LPCWSTR, ctypes.c_void_p, ctypes.POINTER(wt.DWORD), ctypes.c_void_p, ctypes.POINTER(wt.DWORD)]


def raw_value(key, name):
    # Preserve exact byte length too. Some existing REG_DWORD values are only
    # one byte; high-level readers can pad those with uninitialized memory.
    size, kind = wt.DWORD(), wt.DWORD()
    status = advapi.RegQueryValueExW(int(key), name, None, ctypes.byref(kind), None, ctypes.byref(size))
    if status: raise ctypes.WinError(status)
    data = ctypes.create_string_buffer(size.value)
    status = advapi.RegQueryValueExW(int(key), name, None, ctypes.byref(kind), data, ctypes.byref(size))
    if status: raise ctypes.WinError(status)
    return {'type': kind.value, 'raw': base64.b64encode(data.raw[:size.value]).decode('ascii')}


def registry(path, names=None, recursive=False):
    result = {}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ) as key:
            for index in range(winreg.QueryInfoKey(key)[1]):
                name = winreg.EnumValue(key, index)[0]
                if names is None or name in names:
                    result[name] = raw_value(key, name)
            if recursive:
                result['$keys'] = {}
                for index in range(winreg.QueryInfoKey(key)[0]):
                    name = winreg.EnumKey(key, index)
                    result['$keys'][name] = registry(path + '\\' + name, recursive=True)
    except FileNotFoundError:
        return None
    return result


def snapshot():
    keys = {
        r'Control Panel\Cursors': (None, True),
        r'Control Panel\Colors': (None, False),
        r'Control Panel\Desktop': (['WallPaper', 'Wallpaper', 'WallpaperStyle', 'TileWallpaper', 'Pattern'], False),
        r'Software\Microsoft\Windows\CurrentVersion\Themes': (None, True),
        r'Software\Microsoft\Windows\CurrentVersion\ThemeManager': (None, True),
        r'Software\Microsoft\Windows\DWM': (None, False),
        r'Software\Microsoft\Windows\CurrentVersion\Explorer\Accent': (None, False),
        r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced': (['TaskbarAl','TaskbarSi','TaskbarGlomLevel','MMTaskbarGlomLevel','ShowTaskViewButton'], False),
        r'Software\Microsoft\Accessibility': (['CursorSize', 'CursorType', 'CursorColor'], False),
        r'Software\Microsoft\Windows\CurrentVersion\Run': (None, False),
    }
    result = {'registry': {key: registry(key, names, recursive) for key, (names, recursive) in keys.items()}}
    wallpaper = ctypes.create_unicode_buffer(32768)
    if not ctypes.windll.user32.SystemParametersInfoW(0x73, len(wallpaper), wallpaper, 0):
        raise ctypes.WinError()
    result['wallpaper'] = wallpaper.value
    files = []
    for folder in (Path(os.environ['APPDATA']) / 'Microsoft/Windows/Themes', Path(os.environ['LOCALAPPDATA']) / 'Microsoft/Windows/Themes'):
        if folder.is_dir(): files.extend(path for path in folder.rglob('*') if path.is_file())
    seelen = Path(os.environ['APPDATA']) / 'com.seelen.seelen-ui'
    files.extend(path for path in seelen.glob('settings*') if path.is_file())
    for folder in (Path(os.environ['USERPROFILE']) / 'Desktop', Path(os.environ['PUBLIC']) / 'Desktop'):
        if folder.is_dir(): files.extend(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in {'.lnk', '.url'})
    result['files'] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(set(files))}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--compare', type=Path)
    args = parser.parse_args()
    current = snapshot()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.compare:
        before = json.loads(args.compare.read_text(encoding='utf-8'))
        changes = [part for part in sorted(set(before) | set(current)) if before.get(part) != current.get(part)]
        print(json.dumps({'unchanged': not changes, 'changedSections': changes, 'registryAreas': len(current['registry']), 'filesCompared': len(current['files'])}))
        raise SystemExit(bool(changes))
    print(json.dumps({'snapshotSaved': True, 'registryAreas': len(current['registry']), 'filesCompared': len(current['files'])}))
