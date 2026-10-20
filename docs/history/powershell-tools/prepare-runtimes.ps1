param([string]$Extractor)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$cache=Join-Path $projectRoot '.cache\runtimes'
$locks=Get-Content -LiteralPath (Join-Path $projectRoot 'config\runtime-distributions.json') -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Path $cache -Force | Out-Null
function Get-PinnedAsset([string]$Url,[string]$Hash,[string]$Destination){
    if(-not(Test-Path -LiteralPath $Destination) -or (Get-FileHash -LiteralPath $Destination).Hash.ToLowerInvariant() -cne $Hash){
        & curl.exe -f -sS -L --retry 3 --retry-all-errors --connect-timeout 20 --max-time 600 -o $Destination $Url
        if($LASTEXITCODE -ne 0){throw ('Pinned asset download failed: '+$Url)}
    }
    if((Get-FileHash -LiteralPath $Destination).Hash.ToLowerInvariant() -cne $Hash){throw ('Pinned asset SHA-256 mismatch: '+$Destination)}
}
$seelenPackage=Join-Path $cache 'Seelen.UI_2.8.6.0_x64.Msix'
Get-PinnedAsset $locks.seelen.asset $locks.seelen.assetSha256 $seelenPackage
$seelen=Join-Path $cache 'seelen-engine'
New-Item -ItemType Directory -Path $seelen -Force | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive=[IO.Compression.ZipFile]::OpenRead($seelenPackage)
try{
    foreach($entry in $archive.Entries){
        $relative=[Uri]::UnescapeDataString($entry.FullName)
        if(-not $relative.StartsWith('static/') -and $relative -notin @('seelen-ui.exe','slu.exe','slu-service.exe','sluhk.dll','SHA256SUMS','SHA256SUMS.sig')){continue}
        $destination=[IO.Path]::GetFullPath((Join-Path $seelen $relative))
        if(-not $destination.StartsWith([IO.Path]::GetFullPath($seelen).TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'MSIX payload entry escaped its extraction directory.'}
        if($entry.FullName.EndsWith('/')){New-Item -ItemType Directory -Path $destination -Force | Out-Null;continue}
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        [IO.Compression.ZipFileExtensions]::ExtractToFile($entry,$destination,$true)
    }
}finally{$archive.Dispose()}
foreach($property in $locks.seelen.files.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $seelen $property.Name)).Hash.ToLowerInvariant() -cne $property.Value){throw ('Seelen binary mismatch: '+$property.Name)}}
if(Test-Path -LiteralPath (Join-Path $seelen 'AppxManifest.xml')){throw 'Unpackaged Seelen runtime must not carry package identity metadata.'}
$windhawkPackage=Join-Path $cache 'windhawk_setup_offline.exe'
Get-PinnedAsset $locks.windhawk.asset $locks.windhawk.assetSha256 $windhawkPackage
if((Get-AuthenticodeSignature -LiteralPath $windhawkPackage).Status -ne 'Valid'){throw 'Original Windhawk distribution signature is invalid.'}
if(-not $Extractor){$Extractor=(Get-Command 7z.exe -ErrorAction SilentlyContinue).Source}
if(-not $Extractor){$Extractor='C:\Program Files\NVIDIA Corporation\NVIDIA App\7z.exe'}
if(-not(Test-Path -LiteralPath $Extractor)){throw 'A full 7-Zip NSIS extractor is required. Pass its absolute path through -Extractor.'}
$windhawk=Join-Path $cache 'windhawk'
& $Extractor x $windhawkPackage ('-o'+$windhawk) -y -bso0 -bsp0
if($LASTEXITCODE -ne 0){throw 'Windhawk offline distribution extraction failed.'}
$fixedEngine=Join-Path $windhawk 'Engine\2.0'
if(-not(Test-Path -LiteralPath $fixedEngine)){Copy-Item -LiteralPath (Join-Path $windhawk 'Engine\$R1') -Destination $fixedEngine -Recurse}
foreach($property in $locks.windhawk.files.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $windhawk $property.Name)).Hash.ToLowerInvariant() -cne $property.Value){throw ('Windhawk binary mismatch: '+$property.Name)}}
if(-not(Test-Path -LiteralPath (Join-Path $windhawk 'Compiler\bin\clang++.exe'))){throw 'Original offline compiler is missing.'}
Write-Output 'Pinned Seelen and Windhawk distributions are ready; no engine was started.'
