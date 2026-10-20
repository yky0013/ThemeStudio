# Build a non-elevating diagnostic host from the same sources for read-only QA.
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $project
try {
    $release = Join-Path $project 'release\ThemeStudio-0.6.0'
    New-Item -ItemType Directory -Force 'qa' | Out-Null
    $manifest = (Get-Content 'src\host\app.manifest' -Raw).Replace('requireAdministrator', 'asInvoker')
    [IO.File]::WriteAllText((Join-Path $project 'qa\diagnostic.manifest'), $manifest)
    $sources = @(Get-ChildItem 'src\host' -Filter '*.cs' -File | Select-Object -ExpandProperty FullName)
    $csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
    & $csc /nologo /target:winexe /platform:x64 /optimize+ ('/out:' + (Join-Path $release 'ThemeStudio.Diagnostic.exe')) /win32manifest:qa\diagnostic.manifest /win32icon:assets\brand\theme-studio.ico /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Web.Extensions.dll ('/r:' + (Join-Path $release 'Microsoft.Web.WebView2.Core.dll')) ('/r:' + (Join-Path $release 'Microsoft.Web.WebView2.WinForms.dll')) @sources
    if ($LASTEXITCODE -ne 0) { throw 'Diagnostic host compilation failed.' }
    Copy-Item 'src\host\ThemeStudio.exe.config' (Join-Path $release 'ThemeStudio.Diagnostic.exe.config') -Force
    & .\tools\qa-preserve-theme.ps1 -Scenario 'v060' -ApplicationPath (Join-Path $release 'ThemeStudio.Diagnostic.exe')
} finally { Pop-Location }
