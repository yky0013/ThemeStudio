param([switch]$SkipFrontend)
$ErrorActionPreference = 'Stop'
$studioRoot = Split-Path -Parent $PSScriptRoot
$studioPython = Join-Path $studioRoot '.venv\Scripts\python.exe'
$studioRelease = Join-Path $studioRoot 'release\ThemeStudio'
$studioSdk = Join-Path $studioRoot '.cache\webview2'
Push-Location -LiteralPath $studioRoot
try {
    if (-not $SkipFrontend) { & npm.cmd run build; if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' } }
    & $studioPython -X utf8 tools\collect-licenses.py
    if ($LASTEXITCODE -ne 0) { throw 'Dependency notices are incomplete.' }
    & $studioPython -X utf8 -m unittest discover -s components\icon-workbench\tests -p 'test_*.py' -q
    if ($LASTEXITCODE -ne 0) { throw 'Native backend tests failed.' }
    & $studioPython -m PyInstaller --noconfirm --onedir --console --name ThemeStudio.Backend --hidden-import win32timezone --paths components\image-to-ico --distpath build\backend --workpath build\pyinstaller --specpath build\spec components\icon-workbench\desktop_bridge.py
    if ($LASTEXITCODE -ne 0) { throw 'Backend packaging failed.' }
    New-Item -ItemType Directory -Path $studioRelease -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $studioRelease 'backend') -Force | Out-Null
    Copy-Item -Path 'build\backend\ThemeStudio.Backend\*' -Destination (Join-Path $studioRelease 'backend') -Recurse -Force
    New-Item -ItemType Directory -Path (Join-Path $studioRelease 'wwwroot') -Force | Out-Null
    Copy-Item -Path 'dist\*' -Destination (Join-Path $studioRelease 'wwwroot') -Recurse -Force
    Copy-Item -LiteralPath 'licenses' -Destination $studioRelease -Recurse -Force
    Copy-Item -LiteralPath 'LICENSE' -Destination $studioRelease -Force
    foreach ($studioDll in @('Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.WinForms.dll')) { Copy-Item -LiteralPath (Join-Path $studioSdk ('lib\net462\' + $studioDll)) -Destination $studioRelease -Force }
    Copy-Item -LiteralPath (Join-Path $studioSdk 'runtimes\win-x64\native\WebView2Loader.dll') -Destination $studioRelease -Force
    Copy-Item -LiteralPath (Join-Path $studioSdk 'LICENSE.txt') -Destination (Join-Path $studioRelease 'licenses\Microsoft-WebView2-LICENSE.txt') -Force
    Copy-Item -LiteralPath (Join-Path $studioSdk 'NOTICE.txt') -Destination (Join-Path $studioRelease 'licenses\Microsoft-WebView2-NOTICE.txt') -Force
    $studioCompiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
    & $studioCompiler /nologo /target:winexe /platform:x64 /optimize+ ('/out:' + (Join-Path $studioRelease 'ThemeStudio.exe')) /win32manifest:src\host\app.manifest /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Web.Extensions.dll ('/r:' + (Join-Path $studioRelease 'Microsoft.Web.WebView2.Core.dll')) ('/r:' + (Join-Path $studioRelease 'Microsoft.Web.WebView2.WinForms.dll')) src\host\ThemeStudio.cs
    if ($LASTEXITCODE -ne 0) { throw 'Windows host compilation failed.' }
    Copy-Item -LiteralPath 'src\host\ThemeStudio.exe.config' -Destination $studioRelease -Force
    Copy-Item -LiteralPath 'README.md' -Destination $studioRelease -Force
    Write-Output (Join-Path $studioRelease 'ThemeStudio.exe')
} finally { Pop-Location }
