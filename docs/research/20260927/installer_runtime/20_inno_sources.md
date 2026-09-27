# Inno Setup 6.7.3 installer/runtime research checkpoints

## Scope and normalization

This note is limited to the three core official Inno Setup help topics requested for the Theme Studio installer: per-user path/profile constants, non-administrative behavior and uninstall registration, and explicit uninstall deletion. Directive cross-references are included only to pin the exact syntax for the requested Windows/version/architecture gates. No installer was built or executed.

## Source 1 — Constants

**Time**: 2026-09-27, 14:51:07 +08:00
**Source**: https://jrsoftware.org/ishelp/topic_consts.htm
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: `{localappdata}` resolves to the current user's local application-data folder, `{group}` resolves to the Start Menu folder selected by the user, and `{uninstallexe}` resolves to the generated uninstaller. In non-administrative mode, the auto shell-folder constants map to user locations, which is useful for a per-user installer and a user-scoped uninstaller shortcut.

# Relevant extracted content

```iss
[Setup]
DefaultDirName={localappdata}\Programs\ThemeStudio
DefaultGroupName=Theme Studio

[Icons]
Name: "{group}\Theme Studio Uninstall"; Filename: "{uninstallexe}"
```

Microsoft/ Inno Setup documents that `{localappdata}` is the current user's non-roaming Application Data path. `{group}` is the Start Menu folder chosen on the Start Menu page; it is created in the current user's profile in non-administrative mode. `{userprograms}` is the current user's Start Menu Programs path. `{uninstallexe}` is the full path to the generated uninstaller and is intended for an `[Icons]` entry; it is valid when `Uninstallable=yes` (the default).

The auto constants (`{autoprograms}`, `{autostartmenu}`, `{autopf}`, etc.) map to common locations in administrative mode and user locations in non-administrative mode. For a `PrivilegesRequired=lowest` installer, use the user-scoped constants explicitly where the desired location is part of the product contract, and use `{group}` or `{userprograms}` for a per-user Start Menu entry.

---

## Source 3 — [UninstallDelete] section

**Time**: 2026-09-27, 14:52:31 +08:00
**Source**: https://jrsoftware.org/ishelp/topic_uninstalldeletesection.htm
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: `[UninstallDelete]` is opt-in: it deletes additional files/directories only when entries explicitly name them. To preserve `%LOCALAPPDATA%\ThemeStudio` across uninstall, do not add an entry targeting that directory. This keeps the WebView2 profile/UDF, icon assets, and mouse assets available for a later reinstall or deliberate user cleanup.

# Relevant extracted content

```iss
; Intentionally omit any [UninstallDelete] entry for the WebView2 UDF:
; %LOCALAPPDATA%\ThemeStudio

; If a future product-owned cache must be removed, name it narrowly:
[UninstallDelete]
Type: dirifempty; Name: "{localappdata}\ThemeStudio\TransientCache"
```

The section is optional and covers additional files/directories beyond those installed/created by `[Files]` or `[Dirs]`. `filesandordirs` recursively removes a named directory; `dirifempty` removes only an empty named directory. Inno Setup explicitly warns against broad wildcards that delete application data. Therefore the default Theme Studio uninstall should rely on the install log for installed files and omit any UDF/asset deletion rule.

---

## Cross-reference checks for the requested gates

The following official directive topics pin the exact values and are linked from the core help. They are recorded here as cross-references rather than additional core pages:

| Requirement | Minimal directive | Official reference | Boundary |
|---|---|---|---|
| Keep custom directory chooser visible | `DisableDirPage=no` | https://jrsoftware.org/ishelp/topic_setup_disabledirpage.htm | `yes` hides the page; `auto` may hide it for an existing install and then uses the default directory. |
| Minimum Windows version | `MinVersion=10.0` (or the project’s actual minimum) | https://jrsoftware.org/ishelp/topic_setup_minversion.htm | Format is `major.minor`; the directive rejects older Windows. `MinVersion=6.1sp1` is the documented default, not a Windows 10 requirement. |
| x64-compatible runtime | `ArchitecturesAllowed=x64compatible` | https://jrsoftware.org/ishelp/topic_setup_architecturesallowed.htm | `x64compatible` includes x64 Windows and Arm64 Windows 11 x64 emulation; use `x64os` only when true x64 Windows is required. |
| x64 install mode when shipping x64 files | `ArchitecturesInstallIn64BitMode=x64compatible` | https://jrsoftware.org/ishelp/topic_setup_architecturesinstallin64bitmode.htm | Only enable 64-bit install mode for matching 64-bit payloads; pair the allowed expression with the same expression to reject 32-bit Windows. |
| Automatic uninstaller / Windows uninstall entry | `Uninstallable=yes` | https://jrsoftware.org/ishelp/topic_setup_uninstallable.htm; https://jrsoftware.org/ishelp/topic_installorder.htm | Default is `yes`; setting `no` removes automatic uninstall support. Inno's installation order says the Add/Remove Programs entry is created when needed, and the generated uninstaller is the target for `{uninstallexe}`. |

## Minimal bounded ISS fragment

```iss
[Setup]
PrivilegesRequired=lowest
DisableDirPage=no
DefaultDirName={localappdata}\Programs\ThemeStudio
DefaultGroupName=Theme Studio
Uninstallable=yes
UninstallDisplayIcon={app}\ThemeStudio.exe
MinVersion=10.0
ArchitecturesAllowed=x64compatible

[Icons]
Name: "{group}\Theme Studio"; Filename: "{app}\ThemeStudio.exe"; WorkingDir: "{app}"
Name: "{group}\Theme Studio Uninstall"; Filename: "{uninstallexe}"
```

`Uninstallable=yes` is the default; the generated uninstaller is registered in Windows' uninstall metadata and can also be exposed through the explicit Start Menu `{uninstallexe}` icon. Do not add `[UninstallDelete]` for `%LOCALAPPDATA%\ThemeStudio` when the WebView2 profile, icon files, or mouse assets must survive uninstall. Keep the icon and mouse asset paths stable under that preserved app-data root, or have the application resolve them from its preserved data directory after reinstall.

Asset boundary: omitting `[UninstallDelete]` preserves only the separately stored app-data root. Files installed under `{app}` are still normal installed files and are removed by the uninstall log. Therefore icon/cursor assets that must survive uninstall must actually live under `%LOCALAPPDATA%\ThemeStudio` (or another explicitly preserved data root), and runtime references must resolve there; putting them only beside the executable does not make them persistent.

---

## Source 2 — [Setup]: PrivilegesRequired

**Time**: 2026-09-27, 14:51:42 +08:00
**Source**: https://jrsoftware.org/ishelp/topic_setup_privilegesrequired.htm
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: `PrivilegesRequired=lowest` is the direct Inno Setup switch for a non-administrative, per-user installation. It suppresses elevation even for members of the Administrators group; the application and installer must therefore work with unprivileged write access.

# Relevant extracted content

```iss
[Setup]
PrivilegesRequired=lowest
```

The official directive accepts `admin` or `lowest`, defaults to `admin`, and says `lowest` always runs Setup in non-administrative install mode without requesting administrative privileges. The page warns to use it only when the installation succeeds under unprivileged accounts.

For Theme Studio this pairs with a user-writable default such as `{localappdata}\Programs\ThemeStudio` and a user Start Menu target. The resulting uninstall registration is user-scoped in non-administrative mode; see the official non-administrative-mode cross-reference: https://jrsoftware.org/ishelp/topic_admininstallmode.htm

---
