$ErrorActionPreference = 'Stop'
$project = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$qaRoot = Join-Path $project 'qa\preserve-theme\installation'
$destination = Join-Path $qaRoot 'Installed App'
$installer = Join-Path $project 'installers\ThemeStudio-0.5.0-Windows-x64-Setup.exe'
$python = Join-Path $project '.venv\Scripts\python.exe'
$snapshot = Join-Path $PSScriptRoot 'snapshot-appearance.py'
$registration = 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{34717904-40BD-47C3-9AE5-4CA3B55820B5}_is1'
$groupName = 'ThemeStudio 0.5.0 QA'
$groupPath = Join-Path ([Environment]::GetFolderPath('CommonPrograms')) $groupName
$report = [ordered]@{version='0.5.0';passed=$false;stages=@()}
New-Item -ItemType Directory -Path $qaRoot -Force | Out-Null
function Compare-Appearance([string]$Stage) {
    $result = & $python -X utf8 $snapshot (Join-Path $qaRoot ($Stage+'.json')) --compare (Join-Path $qaRoot 'before.json')
    if ($LASTEXITCODE -ne 0) { throw ('Appearance changed during '+$Stage+': '+$result) }
    $report.stages += [ordered]@{stage=$Stage;appearance=($result | ConvertFrom-Json)}
}
try {
    if (-not ([Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Installer QA requires administrator privileges.' }
    $ready = Join-Path $project 'build\installer-ready.json'
    $deadline = (Get-Date).AddMinutes(6)
    while (-not (Test-Path -LiteralPath $ready)) {
        if ((Get-Date) -gt $deadline) { throw 'Final installer build is not ready.' }
        Start-Sleep -Seconds 2
    }
    $expected = Get-Content -LiteralPath $ready -Raw | ConvertFrom-Json
    if ((Get-FileHash -LiteralPath $installer).Hash -ine $expected.sha256) { throw 'Installer changed after final build verification.' }
    $report.installerSha256 = $expected.sha256
    if (-not $destination.StartsWith($project+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'QA destination outside checkout.' }
    if ((Test-Path -LiteralPath $registration) -or (Test-Path -LiteralPath $registration.Replace('HKLM:','HKCU:'))) { throw 'An existing user installation is registered; do not overwrite it for QA.' }
    if ((Test-Path -LiteralPath $destination) -or (Test-Path -LiteralPath $groupPath)) { throw 'QA install path or Start Menu group already exists.' }
    & $python -X utf8 $snapshot (Join-Path $qaRoot 'before.json')
    if ($LASTEXITCODE -ne 0) { throw 'Cannot snapshot original appearance.' }
    $beforeVersion = (Get-Item -LiteralPath $installer).VersionInfo.ProductVersion.Trim()
    if ($beforeVersion -ne '0.5.0') { throw 'Wrong installer version.' }
    foreach ($stage in @('install','reinstall')) {
        $args = @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/TASKS=""',('/DIR="'+$destination+'"'),('/GROUP="'+$groupName+'"'),('/LOG="'+(Join-Path $qaRoot ($stage+'.log'))+'"'))
        $setup = Start-Process -FilePath $installer -ArgumentList $args -WindowStyle Hidden -PassThru -Wait
        if ($setup.ExitCode -ne 0) { throw ('Installer failed: '+$setup.ExitCode) }
        $installed = Get-ItemProperty -LiteralPath $registration
        if ($installed.InstallLocation.TrimEnd('\') -ine $destination.TrimEnd('\') -or $installed.DisplayVersion -ne '0.5.0') { throw 'Unexpected installation registration.' }
        if (Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($destination+'\',[StringComparison]::OrdinalIgnoreCase) }) { throw 'Setup unexpectedly launched an installed program.' }
        Compare-Appearance $stage
    }
    $files = @(Get-ChildItem -LiteralPath $destination -Recurse -File | Where-Object { $_.Name -notmatch '^unins\d+\.' })
    foreach ($file in $files) {
        $relative = [IO.Path]::GetRelativePath($destination,$file.FullName)
        $source = Join-Path $project ('release\ThemeStudio-0.5.0\'+$relative)
        if (-not (Test-Path -LiteralPath $source) -or (Get-FileHash -LiteralPath $source).Hash -ne (Get-FileHash -LiteralPath $file.FullName).Hash) { throw ('Unexpected/mismatched payload: '+$relative) }
    }
    $report.payloadFilesVerified = $files.Count
    & (Join-Path $PSScriptRoot 'qa-preserve-theme.ps1') -Scenario installed-startup -ApplicationPath (Join-Path $destination 'ThemeStudio.exe')
    Compare-Appearance 'startup-preview'
    # Only uninstall the verified QA location. User assets in LOCALAPPDATA remain.
    $installed = Get-ItemProperty -LiteralPath $registration
    if ($installed.InstallLocation.TrimEnd('\') -ine $destination.TrimEnd('\')) { throw 'Registered install changed; refusing cleanup.' }
    $uninstaller = Join-Path $destination 'unins000.exe'
    $uninstall = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/LOG="'+(Join-Path $qaRoot 'uninstall.log')+'"')) -WindowStyle Hidden -PassThru -Wait
    if ($uninstall.ExitCode -ne 0) { throw ('QA uninstall failed: '+$uninstall.ExitCode) }
    if ((Test-Path -LiteralPath $registration) -or (Test-Path -LiteralPath $groupPath)) { throw 'QA uninstall left registration/shortcuts.' }
    Compare-Appearance 'uninstall'
    $report.passed = $true
} catch {
    $report.error = $_.Exception.Message
    throw
} finally {
    $report | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $qaRoot 'result.json') -Encoding utf8
}
