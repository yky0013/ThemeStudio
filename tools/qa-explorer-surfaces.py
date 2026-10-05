"""Temporary Explorer-only paint QA; uses an isolated portable Windhawk profile.

prepare compiles a disabled diagnostic copy, start activates it, stop unloads it.
It never changes ThemeStudio's normal profile or Windows' theme settings.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / 'qa' / 'explorer-surfaces'
sys.path.insert(0, str(ROOT / 'components' / 'icon-workbench'))
from runtime_adapter import RuntimeAdapter, canonical, loaded_libraries, process_images


def profile_hashes():
    profile = Path(os.environ['LOCALAPPDATA']) / 'ThemeStudio'
    result = {}
    for rel in ('settings.json', 'runtime-managed.json', 'explorer-appearance.json',
                'explorer-images/current.json', 'appearance/initial.json', 'appearance/pending.json',
                'windhawk-data/Engine/Mods/local@themestudio-explorer-background.ini'):
        p = profile / rel
        result[rel] = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['prepare', 'start', 'stop'])
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--baseline-ref', default='HEAD', help='Git baseline revision, e.g. v0.6.3 or v0.5.3')
    parser.add_argument('--image', type=Path, help='An existing validated ThemeStudio background BMP (start only)')
    args = parser.parse_args()
    QA.mkdir(parents=True, exist_ok=True)
    runtime = RuntimeAdapter(QA / 'profile')
    mod = 'local@themestudio-explorer-background'
    if args.stage in {'start', 'stop'}:
        owned = canonical(runtime.windhawk_user / 'windhawk.exe')
        if any(Path(path).name.casefold() == 'windhawk.exe' and canonical(path) != owned
               for _, path in process_images()):
            raise RuntimeError('Another Windhawk runtime is active; do not start/stop the global daemon from this QA profile')
    if args.stage == 'prepare':
        (QA / 'profile-before.json').write_text(json.dumps(profile_hashes(), indent=2))
        rel = 'components/explorer-skin/themestudio-explorer-background.wh.cpp'
        source = (subprocess.check_output(['git', 'show', args.baseline_ref + ':' + rel], cwd=ROOT).decode('utf-8')
                  if args.baseline else (ROOT / rel).read_text(encoding='utf-8'))
        trace = str(QA / 'paint-trace.tsv').replace('\\', '\\\\')
        extra = r'''
// QA only: no file names, labels, or document contents are recorded.
void TraceThemePaint(HTHEME theme,HDC dc,int part,int state,const RECT* rect) {
    HWND window=WindowForDC(dc);
    if(!window || !rect || !GetThemeClass_Original)return;
    WCHAR klass[128]{},name[128]{};
    GetClassNameW(window,klass,128);GetThemeClass_Original(theme,name,128);
    std::wstring line=std::wstring(klass)+L"\t"+name+L"\t"+std::to_wstring(part)+L"\t"+
        std::to_wstring(state)+L"\t"+std::to_wstring(rect->left)+L","+std::to_wstring(rect->top)+L","+
        std::to_wstring(rect->right)+L","+std::to_wstring(rect->bottom)+L"\r\n";
    static std::mutex lock;static std::unordered_set<std::wstring> seen;
    std::lock_guard<std::mutex> guard(lock);
    if(seen.size()>=1024 || !seen.insert(line).second)return;
    HANDLE file=CreateFileW(L"TRACE_PATH",FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_ALWAYS,0,nullptr);
    if(file!=INVALID_HANDLE_VALUE){DWORD wrote;WriteFile(file,line.data(),DWORD(line.size()*sizeof(wchar_t)),&wrote,nullptr);CloseHandle(file);}
}
'''.replace('TRACE_PATH', trace)
        anchor = 'bool ReplaceNormalBackground('
        source = source.replace(anchor, extra + '\n' + anchor, 1)
        marker = '    if(g_stopping || g_drawing || g_nativeDrawing || !rect) return false;'
        source = source.replace(marker, '    TraceThemePaint(theme,dc,part,state,rect);\n' + marker, 1)
        diagnostic = QA / 'themestudio-explorer-background.wh.cpp'
        diagnostic.write_text(source, encoding='utf-8')
        result = runtime._wh('mod', 'install', '--file', diagnostic, '--disabled', timeout=600)
        summary = {key: result.get(key) for key in ('id', 'version', 'compiledLocally', 'config')}
        summary['baseline'] = args.baseline
        (QA / 'compiled.json').write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary))
    elif args.stage == 'start':
        image = args.image
        if image is None or not image.is_file() or image.suffix.lower() != '.bmp':
            raise RuntimeError('Existing validated QA background is unavailable')
        runtime._wh('mod', 'settings', 'set', mod, 'imagePath=' + str(image),
                    'textColor=#e4edfa', 'captionColor=#081b32')
        runtime._wh('mod', 'enable', mod)
        root = runtime._windhawk_root()
        subprocess.Popen([str(root / 'windhawk.exe'), '-tray-only'], cwd=root,
                         creationflags=subprocess.CREATE_NO_WINDOW)
        print('Started isolated Explorer paint QA; stop must be run after inspection.')
    else:
        runtime._wh('mod', 'disable', mod)
        runtime._run([runtime.windhawk_user / 'windhawk.exe', '-exit', '-wait', '-timeout', '30000'], timeout=40)
        before = json.loads((QA / 'profile-before.json').read_text())
        checked = runtime._wh('mod', 'show', mod)
        library = checked['config']['libraryFileName'].casefold()
        result = {'normalProfileUnchanged': before == profile_hashes(),
                  'disabled': checked['config']['disabled'],
                  'moduleUnloaded': library not in loaded_libraries({library})}
        (QA / 'restored.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result))
        if not all(result.values()):
            raise RuntimeError('QA restoration did not pass every check')


if __name__ == '__main__':
    main()
