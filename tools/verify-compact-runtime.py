"""Compile disabled, no-op fixtures inside isolated QA storage; never start the engine."""
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'components/icon-workbench'))
from runtime_adapter import RuntimeAdapter
target=ROOT/'qa/compact-runtime';target.mkdir(parents=True,exist_ok=True)
adapter=RuntimeAdapter(target/'data',runtime_root=ROOT/'release/ThemeStudio-0.3.0/runtimes')
results=[]
for arch in ('x86','x86-64'):
    ident='theme-studio-validation-'+arch
    source=target/(ident+'.wh.cpp')
    source.write_text('// ==WindhawkMod==\n// @id '+ident+'\n// @name Theme Studio isolated compiler validation\n// @description Disabled fixture, no hooks\n// @version 1.0\n// @author Theme Studio\n// @include ThemeStudio.Nonexistent.Validation.exe\n// @architecture '+arch+'\n// ==/WindhawkMod==\n#include <windows.h>\nBOOL Wh_ModInit() { return TRUE; }\n',encoding='utf-8')
    result=adapter._wh('mod','install','--file',source,'--disabled',timeout=120)
    if not result.get('compiledLocally') or result.get('config',{}).get('disabled') is not True:
        raise RuntimeError('Compiler did not confirm a disabled compiled fixture')
    results.append({'architecture':arch,'compiled':True,'disabled':True,'result':result})
(target/'verification.json').write_text(json.dumps({'passed':True,'engineStarted':False,'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':True,'architectures':[r['architecture'] for r in results],'engineStarted':False}))
