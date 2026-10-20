$ErrorActionPreference = 'Stop'
$studioRoot = Split-Path -Parent $PSScriptRoot
$runtimeManifest = Get-Content -LiteralPath (Join-Path $studioRoot 'config\webview2-runtime.json') -Raw | ConvertFrom-Json
$runtimeDirectory = Join-Path $studioRoot '.cache\runtime'
New-Item -ItemType Directory -Path $runtimeDirectory -Force | Out-Null
$runtimeFile = Join-Path $runtimeDirectory 'MicrosoftEdgeWebView2RuntimeInstallerX64.exe'
if (-not (Test-Path -LiteralPath $runtimeFile)) { Invoke-WebRequest -Uri $runtimeManifest.url -OutFile $runtimeFile -TimeoutSec 1200 }
if ((Get-FileHash -LiteralPath $runtimeFile -Algorithm SHA256).Hash -ne $runtimeManifest.sha256) { throw 'Runtime hash mismatch; downloaded file retained for inspection.' }
$signature = Get-AuthenticodeSignature -LiteralPath $runtimeFile
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notlike '*Microsoft Corporation*') { throw 'Runtime publisher validation failed.' }
Write-Output $runtimeFile
