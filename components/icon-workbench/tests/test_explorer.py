from pathlib import Path
from types import SimpleNamespace
import tempfile
import sys
import unittest
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from explorer_adapter import ExplorerAdapter, MOD, STORAGE
from runtime_adapter import RuntimeAdapter, read_json
from backend import atomic_json


class ExplorerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.runtime=RuntimeAdapter(Path(self.temp.name))
        self.adapter=ExplorerAdapter(self.runtime)
        self.before={'installed':True,'enabled':False,'theme':'MicaBar'}
        self.after={'installed':True,'enabled':True,'theme':'WindowGlass'}
        p=patch('explorer_adapter.sys.getwindowsversion',return_value=SimpleNamespace(build=26100));p.start();self.addCleanup(p.stop)

    def test_state_reads_without_initializing_or_mutating_engine(self):
        with patch.object(self.runtime,'_wh',side_effect=AssertionError('CLI read mutation')):
            state=self.adapter.state()
        self.assertFalse(state['enabled']); self.assertFalse(self.adapter.record.exists())

    def test_apply_preserves_other_mods_and_restores_prior_theme_and_disabled_state(self):
        current=dict(self.before)
        def apply(items,**kwargs):
            self.assertTrue(kwargs['preserve_others']);current.update(self.after)
        def wh(*args):
            if args[:3]==('mod','settings','set'):current['theme']=args[4][6:]
            if args[:2]==('mod','disable'):current['enabled']=False
        with patch.object(self.adapter,'observed',side_effect=lambda:dict(current)), patch.object(self.runtime,'windhawk_apply',side_effect=apply), patch.object(self.runtime,'_wh',side_effect=wh), patch.object(self.adapter,'state',return_value={}):
            self.adapter.apply('WindowGlass');self.adapter.restore()
        self.assertEqual(current,self.before)
        self.assertEqual(read_json(self.adapter.record)['status'],'restored')

    def test_external_change_blocks_restore(self):
        atomic_json(self.adapter.record,{'status':'applied','before':self.before,'after':self.after})
        with patch.object(self.adapter,'observed',return_value={**self.after,'theme':'Float'}),patch.object(self.runtime,'_wh') as wh:
            with self.assertRaisesRegex(ValueError,'其他操作'):self.adapter.restore()
            wh.assert_not_called()

    def test_failed_apply_rolls_back_and_preserves_older_undo_record(self):
        pending={'status':'applied','before':self.before,'after':self.after};atomic_json(self.adapter.record,pending)
        with patch.object(self.adapter,'observed',return_value=self.after), patch.object(self.runtime,'windhawk_apply',side_effect=RuntimeError('compile failure')),patch.object(self.adapter,'_restore_values') as restore:
            with self.assertRaisesRegex(RuntimeError,'compile failure'):self.adapter.apply('Float')
            restore.assert_called_once_with(self.after)
        self.assertEqual(read_json(self.adapter.record),pending)

    def test_crash_record_remains_recoverable_and_blocks_new_apply(self):
        atomic_json(self.adapter.record,{'status':'prepared','before':self.before})
        with self.assertRaisesRegex(ValueError,'先恢复'):self.adapter.apply('Float')
        with patch.object(self.adapter,'observed',return_value=self.before),patch.object(self.adapter,'_restore_values') as restore:
            self.adapter.restore();restore.assert_called_once_with(self.before)

    def test_invalid_theme_and_unsupported_windows_never_mutate(self):
        with patch.object(self.runtime,'windhawk_apply') as apply:
            for theme in ('',None,'bad'):
                with self.assertRaises(ValueError):self.adapter.apply(theme)
            with patch('explorer_adapter.sys.getwindowsversion',return_value=SimpleNamespace(build=19045)):
                with self.assertRaisesRegex(ValueError,'Windows 11'):self.adapter.apply('Float')
            apply.assert_not_called()
        self.assertFalse(self.adapter.record.exists())

    def test_general_mod_apply_does_not_disable_dedicated_explorer(self):
        compiler=self.runtime.windhawk/'Compiler/bin/clang++.exe'
        with patch.object(Path,'is_file',return_value=True), patch.object(self.runtime,'_wh',return_value={'mods':[{'id':STORAGE,'enabled':True},{'id':'local@mouse-trail','enabled':True}]}) as wh, patch.object(self.runtime,'_managed',return_value={'mods':{STORAGE:{},'local@mouse-trail':{}}}), patch.object(self.runtime,'_windhawk_root',return_value=Path(self.temp.name)), patch.object(self.runtime,'state',return_value={'windhawk':{}}), patch.object(self.runtime,'_record'),patch('runtime_adapter.time.sleep'):
            self.runtime.windhawk_apply([])
            self.assertNotIn(unittest.mock.call('mod','disable',STORAGE), wh.call_args_list)
            self.assertIn(unittest.mock.call('mod','disable','local@mouse-trail'), wh.call_args_list)
