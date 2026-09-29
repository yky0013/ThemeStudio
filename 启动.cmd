@echo off
setlocal
if not exist "%~dp0release\ThemeStudio-0.4.0\ThemeStudio.exe" (
  echo Theme Studio has not been packaged yet. Run tools\package.ps1.
  pause
  exit /b 1
)
start "" "%~dp0release\ThemeStudio-0.4.0\ThemeStudio.exe"
