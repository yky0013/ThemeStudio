# Inno Setup upgrade behavior and Theme Studio handoff checkpoints

## Scope

This bounded note records only the official Inno Setup behavior needed to assess upgrades for the current `ThemeStudio.iss`: same `AppId` with `UsePreviousAppDir`, `/DIR`, `CloseApplications`/`RestartApplications`, and `AppMutex`. It also records read-only observations from `installer/ThemeStudio.iss` and `src/host/ThemeStudio.cs`, with attention to installation paths containing Chinese characters under `C:\` or `E:\`. No code or installer script was changed, built, or executed.

## Current project state inspected

- `installer/ThemeStudio.iss` uses the fixed `AppId={{34717904-40BD-47C3-9AE5-4CA3B55820B5}` and `DefaultDirName={autopf}\ThemeStudio`; it does not declare `UsePreviousAppDir`, so the official default must be applied.
- The script currently declares `CloseApplications=yes` and `RestartApplications=no`.
- The script has no `AppMutex` directive.
- `src/host/ThemeStudio.cs` uses `Path.Combine` and quoted backend arguments for data paths; `FormClosing` cancels while `activeRequests > 0`, then sets `closing=true`, and `FormClosed` closes backend stdin and waits up to 3 seconds for the backend.

---

## Official source checkpoints

**Time**: 2026-09-29, Asia/Shanghai
**Source**: query-search: four official-site queries for `AppId`/`UsePreviousAppDir`, `/DIR`, `CloseApplications`/`RestartApplications`, and `AppMutex`
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: The official Inno Setup help search results resolved the canonical help pages used below. The direct pages were then opened and persisted individually before drawing conclusions.

# Relevant extracted content

> `https://jrsoftware.org/ishelp/topic_setup_appid.htm`
>
> `https://jrsoftware.org/ishelp/topic_setup_usepreviousappdir.htm`
>
> `https://jrsoftware.org/ishelp/topic_setupcmdline.htm`
>
> `https://jrsoftware.org/ishelp/topic_setup_closeapplications.htm`
>
> `https://jrsoftware.org/ishelp/topic_setup_restartapplications.htm`
>
> `https://jrsoftware.org/ishelp/topic_setup_appmutex.htm`

---

**Time**: 2026-09-29, Asia/Shanghai
**Source**: https://jrsoftware.org/ishelp/topic_setup_appmutex.htm
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: `AppMutex` is the explicit Inno Setup gate for blocking installation of a new version or uninstallation while the application is running. Setup and Uninstall check one or more named mutexes at startup and prompt the user to close all instances; the application must create the same named mutex during startup, and Windows compares mutex names case-sensitively.

# Relevant extracted content

> “This directive is used to prevent the user from installing new versions of an application while the application is still running, and to prevent the user from uninstalling a running application.”

> “Use of this directive requires that you add code to your application which creates a mutex with the name you specify in this directive. The code should be executed during your application's startup.”

> “Note that mutex name comparison in Windows is case sensitive.”

The current `ThemeStudio.iss` has no `AppMutex` directive, and the inspected `src/host/ThemeStudio.cs` has no visible named mutex creation. Therefore adding only an `AppMutex` line would not establish a reliable running-process handoff; the script value and startup mutex name would need to be deliberately paired in a future code-and-installer change. This note records the requirement only and makes no code change.

---

**Time**: 2026-09-29, Asia/Shanghai
**Source**: https://jrsoftware.org/ishelp/topic_setup_restartapplications.htm
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: `RestartApplications` defaults to `yes`, but it only restarts applications when `CloseApplications` is `yes` or `force`, and the application must use Windows `RegisterApplicationRestart`. Theme Studio explicitly sets `RestartApplications=no`, so the installer’s close-applications phase does not provide automatic post-upgrade relaunch through this directive.

# Relevant extracted content

> “Valid values: `yes` or `no`” and “Default value: `yes`.”

> “When set to `yes` and `CloseApplications` is also set to `yes` or `force`, Setup restarts the closed applications after the installation has completed.”

> “For Setup to be able to restart an application after the installation has completed, the application needs to be using the Windows `RegisterApplicationRestart` API function.”

The current script’s `RestartApplications=no` is therefore an explicit choice. The script’s `[Run]` entry can still offer `ThemeStudio.exe` as a post-install launch (`postinstall`, `nowait`, `skipifsilent`); that is a separate explicit `[Run]` action, not Restart Manager’s automatic restart. The inspected `ThemeStudio.cs` shows close cleanup but no `RegisterApplicationRestart` call, so there is no evidence in that file for automatic restart support.

---

**Time**: 2026-09-29, Asia/Shanghai
**Source**: https://jrsoftware.org/ishelp/topic_setup_closeapplications.htm
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: `CloseApplications` accepts `force`, `yes`, or `no`, and defaults to `yes`. With `yes` or `force`, interactive Setup pauses on Preparing to Install when it detects an application using files that `[Files]` or `[InstallDelete]` must update, then asks whether to close the applications; with silent Setup it closes/restarts matching applications unless command-line switches say otherwise. `force` enables forced closing and can lose unsaved work; the current script uses the safer prompt-capable `yes`.

# Relevant extracted content

> “Valid values: `force`, `yes`, or `no`” and “Default value: `yes`.”

> “If set to `yes` or `force` and Setup is not running silently, Setup will pause on the Preparing to Install wizard page if it detects applications using files that need to be updated by the `[Files]` or `[InstallDelete]` section, showing the applications and asking the user if Setup should automatically close the applications and restart them after the installation has completed.”

> “If set to `force` Setup will force close when closing applications, unless told not to via the command line. Use with care since this may cause the user to lose unsaved work.”

> “Setup uses Windows Restart Manager to detect, close, and restart applications.”

The current `ThemeStudio.iss` has `CloseApplications=yes`, so an interactive upgrade can reach a close-applications prompt when the running Theme Studio or its loaded files are among the files to replace. `ThemeStudio.cs` has `OnClosing`: it cancels the close while `activeRequests > 0`; once idle it sets `closing=true`, and `OnClosed` closes backend stdin and waits up to 3 seconds. Therefore the handoff assumption is “let active requests drain, then allow close”; a close attempt during an active request can leave the installer waiting or unable to replace locked files and should be retried after the operation finishes. This is a source-backed interaction risk, not a claim that Restart Manager bypasses the application’s close event.

---

**Time**: 2026-09-29, Asia/Shanghai
**Source**: https://jrsoftware.org/ishelp/topic_setupcmdline.htm
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: `/DIR="x:\dirname"` overrides the default directory shown on the Select Destination Location page and requires a fully qualified pathname. The documented form is quoted, so an explicit path such as `/DIR="E:\桌面主题工作室"` should be passed as one argument when the path contains spaces or non-ASCII characters; the page itself does not state a restriction on Chinese characters.

# Relevant extracted content

> “`/DIR="x:\dirname"`”

> “Overrides the default directory name displayed on the Select Destination Location wizard page. A fully qualified pathname must be specified.”

The current script leaves the directory page enabled (`DisableDirPage=no`) and has a default under `{autopf}`. In a managed upgrade, `/DIR="C:\中文路径\ThemeStudio"` or `/DIR="E:\中文路径\ThemeStudio"` is the explicit command-line path supplied to Setup; this is the documented mechanism to override the wizard’s default directory (including the previous directory selected through `UsePreviousAppDir`). The Unicode-path claim still needs a real installer smoke test because this command-line page specifies the pathname form but does not promise a Chinese-path compatibility result.

---

**Time**: 2026-09-29, Asia/Shanghai
**Source**: https://jrsoftware.org/ishelp/topic_setup_usepreviousappdir.htm
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: `UsePreviousAppDir` defaults to `yes`. When enabled, Setup checks the registry for the same application and presents the previous installation directory as the new default. Because the current script omits the directive and keeps the same `AppId`, an upgrade normally proposes the user’s prior directory, including a prior path on `C:\` or `E:\` containing Chinese characters; this is a default proposal, not a forced location.

# Relevant extracted content

> “Default value: `yes`.”

> “When this directive is `yes`, the default, at startup Setup will look in the registry to see if the same application is already installed, and if so, it will use the directory of the previous installation as the default directory presented to the user in the wizard.”

The page does not document a special limitation for Chinese directory names. Treat Unicode path behavior as an implementation verification item rather than claiming this page proves it. The current `DefaultDirName={autopf}\ThemeStudio` is therefore the first-install default; a recognized same-`AppId` upgrade uses the previous registered directory as the wizard’s default.

---

**Time**: 2026-09-29, Asia/Shanghai
**Source**: https://jrsoftware.org/ishelp/topic_setup_appid.htm
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: A fixed `AppId` identifies the same application across installer versions: subsequent Setup runs can append to the existing uninstall log only when the `AppId` matches, and the `AppId` also determines the uninstall registry key. The page explicitly ties a non-empty `AppId` to restoration of previous install settings such as `UsePreviousAppDir`.

# Relevant extracted content

> “Setup will only append to an uninstall log if the `AppId` of the existing uninstall log is the same as the current installation's `AppId`.”

> “If not empty, this value will only be used to attempt to restore previous install settings (like the settings stored by `[Setup]` section directive `UsePreviousAppDir`).”

> “`AppId` also determines the actual name of the Uninstall registry key, to which Inno Setup tacks on `_is1` at the end.”

For the current script, the stable GUID means a later build with the same GUID is recognized as the same product for these upgrade/uninstall records. The source does not make the install directory immutable; the directory choice behavior is pinned by the next `UsePreviousAppDir` source and can still be overridden by `/DIR`.

---

## Bounded conclusions for the current installer

1. **Same application and default directory**: `ThemeStudio.iss:7` keeps the same GUID `AppId`. Since `UsePreviousAppDir` is omitted, its official default is `yes`; a recognized upgrade presents the previously registered directory as the default. The first-install fallback remains `DefaultDirName={autopf}\ThemeStudio` (`ThemeStudio.iss:11`).
2. **Explicit path override**: `/DIR="C:\中文路径\ThemeStudio"` or `/DIR="E:\中文路径\ThemeStudio"` is the documented fully qualified override. Quote it as one command-line argument. The official page does not promise Chinese-path compatibility, so the exact C:/E: Chinese path behavior remains a smoke-test item.
3. **Close handoff**: `CloseApplications=yes` (`ThemeStudio.iss:30`) uses Windows Restart Manager and may prompt in interactive Setup. In the current host file, `ThemeStudio.cs:502-506` cancels `FormClosing` while `activeRequests > 0`; after idle it sets `closing=true`. `ThemeStudio.cs:507-513` closes backend input and waits up to 3 seconds. Upgrade validation should cover both an idle close and an active request that must drain before retrying; `force` is not selected and should not be assumed.
4. **Restart behavior**: `RestartApplications=no` (`ThemeStudio.iss:31`) disables Restart Manager’s automatic relaunch. The `[Run]` entry at `ThemeStudio.iss:59` can offer an ordinary post-install launch when the user selects it and Setup is not silent. No `RegisterApplicationRestart` call was found in the inspected host file.
5. **Running-process gate**: `AppMutex` is absent from the current script, and no named mutex creation was found in the inspected host file. The official requirement is a matching startup-created named mutex with case-sensitive spelling; adding only the installer directive would not complete the gate.
6. **Data-path boundary**: `ThemeStudio.cs` resolves normal user data under `%LOCALAPPDATA%\ThemeStudio` and passes paths through .NET `Path.Combine`/quoted `ProcessStartInfo` arguments. This supports keeping user data independent of whether the program is installed under `C:\` or `E:\`, but it does not replace the missing installer smoke test for non-ASCII install roots.

## Evidence boundary

Confirmed by official pages: fixed same-`AppId` identity and previous-directory default; `/DIR` fully qualified override; `CloseApplications` prompt/Restart Manager behavior; `RestartApplications` dependency on `RegisterApplicationRestart`; and `AppMutex` startup mutex requirement. Not established by those pages: successful Chinese-path installation/upgrade, whether every Theme Studio payload file is released within the 3-second backend wait, or whether future code will create a matching mutex. Those require a local installer/runtime test.
