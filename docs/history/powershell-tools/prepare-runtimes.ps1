param([string]$Extractor)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$cache=Join-Path $projectRoot '.cache\runtimes'
$locks=Get-Content -LiteralPath (Join-Path $projectRoot 'config\runtime-distributions.json') -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Path $cache -Force | Out-Null
function Get-PinnedAsset([string]$Url,[string]$Hash,[string]$Destination){
    if(-not(Test-Path -LiteralPath $Destination) -or (Get-FileHash -LiteralPath $Destination).Hash.ToLowerInvariant() -cne $Hash){
        Invoke-WebRequest -Uri $Url -OutFile $Destination -TimeoutSec 180
    }
    if((Get-FileHash -LiteralPath $Destination).Hash.ToLowerInvariant() -cne $Hash){throw ('Pinned asset SHA-256 mismatch: '+$Destination)}
}
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
Write-Output 'Pinned Windhawk distribution are ready; no engine was started.'
