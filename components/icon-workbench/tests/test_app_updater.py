"""Updater trust/size/version boundaries. No installer or system settings are executed."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app_updater import AppUpdater, LATEST_URL, safe_url


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.updater = AppUpdater(self.root / 'data', '0.4.0')
        self.body = b'MZ' + b'fixture, never executed' * 100
        self.name = 'ThemeStudio-0.4.1-Windows-x64-Setup.exe'
        self.sha256 = hashlib.sha256(self.body).hexdigest()

    def release(self, version='0.4.1'):
        name = f'ThemeStudio-{version}-Windows-x64-Setup.exe'
        return {'tag_name': 'v' + version, 'draft': False, 'prerelease': False, 'body': 'Changes', 'assets': [
            {'name': name, 'state': 'uploaded', 'size': len(self.body), 'digest': 'sha256:' + self.sha256,
             'browser_download_url': f'https://github.com/yky0013/ThemeStudio/releases/download/v{version}/{name}'}]}

    def check(self, release=None):
        with patch('app_updater.fetch_bytes', return_value=json.dumps(release or self.release()).encode()):
            return self.updater.check()

    def test_numeric_version_comparison_no_downgrades(self):
        self.assertTrue(self.check(self.release('0.10.0'))['available'])
        self.assertFalse(self.check(self.release('0.3.9'))['available'])
        self.assertIsNone(self.updater.available)
        self.assertFalse(self.check(self.release('0.4.0'))['available'])

    def test_private_or_missing_release_is_not_reported_up_to_date(self):
        self.check()
        with patch('app_updater.fetch_bytes', side_effect=HTTPError(LATEST_URL, 404, 'Not Found', {}, None)):
            with self.assertRaisesRegex(ValueError, '公开访问'):
                self.updater.check()
        self.assertIsNone(self.updater.available)

    def test_prerelease_missing_installer_and_missing_hash_are_rejected(self):
        prerelease = self.release() | {'prerelease': True}
        missing = self.release() | {'assets': []}
        no_digest = self.release()
        no_digest['assets'][0].pop('digest')
        for release in (prerelease, missing, no_digest):
            with self.assertRaises(ValueError):
                self.check(release)

    def test_sidecar_digest_fallback(self):
        release = self.release()
        release['assets'][0].pop('digest')
        release['assets'].append({'name': self.name + '.sha256', 'state': 'uploaded',
                                  'browser_download_url': release['assets'][0]['browser_download_url'] + '.sha256'})
        with patch('app_updater.fetch_bytes', side_effect=[json.dumps(release).encode(), (self.sha256 + '  ' + self.name).encode()]):
            self.assertEqual(self.updater.check()['sha256'], self.sha256)

    def test_download_success_can_resume_and_reverify_after_restart(self):
        self.check()
        with patch('app_updater.open_url', return_value=io.BytesIO(self.body)):
            prepared = self.updater.download('0.4.1')
        reopened = AppUpdater(self.root / 'data', '0.4.0')
        self.assertEqual(reopened.state()['prepared']['id'], prepared['id'])
        verified = reopened.verify(prepared['id'])
        self.assertEqual(Path(verified['path']).read_bytes(), self.body)
        Path(verified['path']).write_bytes(b'MZchanged')
        with self.assertRaisesRegex(ValueError, '发生变更'):
            reopened.verify(prepared['id'])

    def test_corrupt_and_truncated_downloads_never_become_installable(self):
        self.check()
        for content in (self.body[:-1], self.body + b'extra', b'XX' + self.body[2:]):
            with patch('app_updater.open_url', return_value=io.BytesIO(content)), self.assertRaises(ValueError):
                self.updater.download('0.4.1')
            self.assertIsNone(self.updater.state()['prepared'])
            self.assertEqual(list(self.updater.root.rglob('*.partial')), [])

    def test_cancel_cleans_partial_and_keeps_previous_update(self):
        self.check()
        with patch('app_updater.open_url', return_value=io.BytesIO(self.body)):
            previous = self.updater.download('0.4.1')
        self.updater.progress = lambda **_: self.updater.cancel_path.write_text('cancel')
        with patch('app_updater.open_url', return_value=io.BytesIO(self.body)), self.assertRaisesRegex(ValueError, '取消'):
            self.updater.download('0.4.1')
        self.assertEqual(self.updater.state()['prepared']['id'], previous['id'])

    def test_offline_update_requires_matching_checksum_and_newer_version(self):
        source = self.root / self.name
        source.write_bytes(self.body)
        with self.assertRaisesRegex(ValueError, 'sha256'):
            self.updater.prepare_local(source)
        checksum = source.with_name(source.name + '.sha256')
        checksum.write_text(self.sha256 + '  ' + self.name, encoding='utf-8')
        staged = self.updater.prepare_local(source)
        source.unlink()
        self.assertTrue(Path(self.updater.verify(staged['id'])['path']).is_file())
        stale = self.root / 'ThemeStudio-0.3.9-Windows-x64-Setup.exe'
        stale.write_bytes(self.body)
        with self.assertRaisesRegex(ValueError, '更新的安装包'):
            self.updater.prepare_local(stale)

    def test_urls_cannot_redirect_to_arbitrary_servers(self):
        for url in ('http://github.com/a', 'https://github.com.evil.invalid/a', 'file:///C:/file',
                    'https://user@github.com/a', 'https://github.com:8443/a'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                safe_url(url)
        release = self.release()
        release['assets'][0]['browser_download_url'] = 'https://github.com/other/repo/releases/download/a/file.exe'
        with self.assertRaises(ValueError):
            self.check(release)


if __name__ == '__main__':
    unittest.main()
