"""Durable combined-apply history tests; no live Windows appearance writes."""
from pathlib import Path
import copy,json,sys,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import MagicMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from appearance_adapter import AppearanceAdapter,ALL_DOMAINS,cursor_identity
from cursor_adapter import VALUE_NAMES
from backend import atomic_json


class AppearanceTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name)
        self.machine={'cursors':{'value':'original'},'wallpaper':{'path':'original','native':None},'icons':{},
                      'windhawk':{},'seelen':{'settings':None,'running':False},'explorer':{'images':None,'legacy':None}}
        runtime=SimpleNamespace(_managed=lambda:{})
        self.bridge=SimpleNamespace(store=SimpleNamespace(directory=self.root,history=lambda:[]),runtime=runtime,
             rows=lambda:([],[]),resolve_roles=lambda value:value,templates=SimpleNamespace(current=lambda:{}))
        self.adapter=AppearanceAdapter(self.bridge)
        self.adapter.capture=lambda domains,paths,native:{key:copy.deepcopy(self.machine[key]) for key in domains}
        self.adapter._preflight=MagicMock()
        self.adapter._equivalent=lambda a,b:a==b
        def restore(target,allow_external=False):
            self.machine.update(copy.deepcopy(target));return {'native':target.get('wallpaper',{}).get('native'),'wallpaperIncluded':'wallpaper' in target}
        self.adapter.restore_core=restore
        self.operation=[{'operation':'cursors.apply','label':'cursors','payload':{'roles':{},'size':32}}]

    def apply_cursor(self,value):
        record=self.adapter.begin(self.operation,None);self.machine['cursors']={'value':value};self.adapter.commit(record['id'],None)
        return record

    def test_state_does_not_create_baseline_or_change_live_appearance(self):
        self.assertFalse(self.adapter.state()['canUndo']);self.assertFalse(self.adapter.root.exists())

    def test_initial_baseline_is_not_replaced_by_later_themes(self):
        self.apply_cursor('first');original=self.adapter.baseline.read_bytes();self.apply_cursor('second')
        self.assertEqual(self.adapter.baseline.read_bytes(),original)
        prepared=self.adapter.prepare_restore('initial',None);self.adapter.restore_target(prepared['id']);self.adapter.commit(prepared['id'],None)
        self.assertEqual(self.machine['cursors'],{'value':'original'})
        # Undo of initial restoration recovers the previously selected theme.
        prepared=self.adapter.prepare_restore('last',None);self.adapter.restore_target(prepared['id']);self.adapter.commit(prepared['id'],None)
        self.assertEqual(self.machine['cursors'],{'value':'second'})

    def test_successive_undo_uses_complete_transactions(self):
        self.apply_cursor('first');self.apply_cursor('second')
        for expected in ('first','original'):
            prepared=self.adapter.prepare_restore('last',None);self.adapter.restore_target(prepared['id']);self.adapter.commit(prepared['id'],None)
            self.assertEqual(self.machine['cursors'],{'value':expected})
        self.assertFalse(self.adapter.state()['canUndo'])

    def test_partial_apply_rollback_restores_all_domains_in_one_record(self):
        ops=self.operation+[{'operation':'wallpaper.apply','label':'wallpaper','payload':{}}]
        prepared=self.adapter.begin(ops,None)
        self.machine['cursors']={'value':'new'};self.machine['wallpaper']={'path':'new','native':None}
        self.adapter.rollback(prepared['id']);self.adapter.recovered(prepared['id'])
        self.assertEqual(self.machine['cursors'],{'value':'original'});self.assertEqual(self.machine['wallpaper']['path'],'original')
        self.assertFalse(self.adapter.state()['pending'])

    def test_crash_record_survives_reopen_and_blocks_second_application(self):
        prepared=self.adapter.begin(self.operation,None);self.machine['cursors']={'value':'partial'}
        reopened=AppearanceAdapter(self.bridge);reopened.capture=self.adapter.capture;reopened.restore_core=self.adapter.restore_core;reopened._preflight=MagicMock()
        self.assertTrue(reopened.state()['pending'])
        with self.assertRaisesRegex(ValueError,'未完成'):reopened.begin(self.operation,None)
        recovery=reopened.prepare_restore('last',None);self.assertTrue(recovery['recover'])
        reopened.rollback(recovery['id']);reopened.recovered(recovery['id'])
        self.assertEqual(self.machine['cursors'],{'value':'original'})

    def test_external_change_blocks_undo_but_initial_restore_is_explicit(self):
        self.apply_cursor('first');self.machine['cursors']={'value':'outside'}
        with self.assertRaisesRegex(ValueError,'软件外'):self.adapter.prepare_restore('last',None)
        initial=self.adapter.prepare_restore('initial',None);self.adapter.restore_target(initial['id']);self.adapter.commit(initial['id'],None)
        self.assertEqual(self.machine['cursors'],{'value':'original'})

    def test_duplicate_or_nonappearance_operations_fail_before_snapshot(self):
        for operations in (self.operation*2,[{'operation':'pets.launch','payload':{}}],
                           [{'operation':'runtime.seelen.apply','payload':{}}],
                           [{'operation':'runtime.desktop.apply','payload':{'mode':'mac'}}],[]):
            with self.assertRaises(ValueError):self.adapter.begin(operations,None)
        self.assertFalse(self.adapter.baseline.exists())

    def test_copied_cursor_art_and_registry_type_are_not_a_false_conflict(self):
        a=self.root/'one.cur';b=self.root/'copy.cur';a.write_bytes(b'same cursor');b.write_bytes(a.read_bytes())
        values={key:None for key in VALUE_NAMES};values['Arrow']=[str(a),1];values['CursorBaseSize']=[32,4]
        first={'cursors':values};second=copy.deepcopy(first);second['cursors']['Arrow']=[str(b),2]
        second['cursors']['']=['ASUS TX (Original)',1]
        self.assertEqual(cursor_identity(first),cursor_identity(second))
        second['cursors']['CursorBaseSize']=[64,4];self.assertNotEqual(cursor_identity(first),cursor_identity(second))

    def test_restored_legacy_cursor_history_is_recognized_instead_of_rejected(self):
        values={key:None for key in VALUE_NAMES};values['CursorBaseSize']=[32,4]
        before={'cursors':values,'accessibility':{'CursorSize':[1,4]}}
        self.bridge.templates.current=lambda:{'id':'a'*32,'name':'old','cursors':True,'beforeCursors':before,'afterCursors':{'cursors':{**values,'CursorBaseSize':[64,4]}}}
        with patch('appearance_adapter.snapshot',return_value=before):
            target,ident=self.adapter._legacy_target(None)
        self.assertEqual(target['cursors'],before);self.assertEqual(ident,'a'*32)

    def test_real_shortcut_backup_accepts_serialized_string_paths(self):
        path=self.root/'fixture.url';path.write_text('[InternetShortcut]\nURL=https://example.org/\n',encoding='utf-8')
        item=self.adapter._blob(path)
        AppearanceAdapter._preflight(self.adapter,{'icons':{str(path):item}})
