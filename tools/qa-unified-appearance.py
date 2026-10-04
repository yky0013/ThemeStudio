"""Bounded current-cursor roundtrip, with an independent finally recovery guard."""
from pathlib import Path
import json,subprocess,sys,uuid
import win32api,win32job
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'components/icon-workbench'))
from cursor_adapter import snapshot,restore_snapshot
from template_adapter import current_wallpaper
from backend import atomic_json

version=json.loads((root/'package.json').read_text(encoding='utf-8-sig'))['version']
qa=root/'qa'/('unified-native-'+uuid.uuid4().hex[:8]);(qa/'desktop').mkdir(parents=True,exist_ok=True)
atomic_json(root/'qa/unified-native-last.json',{'directory':str(qa)})
before=snapshot();wallpaper_before=current_wallpaper()
atomic_json(qa/'cursor-before.private.json',before)
app=root/'release'/('ThemeStudio-'+version)/'ThemeStudio.Diagnostic.exe'
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
job=win32job.CreateJobObject(None,'Local\\ThemeStudio.QA.'+uuid.uuid4().hex)
limits=win32job.QueryInformationJobObject(job,win32job.JobObjectExtendedLimitInformation)
limits['BasicLimitInformation']['LimitFlags']|=win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
win32job.SetInformationJobObject(job,win32job.JobObjectExtendedLimitInformation,limits)
try:
    process=subprocess.Popen([str(app),'--smoke-dir',str(qa),'--qa-script',str(root/'tools/qa-unified-appearance.js')],startupinfo=startup)
    win32job.AssignProcessToJobObject(job,process._handle)
    if process.wait(timeout=90):raise RuntimeError('Diagnostic host failed')
    result=json.loads((qa/'qa-result.json').read_text(encoding='utf-8-sig'))
    if not result['passed']:raise RuntimeError(json.dumps(result['errors'],ensure_ascii=False))
finally:
    # Stop every owned writer before the independent restoration guard runs.
    win32api.CloseHandle(job)
    restored_by_guard=snapshot()!=before
    if restored_by_guard:restore_snapshot(before)
    audit={'cursorRegistryRestoredExactly':snapshot()==before,'wallpaperPathUnchanged':current_wallpaper()==wallpaper_before,
           'independentRecoveryGuardUsed':restored_by_guard}
    atomic_json(qa/'system-restoration.json',audit)
    print(json.dumps(audit,ensure_ascii=False))
    if not audit['cursorRegistryRestoredExactly']:raise RuntimeError('Original cursor state could not be verified')
print(json.dumps(result,ensure_ascii=False))
