"""Pack validation and real fixture shortcut transactions; no system appearance writes."""
import base64, ctypes, hashlib, json, shutil, struct, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop_bridge import DesktopBridge
from template_adapter import StaticWallpaper, TemplateAdapter
from cursor_adapter import ROLE_KEYS, validate_cursor
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]

class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.desktop=self.root/'desktop';self.desktop.mkdir()
        self.shortcut=self.desktop/'Chrome 浏览器.url';self.shortcut.write_text('[InternetShortcut]\nURL=https://example.org\n',encoding='utf-8')
        self.bridge=DesktopBridge(self.root/'data',[(self.desktop,'fixture')]);self.adapter=self.bridge.templates
        self.wallpapers=self.bridge.store.directory/'wallpapers';self.wallpapers.mkdir(exist_ok=True)
        image=ROOT/'assets/templates/wuthering-waves/wallpaper.jpg'
        self.media_id=hashlib.sha256(image.read_bytes()).hexdigest()+'.jpg';shutil.copyfile(image,self.wallpapers/self.media_id)
        self.current=['']
        self.original_current=patch('template_adapter.current_wallpaper',side_effect=lambda:self.current[0]);self.original_current.start();self.addCleanup(self.original_current.stop)
        self.original_set=patch('template_adapter.set_wallpaper',side_effect=lambda value:self.current.__setitem__(0,str(value)));self.mock_set=self.original_set.start();self.addCleanup(self.original_set.stop)

    def test_every_pack_has_decodable_wallpaper_icons_and_all_native_cursor_roles(self):
        catalog=self.adapter.catalog();self.assertEqual(len(catalog),10);self.assertEqual(len({x['id'] for x in catalog}),10)
        for item in catalog:
            folder=self.adapter.root/item['id']
            self.assertTrue((self.adapter.root/item['animatedWallpaper']).is_file())
            with Image.open(folder/'wallpaper.jpg') as image:self.assertGreater(image.width,1500);image.verify()
            for role in ROLE_KEYS:
                path=folder/'cursors'/(role+'.cur');validate_cursor(path)
                raw=path.read_bytes();x,y=struct.unpack_from('<HH',raw,10);self.assertLess(x,48);self.assertLess(y,48)
            for key in item['iconMatches']:
                with Image.open(folder/'icons'/(key+'.ico')) as image:self.assertEqual(len(image.ico.sizes()),7)

    def test_template_id_traversal_is_rejected_before_writes(self):
        for value in ('../escape','C:\\escape','not-a-template',None):
            with self.assertRaises(ValueError):self.adapter.plan(value)
        self.mock_set.assert_not_called()

    def test_default_template_application_preserves_original_cursors_and_shortcuts(self):
        before = self.shortcut.read_bytes()
        with patch.object(self.bridge.cursors, 'apply') as cursors:
            result = self.bridge.dispatch('templates.apply', {'id': 'wuthering-waves', 'mediaId': self.media_id})
            self.assertEqual(result['iconsApplied'], 0)
            self.assertEqual(result['cursorsApplied'], 0)
            cursors.assert_not_called()
        self.assertEqual(self.shortcut.read_bytes(), before)
        self.assertEqual(Path(self.current[0]).name, self.media_id)
        self.adapter.restore()
        self.assertEqual(self.shortcut.read_bytes(), before)
        self.assertEqual(self.current[0], '')

    def test_only_explicit_boolean_true_can_opt_into_accessories(self):
        before = self.shortcut.read_bytes()
        for choice in (None, False, 'false', 'true', 1):
            with self.subTest(choice=choice), patch.object(self.bridge.cursors, 'apply') as cursors:
                result = self.bridge.dispatch('templates.apply', {'id': 'wuthering-waves', 'mediaId': self.media_id, 'icons': choice, 'cursors': choice})
                self.assertEqual(result['iconsApplied'], 0)
                self.assertEqual(result['cursorsApplied'], 0)
                self.assertEqual(self.shortcut.read_bytes(), before)
                cursors.assert_not_called()
                self.adapter.restore()

    def test_animated_template_keeps_poster_and_restore_record(self):
        video=ROOT/'assets/templates/wuthering-waves/wallpaper-motion.mp4'
        motion_id=hashlib.sha256(video.read_bytes()).hexdigest()+'.mp4'
        shutil.copyfile(video,self.wallpapers/motion_id)
        applied=self.adapter.apply('wuthering-waves',self.media_id,False,False,'animated',motion_id)
        self.assertEqual(applied['mode'],'animated')
        self.assertEqual(self.adapter.current()['motionMediaId'],motion_id)
        reopened=DesktopBridge(self.bridge.store.directory,[(self.desktop,'fixture')])
        self.assertEqual(reopened.templates.current()['id'],applied['id'])
        reopened.templates.restore();self.assertEqual(self.current[0],'')

    def test_missing_motion_is_rejected_before_shortcut_or_wallpaper_changes(self):
        before=self.shortcut.read_bytes()
        with self.assertRaises(FileNotFoundError):
            self.adapter.apply('wuthering-waves',self.media_id,True,False,'animated','0'*64+'.mp4')
        self.assertEqual(self.shortcut.read_bytes(),before);self.mock_set.assert_not_called()

    def test_static_backend_never_flattens_animated_images(self):
        for extension in ('gif','webp','png'):
            frames=[Image.new('RGB',(16,16),color) for color in ('red','blue')]
            source=self.wallpapers/('0'*64+'.'+extension)
            frames[0].save(source,save_all=True,append_images=frames[1:],duration=100,loop=0)
            with self.assertRaisesRegex(ValueError,'动态壁纸'):
                StaticWallpaper(self.bridge.store.directory).apply(source.name,{})
        self.mock_set.assert_not_called()

    def test_imported_cursor_draft_survives_an_unrelated_state_refresh(self):
        path=ROOT/'assets/templates/wuthering-waves/cursors/Arrow.cur'
        imported=self.bridge.dispatch('cursors.import',{'role':'Arrow','files':[{'name':'Arrow.cur','data':base64.b64encode(path.read_bytes()).decode()}]})
        self.bridge.state()
        self.assertIn(imported['roles']['Arrow'],self.bridge.resources)

    def test_one_click_shortcut_and_wallpaper_can_restore_after_reopening(self):
        before=self.shortcut.read_bytes()
        result=self.adapter.apply('wuthering-waves',self.media_id,use_icons=True,use_cursors=False)
        self.assertEqual(result['iconsApplied'],1);self.assertNotEqual(self.shortcut.read_bytes(),before)
        reopened=DesktopBridge(self.bridge.store.directory,[(self.desktop,'fixture')])
        restored=reopened.templates.restore();self.assertTrue(restored['ok']);self.assertEqual(self.shortcut.read_bytes(),before);self.assertEqual(self.current[0],'')

    def test_wallpaper_failure_rolls_back_shortcuts(self):
        before=self.shortcut.read_bytes()
        with patch.object(self.adapter.wallpaper,'apply',side_effect=RuntimeError('failure')):
            with self.assertRaisesRegex(RuntimeError,'failure'):self.adapter.apply('wuthering-waves',self.media_id,True,False)
        self.assertEqual(self.shortcut.read_bytes(),before)

    def test_restore_does_not_overwrite_external_wallpaper_change(self):
        self.adapter.apply('wuthering-waves',self.media_id,True,False)
        current_icon=self.shortcut.read_bytes();self.current[0]='C:\\external-wallpaper.jpg'
        with self.assertRaises(ValueError):self.adapter.restore()
        self.assertEqual(self.current[0],'C:\\external-wallpaper.jpg');self.assertEqual(self.shortcut.read_bytes(),current_icon)

    def test_static_wallpaper_stack_survives_restart_without_recursive_history(self):
        first=StaticWallpaper(self.bridge.store.directory).apply(self.media_id,{})
        second=StaticWallpaper(self.bridge.store.directory).apply(self.media_id,{})
        path=self.bridge.store.directory/'wallpaper/static.json';record=json.loads(path.read_text())
        self.assertEqual(record['previous'],first['record']);self.assertIsInstance(record['previous'],str)
        restored=StaticWallpaper(self.bridge.store.directory).restore(second['record']);self.assertTrue(restored['active'])
        StaticWallpaper(self.bridge.store.directory).restore(first['record']);self.assertEqual(self.current[0],'')

if __name__=='__main__':unittest.main()
