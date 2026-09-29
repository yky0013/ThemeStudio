$ErrorActionPreference='Stop'
$project=Split-Path -Parent $PSScriptRoot
$version=(Get-Content -LiteralPath (Join-Path $project 'package.json') -Raw | ConvertFrom-Json).version
$qa=Join-Path $project ('qa\runtime\motion-'+$version+'-'+(Get-Date -Format 'yyyyMMddHHmmss'))
New-Item -ItemType Directory -Path (Join-Path $qa 'data\wallpapers'),(Join-Path $qa 'desktop') -Force | Out-Null
$before=(Get-ItemProperty -LiteralPath 'HKCU:\Control Panel\Desktop').Wallpaper
Set-Content -LiteralPath (Join-Path $qa 'wallpaper-before.txt') -Value $before -Encoding utf8
@'
from PIL import Image
from pathlib import Path
import json,hashlib,sys
qa=Path(sys.argv[1]);project=Path(sys.argv[2]);fixtures=[]
for ext in ('gif','webp','png'):
    frames=[Image.new('RGB',(160,90),color) for color in ('#528d9c','#ab7396','#699879')]
    source=qa/('fixture.'+ext)
    frames[0].save(source,save_all=True,append_images=frames[1:],duration=180,loop=0)
    data=source.read_bytes();ident=hashlib.sha256(data).hexdigest()+'.'+ext
    (qa/'data/wallpapers'/ident).write_bytes(data)
    fixtures.append({'format':ext,'id':ident})
(qa/'qa.js').write_text('const qaAnimatedFiles='+json.dumps(fixtures)+';\n'+(project/'tools/qa-native-motion.js').read_text(encoding='utf-8'),encoding='utf-8')
'@ | & (Join-Path $project '.venv\Scripts\python.exe') -X utf8 - $qa $project
if($LASTEXITCODE -ne 0){throw 'Fixture preparation failed'}
$exe=Join-Path $project ('release\ThemeStudio-'+$version+'\ThemeStudio.Diagnostic.exe')
$app=Start-Process -FilePath $exe -ArgumentList @('--smoke-dir',('"'+$qa+'"'),'--qa-script',('"'+(Join-Path $qa 'qa.js')+'"')) -WindowStyle Hidden -PassThru
@{pid=$app.Id;qa=$qa;beforeWallpaper=$before} | ConvertTo-Json -Compress
