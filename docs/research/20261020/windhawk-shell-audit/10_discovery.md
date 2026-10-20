# Local source inventory

**Time**: 2026-10-20, 17:20:00 +08:00
**Source**: `E:\desktop\windows\ThemeStudio-0.6` at commit `b692673878190524ef11501075fd084411348154`; local vendor sources are clean in `git status`.
**Method**: local-read (via `rg`, `Get-Content`, and SHA-256 inventory)
**Confidence**: high
**Insight**: The requested vendor scope contains two A-class internal PowerShell implementations and six B-class compatibility surfaces. No C++ source under `vendor/windhawk` contains a PowerShell token; two non-C++ vendor files are historical/UI fixture references only.

# Relevant extracted content

## A — internal hardcoded PowerShell implementing a mod-owned function

### `vendor/windhawk-mods/mods/net-toggle.wh.cpp`

- SHA-256: `5a2bb38088cc97475331f2ef898e06039083fed991e371b24e7bebffc183c9e6`.
- `RunPowerShellCommand(LPCWSTR psCommand, BOOL targetState)` at lines 274–334 formats `-NoProfile -NonInteractive -WindowStyle Hidden -Command`, elevates `powershell.exe` with `ShellExecuteExW(... lpVerb=L"runas" ...)`, waits up to `POWERSHELL_TIMEOUT_MS` (line 174), and changes `g_networkIsUp` only after exit code 0.
- `WorkerThreadProc` lines 769–772 supplies the hardcoded commands `Get-NetAdapter -Physical | Enable-NetAdapter -Confirm:$false` and the matching disable command. This is a mod-owned network adapter toggle, so it is A.
- `ResetWorkerThreadProc` lines 807–829 supplies the hardcoded sequence `Disable-NetAdapter`, `Start-Sleep -Seconds 2`, `ipconfig /flushdns`, and `Enable-NetAdapter`, again through elevated `powershell.exe`. This is A.
- Native replacement recommendation: enumerate present `GUID_DEVCLASS_NET` devices using `SetupDiGetClassDevsW` + `SetupDiEnumDeviceInfo`, preserve the current physical-adapter filter, then call `CM_Disable_DevNode`/`CM_Enable_DevNode` (or the `DIF_PROPERTYCHANGE`/`SetupDiCallClassInstaller` path) in a privileged helper. Keep per-device `CONFIGRET`/Win32 error reporting and update `g_networkIsUp` only after all selected devices succeed. Replace `Start-Sleep` with `Sleep(2000)`. Treat DNS flush separately: the official `windns.h` index did not expose a public `DnsFlushResolverCache`; retain `ipconfig /flushdns` as a separately invoked command-line dependency or verify an SDK/runtime export before using it. Do not use `CM_DISABLE_PERSIST`, because the current behavior is transient.
- Privilege boundary: the injected mod cannot assume an elevated token. Preserve the current UAC behavior with a small native elevated helper launched with the documented `runas` verb, or another approved broker. A direct medium-integrity call may return access denied.

### `vendor/windhawk-mods/mods/uwp-assets-redirect.wh.cpp`

- SHA-256: `234baa0de8ec8260970e54f74832dde737a1437c26b79b768a5a30ba642a4d94`.
- `g_ownership_command` at lines 2331–2337 is a hardcoded command line: `powershell -NoProfile -WindowStyle minimized Start-Process -Wait -FilePath cmd -Verb RunAs -ArgumentList '/c ... takeown ... & icacls ...'`.
- `CheckWindowsAppsOwner` lines 2339–2461 prompts the user, copies that command into a mutable buffer, and runs it with `CreateProcess(nullptr, commandLine, ...)` at line 2456. This grants access to `C:\Program Files\WindowsApps` for the UWP asset redirector; it is A.
- Native replacement recommendation: use a native elevated helper. Either (1) invoke `takeown.exe`/`icacls.exe` directly with `ShellExecuteExW` and `runas` while retaining the visible/minimized progress behavior, or (2) implement the operation fully with `GetNamedSecurityInfoW`, `SetEntriesInAclW`, and `SetNamedSecurityInfoW`, enabling `SE_TAKE_OWNERSHIP_NAME`/`SE_RESTORE_NAME` as required. The latter avoids `cmd.exe` as well and should resolve the Administrators and current-user SIDs explicitly; preserve the current `takeown /A` owner and current-user `(R)` grant semantics. Check every return code and free ACL/security-descriptor buffers with `LocalFree`.
- Do not alter the separate icon-cache command at lines 497–509: it is a native `cmd /c` command and contains no PowerShell. It is outside this audit’s PowerShell replacement scope.

---

## B — explicit user-selected terminal or user-authored PowerShell/script execution; preserve

### `vendor/windhawk-mods/mods/auto-theme-switcher.wh.cpp`

- SHA-256: `421ac8b0eef2c7dc6e65d374d4c5712113671d7e974e42b593daeaa30785609b`.
- `ScriptPath` is a user setting at line 136 and is passed to `RunScript` at lines 520 and 1159.
- `RunScript` lines 352–370 checks the user-selected path extension and launches `.ps1` with `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <script> -light|-dark`; other extensions are opened directly. This is user-authored script execution, B. Preserve the PowerShell host, `-File`, arguments, and failure logging. Do not classify the `powershell.exe` string as an internal ThemeStudio implementation.

### `vendor/windhawk-mods/mods/magic-mouse.wh.cpp`

- SHA-256: `913d4d43e51c7f64747d75015209a5b236873a368894c303c0380fccd10d5e7c`.
- The documented **Admin Terminal Here** action at line 60 is user-selected and accepts an optional command parameter.
- `ACTION_ADMIN_TERMINAL` lines 3138–3167 derives the current Explorer path, builds `Set-Location -LiteralPath '<path>'; <user actionParam>`, and launches elevated `powershell.exe`. The location setup is internal convenience, but the terminal and optional command are explicit user-authored behavior; preserve B. A future cleanup may use `lpDirectory` for the initial location, but it must not remove the PowerShell terminal or pass-through command parameter.
- The separate **Run Command Line** action at lines 58 and 2867–2892 uses `COMSPEC`/`cmd.exe` for the user-authored command and is not a PowerShell implementation.

### `vendor/windhawk-mods/mods/open-in-admin-terminal.wh.cpp`

- SHA-256: `3e1cf76b77b26ab4f7bc0b1511fa680930c18d89ae9cfcd97563e945ae92f4c9`.
- The mod explicitly offers PowerShell 7 and Windows PowerShell terminal choices (settings/readme lines 25–27, 51, 75–82) and `.ps1` script entries (lines 25, 57, 134–142).
- `ResolveTerminalChoiceExecutable` lines 363–371 resolves `pwsh.exe` or `powershell.exe`; `ResolveAutoTerminal` lines 426–432 keeps them in the Auto order.
- `BuildSetLocationCommand` lines 711–726 and `BuildLaunchSpec` lines 789–829 use `-NoExit -Command Set-Location` to open the selected terminal in the target folder. This is terminal initialization within B; preserve the resulting working directory and terminal choice. `lpDirectory` may replace the location command when the chosen host honors it, but that is an optimization rather than permission to remove PowerShell.
- `BuildScriptInterpreterSpec` lines 861–916 selects the PowerShell host for `.ps1`, emits optional `-NoExit`, optional `-ExecutionPolicy Bypass`, then `-File <scriptPath>`. `BuildScriptLaunchSpec` lines 934–969 wraps it in the selected terminal where needed. Preserve all of this for user-authored scripts.
- `LaunchAdminTerminal` and `LaunchTerminalNonElevated` lines 2092–2174 use `ShellExecuteExW` with `runas`/`open`, so elevation and non-elevated user-selected behavior are already native around the PowerShell host.

### `vendor/windhawk-mods/mods/separate-system-tray-icons.wh.cpp`

- The custom action grammar documents `ps:`/`powershell:` at line 70 and settings lines 197 and 210.
- `ExecuteActionWorker` lines 953–983 strips the user prefix, builds `-NoProfile -ExecutionPolicy Bypass -Command <user text>`, and opens `powershell.exe`. This is an explicit user-authored custom action, B; preserve the prefixes, command text, and hidden launch.

### `vendor/windhawk-mods/mods/ultimate-custom-tray.wh.cpp`

- The custom `shell:` action is documented at lines 40, 49–50.
- `ExecuteAction` lines 710–753 passes the user text after `shell:` to `powershell.exe`, with optional `-NoExit` and `runas`/visible behavior. This is B; preserve the custom action and its elevation/window options.

### `vendor/windhawk-mods/mods/windows-11-start-menu-buttons.wh.cpp`

- The custom `shell:` action is documented at lines 92 and 112–113.
- `ExecuteSingleCommand` lines 1132–1157 passes user-authored text to `powershell.exe`, supports optional `runas`, and adds `-NoExit` for a visible terminal. This is B; preserve it.

---

## C — comments, samples, documentation, identifiers, or visual matching data only

These are exact local matches with no mod-owned PowerShell process or command execution in the matched code:

| File and lines | Evidence and classification |
|---|---|
| `agenda-in-calendar-view.wh.cpp:95` | Readme tells the user to run `icacls` in PowerShell to grant calendar access. C documentation. |
| `click-on-empty-explorer.wh.cpp:70,341` | PowerShell is an example of a context-menu entry to match. C documentation/settings text; the mod invokes the shell menu item generically. |
| `console-quick-paste.wh.cpp:4,20,40–42` | The sample `Start-Process` string is pasted as user-configured text by `PasteCommand` (lines 96–117); no PowerShell process is launched by the mod. C sample setting. |
| `disable-windows-shortcuts.wh.cpp:1138` | Comment says the native prompt replaced PowerShell. C comment; the code already calls the native prompt. |
| `explorer-custom-shortcuts.wh.cpp:59` | Security note mentions interpreter re-parsing and recommends native arguments. C documentation. |
| `gather-windows-to-monitor.wh.cpp:69,78–83` | PowerShell snippet is a user diagnostic for display names. C documentation/sample. |
| `hide-dotfiles-explorer.wh.cpp:61` | Documentation states that Command Prompt/PowerShell visibility is unaffected. C documentation. |
| `macos-minimize-animation.wh.cpp:149–150` | `powershell.exe` is an example process name to exclude; no launch occurs. C identifier/documentation. |
| `monitor-sleep-button.wh.cpp:130–134` | Historical batch/PowerShell example; the mod’s runtime implementation is native. C documentation/sample. |
| `taskbar-clock-customization.wh.cpp:369` | Readme suggests `Get-TimeZone -ListAvailable`. C documentation. |
| `taskbar-empty-space-clicks.wh.cpp:3219` | `pInvoke->Invoke()` matched the broad `invoke-` search because of the preceding hyphen; it contains no PowerShell reference. C false positive. |
| `win11-home-group-restorer.wh.cpp:7023` | Comment-only PowerShell inspection recipe for symbol metadata. C documentation. |
| `windows-11-taskbar-styler.wh.cpp:9925–9931,10447–10453` | Taskbar style selectors and a remote `powershell.png` icon URL; no process or command execution. C visual matching data. |
| `vector-screen-holder.wh.cpp:126–132` | Readme sample `.vbs` calls `powershell -nop -w hidden -c` to signal a named event. Runtime has a native named event at line 1669 and does not execute the sample. C user documentation; preserve the sample if the script-trigger workflow remains supported. |

### `vendor/windhawk` C++ scope

`rg -n -i -S --glob '*.c' --glob '*.cc' --glob '*.cpp' --glob '*.cxx' --glob '*.h' --glob '*.hh' --glob '*.hpp' 'powershell|pwsh|\.ps1|start-process|invoke-' vendor/windhawk` returned no matches. The only vendor/windhawk matches outside C++ are:

- `src/windhawk-vscode/helper_scripts/disable_default_keybindings.py:1081`, a VS Code keybinding condition string `terminalShellType == 'pwsh'`.
- `src/windhawk-webview-ipc-contract/fixtures/listFontFamilies/error.json:8`, a fixture error message saying `powershell.exe exited with code 1`.

Both are C in this audit: neither is C++ runtime code for the Windhawk engine or a Windhawk mod.

---

## Source hashes for B-class runtime files

| File | SHA-256 |
|---|---|
| `auto-theme-switcher.wh.cpp` | `421ac8b0eef2c7dc6e65d374d4c5712113671d7e974e42b593daeaa30785609b` |
| `magic-mouse.wh.cpp` | `913d4d43e51c7f64747d75015209a5b236873a368894c303c0380fccd10d5e7c` |
| `open-in-admin-terminal.wh.cpp` | `3e1cf76b77b26ab4f7bc0b1511fa680930c18d89ae9cfcd97563e945ae92f4c9` |
| `separate-system-tray-icons.wh.cpp` | `cf2d76c9a2327817c9cc6f6a07025768a25f2597aba30682eba7402e33ec5120` |
| `ultimate-custom-tray.wh.cpp` | `d8fb0c070ba6c22fc035664ab12e8634706173752568a11c7bf1ad39d0a6d1ec` |
| `windows-11-start-menu-buttons.wh.cpp` | `25c54054dfb6273b08a755073ba04f7cb8a31634e79d90fdfc46eddee6021fbc` |

---
