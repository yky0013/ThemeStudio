param([Parameter(Mandatory=$true)][string]$Executable,[Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$measurement = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path (Join-Path $measurement 'desktop') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path (Split-Path -Parent $Executable) 'ThemeStudio.exe.config') -Destination ($Executable + '.config') -Force
$app = Start-Process -FilePath $Executable -ArgumentList @('--smoke-dir', ('"'+$measurement+'"'), '--qa-script', ('"'+(Join-Path $taskRoot 'tools\qa-memory.js')+'"')) -WindowStyle Hidden -PassThru
$samples = @()
for ($attempt=0; $attempt -lt 22; $attempt++) {
    Start-Sleep -Seconds 1
    $all = @(Get-CimInstance Win32_Process)
    $ids = [Collections.Generic.HashSet[uint32]]::new(); [void]$ids.Add([uint32]$app.Id)
    do { $added=$false; foreach($item in $all) { if($ids.Contains([uint32]$item.ParentProcessId) -and $ids.Add([uint32]$item.ProcessId)) {$added=$true} } } while($added)
    $rows = @($all | Where-Object {$ids.Contains([uint32]$_.ProcessId)} | ForEach-Object { @{pid=$_.ProcessId;name=$_.Name;working_set_bytes=[long]$_.WorkingSetSize} })
    if($rows.Count -gt 0) {$samples += @{second=$attempt+1;working_set_mib=[math]::Round(($rows | Measure-Object working_set_bytes -Sum).Sum/1MB,2);processes=$rows}}
    if($app.HasExited) {break}
}
if(-not $app.HasExited) { throw 'Measurement still running; inspect the named process.' }
@{metric='sum of process working sets, shared pages can be counted more than once';executable=$Executable;samples=$samples;exit_code=$app.ExitCode} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $measurement 'memory.json') -Encoding utf8
$samples | Select-Object second,working_set_mib | ConvertTo-Json
