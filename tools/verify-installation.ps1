param([ValidateSet('Install','Check','Uninstall')][string]$Stage = 'Check')
$ErrorActionPreference = 'Stop'
$studioRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$qaRoot = Join-Path $studioRoot 'qa\runtime\installer'
$installDirectory = [IO.Path]::GetFullPath((Join-Path $qaRoot '安装 位置\ThemeStudio'))
if (-not $installDirectory.StartsWith($studioRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'QA install path escaped the project.' }
$registryPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{34717904-40BD-47C3-9AE5-4CA3B55820B5}_is1'
$groupName = '桌面主题工作室'
$groupDirectory = Join-Path ([Environment]::GetFolderPath('Programs')) $groupName
$installer = Join-Path $studioRoot 'installers\ThemeStudio-0.1.1-Windows-x64-Setup.exe'
$sentinel = Join-Path $env:LOCALAPPDATA 'ThemeStudio\installer-qa-retention.txt'
New-Item -ItemType Directory -Path $qaRoot -Force | Out-Null

if ($Stage -eq 'Install') {
    if (Test-Path -LiteralPath $registryPath) { throw 'Theme Studio is already registered. Do not overwrite an existing user installation for QA.' }
    if (Test-Path -LiteralPath $installDirectory) { throw 'QA target already exists; inspect it before reuse.' }
    if (Test-Path -LiteralPath $groupDirectory) { throw 'QA Start Menu group already exists; inspect it before reuse.' }
    if (Test-Path -LiteralPath $sentinel) { throw 'QA retention marker already exists; inspect it before reuse.' }
    New-Item -ItemType Directory -Path (Split-Path -Parent $sentinel) -Force | Out-Null
    'Theme Studio installer retention test: do not remove user assets.' | Set-Content -LiteralPath $sentinel -Encoding utf8
    $arguments = @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-',('/DIR="' + $installDirectory + '"'),('/LOG="' + (Join-Path $qaRoot 'install.log') + '"'))
    $process = Start-Process -FilePath $installer -ArgumentList $arguments -WindowStyle Hidden -PassThru -Wait
    if ($process.ExitCode -ne 0) { throw "Installer failed with exit code $($process.ExitCode)." }
    & $PSCommandPath -Stage Check
    return
}

if (-not (Test-Path -LiteralPath $registryPath)) { throw 'QA installation registration is absent.' }
$registration = Get-ItemProperty -LiteralPath $registryPath
if ($registration.InstallLocation.TrimEnd('\') -ine $installDirectory.TrimEnd('\')) { throw 'The registered installation is not the QA copy; refusing to touch it.' }

if ($Stage -eq 'Check') {
    $checks = [ordered]@{
        customPath = $installDirectory
        registeredDisplayName = $registration.DisplayName
        uninstallRegistered = [bool]$registration.UninstallString
        uninstallerExists = Test-Path -LiteralPath (Join-Path $installDirectory 'unins000.exe')
        guideInstalled = Test-Path -LiteralPath (Join-Path $installDirectory 'wwwroot\help\index.html')
        applicationShortcut = Test-Path -LiteralPath (Join-Path $groupDirectory '桌面主题工作室.lnk')
        guideShortcut = Test-Path -LiteralPath (Join-Path $groupDirectory '图文使用教程.lnk')
        uninstallShortcut = Test-Path -LiteralPath (Join-Path $groupDirectory '卸载桌面主题工作室.lnk')
        userDataRetained = Test-Path -LiteralPath $sentinel
    }
    foreach ($file in Get-ChildItem -LiteralPath (Join-Path $studioRoot 'release\ThemeStudio') -File -Recurse) {
        $relative = $file.FullName.Substring((Join-Path $studioRoot 'release\ThemeStudio').Length + 1)
        $installed = Join-Path $installDirectory $relative
        if (-not (Test-Path -LiteralPath $installed) -or (Get-FileHash -LiteralPath $installed).Hash -ne (Get-FileHash -LiteralPath $file.FullName).Hash) { throw "Installed payload mismatch: $relative" }
    }
    $checks.payloadHashesMatch = $true
    foreach ($key in @('uninstallRegistered','uninstallerExists','guideInstalled','applicationShortcut','guideShortcut','uninstallShortcut','userDataRetained')) { if (-not $checks[$key]) { throw "Installation check failed: $key" } }
    $checks | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $qaRoot 'installed.json') -Encoding utf8
    $checks | ConvertTo-Json
    return
}

$uninstaller = Join-Path $installDirectory 'unins000.exe'
$process = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/LOG="' + (Join-Path $qaRoot 'uninstall.log') + '"')) -WindowStyle Hidden -PassThru -Wait
if ($process.ExitCode -ne 0) { throw "Uninstaller failed with exit code $($process.ExitCode)." }
$checks = [ordered]@{
    registryRemoved = -not (Test-Path -LiteralPath $registryPath)
    programRemoved = -not (Test-Path -LiteralPath (Join-Path $installDirectory 'ThemeStudio.exe'))
    shortcutsRemoved = -not (Test-Path -LiteralPath $groupDirectory)
    userDataRetained = Test-Path -LiteralPath $sentinel
}
if ($checks.Values -contains $false) { throw ('Uninstall verification failed: ' + ($checks | ConvertTo-Json -Compress)) }
$checks | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $qaRoot 'uninstalled.json') -Encoding utf8
# Remove only the exact marker created above, never the user's data directory.
if ((Get-Content -LiteralPath $sentinel -Raw).Trim() -eq 'Theme Studio installer retention test: do not remove user assets.') { Remove-Item -LiteralPath $sentinel }
$checks | ConvertTo-Json
