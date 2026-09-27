param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$studioRoot = Split-Path -Parent $PSScriptRoot
$smokeOutput = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path (Join-Path $smokeOutput 'desktop') -Force | Out-Null
$smokeShortcut = Join-Path $smokeOutput 'desktop\Theme Studio test.url'
if (-not (Test-Path -LiteralPath $smokeShortcut)) { "[InternetShortcut]`r`nURL=https://example.org/`r`n" | Set-Content -LiteralPath $smokeShortcut -Encoding utf8 }
$smokeProcess = Start-Process -FilePath (Join-Path $studioRoot 'release\ThemeStudio\ThemeStudio.exe') -ArgumentList @('--smoke-dir', ('"' + $smokeOutput + '"')) -WorkingDirectory $env:TEMP -WindowStyle Hidden -PassThru
if (-not $smokeProcess.WaitForExit(55000)) { throw 'Native smoke run did not finish. Inspect its process before cleanup.' }
if ($smokeProcess.ExitCode -ne 0) { throw 'Native smoke run failed. Inspect native-runtime.json.' }
Get-Content -LiteralPath (Join-Path $smokeOutput 'native-runtime.json') -Raw
