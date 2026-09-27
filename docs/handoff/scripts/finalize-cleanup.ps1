$ErrorActionPreference='Stop'
$workspaceRoot=[IO.Path]::GetFullPath('E:\desktop\windows').TrimEnd('\')
$handoffRoot=Join-Path $workspaceRoot '.handoff'
$sourceRoot=Join-Path $workspaceRoot 'theme-studio'
$installerPath=Join-Path $workspaceRoot 'ThemeStudio-0.1.1-Windows-x64-Setup.exe'
$report=Get-Content -LiteralPath (Join-Path $handoffRoot 'cleanup-result.json') -Raw | ConvertFrom-Json
$plan=Get-Content -LiteralPath (Join-Path $handoffRoot 'cleanup-plan.json') -Raw | ConvertFrom-Json
if($report.uninstall -ne 'Uninstalled; registration removed'){throw 'The project installation has not been verified as uninstalled.'}
if(@($report.assetsVerified).Count -ne 6 -or @($report.assetsVerified | Where-Object {-not $_.verified}).Count -ne 0){throw 'Remote backups are not confirmed.'}
if((git -C $sourceRoot status --porcelain)){throw 'Uncommitted source changes remain.'}
$localHead=(git -C $sourceRoot rev-parse HEAD).Trim()
$remote=(git -C $sourceRoot ls-remote origin refs/heads/main) -split '\s+'
if($remote[0] -cne $localHead){throw 'Final local source commit does not match GitHub.'}
if((Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash -cne 'FEB381F18740A5B3D38AA370F69D45B2D8B51550FBF7398B4B3A562C3DE9000F'){throw 'Installer hash mismatch.'}

foreach($path in @($sourceRoot,$handoffRoot)){
    $absolute=[IO.Path]::GetFullPath($path).TrimEnd('\')
    if(-not $absolute.StartsWith($workspaceRoot + '\',[StringComparison]::OrdinalIgnoreCase)){throw 'Final deletion target escaped workspace.'}
    $resolved=(Resolve-Path -LiteralPath $absolute).ProviderPath.TrimEnd('\')
    if($resolved -ine $absolute){throw 'Final resolved target differs from the explicit directory.'}
    $item=Get-Item -LiteralPath $absolute -Force
    if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Final deletion target is a link.'}
}
foreach($path in $plan.deleteProjectData){if(Test-Path -LiteralPath $path){throw ('Project data was recreated: ' + $path)}}
$expectedRootNames=@('theme-studio','.handoff','ThemeStudio-0.1.1-Windows-x64-Setup.exe')
$unexpected=@(Get-ChildItem -LiteralPath $workspaceRoot -Force | Where-Object {$_.Name -notin $expectedRootNames})
if($unexpected.Count -gt 0){throw ('Unexpected workspace files remain: ' + ($unexpected.Name -join ','))}
if(Test-Path -LiteralPath $plan.uninstall.registeredPath){throw 'Uninstall registry entry reappeared.'}
$projectProcesses=@(Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -like ($workspaceRoot + '\*')})
if($projectProcesses.Count -gt 0){throw 'Project process is still running.'}

Remove-Item -LiteralPath $sourceRoot -Recurse -Force
if(Test-Path -LiteralPath $sourceRoot){throw 'Source directory remains.'}
Remove-Item -LiteralPath $handoffRoot -Recurse -Force
if(Test-Path -LiteralPath $handoffRoot){throw 'Temporary handoff directory remains.'}
$remaining=@(Get-ChildItem -LiteralPath $workspaceRoot -Force)
if($remaining.Count -ne 1 -or $remaining[0].FullName -ine $installerPath){throw 'Workspace is not reduced to the retained installer.'}
$report.deleted+=@($sourceRoot,$handoffRoot)
$report.state='Complete: source, legacy prototypes, build outputs, development dependencies, installed Lively engine, shortcuts, settings, imported assets, backups, browser cache and named temporary project files were removed. The workspace contains only the verified installer.'
$report.time=Get-Date -Format o
$report | Add-Member -NotePropertyName finalSourceCommitOnGitHub -NotePropertyValue $localHead
$report | Add-Member -NotePropertyName remainingWorkspaceFiles -NotePropertyValue @($remaining | Select-Object Name,FullName,Length)
$report | Add-Member -NotePropertyName finalProjectDataAbsent -NotePropertyValue $true
$report | Add-Member -NotePropertyName finalUninstallRegistrationAbsent -NotePropertyValue $true
$report | Add-Member -NotePropertyName finalProjectProcessesAbsent -NotePropertyValue $true
$report | Add-Member -NotePropertyName finalInstallerSha256 -NotePropertyValue ((Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant())
$report | Add-Member -NotePropertyName freeBytesAfterCleanup -NotePropertyValue (Get-PSDrive E).Free
$report | ConvertTo-Json -Depth 12
