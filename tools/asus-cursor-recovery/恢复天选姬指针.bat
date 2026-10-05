@echo off
setlocal
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0restore_asus_tx_cursor.ps1"
set "restore_exit=%errorlevel%"
if not "%restore_exit%"=="0" echo Recovery failed. Please keep the error message above.
if /i not "%~1"=="/nopause" pause
exit /b %restore_exit%
