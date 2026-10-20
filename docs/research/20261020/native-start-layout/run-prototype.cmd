@echo off
setlocal
set "ROOT=%~dp0"
set "CSC=C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not exist "%CSC%" (
  echo Missing C# compiler: %CSC%
  exit /b 2
)
"%CSC%" /nologo /target:exe /platform:x64 /out:"%ROOT%native_start_layout_proof.exe" "%ROOT%native_start_layout_proof.cs"
if errorlevel 1 exit /b %errorlevel%
if not exist "%ROOT%proof-output" mkdir "%ROOT%proof-output"
"%ROOT%native_start_layout_proof.exe" "%ROOT%proof-output\native-com.json"
exit /b %errorlevel%
