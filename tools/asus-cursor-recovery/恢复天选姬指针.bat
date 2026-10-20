@echo off
setlocal
"%~dp0AsusCursorRecovery.exe" %*
set "restore_exit=%errorlevel%"
if not "%restore_exit%"=="0" echo Recovery failed. Please keep the error message above.
if /i not "%~1"=="/nopause" pause
exit /b %restore_exit%
