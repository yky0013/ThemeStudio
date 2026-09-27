# Source checkpoints

Each entry records a source actually inspected. URLs are official Windhawk or the local recovery snapshot. Local source claims are anchored to the recovered checkout; web claims are anchored to the upstream URL and line ranges where available.

## Web checkpoint W1 — CLI command surface

- Retrieved: 2026-09-27.
- URL: https://raw.githubusercontent.com/ramensoftware/windhawk/main/src/windhawk-core/cli/src/args.rs
- Upstream page: https://github.com/ramensoftware/windhawk/blob/main/src/windhawk-core/cli/src/args.rs
- Evidence: `GlobalArgs` defines `--app-root`, `--json`, `--yes`, `--quiet`, and `--arch` (raw lines 22-49). `TopCommand` exposes `mod` and `source` groups (raw lines 78-109). `ModCommand` exposes list/show/enable/disable/remove/config/settings/install/update/compile (raw lines 231-279). `ModInstallArgs` accepts `--file <path>`, optional positional id, `--disabled`, `--no-precompiled` for repository installs, and `--pch-folder` (raw lines 280-303). `source meta <file>` is a separate stateless metadata command (raw lines 422-429).
- Practical implication: call the official `windhawk-cli.exe` with `mod install --file <absolute-source>` and then `mod enable|disable <storage-id>`, using `--json` for machine parsing. Do not implement a compiler or write Windhawk storage directly.

## Web checkpoint W2 — local-source install pipeline

- Retrieved: 2026-09-27.
- URL: https://raw.githubusercontent.com/ramensoftware/windhawk/main/src/windhawk-core/cli/src/commands/mods/install.rs
- Upstream page: https://github.com/ramensoftware/windhawk/blob/main/src/windhawk-core/cli/src/commands/mods/install.rs
- Evidence: the CLI reads the `--file` source or stdin, normalizes BOM/line endings, parses metadata, and reconciles the declared `@id` (raw lines 17-80 and 91-107). `--file` mode always compiles locally and maps the installed storage id to `local@<id>` (raw lines 207-250 and 278-391). The pipeline invokes the shared core `installMod`; the core handles compile-or-download, persist, and cleanup (raw lines 207-250). Successful JSON includes `id`, `version`, `metadata`, `config`, `architectures`, and `compiledLocally`; text reports `Installed from file`, method, architectures, and `[disabled]` state (raw lines 492-533). Recompile uses `mod compile <id>` and the stored source (raw lines 420-461).
- Practical implication: after installing a local `.wh.cpp`, use `local@<declared @id>` for lifecycle commands. `--disabled` stages disabled; omitting it defaults a fresh install to enabled. Verify the returned JSON `data.config.disabled`.

## Web checkpoint W3 — enable/disable/remove semantics

- Retrieved: 2026-09-27.
- URL: https://raw.githubusercontent.com/ramensoftware/windhawk/main/src/windhawk-core/cli/src/commands/mods/lifecycle.rs
- Upstream page: https://github.com/ramensoftware/windhawk/blob/main/src/windhawk-core/cli/src/commands/mods/lifecycle.rs
- Evidence: `mod enable`/`mod disable` check that config exists, then call shared `setModEnabled`; JSON is `{id, enabled, changed}` and text says `Enabled`, `Already enabled`, `Disabled`, or `Already disabled` (raw lines 14-63). `mod remove` removes config/source/DLLs/profile entry and requires global `--yes` (raw lines 67-105).
- Practical implication: use `--json mod enable local@<id>` or `mod disable`; reserve `--json --yes mod remove local@<id>` for explicit destructive removal. Disable is the reversible rollback.

## Web checkpoint W4 — release and permission evidence

- Retrieved: 2026-09-27.
- Release URL: https://github.com/ramensoftware/windhawk/releases/tag/2.0.0-alpha.6
- Evidence: official prerelease tag `2.0.0-alpha.6`, commit prefix `aef1a9f`, released 2026-09-21; release page documents the alpha feature line and non-portable `windhawk://` registration (release lines 133-186). The official release list states alpha 1 introduced `windhawk-cli.exe` that installs/updates/removes/enables/disables mods, manages settings, and compiles local source.
- Issue URL: https://github.com/ramensoftware/windhawk/issues/1050
- Evidence: the official issue says `windhawk-cli` has no self-elevation manifest; ordinary-shell writes fail for local install/enable/remove/config/settings/app-settings, while reads work (issue lines 162-179). It says the UI's elevated broker is separate and the CLI does not use it (issue lines 189-203). This is upstream issue evidence, not a promise of a broker feature.
- Practical implication: invoke current CLI write commands from an elevated process, or obtain explicit user-approved elevation before the bounded write. Do not assume the UI broker services CLI calls. Preflight elevation before compiling to avoid compile-then-registry-failure waste.

## Local checkpoint L1 — vendored provenance and current limitation

- Snapshot root: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1` (recovered source; no edits made there).
- `docs/source-imports.json:15-24` and `vendor/upstream-snapshots/windhawk-source.json:1-5` record `vendor/windhawk`, local snapshot commit `59e458e...`, upstream `ramensoftware/windhawk` commit `aef1a9f1e77f30c8fd96c5dd29373c38181486bf`, and archive SHA-256 `584AEA445B78A6C01CD05CF0F57349E1C7CBA4D3032A76B7CC596B8114A655DA`.
- `docs/source-imports.json:27-35` and `vendor/upstream-snapshots/windhawk-mods-source.json:1-5` record `vendor/windhawk-mods` upstream commit `682a7f72694eb768724bea8ef72b079aedd9c57b` and archive SHA-256 `CA32395FF3AC2A997E20CB3D8A19424BD108764CD48AC552C63D29DD0941BBA5`.
- `vendor/windhawk/src/windhawk-core/Cargo.toml:22-25` reports core workspace version `2.0.0-alpha.6` and Rust `1.96`.
- `docs/verification.json:35` records the current ThemeStudio release limitation: Windhawk selection is configuration only and the injection engine is not active. This is the gap being addressed.

## Local checkpoint L2 — executable/root and session setup

- `vendor/windhawk/src/windhawk-core/cli/src/app_root.rs:1-61`: root precedence is explicit `--app-root` (must contain `windhawk.ini`), `WINDHAWK_UI_PATH`, then CLI executable directory; missing root is `ENV_INVALID`.
- `vendor/windhawk/src/windhawk-core/cli/src/lib.rs:88-128`: session commands load `windhawk-core.dll`, resolve root, create `SessionConfig`, and use product token `windhawk-cli`; `source meta` is stateless and only needs the DLL.
- `vendor/windhawk/src/windhawk-core/core-host/src/loader.rs:18-106`: release CLI resolves `windhawk-core.dll` next to its own executable; host rejects a non-absolute fallback instead of searching PATH, and gates ABI/contract before creating a session.
- Practical implication: ship/use matched `windhawk-cli.exe` and `windhawk-core.dll` from one Windhawk release directory, or pass `--app-root` while keeping CLI and core DLL versions matched. The source checkout alone is not a runnable host.

## Local checkpoint L3 — storage paths and mode split

- `vendor/windhawk/src/windhawk-core/core/src/services/storage.rs:42-191`: sources are `<appData>\ModsSource\<modId>.wh.cpp`, user profile `<appData>\userprofile.json`, compiled DLLs `<appData>\Engine\Mods`, writable per-mod storage `<appData>\Engine\ModsWritable`, and config/settings use portable INI files or registry trees.
- `vendor/windhawk/src/windhawk-core/windows/src/storage.rs:48-118`: `windhawk.ini` `[Storage]` resolves `Portable`, required `AppDataPath`/`EnginePath`, optional `CompilerPath`/`UIPath`, and non-portable `RegistryKey`; portable uses INI backend, non-portable registry backend. `%ProgramData%` expansion is implemented at lines 186-248.
- `vendor/windhawk/src/windhawk-core/core-host/src/windhawk_ini.rs:13-58`: portable is nonzero `[Storage] Portable`; absence or parse failure is treated as non-portable for discovery.
- `vendor/windhawk/src/windhawk/engine/storage_manager.cpp:310-500`: portable enumerates `<appData>\Mods` INI files and watches that directory, non-portable enumerates registry `<RegistryKey>\Mods` and watches it with `RegNotifyChangeKeyValue`.
- Practical implication: do not edit `%ProgramData%`, registry trees, or portable INIs directly. Let `installMod`/`setModEnabled` maintain config, source, DLL naming, profile mirrors, and cleanup.

## Local checkpoint L4 — compiler/runtime and live reload

- `vendor/windhawk/src/windhawk-core/core/src/services/compiler/invoke.rs:20-43`: local compile invokes `<CompilerPath>\bin\clang++.exe`, working directory `<CompilerPath>`, and links `<EnginePath>\<arch>\windhawk.lib`.
- `vendor/windhawk/src/windhawk-core/core/src/services/compiler/orchestrate.rs:136-210` and `:260-355`: non-portable compile probes `<appData>\Engine\Mods` writable; compilation is per declared architecture with unique DLL names; missing output or compiler failure is an error.
- `vendor/windhawk/src/windhawk-core/core/src/services/install/orchestrate.rs:147-275` and `:300-400`: `installMod` compiles or downloads, writes config/source, migrates settings, deletes superseded DLLs, mirrors profile state, and commits pending DLLs.
- `vendor/windhawk/src/windhawk/engine/customization_session.cpp:318-355` and `:480-575`: engine watches mod config changes and calls `ModsManager::ReloadModsAndSettings` unless process mitigation prevents safe dynamic reload. `storage_manager.cpp:431-500` gives portable directory watcher versus non-portable registry watcher.
- Practical implication: successful CLI install plus a running Windhawk engine is the activation path; config writes are observed and reload the engine. Saving ThemeStudio recipe JSON alone has no activation effect.

## Local checkpoint L5 — service/portable runtime boundary

- `vendor/windhawk/src/windhawk/app/app.cpp:231-287` and `:337-372`: non-portable mode starts/uses the Windhawk service; portable mode runs a daemon in the current session. `ExitApp` stops service for non-portable and posts exit to portable daemon.
- `vendor/windhawk/src/windhawk/engine/tool_mod_process.h:1-18` and `:75-95`: session manager is service on regular installs and daemon on portable installs; it launches tool-mod hosts.
- `vendor/windhawk/src/windhawk-core/ui/src/broker/mod.rs:145-170` and `:248-280`: UI broker is a separate privileged helper path for non-portable UI operations; portable and already-elevated windows do their own privileged work.
- Practical implication: call the CLI for install/lifecycle and detect/report whether service/portable daemon is running. Do not reimplement service startup, injection, compiler, or broker protocol. If CLI writes are run elevated, retain elevation only for the bounded write command.

## Local checkpoint L6 — metadata and machine-readable readiness

- `vendor/windhawk/src/windhawk-core/cli/src/commands/source.rs:1-53`: `source meta <file>` parses the selected `.wh.cpp` through stateless `parseModSource`, returns `{"metadata": ...}` under `--json`, and reports malformed input as usage error (exit 2).
- `vendor/windhawk/src/windhawk-core/cli/src/commands/mods/list.rs:38-125` and `:150-208`: `mod list` calls `listInstalledMods` with profile synchronization; JSON rows include id/version/name/description/enabled/config.
- `vendor/windhawk/src/windhawk-core/cli/src/commands/mods/show.rs:1-83`: `mod show <id>` returns metadata, README, initial settings, and config; text includes `State: enabled|disabled`.
- `vendor/windhawk/src/windhawk-core/cli/src/output.rs:1-80` and `error.rs:1-150`: `--json` success is `{schemaVersion:1, success:true, data:...}`. Operational error classes include `ENV_INVALID` exit 3, `MOD_NOT_INSTALLED` 4, `COMPILE_FAILED` 7, `IO_FAILED` 11, and `REGISTRY_FAILED` 12; structured details and compiler diagnostics are retained.
- Practical implication: parse one JSON envelope, require exit 0 and `success:true`, then verify `data.id`, `data.compiledLocally`, `data.config.disabled`, and non-empty `data.config.libraryFileName`; follow with `mod show`/`mod list`. Treat exit 11/12 as environment/permission failures, not blind retry signals.

## Local checkpoint L7 — exact storage layout and versioned Engine path

- Static NSIS extraction used the exact executable `C:\Program Files\NVIDIA Corporation\NVIDIA App\7z.exe` (7-Zip 22.01 x64). It was used only to list/extract installer payload files; no Windhawk executable was started by this extraction step.
- `vendor/windhawk/src/windhawk/app/storage_manager.cpp:13-38` expands `%VAR%` values with `ExpandEnvironmentStringsW` and resolves relative storage paths against the folder containing `windhawk.exe`; absolute expanded paths override that base by normal Windows path semantics.
- `vendor/windhawk/src/windhawk/app/storage_manager.cpp:215-231` reads the main `windhawk.ini` beside `windhawk.exe`; required storage keys are `EnginePath` and `AppDataPath`, optional `UIPath`/`CompilerPath`, and `Portable=1` selects INI storage so `RegistryKey` is not required.
- `vendor/windhawk/src/windhawk/app/storage_manager.cpp:86-119` treats `EnginePath` as the versioned engine root and appends exactly one architecture folder: `32`, `64`, or `arm64`. The NSIS payload lists `Engine\\$R1\\32|64|arm64`; `$R1` is an installer-time placeholder and must not be written literally into a deployed `windhawk.ini`.
- `vendor/windhawk/src/windhawk/shared/version.h:4-13` defines alpha-6 as numeric major/minor/revision `2/0/0` plus `-alpha.6`; the official alpha-2 discussion's installed layout shows `EnginePath=Engine\\2.0`. For this fixed alpha-6 bundle, substitute `$R1` with `2.0`:

  ```ini
  ; <bundle-root>\\windhawk.ini
  [Storage]
  Portable=1
  AppDataPath=%LOCALAPPDATA%\\ThemeStudio
  EnginePath=Engine\\2.0
  CompilerPath=Compiler
  UIPath=UI
  ```

- `vendor/windhawk/src/windhawk/engine/storage_manager.cpp:310-330` reads a second file at `<bundle-root>\\Engine\\2.0\\engine.ini`; it needs its own `[Storage]` with `Portable=1` and the engine data root. To keep the Rust CLI's `<appData>\\Engine\\Mods` and the C++ engine's `appData\\Mods` equivalent, use:

  ```ini
  ; <bundle-root>\\Engine\\2.0\\engine.ini
  [Storage]
  Portable=1
  AppDataPath=%LOCALAPPDATA%\\ThemeStudio\\Engine
  ```

- This yields the expected split: bundled immutable binaries under `<bundle-root>\\Engine\\2.0`, `<bundle-root>\\Compiler`, and `<bundle-root>\\UI`; mutable data under `%LOCALAPPDATA%\\ThemeStudio`, including `ModsSource`, `userprofile.json`, and `%LOCALAPPDATA%\\ThemeStudio\\Engine\\Mods`/`ModsWritable`.

## Web checkpoint W9 — upstream installed-path example

- Retrieved: 2026-09-27 from the official maintainer discussion https://github.com/ramensoftware/windhawk/discussions/1007.
- The alpha-2 installed `windhawk.ini` example shown there uses `Portable=0`, `CompilerPath=Compiler`, `EnginePath=Engine\\2.0`, `UIPath=UI`, `AppDataPath=%ProgramData%\\Windhawk`, and `RegistryKey=HKLM\\SOFTWARE\\Windhawk`.
- This independently corroborates the `EnginePath=Engine\\2.0` major/minor substitution used for the alpha-6 fixed bundle. For portable mode, omit `RegistryKey` and change `Portable=1`; the local alpha-6 sources require the separate `Engine\\2.0\\engine.ini` with its engine data `AppDataPath` and `Portable=1` as recorded in L7.

## Local checkpoint L8 — quiet portable daemon commands

- `vendor/windhawk/src/windhawk/app/app.cpp:80-108` recognizes `-exit`, `-restart`, and `-restart-bg`; there is no `-daemon` action flag. With no recognized action flag, `app.cpp:225-231` executes the default `RunDaemon()` path.
- `app.cpp:231-287` reads `-tray-only`; the portable path then creates the daemon/tray window without showing the UI. Therefore the quiet portable start command is:

  ```text
  <bundle-root>\\windhawk.exe -tray-only
  ```

- `app.cpp:185-200` handles `-exit`; with `-wait` it accepts optional `-timeout` and waits for termination. `app.cpp:343-355` routes portable exit through `PostCommandToRunningDaemon(kExit)`, while non-portable exit stops the service. Therefore the quiet portable stop command is:

  ```text
  <bundle-root>\\windhawk.exe -exit -wait -timeout 30000
  ```

- `service.cpp:80-98` confirms that the non-portable service launches session daemons with `-tray-only`. For non-portable service-only control, the internal commands are `windhawk.exe -service-start` and `windhawk.exe -service-stop -also-no-autostart`; they are not the portable daemon path and may require elevation.
- No start/stop command was executed. These are source-derived command lines only.

## Local checkpoint L9 — static extraction caveat

- The NSIS listing exposes payload paths as `Engine\$R1\...`; this is an installer variable placeholder. 7-Zip extraction preserves the literal `$R1` directory, whereas a normal NSIS run expands it. For a static bundle assembled from the archive, rename the staged literal directory with PowerShell's `-LiteralPath`:

  ```powershell
  Move-Item -LiteralPath '<staging-root>\Engine\$R1' -Destination '<bundle-root>\Engine\2.0'
  ```

- The `2.0` value is supported by `version.h`'s `VERSION_MAJOR=2`/`VERSION_MINOR=0` and the official installed alpha-2 layout example; alpha-6 carries the same major/minor engine layout. This packaging rename was not executed in the research run.

## Web checkpoint W5 — official release API asset inventory

- Retrieved: 2026-09-27 via the official GitHub REST endpoint: https://api.github.com/repos/ramensoftware/windhawk/releases/tags/2.0.0-alpha.6
- Release metadata: tag `2.0.0-alpha.6`, name `2.0 alpha 6`, prerelease `true`, published `2026-09-21T22:15:04Z`, release page https://github.com/ramensoftware/windhawk/releases/tag/2.0.0-alpha.6.
- Exact Windows assets returned by the official API:
  - `windhawk_setup.exe`, 18,216,176 bytes, SHA-256 `f788f5eaf16d45841fc0f06750876a005a48848e6ebb7bb4df1b39c44afb5eab`, URL https://github.com/ramensoftware/windhawk/releases/download/2.0.0-alpha.6/windhawk_setup.exe.
  - `windhawk_setup_offline.exe`, 178,375,960 bytes, SHA-256 `eac905e2e0d87c53241f3a06721124b83a56e7736695eedf1e1a40b536523d23`, URL https://github.com/ramensoftware/windhawk/releases/download/2.0.0-alpha.6/windhawk_setup_offline.exe.
- The release has no separate `.zip` or portable archive asset in the API response. The official Windows distribution is therefore installer-based; CLI inclusion must be verified from the installer payload or an installed/portable extraction of that installer, not inferred from a nonexistent archive URL.

## Web checkpoint W6 — official installer payload inspection

- Retrieved: 2026-09-27 from the W5 `windhawk_setup.exe` URL. The downloaded file is kept for audit at `docs/research/20260927/windhawk_activation/windhawk_setup_2.0.0-alpha.6.exe`.
- Integrity: 18,216,176 bytes; local SHA-256 `F788F5EAF16D45841FC0F06750876A005A48848E6EBB7BB4DF1B39C44AFB5EAB`, matching the official API digest `sha256:f788f5eaf16d45841fc0f06750876a005a48848e6ebb7bb4df1b39c44afb5eab`.
- A read-only 7-Zip listing identified the official NSIS payload entries `windhawk-cli.exe`, `windhawk-core.dll`, `windhawk.exe`, `windhawk-ui.exe`, `windhawk-mod.exe`, `windhawk-mod-uiaccess.exe`, `windhawk-mod-elevated.exe`, `ModsRuntime\32|64|arm64\windhawk-mod-shim.dll`, and versioned `Engine\$R1\32|64|arm64\windhawk.dll` plus `windhawk.lib`. The payload also contains `Compiler\compile_flags.txt`, headers, and compiler runtime libraries.
- The default online installer payload listing did **not** contain `Compiler\bin\clang++.exe`; local `.wh.cpp` compilation therefore requires the optional Development Tools component/reinstall. This agrees with the alpha release's optional-dev-tools design and the local compiler path `<CompilerPath>\bin\clang++.exe`.
- Extracted copies were placed only under `payload_inspection/` for static inspection; no extracted executable was launched. PE version metadata reports:
  - `windhawk-cli.exe`: File/Product version `2.0.0-alpha.6`, FileDescription `Windhawk CLI`, x64 PE; SHA-256 `FCFD4CB9F8A57257E728BE508AAA73A10A6173D8F5FB077EA37FB2316FF39290`.
  - `windhawk-core.dll`: File/Product version `2.0.0-alpha.6`, FileDescription `Windhawk Core`, x64 PE; SHA-256 `9D6D14EFB14605823F0352EC19D36F5699495114D1A4A407C13634A6E332D538`.
  - `windhawk.exe`, `windhawk-ui.exe`, and `windhawk.dll`: version `2.0.0-alpha.6`, x64 PE.
- Safe help-only execution of the extracted CLI (no root/session supplied, no mod command) returned `windhawk-cli 2.0.0-alpha.6`; `mod install --help` confirmed `--file`, `--disabled`, `--json`, `--app-root`, `--arch`, and the rule that `--file` always compiles locally. No engine, install, source, or lifecycle operation was run.

## Web checkpoint W7 — release commit compatibility

- Retrieved: 2026-09-27 via official GitHub REST endpoint `https://api.github.com/repos/ramensoftware/windhawk/commits/aef1a9f1e77f30c8fd96c5dd29373c38181486bf`.
- The response identifies full SHA `aef1a9f1e77f30c8fd96c5dd29373c38181486bf`, commit message `2.0.0-alpha.6`, author Michael Maltsev, date `2026-09-21T19:12:39Z`, and page https://github.com/ramensoftware/windhawk/commit/aef1a9f1e77f30c8fd96c5dd29373c38181486bf.
- Compatibility conclusion: the checked-in source manifest's Windhawk commit, the upstream release commit, the vendored core workspace version, and the extracted official CLI/core PE versions all agree on `2.0.0-alpha.6`. This is the exact release to pair with the checked-in fixed Windhawk source snapshot. The source snapshot itself is not a binary distribution; use the official installer payload for runtime files.

## Web checkpoint W8 — Authenticode integrity

- Retrieved: 2026-09-27 by read-only `Get-AuthenticodeSignature` on the official release asset and extracted payload files.
- `windhawk_setup_2.0.0-alpha.6.exe`, extracted `windhawk-cli.exe`, and extracted `windhawk-core.dll` all returned Authenticode status `Valid` on this Windows host.
- This supplements, but does not replace, the official release URL, API digest, and version/commit checks recorded in W5-W7.
