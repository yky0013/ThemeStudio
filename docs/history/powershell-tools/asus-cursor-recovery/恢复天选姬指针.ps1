# Compatibility entry point; both names use the same recovery implementation.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'restore_asus_tx_cursor.ps1') @args
