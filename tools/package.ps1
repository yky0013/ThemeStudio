param([switch]$SkipFrontend)
$ErrorActionPreference = 'Stop'
$studioRoot = Split-Path -Parent $PSScriptRoot
$studioPython = Join-Path $studioRoot '.venv\Scripts\python.exe'
$studioRelease = Join-Path $studioRoot ('release\ThemeStudio-' + (Get-Content -LiteralPath (Join-Path $studioRoot 'package.json') -Raw | ConvertFrom-Json).version)
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
    $studioHostSources = @(Get-ChildItem -LiteralPath 'src\host' -Filter '*.cs' -File | Select-Object -ExpandProperty FullName)
    & $studioCompiler /nologo /target:winexe /platform:x64 /optimize+ ('/out:' + (Join-Path $studioRelease 'ThemeStudio.exe')) /win32manifest:src\host\app.manifest /win32icon:assets\brand\theme-studio.ico /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Web.Extensions.dll ('/r:' + (Join-Path $studioRelease 'Microsoft.Web.WebView2.Core.dll')) ('/r:' + (Join-Path $studioRelease 'Microsoft.Web.WebView2.WinForms.dll')) @studioHostSources
    if ($LASTEXITCODE -ne 0) { throw 'Windows host compilation failed.' }
    Copy-Item -LiteralPath 'src\host\ThemeStudio.exe.config' -Destination $studioRelease -Force
    Copy-Item -LiteralPath 'README.md' -Destination $studioRelease -Force
    New-Item -ItemType Directory -Path (Join-Path $studioRelease 'docs') -Force | Out-Null
    Copy-Item -LiteralPath 'docs\theme-pack-format.md' -Destination (Join-Path $studioRelease 'docs\theme-pack-format.md') -Force
    Copy-Item -LiteralPath 'docs\development\0.6.0-changes.md' -Destination (Join-Path $studioRelease 'docs\0.6.0-changes.md') -Force
    New-Item -ItemType Directory -Path (Join-Path $studioRelease 'docs\research') -Force | Out-Null
    Copy-Item -LiteralPath 'docs\research\20261001' -Destination (Join-Path $studioRelease 'docs\research') -Recurse -Force
    Copy-Item -LiteralPath 'docs\development\explorer-image-update.md' -Destination (Join-Path $studioRelease 'docs\explorer-image-update.md') -Force
    Copy-Item -LiteralPath 'docs\development\unified-appearance-update.md' -Destination (Join-Path $studioRelease 'docs\unified-appearance-update.md') -Force
    Copy-Item -LiteralPath 'docs\development\transparent-surfaces-update.md' -Destination (Join-Path $studioRelease 'docs\transparent-surfaces-update.md') -Force
    Copy-Item -LiteralPath 'tools\asus-cursor-recovery' -Destination (Join-Path $studioRelease 'docs') -Recurse -Force
    $studioRuntimeOutput = Join-Path $studioRelease 'runtimes'
    New-Item -ItemType Directory -Path $studioRuntimeOutput -Force | Out-Null
    if (-not (Test-Path -LiteralPath '.cache\runtimes\seelen-engine\seelen-ui.exe') -or -not (Test-Path -LiteralPath '.cache\runtimes\windhawk\Compiler\bin\clang++.exe')) { throw 'Pinned upstream runtime payloads are missing; prepare-runtimes must complete before packaging.' }
    $seelenOutput = Join-Path $studioRuntimeOutput 'seelen'
    New-Item -ItemType Directory -Path $seelenOutput -Force | Out-Null
    foreach ($runtimeFile in Get-ChildItem -LiteralPath '.cache\runtimes\seelen-engine' -Force) { Copy-Item -LiteralPath $runtimeFile.FullName -Destination $seelenOutput -Recurse -Force }
    $windhawkOutput = Join-Path $studioRuntimeOutput 'windhawk'
    New-Item -ItemType Directory -Path $windhawkOutput -Force | Out-Null
    foreach ($runtimeFile in @('windhawk.exe','windhawk-cli.exe','windhawk-core.dll','windhawk-ui.exe','windhawk-mod.exe','windhawk-mod-elevated.exe','windhawk-mod-uiaccess.exe','ModsRuntime')) { Copy-Item -LiteralPath (Join-Path '.cache\runtimes\windhawk' $runtimeFile) -Destination $windhawkOutput -Recurse -Force }
    # Theme Studio owns the settings/editor UI. Keep the original compiler and both
    # x86/x64 targets; omit the separate VSCodium editor, language server and ARM64 target.
    $compilerSource = [IO.Path]::GetFullPath('.cache\runtimes\windhawk\Compiler')
    & robocopy.exe $compilerSource (Join-Path $windhawkOutput 'Compiler') /E /MT:8 /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD (Join-Path $compilerSource 'aarch64-w64-mingw32') /XF clangd.exe aarch64-w64-windows-gnu.cfg
    if ($LASTEXITCODE -gt 7) { throw 'Compiler payload copy failed.' }
    New-Item -ItemType Directory -Path (Join-Path $windhawkOutput 'Engine') -Force | Out-Null
    Copy-Item -LiteralPath '.cache\runtimes\windhawk\Engine\2.0' -Destination (Join-Path $windhawkOutput 'Engine') -Recurse -Force
    New-Item -ItemType Directory -Path (Join-Path $windhawkOutput 'AppData\Engine\Mods') -Force | Out-Null
    foreach ($runtimeLibrary in Get-ChildItem -LiteralPath '.cache\runtimes\windhawk\AppData\Engine\Mods' -Recurse -File | Where-Object { $_.Extension -eq '.whl' -or $_.Name -eq 'windhawk-mod-shim.dll' }) {
        $libraryOutput = Join-Path $windhawkOutput ('AppData\Engine\Mods\' + $runtimeLibrary.Directory.Name)
        New-Item -ItemType Directory -Path $libraryOutput -Force | Out-Null
        Copy-Item -LiteralPath $runtimeLibrary.FullName -Destination $libraryOutput -Force
    }
    $studioResources = Join-Path $studioRelease 'resources'
    New-Item -ItemType Directory -Path $studioResources -Force | Out-Null
    @{ version = (Get-Content -LiteralPath 'package.json' -Raw | ConvertFrom-Json).version } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $studioResources 'application.json') -Encoding utf8
    Copy-Item -LiteralPath 'config\runtime-distributions.json' -Destination $studioResources -Force
    Copy-Item -LiteralPath 'vendor\Seelen-UI\src\ui\react\settings\modules\themeWorkbench\domain\catalog.json' -Destination (Join-Path $studioResources 'mod-catalog.json') -Force
    $modOutput = Join-Path $studioResources 'windhawk-mods'
    New-Item -ItemType Directory -Path $modOutput -Force | Out-Null
    Get-ChildItem -LiteralPath 'vendor\windhawk-mods\mods' -File | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $modOutput -Force }
    Copy-Item -LiteralPath 'components\explorer-skin\themestudio-explorer-background.wh.cpp' -Destination $modOutput -Force
    $themeOutput = Join-Path $studioResources 'seelen-themes'
    New-Item -ItemType Directory -Path $themeOutput -Force | Out-Null
    Get-ChildItem -LiteralPath 'vendor\Seelen-UI\src\static\themes' -Force | ForEach-Object {
        $destination = Join-Path $themeOutput $_.Name
        if ($_.PSIsContainer) {
            New-Item -ItemType Directory -Path $destination -Force | Out-Null
            Get-ChildItem -LiteralPath $_.FullName -Force | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $destination -Recurse -Force }
        } else { Copy-Item -LiteralPath $_.FullName -Destination $destination -Force }
    }
    Copy-Item -LiteralPath 'vendor\runtime-sources\Seelen-UI-2.8.6\LICENSE' -Destination (Join-Path $studioRelease 'licenses\Seelen-Runtime-2.8.6-AGPL.txt') -Force
    $global:LASTEXITCODE = 0 # Robocopy success includes exit codes 1 through 7.
    Write-Output (Join-Path $studioRelease 'ThemeStudio.exe')
} finally { Pop-Location }
