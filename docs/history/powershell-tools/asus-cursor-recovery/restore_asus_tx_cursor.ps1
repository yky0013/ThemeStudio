[CmdletBinding()]
param(
    [string]$CursorDirectory = (Join-Path $env:WINDIR 'Resources\Themes\ASUS'),
    [switch]$VerifyOnly
)
$ErrorActionPreference = 'Stop'
$cursorDir = $CursorDirectory
$files = @{
    Arrow='Normal Select.ani'; Help='Help Select.ani'; AppStarting='Working In Background.ani'; Wait='Busy.ani'
    IBeam='Text Select.ani'; NWPen='Handwriting.ani'; No='Unavailable.ani'; SizeNS='Vertical Resize.ani'
    SizeWE='Horizontal Resize.ani'; SizeNWSE='Diagonal Resize 1.ani'; SizeNESW='Diagonal Resize 2.ani'
    SizeAll='Move.ani'; Hand='Link Select.ani'
}
foreach ($name in $files.Keys) {
    $path = Join-Path $cursorDir $files[$name]
    if (-not (Test-Path -LiteralPath $path)) { throw "Cursor file not found: $path" }
}
# Finish validation before changing any settings.
if ($VerifyOnly) { Write-Host 'All 13 ASUS cursor files found. No settings changed.'; exit 0 }
$proofDir = Join-Path $PSScriptRoot 'docs'
New-Item -ItemType Directory -Path $proofDir -Force | Out-Null
$backup = Join-Path $proofDir ('cursor-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.json')
Get-ItemProperty -Path 'HKCU:\Control Panel\Cursors' | Select-Object * -ExcludeProperty PS* | ConvertTo-Json | Set-Content -LiteralPath $backup -Encoding UTF8
foreach ($name in $files.Keys) {
    Set-ItemProperty -Path 'HKCU:\Control Panel\Cursors' -Name $name -Value (Join-Path $cursorDir $files[$name])
}
# These roles are absent from the OEM theme; use Windows defaults, not remnants of another pack.
foreach ($name in @('Crosshair','UpArrow','Pin','Person')) {
    Set-ItemProperty -Path 'HKCU:\Control Panel\Cursors' -Name $name -Value ''
}
Set-ItemProperty -Path 'HKCU:\Control Panel\Cursors' -Name '(default)' -Value 'ASUS TX (Original)'
Set-ItemProperty -Path 'HKCU:\Control Panel\Cursors' -Name 'Scheme Source' -Type DWord -Value 1
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class CursorRefresh { [DllImport("user32.dll", EntryPoint="SystemParametersInfoW", SetLastError=true)] public static extern bool SystemParametersInfo(uint a,uint b,IntPtr c,uint d); }
'@
if (-not [CursorRefresh]::SystemParametersInfo(0x0057,0,[IntPtr]::Zero,0x0002)) { throw ('Windows cursor refresh failed: ' + [Runtime.InteropServices.Marshal]::GetLastWin32Error()) }
Write-Host 'ASUS TX cursor restored.' -ForegroundColor Green
Write-Host ('Backup: ' + $backup)
