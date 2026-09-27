param([switch]$NoBrowser, [ValidateSet('', 'workbench-parallax', 'workbench-desktop', 'workbench-cursors')][string]$Section = '')
$ErrorActionPreference = 'Stop'
$previewWorkspace = $PSScriptRoot
$previewUrl = 'http://127.0.0.1:4317'
$previewHealth = $null
try { $previewHealth = Invoke-RestMethod -Uri ($previewUrl + '/health') -TimeoutSec 2 } catch { }
if ($previewHealth -and $previewHealth.app -ne 'seelen-windhawk-workbench') {
    throw 'Port 4317 is occupied by another application.'
}
if (-not $previewHealth) {
    if (-not (Test-Path -LiteralPath (Join-Path $previewWorkspace 'dist\index.html'))) {
        throw 'Build first: npm ci followed by npm run build in tools/theme-workbench.'
    }
    $previewNode = (Get-Command node.exe -ErrorAction Stop).Source
    $previewProcess = Start-Process -FilePath $previewNode -ArgumentList @('--import','tsx','server.ts') -WorkingDirectory $previewWorkspace -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $previewWorkspace 'preview-stdout.log') -RedirectStandardError (Join-Path $previewWorkspace 'preview-stderr.log')
    [ordered]@{pid=$previewProcess.Id;url=$previewUrl;started=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $previewWorkspace 'preview-process.json') -Encoding utf8
    for ($previewAttempt = 0; $previewAttempt -lt 30; $previewAttempt++) {
        try { $previewHealth = Invoke-RestMethod -Uri ($previewUrl + '/health') -TimeoutSec 1 } catch { }
        if ($previewHealth) { break }
        if ($previewProcess.HasExited) { throw 'Preview failed to start; see preview-stderr.log.' }
        Start-Sleep -Milliseconds 300
    }
    if (-not $previewHealth -or $previewHealth.app -ne 'seelen-windhawk-workbench') { throw 'Preview health check failed.' }
}
$previewOpenUrl = if ($Section) { $previewUrl + '/#' + $Section } else { $previewUrl }
Write-Output $previewOpenUrl
if (-not $NoBrowser) { Start-Process $previewOpenUrl }
