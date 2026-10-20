$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$workspaceRoot = [IO.Path]::GetFullPath((Split-Path -Parent $projectRoot))
if ($workspaceRoot -ine 'E:\desktop\windows' -or $projectRoot -ine (Join-Path $workspaceRoot 'ThemeStudio-dev')) { throw 'This cleanup is scoped to the verified project checkout.' }
$version = (Get-Content -LiteralPath (Join-Path $projectRoot 'package.json') -Raw | ConvertFrom-Json).version
$testResult = Get-Content -LiteralPath (Join-Path $projectRoot 'qa\runtime\installer-0.2.0\result.json') -Raw | ConvertFrom-Json
if (-not $testResult.passed) { throw 'The final installer regression must pass before cleanup.' }
$pendingChanges = @(git -C $projectRoot status --porcelain)
if ($LASTEXITCODE -ne 0 -or $pendingChanges.Count -ne 0) { throw 'Commit and back up all source changes before cleanup.' }
$delivery = Get-Content -LiteralPath (Join-Path $projectRoot 'installers\release.json') -Raw | ConvertFrom-Json
$head = (git -C $projectRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $delivery.sourceCommit -cne $head) { throw 'The source archive does not match the current checkout.' }
$remote = Get-Content -LiteralPath (Join-Path $projectRoot 'installers\github-assets-verified.json') -Raw | ConvertFrom-Json
$expected = @(('ThemeStudio-' + $version + '-Windows-x64-Setup.exe'), ('ThemeStudio-' + $version + '-source.zip'), ('ThemeStudio-' + $version + '-project-data.zip'), 'SHA256.txt', 'release.json')
foreach ($name in $expected) {
    $record = @($remote | Where-Object {$_.name -ceq $name})
    $local = Join-Path $projectRoot ('installers\' + $name)
    if ($record.Count -ne 1 -or -not $record[0].verified -or $record[0].remoteDigest -cne ('sha256:' + (Get-FileHash -LiteralPath $local).Hash.ToLowerInvariant())) { throw ('Remote backup verification is incomplete: ' + $name) }
}
$retainedInstaller = Join-Path $workspaceRoot ('ThemeStudio-' + $version + '-Windows-x64-Setup.exe')
if ((Get-FileHash -LiteralPath $retainedInstaller).Hash -cne (Get-FileHash -LiteralPath (Join-Path $projectRoot ('installers\ThemeStudio-' + $version + '-Windows-x64-Setup.exe'))).Hash) { throw 'The retained installer does not match the published package.' }
$dataRoots = @((Join-Path $env:LOCALAPPDATA 'ThemeStudio'), (Join-Path $env:APPDATA 'com.seelen.seelen-ui'), (Join-Path $env:LOCALAPPDATA 'com.seelen.seelen-ui'))
$profileManifest = Get-Content -LiteralPath (Join-Path $projectRoot 'installers\profile-manifest.json') -Raw | ConvertFrom-Json
foreach ($root in $dataRoots) {
    $absolute = [IO.Path]::GetFullPath($root)
    $entries = @($profileManifest | Where-Object {$_.root -ieq $absolute})
    if (Test-Path -LiteralPath $absolute) {
        $current = @(Get-ChildItem -LiteralPath $absolute -Recurse -File -Force)
        if ($current.Count -ne $entries.Count) { throw 'Profile files changed after archival; preserve them and make a fresh backup.' }
        foreach ($entry in $entries) {
            $file = [IO.Path]::GetFullPath((Join-Path $absolute $entry.relative))
            if (-not $file.StartsWith($absolute.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase) -or (Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant() -cne $entry.sha256) { throw 'A profile file changed or escaped its archive root.' }
        }
    }
}
$allProcesses = @(Get-CimInstance Win32_Process)
foreach ($process in $allProcesses) {
    $path = $process.ExecutablePath
    if ($path -and ($path.StartsWith($projectRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or $path.StartsWith($dataRoots[0] + '\', [StringComparison]::OrdinalIgnoreCase))) { throw ('A project process is still running: ' + $process.Name) }
}
$shell = New-Object -ComObject WScript.Shell
foreach ($desktop in @([Environment]::GetFolderPath('DesktopDirectory'), [Environment]::GetFolderPath('CommonDesktopDirectory'))) {
    foreach ($link in Get-ChildItem -LiteralPath $desktop -Filter '*.lnk' -File) {
        $icon = $shell.CreateShortcut($link.FullName).IconLocation
        foreach ($root in $dataRoots) { if ($icon -and $icon.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) { throw 'A desktop icon still uses a project asset; restore it before deleting the profile.' } }
    }
    foreach ($link in Get-ChildItem -LiteralPath $desktop -Filter '*.url' -File) {
        $text = Get-Content -LiteralPath $link.FullName -Raw
        foreach ($root in $dataRoots) { if ($text.IndexOf($root, [StringComparison]::OrdinalIgnoreCase) -ge 0) { throw 'A desktop internet shortcut still uses a project asset.' } }
    }
}
$cursors = Get-ItemProperty -LiteralPath 'HKCU:\Control Panel\Cursors'
foreach ($property in $cursors.PSObject.Properties) {
    if ($property.Value -is [string]) { foreach ($root in $dataRoots) { if ($property.Value.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) { throw 'A system cursor still uses a project asset.' } } }
}
$projectTargets = @((Join-Path $workspaceRoot '.recovery'), (Join-Path $workspaceRoot 'theme-studio'), $projectRoot)
foreach ($target in $projectTargets) {
    $absolute = [IO.Path]::GetFullPath($target)
    if (-not $absolute.StartsWith($workspaceRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or $absolute -ieq $workspaceRoot) { throw 'Project cleanup target escaped its workspace.' }
}
$removed = @()
Set-Location -LiteralPath $workspaceRoot
foreach ($target in @($dataRoots) + @($projectTargets)) {
    $absolute = [IO.Path]::GetFullPath($target)
    if (Test-Path -LiteralPath $absolute) { Remove-Item -LiteralPath $absolute -Recurse -Force; $removed += $absolute }
}
$oldInstaller = Join-Path $workspaceRoot 'ThemeStudio-0.1.1-Windows-x64-Setup.exe'
if (Test-Path -LiteralPath $oldInstaller) { Remove-Item -LiteralPath $oldInstaller -Force; $removed += $oldInstaller }
[pscustomobject]@{removed=$removed;retainedInstaller=$retainedInstaller;remaining=@(Get-ChildItem -LiteralPath $workspaceRoot -Force | Select-Object -ExpandProperty Name)} | ConvertTo-Json -Depth 4
