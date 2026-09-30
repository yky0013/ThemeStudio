param([string]$Scenario = 'fresh', [string]$ApplicationPath)
$ErrorActionPreference = 'Stop'
if ($Scenario -notmatch '^[a-z0-9-]+$') { throw 'Invalid QA scenario name.' }
$project = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$qaRoot = Join-Path $project ('qa\preserve-theme\' + $Scenario)
$python = Join-Path $project '.venv\Scripts\python.exe'
$snapshotScript = Join-Path $PSScriptRoot 'snapshot-appearance.py'
$qaScript = Join-Path $PSScriptRoot 'qa-native-preserve-theme.js'
if (-not $ApplicationPath) { $ApplicationPath = Join-Path $project 'release\ThemeStudio-0.5.0\ThemeStudio.Diagnostic.exe' }
$ApplicationPath = [IO.Path]::GetFullPath($ApplicationPath)
if (-not $ApplicationPath.StartsWith($project + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'QA executable must be in this checkout.' }
New-Item -ItemType Directory -Path (Join-Path $qaRoot 'desktop') -Force | Out-Null
& $python -X utf8 $snapshotScript (Join-Path $qaRoot 'before.json')
if ($LASTEXITCODE -ne 0) { throw 'Unable to record original appearance.' }
$process = Start-Process -FilePath $ApplicationPath -ArgumentList @('--smoke-dir', ('"' + $qaRoot + '"'), '--qa-script', ('"' + $qaScript + '"')) -WindowStyle Hidden -PassThru
if (-not $process.WaitForExit(55000)) { throw 'Read-only native QA timed out; inspect the process before cleanup.' }
$report = Get-Content -LiteralPath (Join-Path $qaRoot 'qa-result.json') -Raw | ConvertFrom-Json
& $python -X utf8 $snapshotScript (Join-Path $qaRoot 'after.json') --compare (Join-Path $qaRoot 'before.json')
if ($LASTEXITCODE -ne 0) { throw 'Appearance changed during read-only native QA.' }
if ($process.ExitCode -ne 0 -or -not $report.passed) { $report | ConvertTo-Json -Depth 5; throw 'Native startup/preview regression failed.' }
[pscustomobject]@{scenario=$Scenario;passed=$report.passed;checks=$report.checks.Count;appearanceUnchanged=$true} | ConvertTo-Json
