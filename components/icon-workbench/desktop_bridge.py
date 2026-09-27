"""Private stdio adapter for the Seelen workbench. No HTTP server or shell execution.

Reuses backend.py, Cursor Palette's existing adapter and image-to-ico/converter.py.
Only scanned shortcuts and registered resource IDs can be used by the browser.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid

from backend import (Assignment, IconStore, IMAGE_EXTENSIONS, MAX_ICO_BYTES,
                     canonical, friendly_error, scan_shortcuts)
from cursor_adapter import CursorAdapter, ROLE_KEYS, ROLES, snapshot, read_json
from native_icons import ico_image, shortcut_image, cursor_image


def identity(value):
    return hashlib.sha256(str(value).encode('utf-8')).hexdigest()


def preview(image):
    stream = io.BytesIO()
    image.save(stream, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(stream.getvalue()).decode('ascii')


class DesktopBridge:
    def __init__(self, directory=None, folders=None):
        self.store = IconStore(directory)
        self.cursors = CursorAdapter(self.store.directory)
        self.folders = folders
        self.resources = {}
        self.cursor_versions = {}
        self.previews = {}

    def rows(self):
        extras = self.store.read_settings().get('extra_paths', [])
        return scan_shortcuts(self.folders, extras)

    def icon_view(self, item):
        return {'id': item['sha256'], 'name': item['name'], 'preview': preview(ico_image(item['path'], 64))}

    def register_cursor(self, path):
        if not path:
            return ''
        key = identity(canonical(os.path.expandvars(path)))
        self.resources[key] = path
        return key

    def cursor_view(self, scheme, kind='saved'):
        roles = {role: self.register_cursor(scheme['roles'].get(role, '')) for role in ROLE_KEYS}
        return {'id': identity(json.dumps(scheme, sort_keys=True)), 'name': scheme['name'],
                'kind': kind, 'size': scheme['size'], 'roles': roles}

    def state(self):
        rows, errors = self.rows()
        shortcuts = []
        for row in rows:
            key = (row['path'], row['sha256'])
            if key not in self.previews:
                # Applied icons are read directly to avoid a stale Explorer icon cache.
                try:
                    image = ico_image(row['icon_path'], 40)
                except Exception:
                    image = shortcut_image(row['path'], 40)
                self.previews[key] = preview(image)
            shortcuts.append({k: row[k] for k in ('name', 'origin', 'kind', 'sha256')} |
                             {'id': identity(canonical(row['path'])), 'preview': self.previews[key]})
        icons = []
        for item in self.store.read_settings().get('icons', []):
            try:
                icons.append(self.icon_view(self.store.import_icon(item['path']) | {'name': item['name']}))
            except Exception as error:
                errors.append(f"{item.get('name', 'Icon')}：{friendly_error(error)}")
        schemes, cursor_errors = self.cursors.schemes()
        current = snapshot()
        version = identity(json.dumps(current, sort_keys=True))
        self.cursor_versions = {version: current}
        cursor_schemes = [self.cursor_view(s, 'current' if i == 0 else 'default' if i == 1 else 'saved')
                          for i, s in enumerate(schemes)]
        resources = {}
        for key, value in self.resources.items():
            resources[key] = {'name': re.sub(r'^[a-f0-9]{16}_', '', Path(os.path.expandvars(value)).name),
                              'preview': preview(cursor_image(value, 40))}
        history = [{'id': item['id'], 'created': item['created'],
                    'count': sum(e['status'] in {'applied', 'prepared', 'needs_attention', 'restoring'}
                                 for e in item['entries'])}
                   for item in self.store.history()]
        cursor_restore = any(read_json(p, {}).get('status') == 'applied' for p in self.cursors.history.glob('*.json'))
        return {'shortcuts': shortcuts, 'icons': icons, 'history': [h for h in history if h['count']][:30],
                'cursors': {'schemes': cursor_schemes, 'resources': resources,
                            'roles': [r[0] for r in ROLES], 'version': version, 'canRestore': cursor_restore},
                'errors': errors + cursor_errors}

    def upload(self, item, folder, extensions):
        name = item.get('name', '')
        if not isinstance(name, str) or not name or Path(name).name != name or any(c in name for c in '\\/:\0'):
            raise ValueError('文件名无效。')
        if Path(name).suffix.lower() not in extensions:
            raise ValueError('不支持此文件格式。')
        data = base64.b64decode(item.get('data', ''), validate=True)
        if not data or len(data) > MAX_ICO_BYTES:
            raise ValueError('文件必须小于 32 MB 且不能为空。')
        target = Path(folder) / name
        with target.open('xb') as stream:
            stream.write(data)
        return target

    def resolve_roles(self, roles):
        if not isinstance(roles, dict) or set(roles) != set(ROLE_KEYS):
            raise ValueError('请提供完整的 17 状态指针方案。')
        values = {}
        for role, ref in roles.items():
            if ref == '':
                values[role] = ''
            elif isinstance(ref, str) and ref in self.resources:
                values[role] = self.resources[ref]
            else:
                raise ValueError('指针资源已失效，请重新读取或导入。')
        return values

    def dispatch(self, operation, payload):
        if operation == 'state':
            return self.state()
        if operation == 'recipe.export':
            if not isinstance(payload, dict) or payload.get('schemaVersion') != 1:
                raise ValueError('主题配置无效。')
            text = json.dumps(payload, ensure_ascii=False, indent=2)
            if len(text.encode('utf-8')) > 1024 * 1024:
                raise ValueError('主题配置超过 1 MB。')
            name = re.sub(r'[^\w\-]', '_', str(payload.get('name', 'theme')))[:80]
            directory = self.store.directory / 'exports'
            directory.mkdir(exist_ok=True)
            output = directory / (name + '-' + uuid.uuid4().hex[:8] + '.theme.json')
            with output.open('x', encoding='utf-8') as stream:
                stream.write(text)
            return {'path': str(output)}
        if operation == 'icons.import':
            with tempfile.TemporaryDirectory(prefix='theme-artwork-') as folder:
                source = self.upload(payload, folder, IMAGE_EXTENSIONS)
                item = self.store.import_image(source)
                # Keep the original display name but never persist the transient upload path.
                item['source'] = payload['name']
                with self.store.lock():
                    settings = self.store.read_settings()
                    settings['icons'] = [i for i in settings.get('icons', []) if i.get('path') != item['path']] + [item]
                    from backend import atomic_json
                    atomic_json(self.store.directory / 'settings.json', settings)
                return self.icon_view(item)
        if operation == 'icons.apply':
            items = payload.get('items')
            if not isinstance(items, list) or not 1 <= len(items) <= 500:
                raise ValueError('请选择 1–500 个桌面快捷方式。')
            icon_id = payload.get('icon')
            icons = {i.get('sha256'): i for i in self.store.read_settings().get('icons', [])}
            if icon_id not in icons:
                raise ValueError('请先选择图片。')
            rows, _ = self.rows()
            known = {identity(canonical(row['path'])): row for row in rows}
            assignments = []
            for item in items:
                row = known.get(item.get('id'))
                if not row:
                    raise ValueError('桌面快捷方式已不存在，请刷新列表。')
                assignments.append(Assignment(row['path'], icons[icon_id]['path'], item.get('sha256', '')))
            result = self.store.apply(assignments)
            return {'entries': [{k: e[k] for k in ('name', 'status', 'error')} for e in result['entries']],
                    'id': result['id']}
        if operation == 'icons.restore':
            result = self.store.restore(payload.get('id', ''))
            return {'entries': [{k: e[k] for k in ('name', 'status', 'error')} for e in result['entries']],
                    'id': result['id']}
        if operation == 'cursors.import':
            files = payload.get('files', [])
            if not isinstance(files, list) or not 1 <= len(files) <= 100:
                raise ValueError('请选择 1–100 个 CUR / ANI 文件。')
            role = payload.get('role')
            if role is not None and (role not in ROLE_KEYS or len(files) != 1):
                raise ValueError('请选择一个指针状态和一个文件。')
            with tempfile.TemporaryDirectory(prefix='theme-cursors-') as folder:
                paths = [self.upload(item, folder, {'.cur', '.ani'}) for item in files]
                mapping = {role: self.cursors.import_file(paths[0])} if role else self.cursors.match_folder(folder)
                return {'roles': {r: self.register_cursor(p) for r, p in mapping.items()},
                        'resources': {self.register_cursor(p): {'name': re.sub(r'^[a-f0-9]{16}_', '', Path(p).name),
                                      'preview': preview(cursor_image(p, 40))} for p in mapping.values()},
                        'matched': len(mapping), 'total': len(paths)}
        if operation in {'cursors.apply', 'cursors.save'}:
            values = self.resolve_roles(payload.get('roles'))
            size = payload.get('size')
            if type(size) is not int or size not in range(32, 257, 16):
                raise ValueError('指针尺寸应为 32–256，按 16 递增。')
            if operation == 'cursors.apply':
                expected = self.cursor_versions.get(payload.get('version'))
                if expected is None:
                    raise ValueError('鼠标设置已更新，请重新读取后再应用。')
                self.cursors.apply(values, size, expected_state=expected)
                return {'ok': True}
            name = payload.get('name', '')
            if not isinstance(name, str) or not 1 <= len(name.strip()) <= 120:
                raise ValueError('请填写 1–120 字的方案名称。')
            scheme = self.cursors.save_scheme(name, values, size)
            return self.cursor_view(scheme)
        if operation == 'cursors.restore':
            self.cursors.restore()
            return {'ok': True}
        raise ValueError('不支持的桌面操作。')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--scan-dir', type=Path)
    args = parser.parse_args()
    bridge = DesktopBridge(args.data_dir, [(args.scan_dir, '测试桌面')] if args.scan_dir else None)
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    while line := sys.stdin.readline(48 * 1024 * 1024 + 1):
        request = {}
        try:
            if len(line) > 48 * 1024 * 1024:
                raise ValueError('请求超过大小限制。')
            request = json.loads(line)
            result = bridge.dispatch(request['operation'], request.get('payload', {}))
            response = {'id': request['id'], 'result': result}
        except Exception as error:
            response = {'id': request.get('id'), 'error': friendly_error(error)}
        print(json.dumps(response, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
