"""Publish a manifest-defined private GitHub release; never log credentials.

Usage: python tools/sync-github-release.py MANIFEST [--stage prepare|upload|verify|publish]
The manifest is local deployment data, not a source file to commit. Published
assets are immutable here: a same-name/different-digest asset is an error.
"""
from __future__ import annotations
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

REPOSITORY = 'yky0013/ThemeStudio'
API = 'https://api.github.com/repos/' + REPOSITORY


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def credentials():
    env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'Never'}
    result = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                            text=True, capture_output=True, env=env, check=False)
    if result.returncode:
        raise RuntimeError('GitHub credential manager could not authenticate.')
    fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    if not fields.get('password'):
        raise RuntimeError('GitHub credential unavailable.')
    return fields['password']


class GitHub:
    def __init__(self):
        self.headers = {'Authorization': 'Bearer ' + credentials(), 'Accept': 'application/vnd.github+json',
                        'User-Agent': 'ThemeStudio-release-sync', 'X-GitHub-Api-Version': '2022-11-28'}
        if self.request('https://api.github.com/user')['login'] != 'yky0013':
            raise RuntimeError('Unexpected GitHub account.')
        repo = self.request(API)
        if repo.get('visibility') != 'private' or not repo.get('permissions', {}).get('push'):
            raise RuntimeError('Expected the writable private ThemeStudio repository.')

    def request(self, url, method='GET', body=None, allow_missing=False):
        if urllib.parse.urlsplit(url).hostname != 'api.github.com':
            raise ValueError('Unexpected API host.')
        data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        headers = {**self.headers, **({'Content-Type': 'application/json'} if data else {})}
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    raw = response.read()
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as error:
                if allow_missing and error.code == 404:
                    return None
                if method == 'GET' and error.code in {429, 500, 502, 503, 504} and attempt < 2:
                    time.sleep(3); continue
                raise RuntimeError(f'GitHub API {method} failed with HTTP {error.code}.') from None
            except OSError:
                if method != 'GET' or attempt == 2:
                    raise RuntimeError(f'GitHub API {method} connection interrupted.') from None
                time.sleep(3)

    def release(self, tag):
        # GitHub's by-tag endpoint can omit drafts, so use the authenticated list.
        found, page = [], 1
        while True:
            batch = self.request(API + f'/releases?per_page=100&page={page}')
            found.extend(item for item in batch if item['tag_name'] == tag)
            if len(batch) < 100:
                break
            page += 1
        if len(found) > 1:
            raise RuntimeError('Multiple release records for this tag; inspect them before upload.')
        return found[0] if found else None

    def assets(self, release_id):
        items, page = [], 1
        while True:
            batch = self.request(API + f'/releases/{release_id}/assets?per_page=100&page={page}')
            items.extend(batch)
            if len(batch) < 100:
                return items
            page += 1

    def upload(self, release, path):
        parsed = urllib.parse.urlsplit(release['upload_url'].split('{', 1)[0])
        if parsed.scheme != 'https' or parsed.hostname != 'uploads.github.com':
            raise ValueError('Unexpected release upload host.')
        target = urllib.parse.urlunsplit(parsed) + '?name=' + urllib.parse.quote(path.name, safe='')
        headers = {**self.headers, 'Content-Type': 'application/octet-stream', 'Content-Length': str(path.stat().st_size)}
        curl = shutil.which('curl.exe') or shutil.which('curl')
        if curl:
            # Pass the authorization header through stdin, never argv or a disk file.
            quote = lambda value: '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
            config = ''.join('header = ' + quote(key + ': ' + value) + '\n' for key, value in headers.items())
            proxy = urllib.request.getproxies().get('https')
            if proxy:
                config += 'proxy = ' + quote(proxy) + '\n'
            result = subprocess.run([curl, '--silent', '--show-error', '--http1.1', '--connect-timeout', '30',
                '--max-time', '1200', '--request', 'POST', '--data-binary', '@' + str(path),
                '--config', '-', '--url', target, '--write-out', '\n%{http_code}'],
                input=config.encode(), capture_output=True, check=False)
            if result.returncode:
                raise RuntimeError(f'GitHub upload transport failed (curl {result.returncode}).')
            body, code = result.stdout.rsplit(b'\n', 1)
            if code != b'201':
                raise RuntimeError('GitHub upload failed with HTTP ' + code.decode('ascii', errors='replace'))
            return json.loads(body)
        # urllib streams the file through the user's standard HTTPS proxy settings.
        with path.open('rb') as stream:
            request = urllib.request.Request(target, data=stream, headers=headers, method='POST')
            with urllib.request.urlopen(request, timeout=1200) as response:
                if response.status != 201:
                    raise RuntimeError(f'GitHub asset upload failed with HTTP {response.status}.')
                return json.loads(response.read())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--stage', choices=['prepare', 'upload', 'verify', 'publish'], default='verify')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    tag, commit = manifest['tag'], manifest['commit']
    if manifest['repository'] != REPOSITORY or not re.fullmatch(r'v\d+\.\d+\.\d+', tag) or not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Invalid repository, version or commit.')
    if not manifest.get('prerelease', True) and not manifest.get('realExplorerVisualVerified', False):
        raise ValueError('Unverified Explorer visuals must remain a prerelease.')
    local = []
    for item in manifest['assets']:
        path = Path(item['path']).resolve()
        if path.name != item['name'] or not path.is_file() or path.stat().st_size != item['bytes'] or sha256(path) != item['sha256']:
            raise ValueError('Local artifact no longer matches manifest: ' + item['name'])
        local.append((item, path))
    api = GitHub()
    remote = api.request(API + '/commits/' + urllib.parse.quote(tag, safe=''))
    if remote['sha'] != commit:
        raise RuntimeError('Remote tag differs from the reviewed source commit.')
    release = api.release(tag)
    if release is None:
        if args.stage not in {'prepare', 'upload'}:
            raise RuntimeError('Prepare the release before verification or publication.')
        release = api.request(API + '/releases', 'POST', {
            'tag_name': tag, 'target_commitish': commit, 'name': manifest['title'], 'body': manifest['notes'],
            'draft': True, 'prerelease': manifest.get('prerelease', True), 'make_latest': 'false'})
    if release.get('prerelease') != manifest.get('prerelease', True):
        raise RuntimeError('Release classification does not match the manifest.')
    if args.stage == 'prepare':
        print(json.dumps({'tag': tag, 'url': release['html_url'], 'draft': release['draft']}), flush=True)
        return
    verified = []
    for item, path in local:
        for attempt in range(4):
            matches = [asset for asset in api.assets(release['id']) if asset['name'] == item['name']]
            if (len(matches) == 1 and matches[0]['state'] == 'starter' and not matches[0].get('digest')
                    and matches[0]['size'] in {0, item['bytes']}
                    and args.stage == 'upload' and release['draft']):
                # A failed starter carries the advertised Content-Length even
                # when no completed downloadable artifact exists.
                api.request(API + '/releases/assets/' + str(matches[0]['id']), 'DELETE')
                matches = []
            if matches:
                if len(matches) != 1 or matches[0]['state'] != 'uploaded' or matches[0]['size'] != item['bytes'] or matches[0].get('digest') != 'sha256:' + item['sha256']:
                    raise RuntimeError('Remote asset mismatch; not overwritten: ' + item['name'])
                verified.append({'name': item['name'], 'sha256': item['sha256'], 'bytes': item['bytes'],
                                 'url': matches[0]['browser_download_url'], 'remoteDigestVerified': True})
                print('Verified ' + tag + ' ' + item['name'], flush=True)
                break
            if args.stage != 'upload':
                raise RuntimeError('Remote asset missing: ' + item['name'])
            if attempt == 3:
                raise RuntimeError('Asset upload failed after retries: ' + item['name'])
            if not release['draft']:
                raise RuntimeError('Uploads only target unpublished drafts.')
            print('Uploading ' + tag + ' ' + item['name'], flush=True)
            try:
                api.upload(release, path)
            except (OSError, http.client.HTTPException, RuntimeError) as failure:
                # Refresh by exact name before a retry: an interrupted response
                # can still have produced a complete GitHub asset.
                print('Upload interrupted; rechecking remote state (' + type(failure).__name__ + ').', flush=True)
                time.sleep(3)
        else:
            raise RuntimeError('Asset upload could not be verified: ' + item['name'])
    if args.stage == 'publish' and release['draft']:
        release = api.request(API + '/releases/' + str(release['id']), 'PATCH', {
            'draft': False, 'name': manifest['title'], 'body': manifest['notes'], 'make_latest': 'false'})
    result = {'repository': REPOSITORY, 'tag': tag, 'commit': commit, 'url': release['html_url'],
              'draft': release['draft'], 'prerelease': release['prerelease'], 'assets': verified}
    args.manifest.with_suffix('.verified.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'tag': tag, 'draft': result['draft'], 'assetsVerified': len(verified), 'url': result['url']}), flush=True)


if __name__ == '__main__':
    main()
