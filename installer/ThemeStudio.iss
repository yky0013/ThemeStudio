; Theme Studio offline installer. User data is owned by the application,
; outside {app}, and is intentionally retained on uninstall.
#define AppName "桌面主题工作室"
#define AppVersion "0.4.0"

[Setup]
AppId={{34717904-40BD-47C3-9AE5-4CA3B55820B5}
AppMutex=Local\ThemeStudio.Application
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Theme Studio
DefaultDirName={autopf}\ThemeStudio
DefaultGroupName={#AppName}
DisableDirPage=no
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableReadyPage=no
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible and not arm64
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.19041
Uninstallable=yes
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\ThemeStudio.exe
OutputDir=..\installers
OutputBaseFilename=ThemeStudio-{#AppVersion}-Windows-x64-Setup
WizardStyle=modern
Compression=lzma2/max
LZMAUseSeparateProcess=yes
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
InfoBeforeFile=安装说明.txt
VersionInfoDescription=桌面主题工作室精简安装程序
VersionInfoProductName={#AppName}
VersionInfoVersion=0.4.0.0
SetupIconFile=..\assets\brand\theme-studio.ico

[Languages]
Name: "chinesesimp"; MessagesFile: "ChineseSimplified.isl"

[Messages]
ConfirmUninstall=确定要卸载 %1 吗？%n%n卸载只删除程序文件，素材和备份会保留，已应用的图标和鼠标也会保留。%n如需恢复原外观，请先取消卸载，在程序内恢复后再卸载。

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式："; Flags: unchecked

[Files]
Source: "..\release\ThemeStudio-{#AppVersion}\*"; DestDir: "{app}"; Excludes: "ThemeStudio.Diagnostic.exe,ThemeStudio.Diagnostic.exe.config"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\.cache\runtime\MicrosoftEdgeWebview2Setup.exe"; Flags: dontcopy nocompression

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\ThemeStudio.exe"; WorkingDir: "{app}"
Name: "{group}\图文使用教程"; Filename: "{app}\wwwroot\help\index.html"
Name: "{group}\卸载桌面主题工作室"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\ThemeStudio.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\ThemeStudio.exe"; Description: "启动桌面主题工作室"; Flags: nowait postinstall skipifsilent runascurrentuser
Filename: "{app}\wwwroot\help\index.html"; Description: "打开图文使用教程"; Flags: shellexec nowait postinstall skipifsilent unchecked runasoriginaluser

[UninstallRun]
Filename: "{app}\ThemeStudio.exe"; Parameters: "--stop-runtimes"; Flags: runhidden waituntilterminated; RunOnceId: "ThemeStudioStopOwnedRuntimes"

[Code]
const
  WebViewKey = 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}';

function HasWebViewAt(RootKey: Integer): Boolean;
var
  Version: String;
begin
  Version := '';
  Result := RegQueryStringValue(RootKey, WebViewKey, 'pv', Version) and
    (Trim(Version) <> '') and (Trim(Version) <> '0.0.0.0');
end;

function HasWebView: Boolean;
begin
  Result := HasWebViewAt(HKLM32) or HasWebViewAt(HKCU32) or
    HasWebViewAt(HKLM64) or HasWebViewAt(HKCU64);
end;

function InitializeSetup: Boolean;
var
  NetRelease: Cardinal;
begin
  Result := True;
  NetRelease := 0;
  if not RegQueryDWordValue(HKLM32, 'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full', 'Release', NetRelease) then
    RegQueryDWordValue(HKLM64, 'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full', 'Release', NetRelease);
  if NetRelease < 528040 then begin
    SuppressibleMsgBox('需要 Microsoft .NET Framework 4.8。请先通过微软官方渠道安装或修复该组件，再运行本安装包。', mbError, MB_OK, IDOK);
    Result := False;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ExitCode: Integer;
  Attempt: Integer;
begin
  Result := '';
  if HasWebView then begin
    Log('WebView2 Runtime already present; bundled runtime skipped.');
    Exit;
  end;
  WizardForm.PreparingLabel.Caption := '正在从微软下载 WebView2 运行库，请保持网络连接…';
  ExtractTemporaryFile('MicrosoftEdgeWebview2Setup.exe');
  if not Exec(ExpandConstant('{tmp}\MicrosoftEdgeWebview2Setup.exe'),
      '/silent /install', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) then begin
    Result := Format('无法启动 WebView2 运行库安装程序（错误 %d）。请保留安装日志后重试。', [ExitCode]);
    Exit;
  end;
  Log(Format('WebView2 installer returned %d; checking runtime registration.', [ExitCode]));
  for Attempt := 1 to 20 do begin
    if HasWebView then Exit;
    Sleep(500);
  end;
  Result := Format('WebView2 运行库尚未就绪（安装程序返回 %d）。请保留日志，重启电脑后重试。', [ExitCode]);
end;
