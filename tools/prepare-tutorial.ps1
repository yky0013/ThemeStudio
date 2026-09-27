$ErrorActionPreference = 'Stop'
$studioRoot = Split-Path -Parent $PSScriptRoot
$tutorialRoot = Join-Path $studioRoot 'qa\runtime\tutorial-app'
New-Item -ItemType Directory -Path $tutorialRoot -Force | Out-Null
Copy-Item -Path (Join-Path $studioRoot 'release\ThemeStudio\*') -Destination $tutorialRoot -Recurse -Force
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
& $compiler /nologo /target:winexe /platform:x64 /optimize+ /define:TUTORIAL_MODE ('/out:' + (Join-Path $tutorialRoot 'ThemeStudio.exe')) ('/win32manifest:' + (Join-Path $studioRoot 'src\host\app.manifest')) /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Web.Extensions.dll ('/r:' + (Join-Path $tutorialRoot 'Microsoft.Web.WebView2.Core.dll')) ('/r:' + (Join-Path $tutorialRoot 'Microsoft.Web.WebView2.WinForms.dll')) (Join-Path $studioRoot 'src\host\ThemeStudio.cs')
if ($LASTEXITCODE -ne 0) { throw 'Tutorial fixture host compilation failed.' }
& (Join-Path $studioRoot '.venv\Scripts\python.exe') -X utf8 (Join-Path $studioRoot 'tools\tutorial-fixtures.py')
if ($LASTEXITCODE -ne 0) { throw 'Tutorial fixture preparation failed.' }
Write-Output (Join-Path $tutorialRoot 'ThemeStudio.exe')
