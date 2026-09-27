param([switch]$SkipPackage)
$ErrorActionPreference = 'Stop'
$studioRoot = Split-Path -Parent $PSScriptRoot
$studioCompiler = Join-Path $studioRoot '.tools\inno-6.7.3\ISCC.exe'
$runtime = Join-Path $studioRoot '.cache\runtime\MicrosoftEdgeWebView2RuntimeInstallerX64.exe'
Push-Location -LiteralPath $studioRoot
try {
    if (-not $SkipPackage) { & .\tools\package.ps1; if ($LASTEXITCODE -ne 0) { throw 'Application packaging failed.' } }
    $runtimeManifest = Get-Content -LiteralPath 'config\webview2-runtime.json' -Raw | ConvertFrom-Json
    if ((Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash -ne $runtimeManifest.sha256) { throw 'Bundled WebView2 runtime hash mismatch.' }
    $signature = Get-AuthenticodeSignature -LiteralPath $runtime
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notlike '*Microsoft Corporation*') { throw 'Bundled runtime is not a verified Microsoft binary.' }
    & $studioCompiler /Q installer\ThemeStudio.iss
    if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed.' }
    $version = (Get-Content -LiteralPath 'package.json' -Raw | ConvertFrom-Json).version
    $installer = Join-Path $studioRoot ('installers\ThemeStudio-' + $version + '-Windows-x64-Setup.exe')
    Get-FileHash -LiteralPath $installer -Algorithm SHA256
    Write-Output $installer
} finally { Pop-Location }
