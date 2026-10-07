"""Activate the bundled, pinned upstream engines through their real interfaces.

Windhawk source parsing, compilation, storage and injection remain upstream.
Seelen renders its own Dock/toolbar and loads resources with its original CLI.
"""
from __future__ import annotations

import copy
import ctypes
from ctypes import wintypes as wt
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

import win32api
import win32process
import win32com.client
import win32file
import pywintypes
from backend import atomic_json, canonical, com_session





kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
kernel32.OpenProcess.restype = wt.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
kernel32.QueryFullProcessImageNameW.restype = wt.BOOL
kernel32.CloseHandle.argtypes = [wt.HANDLE]
kernel32.GetPrivateProfileStringW.argtypes = [wt.LPCWSTR, wt.LPCWSTR, wt.LPCWSTR, wt.LPWSTR, wt.DWORD, wt.LPCWSTR]
kernel32.GetPrivateProfileStringW.restype = wt.DWORD


def read_json(path, fallback=None):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return fallback


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(part)
    return digest.hexdigest()


def process_images():
    result = []
    for pid in win32process.EnumProcesses():
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            continue
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            count = wt.DWORD(len(buffer))
            if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(count)):
                result.append((pid, buffer.value))
        finally:
            kernel32.CloseHandle(handle)
    return result


def loaded_libraries(names):
    found = set()
    if not names:
        return found
    for pid, _ in process_images():
        handle = None
        try:
            handle = win32api.OpenProcess(0x410, False, pid)
            for module in win32process.EnumProcessModules(handle):
                name = Path(win32process.GetModuleFileNameEx(handle, module)).name.casefold()
                if name in names:
                    found.add(name)
        except Exception:
            # Protected processes may deny inspection. Never infer a load from that.
            pass
        finally:
            if handle:
                handle.Close()
    return found


class RuntimeAdapter:
    def __init__(self, data_directory, runtime_root=None):
        self.data = Path(data_directory)
        self.project = Path(__file__).resolve().parents[2]
        if getattr(sys, 'frozen', False):
            application = Path(sys.executable).parent.parent
            self.runtimes = Path(runtime_root) if runtime_root else application / 'runtimes'
            self.mod_sources = application / 'resources' / 'windhawk-mods'
            catalog_path = application / 'resources' / 'mod-catalog.json'
            lock_path = application / 'resources' / 'runtime-distributions.json'
        else:
            self.runtimes = Path(runtime_root) if runtime_root else self.project / '.cache' / 'runtimes'
            self.mod_sources = self.project / 'vendor' / 'windhawk-mods' / 'mods'
            catalog_path = self.project / 'vendor' / 'Seelen-UI' / 'src' / 'ui' / 'react' / 'settings' / 'modules' / 'themeWorkbench' / 'domain' / 'catalog.json'
            lock_path = self.project / 'config' / 'runtime-distributions.json'
        self.windhawk = self.runtimes / 'windhawk'
        self.windhawk_user = self.data / 'windhawk-runtime'
        self.windhawk_data = self.data / 'windhawk-data'
        self.history = self.data / 'runtime-history'
        self.management = self.data / 'runtime-managed.json'
        self.catalog = {item['id']: item for item in read_json(catalog_path, {}).get('mods', [])}
        self.lock = read_json(lock_path, {})
        self.progress = lambda stage, name='': None

    def _check(self, kind, names):
        if kind != 'windhawk':
            raise ValueError('此实验分支不包含 Seelen 运行组件。')
        root = self.windhawk
        if not root.is_dir():
            raise RuntimeError(f'{kind} 运行包不存在，请保留完整的安装目录。')
        expected = self.lock.get(kind, {}).get('files', {})
        for name in names:
            target = root / name
            if not target.is_file() or name not in expected or file_hash(target) != expected[name]:
                raise RuntimeError(f'{kind} 运行文件校验失败：{name}。请重新安装。')

    def _run(self, arguments, timeout=120):
        result = subprocess.run([str(item) for item in arguments], capture_output=True,
                                encoding='utf-8', errors='replace', timeout=timeout,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or f'运行引擎返回 {result.returncode}').strip()[-6000:])
        return result.stdout

    def _windhawk_root(self):
        self._check('windhawk', ['windhawk.exe', 'windhawk-cli.exe', 'windhawk-core.dll'])
        self.windhawk_user.mkdir(parents=True, exist_ok=True)
        for name in ['windhawk.exe', 'windhawk-cli.exe', 'windhawk-core.dll', 'windhawk-mod.exe', 'windhawk-mod-elevated.exe', 'windhawk-mod-uiaccess.exe']:
            source, target = self.windhawk / name, self.windhawk_user / name
            if not target.is_file() or file_hash(target) != file_hash(source):
                shutil.copy2(source, target)
        engine_source = self.windhawk / 'Engine' / '2.0'
        engine = self.windhawk_user / 'Engine' / '2.0'
        if not (engine_source / '64' / 'windhawk.lib').is_file():
            raise RuntimeError('Windhawk 原运行引擎及编译导入库不完整。')
        if not engine.is_dir():
            shutil.copytree(engine_source, engine)
        mods_runtime = self.windhawk_user / 'ModsRuntime'
        if not mods_runtime.is_dir():
            shutil.copytree(self.windhawk / 'ModsRuntime', mods_runtime)
        # These are the original NSIS-installed LLVM runtime dependencies. The
        # compiler's DLLs import .whl files from their own architecture folder.
        for source in (self.windhawk / 'AppData' / 'Engine' / 'Mods').glob('*/*'):
            if not source.is_file() or (source.suffix != '.whl' and source.name != 'windhawk-mod-shim.dll'):
                continue
            destination = self.windhawk_data / 'Engine' / 'Mods' / source.parent.name / source.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.is_file() or file_hash(destination) != file_hash(source):
                shutil.copy2(source, destination)
        text = '\n'.join(['[Storage]', 'Portable=1', f'AppDataPath={self.windhawk_data}',
                          f'EnginePath={engine}', f'CompilerPath={self.windhawk / "Compiler"}',
                          f'UIPath={self.windhawk / "UI"}', ''])
        (self.windhawk_user / 'windhawk.ini').write_text(text, encoding='utf-16')
        # The engine's original INI owns its own data root. This is a runtime
        # location bridge; mod/config writes are exclusively official CLI calls.
        engine_ini = engine / 'engine.ini'
        engine_ini.write_text('[Storage]\nPortable=1\nAppDataPath=' + str(self.windhawk_data / 'Engine') + '\n', encoding='utf-16')
        return self.windhawk_user

    def _wh(self, *arguments, timeout=120):
        root = self._windhawk_root()
        text = self._run([root / 'windhawk-cli.exe', '--app-root', root, '--json', *arguments], timeout)
        try:
            response = json.loads(text)
        except ValueError as error:
            raise RuntimeError('Windhawk 没有返回有效的运行结果。') from error
        if response.get('success') is not True:
            raise RuntimeError(str(response.get('error', 'Windhawk 操作失败。')))
        return response['data']

    def _managed(self):
        return read_json(self.management, {'mods': {}, 'seelen': {}})

    def _installed_mods_readonly(self):
        """Read the pinned portable engine's [Mod] records without initializing it.

        The upstream `mod list` CLI synchronizes its profile, and _wh also copies
        runtime files and rewrites INIs. Neither belongs in startup/status reads.
        GetPrivateProfileStringW matches the engine's UTF-16 INI reader.
        """
        mods = []
        managed = self._managed().get('mods', {})
        for path in sorted((self.windhawk_data / 'Engine' / 'Mods').glob('*.ini')):
            def value(name, default=''):
                buffer = ctypes.create_unicode_buffer(32768)
                count = kernel32.GetPrivateProfileStringW('Mod', name, default, buffer, len(buffer), str(path.resolve()))
                if count >= len(buffer) - 1:
                    raise ValueError('Windhawk 模组状态过长，请检查：' + path.name)
                return buffer.value
            library = value('LibraryFileName')
            if not library:
                continue
            disabled = value('Disabled', '0') != '0'
            metadata = managed.get(path.stem, self.catalog.get(path.stem.removeprefix('local@'), {}))
            mods.append({'id': path.stem, 'name': metadata.get('name', path.stem),
                         'version': value('Version'), 'enabled': not disabled,
                         'config': {'libraryFileName': library, 'disabled': disabled}})
        return mods

    def state(self):
        images = process_images()
        windhawk_running = any(canonical(image) == canonical(self.windhawk_user / 'windhawk.exe') for _, image in images)
        mods, issue = [], ''
        if (self.windhawk_user / 'windhawk.ini').is_file():
            try:
                mods = self._installed_mods_readonly()
            except Exception as error:
                issue = str(error)
        libraries = {str((item.get('config') or {}).get('libraryFileName', '')).casefold()
                     for item in mods if item.get('enabled')}
        loaded = loaded_libraries(libraries) if windhawk_running else set()
        for item in mods:
            library = str((item.get('config') or {}).get('libraryFileName', '')).casefold()
            item['loaded'] = bool(library and library in loaded)
        return {'desktopMode': 'windows',
                'seelen': {'available': False, 'running': False, 'dock': False, 'toolbar': False,
                           'version': 'removed', 'themes': [], 'removed': True},
                'windhawk': {'available': (self.windhawk / 'windhawk-cli.exe').is_file(), 'running': windhawk_running,
                             'version': '2.0.0-alpha.6', 'compiler': (self.windhawk / 'Compiler' / 'bin' / 'clang++.exe').is_file(),
                             'mods': mods, 'error': issue}}

    def _journal(self, kind, before):
        self.history.mkdir(parents=True, exist_ok=True)
        key = datetime.now().strftime('%Y%m%dT%H%M%S') + '_' + uuid.uuid4().hex[:8]
        record = {'id': key, 'kind': kind, 'before': before, 'status': 'prepared'}
        atomic_json(self.history / (key + '.json'), record)
        return record


    def _record(self, record, result):
        record.update(status='applied', result=result)
        atomic_json(self.history / (record['id'] + '.json'), record)




    def _validate_mods(self, selections):
        if not isinstance(selections, list) or len(selections) > 30:
            raise ValueError('每次最多启用 30 个模组，请分组应用。')
        result, seen = [], set()
        for item in selections:
            if not isinstance(item, dict) or item.get('id') in seen:
                raise ValueError('模组配置包含重复或无效项目。')
            identifier = item.get('id')
            mod = self.catalog.get(identifier)
            if not mod or not re.fullmatch(r'[a-z0-9-]+', identifier):
                raise ValueError('模组不在已核验的本地源码库中。')
            source = self.mod_sources / (identifier + '.wh.cpp')
            if not getattr(sys, 'frozen', False) and mod.get('sourceKind') == 'themestudio':
                source = self.project / 'components' / 'explorer-skin' / (identifier + '.wh.cpp')
            canonical_source_hash = hashlib.sha256(source.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
            if item.get('sourceHash') != mod['sha256'] or canonical_source_hash != mod['sha256']:
                raise ValueError(f'模组 {identifier} 的源码已变化，请重新选择。')
            settings = item.get('settings', {})
            if not isinstance(settings, dict) or any(not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_.\[\]-]+', key) or type(value) not in {str, int, bool, float} for key, value in settings.items()):
                raise ValueError('模组设置无效。')
            if 'theme' in settings and settings['theme'] not in {choice['id'] for choice in mod['themeChoices']}:
                raise ValueError('所选模组预设不存在。')
            clean = {'id': identifier, 'sourceHash': item['sourceHash'], 'settings': settings}
            seen.add(identifier); result.append((clean, mod, source))
        return result

    def windhawk_apply(self, selections, preserve_others=False):
        validated = self._validate_mods(selections)
        if any(Path(image).name.casefold() == 'windhawk.exe' and
               canonical(image) != canonical(self.windhawk_user / 'windhawk.exe')
               for _, image in process_images()):
            raise ValueError('另一个 Windhawk 正在运行，请先退出对应版本，再应用本体验分支的模组。')
        if not (self.windhawk / 'Compiler' / 'bin' / 'clang++.exe').is_file():
            raise RuntimeError('Windhawk 离线开发工具缺失，请重新安装完整版本。')
        current = self._wh('mod', 'list').get('mods', [])
        record = self._journal('windhawk', current)
        managed = self._managed(); managed.setdefault('mods', {})
        selected = {'local@' + item['id'] for item, _, _ in validated}
        for installed in current:
            if (not preserve_others and installed['id'] not in {'local@windows-11-file-explorer-styler', 'local@themestudio-explorer-background'}
                    and installed['id'] in managed['mods'] and installed['id'] not in selected and installed.get('enabled')):
                self._wh('mod', 'disable', installed['id'])
        for item, mod, source in validated:
            storage_id = 'local@' + item['id']
            previous = managed['mods'].get(storage_id)
            if previous is None or previous.get('sourceHash') != mod['sha256']:
                self.progress('compile', mod['name'])
                result = self._wh('mod', 'install', '--file', source, '--disabled', timeout=600)
                if result.get('id') != storage_id or result.get('compiledLocally') is not True or result.get('config', {}).get('disabled') is not True or not result.get('config', {}).get('libraryFileName'):
                    raise RuntimeError('Windhawk 未确认源码编译和安装结果。')
                managed['mods'][storage_id] = {'sourceHash': mod['sha256'], 'version': mod['version'], 'name': mod['name']}
                atomic_json(self.management, managed)
            if item['settings']:
                pairs = [key + '=' + (str(value).lower() if isinstance(value, bool) else str(value)) for key, value in item['settings'].items()]
                self._wh('mod', 'settings', 'set', storage_id, *pairs)
            self.progress('enable', mod['name'])
            self._wh('mod', 'enable', storage_id)
            checked = self._wh('mod', 'show', storage_id)
            if checked.get('config', {}).get('disabled') is not False:
                raise RuntimeError(f'Windhawk 未确认启用 {mod["name"]}。')
        root = self._windhawk_root()
        if validated and not any(canonical(image) == canonical(root / 'windhawk.exe') for _, image in process_images()):
            self.progress('windhawk_start')
            subprocess.Popen([str(root / 'windhawk.exe'), '-tray-only'], cwd=root, creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(1)
        result = self.state()['windhawk']
        if validated and not result['running']:
            raise RuntimeError('模组已编译，但 Windhawk 运行引擎没有启动。')
        self._record(record, result)
        return result

    def windhawk_stop(self):
        managed = self._managed()
        for item in self._wh('mod', 'list').get('mods', []):
            if item['id'] in managed.get('mods', {}) and item.get('enabled'):
                self._wh('mod', 'disable', item['id'])
        return self.state()['windhawk']

    def shutdown(self):
        if (self.windhawk_user / 'windhawk.ini').is_file():
            self.windhawk_stop()
            if any(canonical(image) == canonical(self.windhawk_user / 'windhawk.exe') for _, image in process_images()):
                self._run([self.windhawk_user / 'windhawk.exe', '-exit', '-wait', '-timeout', '30000'], timeout=40)
        return {'stopped': True}

    def dispatch(self, operation, payload):
        if operation == 'runtime.state':
            return self.state()
        if operation.startswith('runtime.seelen.') or operation == 'runtime.desktop.apply':
            raise ValueError('此实验分支已移除 Seelen Dock、工具栏和桌面布局功能。')
        if operation == 'runtime.windhawk.apply':
            return self.windhawk_apply(payload.get('mods'))
        if operation == 'runtime.windhawk.stop':
            return self.windhawk_stop()
        if operation == 'runtime.apply':
            recipe = payload.get('recipe', {})
            self._validate_mods(recipe.get('windhawk', []))
            windhawk = self.windhawk_apply(recipe.get('windhawk', []))
            return {'windhawk': windhawk}
        raise ValueError('不支持的运行引擎操作。')
