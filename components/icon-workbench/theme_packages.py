"""Portable, data-only theme archives; immutable assets and an atomic library index."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat
import tempfile
import zipfile

from PIL import Image

from backend import atomic_json
from cursor_adapter import ROLE_KEYS, validate_cursor

MAX_ARCHIVE = 512 * 1024 * 1024
MAX_EXPANDED = 1024 * 1024 * 1024
MAX_ENTRIES = 2048
IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
DATA_TYPES = IMAGE_TYPES | {'.ico', '.cur', '.ani', '.mp4', '.txt', '.json'}
PACK_HOST = 'https://packs.theme-studio.invalid/'


def file_hash(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r'(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})', value):
        raise ValueError('版本号应为三个数字，例如 1.0.0。')
    return tuple(map(int, value.split('.')))


def relative_path(value):
    if not isinstance(value, str) or not value or len(value) > 180 or '\\' in value:
        raise ValueError('数据包内的路径无效。请使用包内相对路径和 / 分隔符。')
    parts = value.split('/')
    for part in parts:
        if (not part or part in {'.', '..'} or part[-1] in '. ' or
                any(ord(c) < 32 or c in ':*?"<>|' for c in part) or
                re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\..*)?', part, re.I)):
            raise ValueError('数据包含有不安全的文件路径。')
    return value


def checked_asset(root, value, suffixes):
    path = Path(root) / relative_path(value)
    if path.suffix.lower() not in suffixes or not path.is_file() or path.is_symlink():
        raise ValueError(f'素材缺失或格式不支持：{value}')
    if not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('素材不能指向数据包以外。')
    return path


def checked_image(root, value, icon=False):
    path = checked_asset(root, value, {'.ico'} if icon else IMAGE_TYPES)
    if path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError('单张图片或图标不能超过 32 MB。')
    with Image.open(path) as image:
        if image.width * image.height > 40_000_000 or getattr(image, 'is_animated', False):
            raise ValueError('静态壁纸和预览须为不超过 4000 万像素的静态图片。')
        if icon and image.format != 'ICO':
            raise ValueError('图标必须是有效的 ICO 文件。')
        image.load()
    return value


def text_field(data, key, default='', limit=300):
    value = data.get(key, default)
    if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 for c in value):
        raise ValueError(f'数据包字段 {key} 无效。')
    return value.strip()


def validate_manifest(root, manifest):
    if not isinstance(manifest, dict) or type(manifest.get('schemaVersion')) is not int or manifest['schemaVersion'] != 1:
        raise ValueError('不支持此数据包格式，请使用 schemaVersion 为 1 的 theme.json。')
    ident = manifest.get('id')
    if not isinstance(ident, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', ident):
        raise ValueError('套装 id 应为 1–64 位小写字母、数字或连字符。')
    version_tuple(manifest.get('version'))
    name = text_field(manifest, 'name', limit=80)
    if not name:
        raise ValueError('请在 theme.json 中填写套装名称。')
    result = {key: text_field(manifest, key) for key in ('subtitle', 'author', 'artwork', 'motionLabel')}
    result.update(schemaVersion=1, id=ident, name=name, version=manifest['version'])
    for key, default in (('accent', '#7967c6'), ('pale', '#e6e0f7')):
        value = manifest.get(key, default)
        if not isinstance(value, str) or not re.fullmatch(r'#[a-fA-F0-9]{6}', value):
            raise ValueError(f'{key} 应为 #RRGGBB 颜色。')
        result[key] = value
    result['wallpaper'] = checked_image(root, manifest.get('wallpaper'))
    result['thumbnail'] = checked_image(root, manifest.get('thumbnail', result['wallpaper']))
    motion = manifest.get('animatedWallpaper')
    if motion:
        path = checked_asset(root, motion, {'.mp4'})
        with path.open('rb') as stream:
            header = stream.read(32)
        if len(header) < 12 or header[4:8] != b'ftyp':
            raise ValueError('动态壁纸不是有效的 MP4 容器。')
        result['animatedWallpaper'] = motion
        result['motionLabel'] = result['motionLabel'] or '动态壁纸'
    size = manifest.get('cursorSize', 48)
    if type(size) is not int or size not in range(32, 257, 16):
        raise ValueError('cursorSize 应为 32–256，按 16 递增。')
    result['cursorSize'] = size
    cursors = manifest.get('cursors', {})
    if not isinstance(cursors, dict) or (cursors and set(cursors) != set(ROLE_KEYS)):
        raise ValueError('带指针的套装必须提供完整的 17 状态 cursors。')
    for value in cursors.values():
        validate_cursor(checked_asset(root, value, {'.cur', '.ani'}))
    result['cursors'] = cursors
    if manifest.get('cursorPreview'):
        result['cursorPreview'] = checked_image(root, manifest['cursorPreview'])
    icons = manifest.get('icons', {})
    if not isinstance(icons, dict) or len(icons) > 100:
        raise ValueError('套装最多包含 100 款图标。')
    for key, value in icons.items():
        if not isinstance(key, str) or not re.fullmatch(r'[a-z0-9-]{1,40}', key) or not isinstance(value, dict):
            raise ValueError('图标配置无效。')
        checked_image(root, value.get('file'), icon=True)
        matches = value.get('matches')
        if not isinstance(matches, list) or not 1 <= len(matches) <= 30 or any(
                not isinstance(word, str) or not word.strip() or len(word) > 80 for word in matches):
            raise ValueError('每款图标须指定 1–30 个快捷方式名称关键词。')
    result['icons'] = icons
    return result


class PackageLibrary:
    def __init__(self, data):
        self.root = Path(data) / 'theme-packs'
        self.assets = self.root / 'assets'
        self.index = self.root / 'index.json'

    def entries(self):
        if not self.index.exists():
            return {}
        data = json.loads(self.index.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('套装索引损坏，请保留数据目录后修复。')
        return data

    def catalog(self):
        items = []
        for ident, entry in self.entries().items():
            digest = entry['sha256']
            if not re.fullmatch(r'[a-f0-9]{64}', digest):
                raise ValueError('套装资源编号无效。')
            item = dict(entry['manifest'])
            item.update(id=ident, packageId=item['id'], source='imported', assetBase=PACK_HOST + digest + '/',
                        assetFolder=digest, iconMatches={key: icon['matches'] for key, icon in item['icons'].items()})
            items.append(item)
        return items

    def import_archive(self, source):
        source = Path(source)
        if source.suffix.lower() not in {'.zip', '.tspack'} or not source.is_file():
            raise ValueError('请选择 .tspack 或 .zip 主题数据包。')
        if not 0 < source.stat().st_size <= MAX_ARCHIVE:
            raise ValueError('主题数据包不能为空或超过 512 MB。')
        self.root.mkdir(parents=True, exist_ok=True)
        self.assets.mkdir(exist_ok=True)
        # Work on a snapshot so a source being replaced cannot change after verification.
        with tempfile.TemporaryDirectory(prefix='import-', dir=self.root) as temporary:
            temp = Path(temporary)
            copied = temp / 'archive.zip'
            with source.open('rb') as incoming, copied.open('xb') as output:
                size = 0
                while chunk := incoming.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_ARCHIVE:
                        raise ValueError('主题数据包超过 512 MB。')
                    output.write(chunk)
            digest = file_hash(copied)
            staging = temp / 'assets'
            staging.mkdir()
            with zipfile.ZipFile(copied) as archive:
                entries = archive.infolist()
                if not entries or len(entries) > MAX_ENTRIES:
                    raise ValueError('数据包文件数量无效或超过 2048 项。')
                seen = set()
                expanded = 0
                for entry in entries:
                    if entry.orig_filename != entry.filename:
                        raise ValueError('数据包文件名含有被系统改写的路径或空字符。')
                    name = relative_path(entry.filename.rstrip('/') if entry.is_dir() else entry.filename)
                    mode = stat.S_IFMT(entry.external_attr >> 16)
                    if mode not in {0, stat.S_IFREG, stat.S_IFDIR} or entry.flag_bits & 1:
                        raise ValueError('数据包不能包含链接、特殊文件或加密文件。')
                    if name.casefold() in seen:
                        raise ValueError('数据包内含重复文件名。')
                    seen.add(name.casefold())
                    expanded += entry.file_size
                    if entry.file_size > MAX_ARCHIVE or expanded > MAX_EXPANDED:
                        raise ValueError('数据包解压后超过大小限制。')
                    if entry.is_dir():
                        continue
                    if Path(name).suffix.lower() not in DATA_TYPES:
                        raise ValueError(f'主题数据包只接受素材文件，不接受：{name}')
                    if name == 'theme.json' and entry.file_size > 256 * 1024:
                        raise ValueError('theme.json 不能超过 256 KB。')
                    target = staging / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(entry) as incoming, target.open('xb') as output:
                        written = 0
                        while chunk := incoming.read(1024 * 1024):
                            written += len(chunk)
                            if written > entry.file_size:
                                raise ValueError('数据包文件大小与目录不符。')
                            output.write(chunk)
                manifest_path = staging / 'theme.json'
                if not manifest_path.is_file():
                    raise ValueError('数据包根目录缺少 theme.json。普通 Windows .themepack 不适用于本应用。')
                manifest = validate_manifest(staging, json.loads(manifest_path.read_text(encoding='utf-8-sig')))
            ident = 'imported-' + hashlib.sha256(manifest['id'].encode('utf-8')).hexdigest()[:32]
            entries = self.entries()
            previous = entries.get(ident)
            if previous:
                if previous['sha256'] == digest:
                    return {'id': ident, 'name': manifest['name'], 'version': manifest['version'], 'duplicate': True}
                if version_tuple(manifest['version']) <= version_tuple(previous['manifest']['version']):
                    raise ValueError('已存在同名同版本或更新的套装。修改素材后请提高 theme.json 中的 version。')
            destination = self.assets / digest
            if not destination.exists():
                staging.rename(destination)
            entries[ident] = {'sha256': digest, 'manifest': manifest}
            atomic_json(self.index, entries)
            return {'id': ident, 'name': manifest['name'], 'version': manifest['version'], 'duplicate': False, 'updated': bool(previous)}
