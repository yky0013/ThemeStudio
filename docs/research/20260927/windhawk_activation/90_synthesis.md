# Concrete Windhawk activation workflow for ThemeStudio

Status: research-only recommendation. No Windhawk binary was installed, no `.wh.cpp` was compiled, no mod was enabled, and no system setting was changed during this run.

## Recommended boundary

ThemeStudio should treat Windhawk as an external runtime and invoke its matched upstream `windhawk-cli.exe`. The CLI already owns source parsing, metadata validation, Clang invocation, per-architecture DLL creation, config/source persistence, settings migration, profile mirroring, cleanup, and enable/disable state. ThemeStudio should pass an absolute local `.wh.cpp` path, parse the CLI's JSON envelope, and surface the result. It should not copy DLLs, edit registry/INI storage, implement injection, or reimplement the compiler.

This is the upstream implementation path documented by the CLI command tree and install/lifecycle sources: [CLI arguments](https://github.com/ramensoftware/windhawk/blob/main/src/windhawk-core/cli/src/args.rs), [local install pipeline](https://github.com/ramensoftware/windhawk/blob/main/src/windhawk-core/cli/src/commands/mods/install.rs), and [lifecycle commands](https://github.com/ramensoftware/windhawk/blob/main/src/windhawk-core/cli/src/commands/mods/lifecycle.rs).

## Exact command sequence

Assume `root` is the actual Windhawk installation directory containing `windhawk.ini`, `windhawk-cli.exe`, and the matched `windhawk-core.dll`; `source` is the user-selected absolute `.wh.cpp` file.

```text
windhawk-cli.exe --app-root <root> --json source meta <source>
windhawk-cli.exe --app-root <root> --json mod list
windhawk-cli.exe --app-root <root> --json mod install --file <source> --disabled
windhawk-cli.exe --app-root <root> --json mod show local@<id>
windhawk-cli.exe --app-root <root> --json mod enable local@<id>
windhawk-cli.exe --app-root <root> --json mod show local@<id>
windhawk-cli.exe --app-root <root> --json mod list --enabled
```

1. Run `source meta` first. Read `data.metadata.id`, `version`, `architecture`, and `include`; do not derive the id from the filename. The command is stateless and validates the actual file.
2. Read the existing state with `mod list`. If `local@<id>` already exists, retain a copy/hash of the current source and record `mod show` before replacing it.
3. Install with `--file ... --disabled`. A local-file install always compiles locally; do not add `--no-precompiled` because upstream rejects that combination. The CLI normalizes the source, validates `@id`, compiles all selected declared architecture targets, writes the source/config/DLLs through `installMod`, and returns the installed storage id as `local@<id>`.
4. Require process exit 0, JSON `success:true`, `data.compiledLocally:true`, a non-empty `data.config.libraryFileName`, and `data.config.disabled:true` for the staged install.
5. Run `mod show local@<id>` and verify the persisted metadata/config. Only after the user-selected mod passes this compile/install check, run `mod enable local@<id>`.
6. Require enable JSON `data.enabled:true`; then run `mod show` and `mod list --enabled` as the persisted-state check.

The local-source id prefix is material: the upstream CLI intentionally stores a file install under `local@<id>` and does not track that mod in the repository user profile. This is appropriate for bundled or user-selected source snapshots, but it means repository update/profile semantics should not be assumed.

## Runtime prerequisites

Use one matched Windhawk release directory. The recovered ThemeStudio source is pinned to upstream `ramensoftware/windhawk` commit `aef1a9f1e77f30c8fd96c5dd29373c38181486bf`, release `2.0.0-alpha.6`; the core workspace declares the same version. The official release page is [2.0 alpha 6](https://github.com/ramensoftware/windhawk/releases/tag/2.0.0-alpha.6). Do not mix the vendored alpha-6 CLI/core with a different Windhawk engine or compiler build.

The exact official Windows download is the NSIS installer asset [windhawk_setup.exe for 2.0.0-alpha.6](https://github.com/ramensoftware/windhawk/releases/download/2.0.0-alpha.6/windhawk_setup.exe), SHA-256 `f788f5eaf16d45841fc0f06750876a005a48848e6ebb7bb4df1b39c44afb5eab`. The official release also publishes [windhawk_setup_offline.exe](https://github.com/ramensoftware/windhawk/releases/download/2.0.0-alpha.6/windhawk_setup_offline.exe), SHA-256 `eac905e2e0d87c53241f3a06721124b83a56e7736695eedf1e1a40b536523d23`; there is no separate ZIP/portable archive asset. A read-only listing of the 18 MB online installer, using `C:\Program Files\NVIDIA Corporation\NVIDIA App\7z.exe` (7-Zip 22.01 x64), verified that its payload contains `windhawk-cli.exe`, `windhawk-core.dll`, `windhawk.exe`, `windhawk-ui.exe`, mod host executables, `ModsRuntime` shims, and versioned engine DLL/import libraries. Extracted CLI/core version metadata is `2.0.0-alpha.6`; `windhawk-cli.exe --version` returned the same version. The default online payload has no `Compiler\bin\clang++.exe`, so local compilation needs the optional Development Tools component installed by the same release installer (`/AUTO_REINSTALL /DEVTOOLS` is the upstream update service's documented dev-tools path).

Required for the CLI path:

- `windhawk-cli.exe` — the official CLI introduced in Windhawk 2.0 alpha.
- `windhawk-core.dll` — matched to the CLI; the host loads it from the CLI executable directory and gates ABI/contract compatibility.
- `windhawk.ini` and the rest of the selected Windhawk installation metadata so `--app-root` resolves storage.
- Windhawk engine/runtime and its normal host (`windhawk.exe` plus the matched engine files). The normal non-portable runtime uses the Windhawk service; a portable runtime uses a session daemon. The CLI write can persist a mod without that runtime, but injection cannot be considered active until the engine is running.

Required for a local `.wh.cpp` compile:

- Development Tools / compiler component enabled in that Windhawk installation.
- `<CompilerPath>\bin\clang++.exe` and its compiler runtime files.
- `<EnginePath>\32\windhawk.lib`, `<EnginePath>\64\windhawk.lib`, and any selected ARM64 library, plus the matching engine DLL/runtime files. The compiler writes generated mod DLLs below `<appData>\Engine\Mods\<arch>`.

The 2.0 alpha release made Development Tools optional, so a normal small Windhawk install may lack `CompilerPath`. In that case `mod install --file` cannot satisfy this workflow; ThemeStudio should report that the Windhawk development tools/compiler are missing and leave its source recipe unchanged.

## Installed versus portable mode

`windhawk.ini` `[Storage] Portable` controls the mode. Portable mode uses INI files below its app-data path; non-portable mode uses the configured registry root, normally with app data under `%ProgramData%\Windhawk`. The engine watches portable mod INI files or the non-portable registry tree and reloads mods/settings after a change. These paths are implementation details owned by Windhawk; ThemeStudio must not write them directly.

Non-portable write commands need elevation in the current CLI. Upstream issue [#1050](https://github.com/ramensoftware/windhawk/issues/1050) records that the CLI has no self-elevation manifest: ordinary-shell local install/enable/remove/config/settings writes fail, while reads work. The failure may be exit 12 (`REGISTRY_FAILED`) or exit 11 (`IO_FAILED`), and an install can compile before failing at the registry write. ThemeStudio should preflight the elevation boundary before invoking the compile-bearing install command and ask for elevation only around the bounded CLI write.

Portable mode avoids the registry, but the process still needs write access to its installation/app-data directory. A portable copy in a protected location can still require elevation. Some individual mods may also have their own protected-process requirements; read the selected source's README/metadata and report those separately.

`--app-root <path>` is operational in the alpha-6 CLI: its help output exposes the flag, and the CLI source requires that the path contain `windhawk.ini`, then reads `[Storage] Portable` to select the portable backend. This flag only points the CLI/core at an existing root; it does not start the portable daemon. The exact alpha-6 payload includes the `windhawk.exe`/`windhawk-ui.exe` hosts and engine files, and the checked-in alpha-6 source routes non-portable installs through the service and portable installs through a session daemon. Portable daemon startup was not run in this research-only pass, so the evidence is source/payload compatibility rather than a live runtime test.

For a bundled immutable runtime with mutable data under `%LOCALAPPDATA%\ThemeStudio`, use the following two upstream storage files. The main file sits beside `windhawk.exe`, `windhawk-cli.exe`, and `windhawk-core.dll`; `EnginePath` is the numeric major/minor folder produced by replacing the installer archive's `$R1` placeholder with `2.0`.

```ini
; <bundle-root>\windhawk.ini
[Storage]
Portable=1
AppDataPath=%LOCALAPPDATA%\ThemeStudio
EnginePath=Engine\2.0
CompilerPath=Compiler
UIPath=UI
```

```ini
; <bundle-root>\Engine\2.0\engine.ini
[Storage]
Portable=1
AppDataPath=%LOCALAPPDATA%\ThemeStudio\Engine
```

The first file is consumed by the CLI/app storage managers. The second is consumed by the injected engine; its engine app-data root makes the C++ engine's `Mods`/`ModsWritable` paths line up with the CLI/core's `%LOCALAPPDATA%\ThemeStudio\Engine\Mods` and `...\ModsWritable` paths. Keep `Engine\2.0`, `Compiler`, `UI`, and `ModsRuntime` in the immutable bundle; keep `ModsSource`, `userprofile.json`, settings, compiled mod DLLs, and writable mod storage below `%LOCALAPPDATA%\ThemeStudio`.

If the NSIS payload is unpacked with 7-Zip instead of run through NSIS, the archive's `Engine\$R1` placeholder remains literal. The packaging step must rename that staged directory to `Engine\2.0` before using the files, for example:

```powershell
Move-Item -LiteralPath '<staging-root>\Engine\$R1' -Destination '<bundle-root>\Engine\2.0'
```

`$R1` must not appear in the deployed `EnginePath`; it is an installer variable placeholder, not a runtime directory name.

The alpha-6 app has no `-daemon` switch. Its default action is `RunDaemon`; `-tray-only` suppresses UI opening. The quiet portable commands are therefore:

```text
<bundle-root>\windhawk.exe -tray-only
<bundle-root>\windhawk.exe -exit -wait -timeout 30000
```

The second command posts the portable daemon's exit message and waits. Non-portable service-only controls are separate internal flags (`-service-start`, `-service-stop -also-no-autostart`) and may require elevation. None of these commands was executed during research.

There is no need to build the CLI from source for this snapshot: the official alpha-6 installer already distributes it. If a later offline deployment is required, use the official `windhawk_setup_offline.exe` asset or extract the official NSIS payload; do not substitute a hand-built CLI/core pair. Development Tools are a separate optional installer component, so absence of VS/Rust on the host does not block using the released CLI, but it does block local `.wh.cpp` compilation until that component is installed.

## Readiness and evidence limits

The CLI-level readiness gate is:

- `source meta` succeeds for the exact selected source.
- Install exits 0 with `success:true`, `compiledLocally:true`, `id:local@<id>`, and a non-empty `config.libraryFileName`.
- `mod show local@<id>` returns the expected source metadata and `config.disabled:false` after enable.
- `mod list --enabled` contains that id with `enabled:true`.

This proves Windhawk stored a compiled, enabled mod. It does not prove that a particular target process has already loaded the hook. The Windhawk engine source shows that config changes are watched and trigger `ReloadModsAndSettings`; target-process behavior still depends on the runtime being active, architecture/include rules, Windows protections, and whether the target process was restarted or safely reloaded. ThemeStudio should label the result as “Windhawk install/enable acknowledged” until a user-observable target behavior or Windhawk diagnostics confirms injection.

Do not use a saved ThemeStudio recipe, a source-card selection, or a successful `mod list` alone as proof of injection.

## Rollback

The bounded rollback sequence is:

```text
windhawk-cli.exe --app-root <root> --json mod disable local@<id>
windhawk-cli.exe --app-root <root> --json mod show local@<id>
```

This keeps the source/config/DLL for later re-enable and is the default failure recovery. Re-enable with `mod enable local@<id>` after the issue is understood.

For explicit full removal, after the user confirms the destructive action:

```text
windhawk-cli.exe --app-root <root> --json --yes mod remove local@<id>
```

Upstream `mod remove` removes config, stored source, compiled DLLs, and the profile entry where applicable. If a pre-existing `local@<id>` was replaced, preserve its source and pre-action `mod show`/settings before installation; restoring that source is another official `mod install --file <saved-source>` operation followed by the prior enable/disable state. Do not attempt manual DLL/registry cleanup.

## ThemeStudio-specific scope decision

This workflow intentionally makes no provider choice. It applies to whichever user-selected Windhawk source the UI passes. Taskbar/Dock candidates remain unselected, while the already-declared Windhawk cursor-effects provider can use the same path when the user explicitly chooses a concrete `.wh.cpp` source.

## Provenance

The recovered project records Windhawk source provenance in `docs/source-imports.json` and `vendor/upstream-snapshots/windhawk-source.json`: upstream commit `aef1a9f1e77f30c8fd96c5dd29373c38181486bf`, source archive SHA-256 `584AEA445B78A6C01CD05CF0F57349E1C7CBA4D3032A76B7CC596B8114A655DA`, and local snapshot commit `59e458e56268236d2e528daf7d0d6bd5068e8c53`. The official release commit API confirms that full SHA is the `2.0.0-alpha.6` commit. The extracted installer CLI/core PE versions also report `2.0.0-alpha.6`, so this is a compatible runtime pairing. The vendored source is upstream alpha 6, not an independently reimplemented compiler/injection engine. The current ThemeStudio verification record explicitly says Windhawk selection is configuration-only and injection is inactive, so the CLI integration described here is a planned activation boundary pending implementation and runtime QA.
