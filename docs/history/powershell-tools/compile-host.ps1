param([switch]$Diagnostic)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$version=(Get-Content -LiteralPath (Join-Path $taskRoot 'package.json') -Raw | ConvertFrom-Json).version
$release=Join-Path $taskRoot ('release\ThemeStudio-'+$version)
$compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$sources=@(Get-ChildItem -LiteralPath (Join-Path $taskRoot 'src\host') -Filter '*.cs' -File | Select-Object -ExpandProperty FullName)
$name=if($Diagnostic){'ThemeStudio.Diagnostic.exe'}else{'ThemeStudio.exe'}
[string[]]$manifest=@()
if(-not $Diagnostic){$manifest=@('/win32manifest:'+(Join-Path $taskRoot 'src\host\app.manifest'))}
& $compiler /nologo /target:winexe /platform:x64 /optimize+ ('/out:'+(Join-Path $release $name)) ('/win32icon:'+(Join-Path $taskRoot 'assets\brand\theme-studio.ico')) @manifest /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Web.Extensions.dll ('/r:'+(Join-Path $release 'Microsoft.Web.WebView2.Core.dll')) ('/r:'+(Join-Path $release 'Microsoft.Web.WebView2.WinForms.dll')) @sources
if($LASTEXITCODE -ne 0){throw 'Native host compile failed'}
Copy-Item -LiteralPath (Join-Path $taskRoot 'src\host\ThemeStudio.exe.config') -Destination (Join-Path $release ($name+'.config')) -Force
Write-Output (Join-Path $release $name)
