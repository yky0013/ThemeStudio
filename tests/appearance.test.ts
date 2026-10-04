import test from 'node:test';
import assert from 'node:assert/strict';
import { AppearanceDraft } from '../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/appearance.ts';

test('custom cursor/icon choices replace theme accessories within one combined plan',()=>{
  const draft=new AppearanceDraft();
  draft.set('theme',{label:'theme',operation:'templates.apply',payload:{id:'sample',icons:true,cursors:true,explorer:true}});
  draft.set('cursors',{label:'cursor',operation:'cursors.apply',payload:{roles:{},size:48}});
  draft.set('icons',{label:'icons',operation:'icons.apply',payload:{items:[]}});
  const plan=draft.plan();
  assert.equal(plan[0]!.payload.cursors,false);assert.equal(plan[0]!.payload.icons,false);
  assert.equal(draft.get('theme')!.payload.cursors,true);
  assert.deepEqual(plan.map(p=>p.operation),['templates.apply','icons.apply','cursors.apply']);
});
test('Mac selection and its color selection produce one Seelen activation',()=>{
  const draft=new AppearanceDraft();draft.seelen={activeThemes:['@default/theme','@eythaann/bubbles']};
  draft.set('desktop',{label:'Mac',operation:'runtime.desktop.apply',payload:{mode:'mac'}});
  draft.set('seelen',{label:'color',operation:'runtime.seelen.apply',payload:{seelen:{}}});
  const plan=draft.plan();assert.equal(plan.length,1);assert.equal(plan[0]!.operation,'runtime.seelen.apply');
  assert.deepEqual(plan[0]!.payload.seelen,draft.seelen);
});
test('locked drafts reject racing edits; completing an apply leaves no second apply pending',()=>{
  const draft=new AppearanceDraft();draft.set('cursors',{label:'cursor',operation:'cursors.apply',payload:{size:32}});
  draft.setBusy(true);draft.set('cursors',{label:'changed',operation:'cursors.apply',payload:{size:64}});
  assert.equal(draft.get('cursors')!.payload.size,32);draft.clear();draft.setBusy(false);assert.equal(draft.plan().length,0);
});
