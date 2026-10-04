"""Transaction and rendering tests without changing the user's Explorer."""
from pathlib import Path
import copy
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from explorer_image import ExplorerImageAdapter, IMAGE_MOD, FRAME_MOD, appearance
from backend import atomic_json
from runtime_adapter import read_json


class ExplorerImageTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(); self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.runtime = SimpleNamespace(data=self.root, catalog={key: {'sha256': key} for key in (IMAGE_MOD, FRAME_MOD)},
                                       _validate_mods=MagicMock(), windhawk_apply=MagicMock())
        self.adapter = ExplorerImageAdapter(self.runtime)
        self.source = self.root / '测试背景.png'
        Image.new('RGB', (80, 40), (200, 100, 50)).save(self.source)
        self.values = {}
        self.adapter.observed = lambda settings: {key: {'installed': key in self.values,
            'enabled': self.values.get(key, {}).get('enabled', False),
            'settings': {name: self.values.get(key, {}).get('settings', {}).get(name, '') for name in value}}
            for key, value in settings.items()}
        def apply(items, **kwargs):
            self.assertTrue(kwargs['preserve_others'])
            for item in items:
                self.values[item['id']] = {'enabled': True, 'settings': {k:str(v) for k,v in item['settings'].items()}}
        self.runtime.windhawk_apply.side_effect = apply
        self.adapter._restore_values = lambda before: self.values.update(copy.deepcopy(before))
        p = patch('explorer_image.sys.getwindowsversion', return_value=SimpleNamespace(build=26100))
        p.start(); self.addCleanup(p.stop)

    def test_preview_blend_matches_decoded_native_bitmap_and_png(self):
        bmp, png, _ = self.adapter.prepare(self.source, {'imageOpacity': 50, 'tint': '#000000'})
        for file in (bmp,png):
            with Image.open(file) as result:
                self.assertEqual(result.getpixel((10,10)), (100,50,25))
        self.assertEqual(self.adapter.prepare(self.source, {'imageOpacity':50,'tint':'#000000'})[0],bmp)
        self.assertFalse(self.adapter.record.exists())

    def test_changing_theme_has_persistent_stack_and_restores_both_components(self):
        first=self.adapter.apply(self.source,'first')
        baseline=copy.deepcopy(self.values)
        second=self.adapter.apply(self.source,'second',{'imageOpacity':55,'tint':'#102030'})
        self.assertNotEqual(first['recordId'],second['recordId'])
        self.adapter.restore(second['recordId'])
        self.assertEqual(self.adapter.state()['packId'],'first')
        self.assertEqual(self.values, {key:{**value,'installed':True} for key,value in baseline.items()})
        self.adapter.restore(first['recordId'])
        self.assertFalse(any(v['enabled'] for v in self.values.values()))

    def test_partial_enable_failure_rolls_back_both_and_keeps_previous_undo(self):
        first=self.adapter.apply(self.source,'first')
        prior=read_json(self.adapter.record)
        def fail(items, **kwargs):
            self.values[IMAGE_MOD]['settings']['imagePath']='partial'
            raise RuntimeError('second component failed')
        self.runtime.windhawk_apply.side_effect=fail
        with self.assertRaisesRegex(RuntimeError,'second component'):self.adapter.apply(self.source,'second')
        self.assertEqual(read_json(self.adapter.record),prior)
        self.adapter.can_restore(first['recordId'])

    def test_unrelated_external_change_blocks_entire_restore(self):
        self.adapter.apply(self.source,'first')
        self.values[FRAME_MOD]['settings']['theme']='WindowGlass'
        with self.assertRaisesRegex(ValueError,'其他操作'):self.adapter.restore()
        self.assertEqual(self.values[FRAME_MOD]['settings']['theme'],'WindowGlass')

    def test_invalid_parameters_and_old_windows_never_enable(self):
        for value in ({'imageOpacity':True},{'imageOpacity':71},{'tint':'url(x)'},[]):
            with self.assertRaises(ValueError):appearance(value)
        with patch('explorer_image.sys.getwindowsversion',return_value=SimpleNamespace(build=19045)):
            with self.assertRaises(ValueError):self.adapter.apply(self.source,'first')
        self.runtime.windhawk_apply.assert_not_called()

    def test_rollback_failure_remains_recoverable(self):
        self.runtime.windhawk_apply.side_effect=RuntimeError('enable failed')
        self.adapter._restore_values=MagicMock(side_effect=RuntimeError('restore failed'))
        with self.assertRaisesRegex(RuntimeError,'恢复未完成'):self.adapter.apply(self.source,'first')
        self.assertEqual(read_json(self.adapter.record)['status'],'needs_attention')
        self.assertTrue(self.adapter.state()['canRestore'])
        with self.assertRaisesRegex(ValueError,'先恢复'):self.adapter.apply(self.source,'next')
