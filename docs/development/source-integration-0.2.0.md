# 0.2.0 source integration and verification

The user selected Seelen Dock and toolbar on 2026-09-27. The setting page remains centralized. Windhawk taskbar selections are rejected before activation, so the two taskbar providers are not enabled together.

## Source and runtime provenance

* The existing Seelen UI components are based on `faaf24498e2040b613e6f68c405bc5047cd0df97`. The wallpaper image/video renderer and parallax component are reused. `src/host/DesktopWallpaper.cs` ports the WorkerW detection and window parenting from `src/background/widgets/wallpaper_manager/mod.rs`; the local changes add a desktop pointer input, media completion messages, and native apply/pause/stop controls.
* The actual Seelen desktop engine is the unmodified signed 2.8.6 distribution. Its complete corresponding source is in `vendor/runtime-sources/Seelen-UI-2.8.6` at `079c38584d48ef02e800d6f596bbef97bd00e327`. The MSIX is expanded for the upstream unpackaged mode. Package metadata is omitted and URI-encoded archive paths are decoded. Executables, static assets, signatures, and licenses remain unchanged.
* The actual Windhawk engine and compiler are the official offline 2.0.0-alpha.6 distribution, matching the existing source at `aef1a9f1e77f30c8fd96c5dd29373c38181486bf`. The upstream CLI parses and compiles the existing pinned mod source, writes settings, and enables/disables mods. The portable adapter supplies owned runtime/data paths and includes the original `.whl` and shim dependencies.
* `config/runtime-distributions.json` records download URLs, source commits, and binary/archive SHA-256 values. `tools/prepare-runtimes.ps1` reproduces the unpacking without launching an engine. Existing source import and license records remain in `docs/source-imports.json`, `docs/vendor-changes.json`, and `licenses/`.
* Mod source SHA-256 values now use canonical LF line endings in both the catalog builder and activation integrity check. Windows CRLF checkouts remain valid. Actual source changes still fail validation. Some older saved recipes may need the affected mod to be selected again because the earlier catalog used mixed line-ending hashes.

## Implementation boundaries

Desktop shortcut images use independent persisted mappings, with thumbnail arrows, per-row selection/import, library click, and drag/drop. Changes retain an exact shortcut backup. Public desktop modifications use the elevated installed application.

Desktop backgrounds are separate WorkerW child windows, behind desktop icons. They reuse the selected media and motion components on each detected monitor. The original Windows wallpaper setting is not overwritten; stopping the background reveals it. A single 2560 x 1600 display was verified locally with both an image and a video, including pause/resume/stop. Multi-monitor behavior is implemented but was not tested on physical multi-monitor hardware.

Seelen Dock and toolbar are started using the original signed GUI/service and upstream launch behavior. The 2.8.6 engine does not live-reload `settings.json`, so applying changed settings restarts this bundle's engine. Another installed Seelen engine is never terminated. Windhawk reports enabled state separately from a DLL actually observed in a target process; the local mouse-trail test confirmed both. The other source-backed mods have not all been exercised on this machine and may require their target applications or compatible Windows versions.

Uninstall stops the owned desktop background and Seelen/Windhawk engines. A Seelen scheduled task is removed only when its action points to this installation's service. Imported assets and original icon/cursor backups remain in the user's local application data.

## Evidence

`docs/development/verification-0.2.0` contains bounded native test results: independent icon pairing and exact restoration, elevated public-desktop writing and restoration, real image/video desktop parenting/playback, Seelen activation and engine stop, Windhawk DLL loading, and system state restoration. Installer evidence is added after the final installer regression.

The automated checks passed 20 frontend tests, TypeScript checking, and 31 Windows backend tests. The backend suite uses temporary shortcuts/data and does not change the user's system cursor configuration.
