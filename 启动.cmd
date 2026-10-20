@echo off
setlocal
if not exist "%~dp0release\ThemeStudio-0.5.5\ThemeStudio.exe" (
  echo Run python tools\studio.py package first.
  pause
  exit /b 1
)
start "" "%~dp0release\ThemeStudio-0.5.5\ThemeStudio.exe"
