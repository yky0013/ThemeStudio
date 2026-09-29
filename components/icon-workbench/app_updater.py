"""Explicit stable-release checks and verified installer staging. Never executes code."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from backend import atomic_json
from theme_packages import file_hash, version_tuple

REPOSITORY = 'yky0013/ThemeStudio'
RELEASE_PAGE = 'https://github.com/' + REPOSITORY + '/releases'
LATEST_URL = 'https://api.github.com/repos/' + REPOSITORY + '/releases/latest'
MAX_INSTALLER = 1024 * 1024 * 1024
NAME_PATTERN = r'ThemeStudio-([0-9]+\.[0-9]+\.[0-9]+)-Windows-x64-Setup\.exe'


def app_version():
    path = (Path(sys.executable).parent.parent / 'resources' / 'application.json' if getattr(sys, 'frozen', False)
            else Path(__file__).resolve().parents[2] / 'package.json')
    value = json.loads(path.read_text(encoding='utf-8-sig'))['version']
    version_tuple(value)
    return value


def safe_url(url, asset=False):
    if not isinstance(url, str):
        raise ValueError('更新地址无效。')
    parsed = urllib.parse.urlsplit(url)
    hosts = {'github.com', 'api.github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'}
    if (parsed.scheme != 'https' or parsed.hostname not in hosts or parsed.username or parsed.password or
            parsed.port not in {None, 443} or parsed.fragment):
        raise ValueError('更新仅接受 GitHub 官方 HTTPS 下载地址。')
    if asset and (parsed.hostname != 'github.com' or not parsed.path.startswith('/' + REPOSITORY + '/releases/download/')):
        raise ValueError('更新文件不属于 ThemeStudio 发布源。')
    return url


class GitHubRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        safe_url(newurl)
        return super().redirect_request(request, response, code, message, headers, newurl)


def open_url(url):
    safe_url(url)
    request = urllib.request.Request(url, headers={
        'User-Agent': 'ThemeStudio-Updater', 'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    return urllib.request.build_opener(GitHubRedirect()).open(request, timeout=30)


def fetch_bytes(url, limit):
    with open_url(url) as response:
        value = response.read(limit + 1)
    if len(value) > limit:
        raise ValueError('更新服务器返回的数据过大。')
    return value


def parse_checksum(data, name):
    text = data.decode('utf-8-sig')
    found = []
    for line in text.splitlines():
        line = line.strip()
        match = re.fullmatch(r'([a-fA-F0-9]{64})(?:\s+\*?(.+))?', line)
        if match and (match[2] is None or match[2] == name):
            found.append(match[1].lower())
    if len(found) != 1:
        raise ValueError('找不到与安装包文件名对应的唯一 SHA-256 校验值。')
    return found[0]


class AppUpdater:
    def __init__(self, data, current=None):
        self.current = current or app_version()
        version_tuple(self.current)
        self.root = Path(data) / 'updates'
        self.record_path = self.root / 'staged.json'
        self.cancel_path = self.root / 'cancel'
        self.available = None
        self.progress = lambda **values: None

    def state(self):
        prepared = None
        if self.record_path.is_file():
            try:
                record = json.loads(self.record_path.read_text(encoding='utf-8'))
                self.record_file(record)
                prepared = self.public(record)
            except (KeyError, ValueError, OSError):
                pass
        return {'currentVersion': self.current, 'releasePage': RELEASE_PAGE, 'prepared': prepared}

    @staticmethod
    def public(record):
        return {key: record[key] for key in ('id', 'version', 'name', 'size', 'sha256', 'source')}

    def check(self):
        self.available = None
        try:
            release = json.loads(fetch_bytes(LATEST_URL, 2 * 1024 * 1024))
        except urllib.error.HTTPError as error:
            error.close()
            if error.code == 404:
                raise ValueError('更新源暂未提供可公开访问的正式版本。可以选择离线安装包更新。') from error
            if error.code in {403, 429}:
                raise ValueError('GitHub 暂时限制了更新请求，请稍后重试或使用离线更新。') from error
            raise ValueError(f'检查更新失败（HTTP {error.code}），请稍后重试。') from error
        except (OSError, ValueError) as error:
            raise ValueError('无法连接更新源，请检查网络后重试，或使用离线更新。') from error
        if not isinstance(release, dict) or release.get('draft') or release.get('prerelease'):
            raise ValueError('更新源没有可用的正式版本。')
        version = str(release.get('tag_name', '')).removeprefix('v')
        newer = version_tuple(version) > version_tuple(self.current)
        result = {'currentVersion': self.current, 'latestVersion': version, 'available': newer,
                  'releasePage': RELEASE_PAGE, 'notes': str(release.get('body') or '')[:12000]}
        if not newer:
            return result
        name = f'ThemeStudio-{version}-Windows-x64-Setup.exe'
        assets = release.get('assets', [])
        matches = [asset for asset in assets if isinstance(asset, dict) and asset.get('name') == name and asset.get('state') == 'uploaded']
        if len(matches) != 1:
            raise ValueError('新版本尚未提供完整的 Windows x64 安装包，请稍后重试。')
        asset = matches[0]
        size = asset.get('size')
        if type(size) is not int or not 0 < size <= MAX_INSTALLER:
            raise ValueError('更新安装包大小无效。')
        digest = asset.get('digest')
        if isinstance(digest, str) and re.fullmatch(r'sha256:[a-fA-F0-9]{64}', digest):
            checksum = digest[7:].lower()
        else:
            checksums = [item for item in assets if isinstance(item, dict) and item.get('name') in {name + '.sha256', 'SHA256.txt', 'SHA256SUMS'} and item.get('state') == 'uploaded']
            if not checksums:
                raise ValueError('新版本缺少 SHA-256 校验信息，暂不能下载更新。')
            checksums.sort(key=lambda item: item['name'] != name + '.sha256')
            checksum = parse_checksum(fetch_bytes(safe_url(checksums[0].get('browser_download_url'), asset=True), 64 * 1024), name)
        self.available = {'version': version, 'name': name, 'size': size, 'sha256': checksum,
                          'url': safe_url(asset.get('browser_download_url'), asset=True), 'source': 'GitHub 正式版本'}
        return result | {'size': size, 'sha256': checksum}

    def prepare_stream(self, stream, descriptor):
        self.root.mkdir(parents=True, exist_ok=True)
        ident = uuid.uuid4().hex
        folder = self.root / ident
        folder.mkdir()
        partial = folder / (descriptor['name'] + '.partial')
        output = folder / descriptor['name']
        received = 0
        deadline = time.monotonic() + 600
        last_update = 0
        try:
            with partial.open('xb') as target:
                while True:
                    if self.cancel_path.exists():
                        raise ValueError('已取消更新下载。')
                    if time.monotonic() > deadline:
                        raise ValueError('更新下载超时，请重试。')
                    chunk = stream.read(256 * 1024)
                    if not chunk:
                        break
                    received += len(chunk)
                    if received > descriptor['size'] or received > MAX_INSTALLER:
                        raise ValueError('安装包大小与发布信息不符。')
                    target.write(chunk)
                    if time.monotonic() - last_update >= .3:
                        self.progress(stage='download', received=received, total=descriptor['size'])
                        last_update = time.monotonic()
            self.progress(stage='verify', received=received, total=descriptor['size'])
            if received != descriptor['size'] or file_hash(partial) != descriptor['sha256']:
                raise ValueError('安装包 SHA-256 或大小校验失败，已丢弃下载内容，请重试。')
            with partial.open('rb') as check:
                if check.read(2) != b'MZ':
                    raise ValueError('更新文件不是 Windows 安装程序。')
            if self.cancel_path.exists():
                raise ValueError('已取消更新下载。')
            partial.rename(output)
            record = {key: descriptor[key] for key in ('version', 'name', 'size', 'sha256', 'source')}
            record['id'] = ident
            atomic_json(self.record_path, record)
            return self.public(record)
        finally:
            partial.unlink(missing_ok=True)
            if not output.exists():
                folder.rmdir()
            self.cancel_path.unlink(missing_ok=True)

    def download(self, version):
        if not self.available or self.available['version'] != version:
            raise ValueError('请先检查更新，再下载显示的新版本。')
        self.root.mkdir(parents=True, exist_ok=True)
        self.cancel_path.unlink(missing_ok=True)
        try:
            with open_url(self.available['url']) as stream:
                return self.prepare_stream(stream, self.available)
        except (urllib.error.URLError, TimeoutError) as error:
            raise ValueError('更新下载中断，请检查网络后重试。') from error

    def prepare_local(self, source):
        source = Path(source)
        match = re.fullmatch(NAME_PATTERN, source.name)
        if not match or not source.is_file():
            raise ValueError('请选择 ThemeStudio-版本号-Windows-x64-Setup.exe。')
        version = match[1]
        if version_tuple(version) <= version_tuple(self.current):
            raise ValueError('请选择比当前版本更新的安装包。')
        checksum = source.with_name(source.name + '.sha256')
        if not checksum.is_file() or checksum.stat().st_size > 64 * 1024:
            raise ValueError('请把安装包配套的 .exe.sha256 文件放在同一文件夹，再重新选择安装包。')
        size = source.stat().st_size
        if not 0 < size <= MAX_INSTALLER:
            raise ValueError('安装包不能为空或超过 1 GB。')
        descriptor = {'version': version, 'name': source.name, 'size': size,
                      'sha256': parse_checksum(checksum.read_bytes(), source.name), 'source': '本地安装包'}
        self.cancel_path.unlink(missing_ok=True)
        with source.open('rb') as stream:
            return self.prepare_stream(stream, descriptor)

    def record_file(self, record):
        ident = record['id']
        if not isinstance(ident, str) or not re.fullmatch(r'[a-f0-9]{32}', ident):
            raise ValueError('更新缓存编号无效。')
        expected = f"ThemeStudio-{record['version']}-Windows-x64-Setup.exe"
        if record['name'] != expected or version_tuple(record['version']) <= version_tuple(self.current):
            raise ValueError('更新缓存的版本无效，请重新检查更新。')
        path = self.root / ident / expected
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(self.root.resolve()):
            raise ValueError('安装包缓存已丢失，请重新下载。')
        return path

    def verify(self, ident):
        if not self.record_path.is_file():
            raise ValueError('请先下载或选择安装包。')
        record = json.loads(self.record_path.read_text(encoding='utf-8'))
        if ident != record['id']:
            raise ValueError('已选择其他安装包，请刷新更新页面。')
        path = self.record_file(record)
        if path.stat().st_size != record['size'] or file_hash(path) != record['sha256']:
            raise ValueError('安装包在校验后发生变更，请重新下载。')
        return self.public(record) | {'path': str(path)}

    def dispatch(self, operation, payload):
        if operation == 'updates.state':
            return self.state()
        if operation == 'updates.check':
            return self.check()
        if operation == 'updates.download':
            return self.download(payload.get('version'))
        if operation == 'updates.local':
            return self.prepare_local(payload.get('path', ''))
        if operation == 'updates.verify':
            return self.verify(payload.get('id'))
        raise ValueError('不支持的更新操作。')
