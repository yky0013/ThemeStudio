$ErrorActionPreference='Stop'
$workspaceRoot=[IO.Path]::GetFullPath('E:\desktop\windows').TrimEnd('\')
$handoffRoot=Join-Path $workspaceRoot '.handoff'
$plan=Get-Content -LiteralPath (Join-Path $handoffRoot 'cleanup-plan.json') -Raw | ConvertFrom-Json
$assets=@(Get-Content -LiteralPath (Join-Path $handoffRoot 'github-assets-verified.json') -Raw | ConvertFrom-Json)
if($assets.Count -ne 6 -or @($assets | Where-Object {-not $_.verified}).Count -ne 0){throw 'All six remote backup and release assets must be verified before cleanup.'}
$installer=[IO.Path]::GetFullPath([string]$plan.keep)
if($installer -cne (Join-Path $workspaceRoot 'ThemeStudio-0.1.1-Windows-x64-Setup.exe')){throw 'Unexpected installer exception.'}
if((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash -cne 'FEB381F18740A5B3D38AA370F69D45B2D8B51550FBF7398B4B3A562C3DE9000F'){throw 'Retained installer hash mismatch.'}
$gitRoot=Join-Path $workspaceRoot 'theme-studio'
if((git -C $gitRoot status --porcelain)){throw 'Source tree has uncommitted changes; push them before cleanup.'}
$localHead=(git -C $gitRoot rev-parse HEAD).Trim()
$remote=(git -C $gitRoot ls-remote origin refs/heads/main) -split '\s+'
if($remote[0] -cne $localHead){throw 'Current local source commit is not confirmed on GitHub.'}

function Assert-WorkspaceTarget([string]$Path){
    $absolute=[IO.Path]::GetFullPath($Path).TrimEnd('\')
    if(-not $absolute.StartsWith($workspaceRoot + '\',[StringComparison]::OrdinalIgnoreCase)){throw ('Deletion target escaped workspace: ' + $absolute)}
    if($absolute -ieq $installer -or $absolute -ieq $workspaceRoot){throw ('Deletion target is protected: ' + $absolute)}
    if(Test-Path -LiteralPath $absolute){
        $resolved=(Resolve-Path -LiteralPath $absolute).ProviderPath.TrimEnd('\')
        if(-not $resolved.StartsWith($workspaceRoot + '\',[StringComparison]::OrdinalIgnoreCase)){throw ('Resolved deletion target escaped workspace: ' + $resolved)}
        $item=Get-Item -LiteralPath $absolute -Force
        if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw ('Root deletion target is a link; inspect before deletion: ' + $absolute)}
    }
    return $absolute
}

$externalAllowed=@(
    (Join-Path $env:LOCALAPPDATA 'ThemeStudio'),
    (Join-Path $env:LOCALAPPDATA 'DesktopIconWorkbench'),
    (Join-Path $env:LOCALAPPDATA 'Cursor-Palette'),
    (Join-Path $env:LOCALAPPDATA 'Lively Wallpaper'),
    (Join-Path $env:TEMP 'Lively Wallpaper'),
    (Join-Path $env:TEMP 'Setup Log 2026-09-27 #001.txt')
) | ForEach-Object {[IO.Path]::GetFullPath($_).TrimEnd('\')}

foreach($path in $plan.deleteWorkspaceChildren){[void](Assert-WorkspaceTarget $path)}
foreach($path in $plan.deleteProjectData){
    $absolute=[IO.Path]::GetFullPath([string]$path).TrimEnd('\')
    if($absolute -notin $externalAllowed){throw ('External deletion target is not explicitly allowed: ' + $absolute)}
    if(Test-Path -LiteralPath $absolute){
        $resolved=(Resolve-Path -LiteralPath $absolute).ProviderPath.TrimEnd('\')
        if($resolved -ine $absolute){throw ('External resolved path mismatch: ' + $resolved)}
        $item=Get-Item -LiteralPath $absolute -Force
        if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw ('External deletion target is a link: ' + $absolute)}
    }
}

$registryPath=[string]$plan.uninstall.registeredPath
$uninstallResult='Already absent'
if(Test-Path -LiteralPath $registryPath){
    $registration=Get-ItemProperty -LiteralPath $registryPath
    $expected=[IO.Path]::GetFullPath([string]$plan.uninstall.expectedInstallDirectory).TrimEnd('\')
    [void](Assert-WorkspaceTarget $expected)
    if([IO.Path]::GetFullPath([string]$registration.InstallLocation).TrimEnd('\') -ine $expected){throw 'Lively registration does not match the project installation.'}
    $uninstaller=Join-Path $expected 'unins000.exe'
    $registeredUninstaller=([string]$registration.UninstallString).Trim('"')
    if($registeredUninstaller -ine $uninstaller){throw 'Registered Lively uninstaller differs from the expected project uninstaller.'}
    Write-Output 'Uninstalling project-owned Lively Wallpaper installation.'
    $process=Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/LOG="' + (Join-Path $handoffRoot 'lively-uninstall.log') + '"')) -WindowStyle Hidden -PassThru -Wait
    if($process.ExitCode -ne 0){throw ('Lively uninstall failed: ' + $process.ExitCode)}
    if(Test-Path -LiteralPath $registryPath){throw 'Lively uninstall registration remains.'}
    $uninstallResult='Uninstalled; registration removed'
}

$programsRoot=[Environment]::GetFolderPath('Programs')
$shortcut=Join-Path $programsRoot 'Lively Wallpaper.lnk'
if(Test-Path -LiteralPath $shortcut){
    $shortcutPath=[IO.Path]::GetFullPath($shortcut)
    if(-not $shortcutPath.StartsWith([IO.Path]::GetFullPath($programsRoot).TrimEnd('\') + '\',[StringComparison]::OrdinalIgnoreCase)){throw 'Shortcut deletion target escaped the Start Menu.'}
    $shellObject=New-Object -ComObject WScript.Shell
    $link=$shellObject.CreateShortcut($shortcutPath)
    if(-not $link.TargetPath.StartsWith($workspaceRoot + '\',[StringComparison]::OrdinalIgnoreCase)){throw 'Lively Start Menu shortcut points to an unrelated installation.'}
    Remove-Item -LiteralPath $shortcutPath -Force
}

$remainingProcesses=@(Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -like ($workspaceRoot + '\*')})
if($remainingProcesses.Count -gt 0){throw ('Project process is still running: ' + ($remainingProcesses.ProcessId -join ','))}
$currentWallpaper=(Get-ItemProperty -LiteralPath 'HKCU:\Control Panel\Desktop').Wallpaper
$currentCursors=Get-ItemProperty -LiteralPath 'HKCU:\Control Panel\Cursors'
foreach($value in $currentCursors.PSObject.Properties){
    if($value.Name -notmatch '^PS' -and [string]$value.Value -match 'E:\\desktop\\windows|AppData\\Local\\(ThemeStudio|DesktopIconWorkbench|Cursor-Palette|Lively Wallpaper)'){throw ('Active cursor still depends on project data: ' + $value.Name)}
}
if($currentWallpaper -match 'E:\\desktop\\windows|AppData\\Local\\(ThemeStudio|DesktopIconWorkbench|Cursor-Palette|Lively Wallpaper)'){throw 'Active wallpaper still depends on project data.'}

$shellObject=New-Object -ComObject WScript.Shell
$desktopRoots=@([Environment]::GetFolderPath('DesktopDirectory'),[Environment]::GetFolderPath('CommonDesktopDirectory'))
$programRoots=@([Environment]::GetFolderPath('Programs'),[Environment]::GetFolderPath('CommonPrograms'))
$shortcutFiles=@(foreach($desktopRoot in $desktopRoots){Get-ChildItem -LiteralPath $desktopRoot -File -Filter '*.lnk' -ErrorAction SilentlyContinue})
$shortcutFiles+=@(foreach($programRoot in $programRoots){Get-ChildItem -LiteralPath $programRoot -File -Filter '*.lnk' -Recurse -ErrorAction SilentlyContinue})
foreach($shortcutFile in $shortcutFiles){
    $link=$shellObject.CreateShortcut($shortcutFile.FullName)
    $references=[Environment]::ExpandEnvironmentVariables($link.TargetPath + ' ' + $link.Arguments + ' ' + $link.IconLocation)
    if($references -match 'E:\\desktop\\windows|AppData\\Local\\(ThemeStudio|DesktopIconWorkbench|Cursor-Palette|Lively Wallpaper)'){
        throw ('Active shortcut still depends on project files: ' + $shortcutFile.FullName)
    }
}

$deleted=@()
foreach($path in $plan.deleteProjectData){
    $absolute=[IO.Path]::GetFullPath([string]$path).TrimEnd('\')
    if(Test-Path -LiteralPath $absolute){Remove-Item -LiteralPath $absolute -Recurse -Force; $deleted+=@($absolute)}
    if(Test-Path -LiteralPath $absolute){throw ('Project data remains: ' + $absolute)}
}
foreach($path in $plan.deleteWorkspaceChildren){
    $absolute=Assert-WorkspaceTarget $path
    if($absolute -ieq $gitRoot){continue}
    if(Test-Path -LiteralPath $absolute){Write-Output ('Removing ' + [IO.Path]::GetFileName($absolute)); Remove-Item -LiteralPath $absolute -Recurse -Force; $deleted+=@($absolute)}
    if(Test-Path -LiteralPath $absolute){throw ('Workspace artifact remains: ' + $absolute)}
}
$result=[ordered]@{time=(Get-Date -Format o);repository='https://github.com/yky0013/ThemeStudio';sourceCommitBeforeCleanup=$localHead;assetsVerified=$assets;uninstall=$uninstallResult;deleted=$deleted;retainedInstaller=$installer;retainedInstallerSha256=(Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant();currentWallpaper=(Get-ItemProperty -LiteralPath 'HKCU:\Control Panel\Desktop').Wallpaper;currentCursors=(Get-ItemProperty -LiteralPath 'HKCU:\Control Panel\Cursors' | Select-Object Arrow,Help,AppStarting,Wait,Crosshair,IBeam,NWPen,No,SizeNS,SizeWE,SizeNWSE,SizeNESW,SizeAll,UpArrow,Hand,Pin,Person);freeBytes=(Get-PSDrive E).Free;state='Legacy workspace, installed engine, startup shortcut and project data removed. Final source and temporary handoff files remain until evidence is uploaded.'}
$result | ConvertTo-Json -Depth 9 | Set-Content -LiteralPath (Join-Path $handoffRoot 'cleanup-result.json') -Encoding utf8
[pscustomobject]@{Uninstall=$uninstallResult;DeletedEntries=$deleted.Count;DataClean=$true;Installer=$installer;State=$result.state} | ConvertTo-Json
