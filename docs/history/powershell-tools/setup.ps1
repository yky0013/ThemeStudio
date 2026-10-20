$ErrorActionPreference = 'Stop'
$studioRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $studioRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { & python.exe -m venv .venv; if ($LASTEXITCODE -ne 0) { throw 'Python virtual environment setup failed.' } }
    & .\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r components\icon-workbench\build-requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency setup failed.' }
    & npm.cmd ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency setup failed.' }
    $sdk = Get-Content -LiteralPath 'config\webview2-sdk.json' -Raw | ConvertFrom-Json
    $cache = Join-Path $studioRoot '.cache'
    New-Item -ItemType Directory -Path $cache -Force | Out-Null
    $package = Join-Path $cache ('microsoft.web.webview2.' + $sdk.version + '.nupkg')
    if (-not (Test-Path -LiteralPath $package)) { Invoke-WebRequest -Uri $sdk.source -OutFile $package -TimeoutSec 120 }
    if ((Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sdk.sha256.ToLowerInvariant()) { throw 'WebView2 SDK package hash mismatch; package retained for inspection.' }
    $sdkDirectory = Join-Path $cache 'webview2'
    if (-not (Test-Path -LiteralPath (Join-Path $sdkDirectory 'lib\net462\Microsoft.Web.WebView2.Core.dll'))) {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [IO.Compression.ZipFile]::ExtractToDirectory($package, $sdkDirectory)
    }
    Write-Output 'Theme Studio build dependencies are ready.'
} finally { Pop-Location }
