param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$studioRoot = Split-Path -Parent $PSScriptRoot
$studioUrl = 'http://127.0.0.1:4327'
$studioHealth = $null
try { $studioHealth = Invoke-RestMethod -Uri ($studioUrl + '/health') -TimeoutSec 2 } catch { }
if ($studioHealth -and $studioHealth.app -ne 'theme-studio') { throw 'Port 4327 is used by another program.' }
if (-not $studioHealth) {
    if (-not (Test-Path -LiteralPath (Join-Path $studioRoot 'dist\index.html'))) { throw 'Run npm run build first.' }
    $studioNode = (Get-Command node.exe -ErrorAction Stop).Source
    New-Item -ItemType Directory -Path (Join-Path $studioRoot 'build') -Force | Out-Null
    $studioProcess = Start-Process -FilePath $studioNode -ArgumentList @('--import','tsx','tools/dev-server.ts') -WorkingDirectory $studioRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $studioRoot 'build\dev-stdout.log') -RedirectStandardError (Join-Path $studioRoot 'build\dev-stderr.log')
    [ordered]@{pid=$studioProcess.Id;started=(Get-Date).ToString('o');url=$studioUrl} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $studioRoot 'build\dev-process.json')
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try { $studioHealth = Invoke-RestMethod -Uri ($studioUrl + '/health') -TimeoutSec 1 } catch { }
        if ($studioHealth) { break }
        if ($studioProcess.HasExited) { throw 'Development host failed. Check build/dev-stderr.log.' }
        Start-Sleep -Milliseconds 300
    }
    if (-not $studioHealth) { throw 'Development host did not start.' }
}
Write-Output $studioUrl
if (-not $NoBrowser) { Start-Process $studioUrl }
