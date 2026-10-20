$ErrorActionPreference='Stop'
$project=Split-Path -Parent $PSScriptRoot
$version=(Get-Content -LiteralPath (Join-Path $project 'package.json') -Raw | ConvertFrom-Json).version
$qa=Join-Path $project ('qa\runtime\packages-'+$version+'-'+(Get-Date -Format 'yyyyMMddHHmmss'))
New-Item -ItemType Directory -Path (Join-Path $qa 'desktop') -Force | Out-Null
@'
from pathlib import Path
import json,sys,zipfile
qa=Path(sys.argv[1]);project=Path(sys.argv[2]);sys.path.insert(0,str(project/'components/icon-workbench'))
from desktop_bridge import DesktopBridge
bridge=DesktopBridge(qa/'data',[(qa/'desktop','fixture')])
exported=bridge.templates.export('wuthering-waves')
sample=project/'installers/ThemeStudio-示例套装.tspack'
with zipfile.ZipFile(exported['path']) as source, zipfile.ZipFile(sample,'w',zipfile.ZIP_DEFLATED) as output:
    manifest=json.loads(source.read('theme.json'));manifest['id']='demo-wuthering-waves';manifest['name']='鸣潮 · 导入示例'
    output.writestr('theme.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    for entry in source.infolist():
        if entry.filename!='theme.json':output.writestr(entry,source.read(entry))
full=bridge.templates.packages.import_archive(sample)
static=qa/'static.tspack'
with zipfile.ZipFile(static,'w',zipfile.ZIP_DEFLATED) as output:
    output.writestr('theme.json',json.dumps({'schemaVersion':1,'id':'static-demo','version':'1.0.0','name':'纯静态 · 导入示例','subtitle':'只含壁纸，保留现有鼠标与图标','wallpaper':'素材/测试 壁纸.jpg'},ensure_ascii=False))
    output.write(project/'assets/templates/milk-mocha-dogs/wallpaper.jpg','素材/测试 壁纸.jpg')
still=bridge.templates.packages.import_archive(static)
duplicate=bridge.templates.packages.import_archive(sample)
assert duplicate['duplicate']
assert len(DesktopBridge(qa/'data',[(qa/'desktop','fixture')]).templates.catalog())==12
(qa/'import-result.json').write_text(json.dumps({'full':full,'static':still,'duplicate':duplicate,'reopenedCount':12},ensure_ascii=False,indent=2),encoding='utf-8')
'@ | & (Join-Path $project '.venv\Scripts\python.exe') -X utf8 - $qa $project
if($LASTEXITCODE -ne 0){throw 'Fixture import failed'}
$exe=Join-Path $project ('release\ThemeStudio-'+$version+'\ThemeStudio.Diagnostic.exe')
$script=Join-Path $project 'tools\qa-native-packages.js'
$app=Start-Process -FilePath $exe -ArgumentList @('--smoke-dir',('"'+$qa+'"'),'--qa-script',('"'+$script+'"')) -WindowStyle Hidden -PassThru
@{pid=$app.Id;qa=$qa} | ConvertTo-Json -Compress
