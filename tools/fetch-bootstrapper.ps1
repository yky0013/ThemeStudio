$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$manifest=Get-Content -LiteralPath (Join-Path $taskRoot 'config\webview2-bootstrapper.json') -Raw | ConvertFrom-Json
$output=Join-Path $taskRoot '.cache\runtime\MicrosoftEdgeWebview2Setup.exe'
New-Item -ItemType Directory -Path (Split-Path -Parent $output) -Force | Out-Null
if(-not (Test-Path -LiteralPath $output)){Invoke-WebRequest -Uri $manifest.source -OutFile $output -TimeoutSec 120}
if((Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash -ne $manifest.sha256){throw 'Bootstrapper changed upstream; verify the new Microsoft signature and update the pinned manifest before packaging. Download retained for review.'}
$signature=Get-AuthenticodeSignature -LiteralPath $output
if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notlike '*Microsoft Corporation*'){throw 'Invalid Microsoft Bootstrapper signature'}
Write-Output $output
