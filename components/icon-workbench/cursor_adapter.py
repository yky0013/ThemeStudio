"""Cursor Palette compatible presets and reversible current-user cursor settings.

Role names, aliases and registry protocol adapted from Cursor Palette (MIT).
See licenses/Cursor-Palette.txt and THIRD_PARTY.md. Upstream preset files are read-only.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as wt
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import uuid
import winreg

from backend import IconStore, atomic_json

ROLES = (
    ('Arrow', '普通选择', 'normal arrow default pointer aero_arrow'),
    ('Help', '帮助选择', 'help helpsel aero_helpsel'),
    ('AppStarting', '后台运行', 'working appstarting workinginbackground aero_working'),
    ('Wait', '忙碌', 'busy wait aero_busy'),
    ('Crosshair', '精确选择', 'precision cross crosshair'),
    ('IBeam', '文本选择', 'text ibeam beam'),
    ('NWPen', '手写', 'handwriting pen nwpen aero_pen'),
    ('No', '不可用', 'unavailable no unavail aero_unavail'),
    ('SizeNS', '垂直调整', 'vertical ns sizens vert aero_ns'),
    ('SizeWE', '水平调整', 'horizontal ew sizewe horz aero_ew'),
    ('SizeNWSE', '对角调整 1', 'diagonal1 nwse sizenwse dgn1 aero_nwse'),
    ('SizeNESW', '对角调整 2', 'diagonal2 nesw sizenesw dgn2 aero_nesw'),
    ('SizeAll', '移动', 'move sizeall aero_move'),
    ('UpArrow', '备用选择', 'alternate up uparrow aero_up'),
    ('Hand', '链接选择', 'link hand aero_link'),
    ('Person', '人员选择', 'person aero_person'),
    ('Pin', '位置选择', 'pin aero_pin location'),
)
ROLE_KEYS = tuple(r[0] for r in ROLES)
CURSOR_KEY = r'Control Panel\Cursors'
ACCESS_KEY = r'Software\Microsoft\Accessibility'
VALUE_NAMES = ROLE_KEYS + ('', 'Scheme Source', 'CursorBaseSize')
user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.LoadImageW.argtypes = [wt.HINSTANCE, wt.LPCWSTR, wt.UINT, ctypes.c_int, ctypes.c_int, wt.UINT]
user32.LoadImageW.restype = wt.HANDLE
user32.DestroyCursor.argtypes = [wt.HANDLE]
user32.SystemParametersInfoW.argtypes = [wt.UINT, wt.UINT, ctypes.c_void_p, wt.UINT]
user32.SystemParametersInfoW.restype = wt.BOOL


def read_json(path, fallback=None):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return fallback


def read_values(path, names):
    result = {name: None for name in names}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            for name in names:
                try:
                    value, kind = winreg.QueryValueEx(key, name)
                    result[name] = [value, kind]
                except FileNotFoundError:
                    pass
    except FileNotFoundError:
        pass
    return result


def write_values(path, values):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, path) as key:
        for name, entry in values.items():
            if entry is None:
                try:
                    winreg.DeleteValue(key, name)
                except FileNotFoundError:
                    pass
            else:
                winreg.SetValueEx(key, name, 0, entry[1], entry[0])


def snapshot():
    return {'cursors': read_values(CURSOR_KEY, VALUE_NAMES),
            'accessibility': read_values(ACCESS_KEY, ('CursorSize',))}


def refresh(size):
    if not user32.SystemParametersInfoW(0x2029, 0, ctypes.c_void_p(size), 3):
        raise ctypes.WinError(ctypes.get_last_error())
    # The registry is already persisted above. Some Windows installations reject
    # SPIF_UPDATEINIFILE for this reload-only action; no extra profile write is needed.
    if not user32.SystemParametersInfoW(0x57, 0, None, 0):
        raise ctypes.WinError(ctypes.get_last_error())


def restore_snapshot(state):
    # SPI may itself persist values: reload the exact original types/absence last.
    write_values(CURSOR_KEY, state['cursors'])
    write_values(ACCESS_KEY, state['accessibility'])
    size = (state['cursors'].get('CursorBaseSize') or [32])[0]
    refresh(size)
    write_values(CURSOR_KEY, state['cursors'])
    write_values(ACCESS_KEY, state['accessibility'])


def current_scheme():
    state = snapshot()['cursors']
    return {'name': '当前系统指针', 'size': (state.get('CursorBaseSize') or [32])[0],
            'roles': {role: (state.get(role) or [''])[0] for role in ROLE_KEYS}}


def default_scheme():
    names = ('aero_arrow.cur', 'aero_helpsel.cur', 'aero_working.ani', 'aero_busy.ani',
             '', '', 'aero_pen.cur', 'aero_unavail.cur', 'aero_ns.cur', 'aero_ew.cur',
             'aero_nwse.cur', 'aero_nesw.cur', 'aero_move.cur', 'aero_up.cur',
             'aero_link.cur', 'aero_person.cur', 'aero_pin.cur')
    values = {role: str(Path(os.environ['SystemRoot']) / 'Cursors' / name) if name else ''
              for role, name in zip(ROLE_KEYS, names)}
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\Control Panel\Cursors\Schemes') as key:
            data = winreg.QueryValueEx(key, 'Windows Default')[0]
            values.update(zip(ROLE_KEYS, (p.strip() for p in data.split(','))))
    except OSError:
        pass
    return {'name': 'Windows 默认', 'size': 32, 'roles': values}


def validate_cursor(path):
    path = Path(os.path.expandvars(str(path))).absolute()
    if path.suffix.lower() not in {'.cur', '.ani'} or not path.is_file():
        raise ValueError(f'指针文件不存在或不是 CUR / ANI：{path}')
    if path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError(f'指针文件超过 32 MB：{path.name}')
    with path.open('rb') as stream:
        head = stream.read(12)
    valid = ((path.suffix.lower() == '.cur' and head[:4] == b'\x00\x00\x02\x00') or
             (path.suffix.lower() == '.ani' and head[:4] == b'RIFF' and head[8:12] == b'ACON'))
    if not valid:
        raise ValueError(f'指针格式校验失败：{path.name}')
    # LR_LOADFROMFILE without LR_SHARED: this handle is ours to destroy.
    handle = user32.LoadImageW(None, str(path), 2, 0, 0, 0x10)
    if not handle:
        raise ValueError(f'Windows 无法读取指针：{path.name}')
    user32.DestroyCursor(handle)
    return path


def safe_child(parent, relative):
    path = (Path(parent) / relative).resolve()
    if not path.is_relative_to(Path(parent).resolve()):
        raise ValueError('方案中的资源路径超出了预设目录。')
    return path


class CursorAdapter:
    def __init__(self, directory, upstream=None):
        self.store = IconStore(directory)
        self.directory = self.store.directory / 'cursor-settings'
        self.assets = self.directory / 'files'
        self.history = self.directory / 'history'
        self.presets = self.directory / 'presets'
        for path in (self.assets, self.history, self.presets):
            path.mkdir(parents=True, exist_ok=True)
        self.upstream = Path(upstream) if upstream else Path(os.environ['LOCALAPPDATA']) / 'Cursor-Palette' / 'presets'

    def schemes(self):
        result = [current_scheme(), default_scheme()]
        errors = []
        for path in self.presets.glob('*.json'):
            item = read_json(path)
            if isinstance(item, dict) and isinstance(item.get('roles'), dict):
                result.append(item)
        for manifest in self.upstream.glob('*/manifest.json'):
            try:
                data = read_json(manifest)
                if not isinstance(data, dict):
                    raise ValueError('清单无法读取')
                values = dict(default_scheme()['roles'])
                for role in ROLE_KEYS:
                    ref = data.get('RoleRefs', {}).get(role)
                    if ref:
                        path = safe_child(self.upstream, ref['PresetId'] + '/files/' + ref['FileName'])
                        values[role] = str(path)
                    elif role in data.get('Roles', {}):
                        values[role] = str(safe_child(manifest.parent / 'files', data['Roles'][role]))
                result.append({'name': 'Cursor Palette · ' + data.get('Name', manifest.parent.name),
                               'size': data.get('BaseSize', 32), 'roles': values,
                               'uses_scaling': bool(data.get('UseScaling'))})
            except (KeyError, TypeError, ValueError, OSError) as error:
                errors.append(f'{manifest.parent.name}：{error}')
        return result, errors

    def import_file(self, path):
        path = validate_cursor(path)
        data = path.read_bytes()
        if path.parent.resolve() == self.assets.resolve():
            return str(path)
        target = self.assets / (hashlib.sha256(data).hexdigest()[:16] + '_' + path.name)
        if not target.exists():
            with target.open('xb') as output:
                output.write(data)
        elif target.read_bytes() != data:
            raise ValueError('资源目录中的指针文件损坏。')
        return str(target)

    def match_folder(self, folder):
        candidates = {}
        for path in sorted(Path(folder).iterdir()):
            if path.suffix.lower() not in {'.cur', '.ani'} or not path.is_file():
                continue
            stem = path.stem.lower()
            matches = [r[0] for r in ROLES if stem in r[2].split() or stem == r[0].lower()]
            if not matches:
                words = set(re.split(r'[\s_.()\[\]-]+', stem))
                matches = [r[0] for r in ROLES if words.intersection(r[2].split())]
            if len(matches) == 1:
                candidates.setdefault(matches[0], []).append(path)
        return {role: self.import_file(paths[0]) for role, paths in candidates.items() if len(paths) == 1}

    def save_scheme(self, name, roles, size):
        if not name.strip():
            raise ValueError('请填写方案名称。')
        # Materialize resources so user files may move after the save.
        values = {r: self.import_file(roles[r]) if roles.get(r) else '' for r in ROLE_KEYS}
        entry = {'name': name.strip(), 'size': size, 'roles': values}
        with self.store.lock():
            atomic_json(self.presets / (uuid.uuid4().hex + '.json'), entry)
        return entry

    def apply(self, roles, size, expected_state=None):
        size = int(size)
        if size not in range(32, 257, 16):
            raise ValueError('指针尺寸应为 32–256，按 16 递增。')
        # Validate every role before any system write.
        values = {r: self.import_file(roles[r]) if roles.get(r) else '' for r in ROLE_KEYS}
        with self.store.lock():
            before = snapshot()
            if expected_state is not None and before != expected_state:
                raise ValueError('鼠标设置已被其他操作修改，请重新读取后再应用。')
            record = {'created': datetime.now().isoformat(), 'before': before, 'status': 'prepared'}
            path = self.history / (datetime.now().strftime('%Y%m%dT%H%M%S%f') + '_' + uuid.uuid4().hex[:8] + '.json')
            atomic_json(path, record)
            try:
                write_values(CURSOR_KEY, {r: [v, winreg.REG_EXPAND_SZ] for r, v in values.items()})
                write_values(CURSOR_KEY, {'Scheme Source': [2, winreg.REG_DWORD],
                                          'CursorBaseSize': [size, winreg.REG_DWORD]})
                write_values(ACCESS_KEY, {'CursorSize': [(size - 16) // 16, winreg.REG_DWORD]})
                refresh(size)
                after = snapshot()
                if any((after['cursors'].get(r) or [''])[0] != value for r, value in values.items()):
                    raise RuntimeError('指针应用后的系统设置与目标不一致。')
                record.update(status='applied', after=after)
                atomic_json(path, record)
            except Exception:
                try:
                    restore_snapshot(before)
                    record['status'] = 'rolled_back'
                except Exception as error:
                    record.update(status='recovery_needed', recovery_error=str(error))
                atomic_json(path, record)
                raise
        return '鼠标指针已应用，并保存恢复记录。'

    def restore(self):
        with self.store.lock():
            for path in sorted(self.history.glob('*.json'), reverse=True):
                record = read_json(path, {})
                if record.get('status') != 'applied':
                    continue
                if snapshot() != record['after']:
                    raise ValueError('指针已被其他操作修改，已保留当前设置。请重新读取后确认。')
                restore_snapshot(record['before'])
                if snapshot() != record['before']:
                    raise RuntimeError('指针恢复后的设置核对失败，备份仍保留。')
                record['status'] = 'restored'
                atomic_json(path, record)
                return '已恢复上一次应用前的鼠标设置。'
        raise ValueError('还没有可恢复的鼠标应用记录。')
