@echo off
setlocal
if not exist "%~dp0release\ThemeStudio\ThemeStudio.exe" (
  echo Theme Studio has not been packaged yet. Run tools\package.ps1.
  pause
  exit /b 1
)
start "" "%~dp0release\ThemeStudio\ThemeStudio.exe"
