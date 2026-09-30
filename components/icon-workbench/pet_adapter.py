"""Register installed desktop pets without copying dependencies or auto-starting."""
from pathlib import Path
import hashlib
import os
import subprocess
import struct
import win32com.client
from backend import atomic_json, canonical, com_session
from runtime_adapter import read_json, file_hash, process_images


def validate_executable(value):
    if not isinstance(value, str) or not value or not Path(value).is_absolute():
        raise ValueError('请选择本机已解压或已安装桌宠的 EXE 主程序。')
    path = Path(value).resolve(strict=True)
    if str(path).startswith('\\\\') or path.suffix.lower() != '.exe' or not path.is_file():
        raise ValueError('只支持本机 EXE 主程序，请先解压桌宠文件夹。')
    if not 64 <= path.stat().st_size <= 2 * 1024**3:
        raise ValueError('桌宠主程序大小无效。')
    with path.open('rb') as stream:
        header = stream.read(64)
        if header[:2] != b'MZ':
            raise ValueError('所选文件不是 Windows 可执行程序。')
        stream.seek(struct.unpack_from('<I', header, 0x3c)[0])
        if stream.read(4) != b'PE\0\0':
            raise ValueError('所选文件不是有效的 Windows EXE。')
    return path


class PetAdapter:
    def __init__(self, data):
        self.data = Path(data)
        self.registry = self.data / 'desktop-pets.json'

    def _items(self):
        value = read_json(self.registry, {'pets': []})
        return value.get('pets', [])

    def _save(self, items):
        atomic_json(self.registry, {'schemaVersion': 1, 'pets': items})

    def state(self):
        running = {canonical(path) for _, path in process_images()}
        return {'pets': [{**item, 'available': Path(item['path']).is_file(),
                          'running': canonical(item['path']) in running} for item in self._items()]}

    def import_executable(self, value):
        path = validate_executable(value)
        items = self._items()
        ident = hashlib.sha256(canonical(path).encode('utf-8')).hexdigest()
        duplicate = any(item['id'] == ident for item in items)
        if not duplicate and len(items) >= 100:
            raise ValueError('最多保存 100 个桌宠，请先移除不再使用的记录。')
        item = {'id': ident, 'name': path.stem, 'path': str(path), 'sha256': file_hash(path)}
        self._save([old for old in items if old['id'] != ident] + [item])
        return {**item, 'duplicate': duplicate}

    def item(self, ident):
        item = next((item for item in self._items() if item['id'] == ident), None)
        if item is None:
            raise ValueError('桌宠未导入，请刷新列表。')
        return item

    def launch(self, ident):
        item = self.item(ident)
        path = validate_executable(item['path'])
        if file_hash(path) != item['sha256']:
            raise ValueError('桌宠主程序已更新，请重新导入后启动。')
        if canonical(path) in {canonical(image) for _, image in process_images()}:
            return {'alreadyRunning': True, 'requested': False}
        # Explorer opens a local shortcut as the desktop user; do not inherit
        # this elevated backend's token or pass browser-supplied arguments.
        folder = self.data / 'pet-shortcuts'
        folder.mkdir(parents=True, exist_ok=True)
        link = folder / (item['id'] + '.lnk')
        with com_session():
            shortcut = win32com.client.Dispatch('WScript.Shell').CreateShortcut(str(link))
            shortcut.TargetPath = str(path)
            shortcut.WorkingDirectory = str(path.parent)
            shortcut.Arguments = ''
            shortcut.Save()
        subprocess.Popen([str(Path(os.environ['WINDIR']) / 'explorer.exe'), str(link)], creationflags=subprocess.CREATE_NO_WINDOW)
        return {'requested': True, 'alreadyRunning': False}

    def remove(self, ident):
        self.item(ident)
        self._save([item for item in self._items() if item['id'] != ident])
        return {'removed': True}
