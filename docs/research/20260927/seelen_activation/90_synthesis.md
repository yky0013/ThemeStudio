# Seelen activation synthesis — 2026-09-27

## Scope and conclusion

This is a research-only result. No Seelen engine, CLI, IPC endpoint, desktop setting, or wallpaper host was installed, started, or changed. The recovered ThemeStudio source is at `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1`; only this research folder is owned by this subtask.

The shortest source-grounded route is to run the original Seelen engine and use its own resource manager and wallpaper widget. The recovered project already has the correct Seelen settings composition logic, but 0.1.1 currently stops at saving a recipe: it does not ship `seelen-ui.exe`, `slu.exe`, `slu-service.exe`, or a WorkerW wallpaper window. For a real desktop result, the next implementation must add a pinned Seelen runtime distribution or deliberately port the upstream WorkerW/media path into a dedicated ThemeStudio wallpaper WebView2.

The user has now selected Seelen Dock and toolbar as the taskbar provider. The activation payload should enable `@seelen/weg` and `@seelen/fancy-toolbar`, preserve the user’s Dock/toolbar geometry settings, keep `@seelen/window-manager` disabled, and leave Start/launcher and unrelated widgets untouched. It should also enable `@seelen/wallpaper-manager` plus selected themes/icon packs. The user-selected wallpaper composition remains Seelen image/video playback with Windhawk parallax algorithms in the same media layer, and both stock wallpaper renderers must not be started.

Evidence is persisted in [10_discovery.md](10_discovery.md) and [20_sources.md](20_sources.md). The most relevant local checkpoints are [20_sources.md:6-27](20_sources.md:6), [20_sources.md:51-68](20_sources.md:51), [20_sources.md:70-102](20_sources.md:70), [20_sources.md:104-161](20_sources.md:104), [20_sources.md:192-270](20_sources.md:192), and [20_sources.md:430-466](20_sources.md:430).

## Exact activation paths

The recovered native workbench’s apply function is the correct shape for a deterministic composition. It reads current Seelen settings with `SeelenCommand.StateGetSettings`, spreads the complete current object to preserve unrelated fields, sets `activeThemes` and `activeIconPacks` with mandatory base entries, writes with `SeelenCommand.StateWriteSettings`, and then updates the in-memory settings object. See the recovered `themeWorkbench/infra/index.tsx:25-68` checkpoint at [20_sources.md:6-27](20_sources.md:6).

The serialized settings fields are camelCase because the Rust `Settings` struct uses `rename_all = "camelCase"`. The relevant JSON paths are:

```text
activeThemes: string[]
activeIconPacks: string[]
byWidget["@seelen/wallpaper-manager"].enabled
byWidget["@seelen/wallpaper-manager"].defaultCollection
byWidget["@seelen/weg"].enabled
byWidget["@seelen/fancy-toolbar"].enabled
byWidget["@seelen/window-manager"].enabled
byTheme[themeId]
byWallpaper[wallpaperId]
wallpaperCollections[] = { id, name, wallpapers[], hidden }
monitorsV3[monitorId].wallpaperCollection
monitorsV3[monitorId].byWorkspace[workspaceId].wallpaperCollection
```

The base entries are always reinserted by Seelen sanitization: `@default/theme` and `@system/icon-pack`. Do not replace the whole JSON with a small recipe object. `Settings::save` also writes `<stem>_shortcuts.json` and `<stem>_by_app.yml`; a safe writer must preserve them and unknown fields. With Tauri identifier `com.seelen.seelen-ui`, the normal unpackaged/NSIS path is `%APPDATA%\com.seelen.seelen-ui\settings.json`; themes/plugins/widgets/wallpapers/iconpacks are sibling directories under that root. MSIX may redirect/virtualize the location, so query the live `app_data_dir()` result rather than hard-code it ([20_sources.md:104-161](20_sources.md:104), [20_sources.md:579-610](20_sources.md:579)).

The resource-first path is the original supported CLI:

```text
slu resource load theme <absolute-theme-folder-or-file>
slu resource load icon-pack <absolute-icon-pack-folder-or-file>
slu resource load wallpaper <absolute-image-video-file-or-folder>
slu resource unload theme <same-path>
```

Official docs confirm that `load` registers the resource immediately in a running Seelen instance and that loaded resources are session-only unless permanently installed through Seelen settings ([Seelen Resource Guidelines](https://seelen.io/docs/resource-guidelines), [20_sources.md:290-306](20_sources.md:290)). Upstream `src/background/resources/cli.rs` then calls `ResourceManager::load`, stores the manual path, emits the kind-changed event, and invokes `enable_resource` for a returned ID ([20_sources.md:85-102](20_sources.md:85)).

The exact `enable_resource` behavior matters:

| Kind | Upstream effect | Safe ThemeStudio scope |
|---|---|---|
| Theme | Appends the theme ID; if it has shared styles, resets the active list to `@default/theme` first | Set selected theme IDs only; preserve all other settings |
| IconPack | Appends the icon-pack ID | Set selected icon-pack IDs only |
| Widget | Calls `set_widget_enabled(widgetId, true)` | Enable `@seelen/weg`, `@seelen/fancy-toolbar`, and `@seelen/wallpaper-manager`; keep window manager/launcher/other widgets unchanged |
| Wallpaper | Creates a hidden one-wallpaper collection and sets `byWidget.wall.defaultCollection` | Use only for the selected desktop media resource, then read back collection/ID |
| Plugin | Loads/registers the plugin and emits plugin events | Do not enable unless explicitly selected as a widget/plugin feature |

The CLI `unload` operation removes the path from the in-memory resource registry; it does not restore a previous settings snapshot. Therefore unloading alone is not a rollback of an activation. A rollback must restore settings fields and then unload/remove the resource only after checking that the current resource path/ID still matches the activation record.

The concrete Dock/toolbar workflow is:

1. Start the matching Seelen engine and service, then read the live settings/resource snapshot. Built-in `@seelen/weg` and `@seelen/fancy-toolbar` are loaded from Seelen’s bundled resources at startup; do not try to import them as third-party paths.
2. For user-selected resources, call `slu resource load theme <path>`, `slu resource load icon-pack <path>`, and `slu resource load wallpaper <path>` while the main Seelen instance is running. Record the returned/readback IDs and exact paths.
3. Through the Seelen settings bridge (or a helper implementing the same read-modify-write semantics), set `activeThemes` and `activeIconPacks`, set `byWidget["@seelen/weg"].enabled = true`, set `byWidget["@seelen/fancy-toolbar"].enabled = true`, set `byWidget["@seelen/wallpaper-manager"].enabled = true` for the chosen wallpaper provider, and set `byWidget["@seelen/window-manager"].enabled = false`. Preserve `SeelenWegSettings.mode`, `position`, `size`, margins, paddings, visibility, shortcuts, and every unrelated field.
4. Leave Start/launcher and all other `byWidget` entries unchanged. Do not infer that a theme or icon pack should enable another widget.
5. Write settings, wait for `StateSettingsChanged`/resource events, then verify the Dock and toolbar windows/deployments separately from the settings flags. `slu wallpaper next`/`prev` are available for the original wallpaper manager after it is running.

The readback command set is already declared in Seelen’s generated command contract: `StateGetSettings`, `StateWriteSettings`, `StateGetThemes`, `StateGetIconPacks`, `StateGetWallpapers`, and `StateGetWidgets`/`StateGetPlugins`. `StateGetSettings` is the authoritative source for the Dock/toolbar/window-manager flags; the resource getters provide IDs plus metadata paths for provenance and rollback.

For a newly initialized profile, Seelen’s typed defaults are already `@seelen/weg.enabled = true`, `@seelen/fancy-toolbar.enabled = true`, `@seelen/window-manager.enabled = false`, and `@seelen/wallpaper-manager.enabled = true`; there is no default wallpaper collection. If “only Dock/toolbar” means no wallpaper process during the initial profile stage, explicitly set `@seelen/wallpaper-manager.enabled = false` before writing that new profile, then enable it in the separate wallpaper transaction. For the user’s final selected composition, set wallpaper manager true and point `defaultCollection` to the selected collection. Never apply this new-profile template over an existing profile: read the live settings first and patch only the selected flags.

Conceptual new-profile flag shape (the complete Seelen `Settings` object still comes from `Settings::default`/`Settings::load`; this snippet was not written):

```json
{
  "activeThemes": ["@default/theme"],
  "activeIconPacks": ["@system/icon-pack"],
  "byWidget": {
    "@seelen/weg": { "enabled": true },
    "@seelen/fancy-toolbar": { "enabled": true },
    "@seelen/window-manager": { "enabled": false },
    "@seelen/wallpaper-manager": { "enabled": false }
  },
  "wallpaperCollections": []
}
```

## Individual components with Dock/toolbar selected

The typed `SettingsByWidget` object maps `@seelen/wallpaper-manager` to `byWidget.wall`, while `@seelen/weg`, `@seelen/fancy-toolbar`, and `@seelen/window-manager` map to separate fields. `set_enabled` changes only the selected ID. The widget manager removes disabled deployments and creates deployments only for enabled resources ([20_sources.md:121-161](20_sources.md:121), [20_sources.md:192-204](20_sources.md:192)).

For the new policy, the activation payload should explicitly set only the provider flags and leave all geometry/appearance fields untouched unless the user has selected values:

```json
{
  "byWidget": {
    "@seelen/weg": { "enabled": true, "...preserve existing fields": true },
    "@seelen/fancy-toolbar": { "enabled": true, "...preserve existing fields": true },
    "@seelen/window-manager": { "enabled": false, "...preserve existing fields": true }
  }
}
```

The pseudo-JSON above means a read-modify-write operation; do not write the placeholder key. Seelen defaults are `@seelen/weg.enabled = true`, `@seelen/fancy-toolbar.enabled = true`, and `@seelen/window-manager.enabled = false`; Dock mode, position, size, padding, margin, visibility, and shortcut overrides remain the existing values ([20_sources.md:192-204](20_sources.md:192)). The old recovered `feature-policy.json` says `taskbar: awaiting_user`, but the parent task’s new user instruction supersedes that stale decision; update the decision record before applying.

Selected themes and icon packs do not themselves start Dock/toolbar processes; the widget flags and running Seelen engine do. The status report should distinguish “theme ID active,” “Dock/toolbar flags enabled,” and “Dock/toolbar windows running.” The window manager must remain disabled, and no Start/launcher or other desktop widget should be auto-enabled.

## Wallpaper implementation choices

### Preferred: let original Seelen own the desktop wallpaper window

Build and distribute a pinned Seelen runtime, start its normal background process/service, import/load the selected wallpaper, and enable `@seelen/wallpaper-manager`. Seelen’s own widget manager will create the wallpaper WebView, run the original media components, attach to WorkerW, handle monitor geometry, and process pause/mute/parallax state. The upstream wallpaper widget calls `SetAsWallpaper` before ready and uses monitor-relative rectangles; it is the most faithful path to the original implementation ([20_sources.md:206-240](20_sources.md:206)).

This path needs ThemeStudio-to-Seelen control rather than a second renderer. The supported command surface is `slu resource load/unload`; deterministic composition still needs either the existing Seelen-side Tauri `StateGetSettings`/`StateWriteSettings` bridge or a helper that uses the same settings semantics. A plain external `slu` invocation cannot set an arbitrary active-theme list by itself.

### Alternative: dedicated ThemeStudio WebView2 wallpaper host

If shipping the full Seelen engine is intentionally avoided, add a separate borderless WebView2 child window for wallpaper and port the upstream WorkerW attachment into the existing C# host. The exact native sequence is available in Seelen’s `src/background/widgets/wallpaper_manager/mod.rs` and `handlers.rs`: detect existing WorkerW first, send Explorer `0x052C` only when absent, clear `WS_EX_APPWINDOW` and `WS_EX_WINDOWEDGE`, add `WS_CHILDWINDOW`, remove `WS_CLIPSIBLINGS`, call `SetParent`, and size the child to the virtual screen. Do not blindly send `0x052C` on every remount: upstream documents that doing so can destroy/recreate WorkerW and destroy the already-parented WebView ([20_sources.md:206-226](20_sources.md:206), [Seelen WorkerW source](https://github.com/eythaann/Seelen-UI/blob/faaf24498e2040b613e6f68c405bc5047cd0df97/src/background/widgets/wallpaper_manager/mod.rs)).

The existing Seelen `Wallpaper.svelte`, `ImageWallpaper.svelte`, `VideoWallpaper.svelte`, and `ParallaxLayer.svelte` can remain the media layer. ThemeStudio’s `ParallaxPreview.svelte` already passes `sourceOverride` URLs to those components, avoiding Tauri-only `convertFileSrc`; the same seam can feed a real wallpaper WebView. A WebView2 virtual-host folder mapping can expose a controlled media directory, but Microsoft warns that virtual-host media may load slowly. Use a dedicated writable WebView2 user-data folder and benchmark video before shipping ([20_sources.md:242-270](20_sources.md:242), [WebView2 local content](https://learn.microsoft.com/en-us/microsoft-edge/webview2/reference/winrt/microsoft_web_webview2_core/corewebview2)).

This alternative is a new desktop renderer owned by ThemeStudio, so it must implement the missing native lifecycle: media source selection, monitor geometry, WorkerW recreation after Explorer changes, pause-on-coverage/performance mode, per-monitor mute, and rollback on close. The current `ThemeStudio.cs` has only one UI WebView2 and no WorkerW code; this is confirmed missing work, not an already available path.

## Status, provenance, and rollback contract

Before any future activation, capture a transaction record containing:

1. Seelen engine executable paths, file versions, source commit, and WebView2 runtime mode/version.
2. SHA-256 and exact paths of the selected resource files/folders.
3. A copy/hash of Seelen `settings.json`, `<stem>_shortcuts.json`, and `<stem>_by_app.yml` if present.
4. Current `activeThemes`, `activeIconPacks`, `byWidget` entries, `byTheme`, `byWallpaper`, `wallpaperCollections`, and monitor/workspace collection assignments.
5. The resource metadata readback: ID, kind, `metadata.internal.path`, `bundled`, `written_at`, and optional `remote` provenance.

After activation, verify all of the following before reporting success:

- Resource list contains every selected theme/icon/wallpaper ID and its metadata path.
- `activeThemes` contains `@default/theme` plus the selected themes, without duplicate IDs.
- `activeIconPacks` contains `@system/icon-pack` plus the selected packs, without duplicate IDs.
- `byWidget["@seelen/wallpaper-manager"].enabled` is true only when wallpaper provider `seelen`/`both` is selected.
- `wallpaperCollections` contains the selected wallpaper ID and `byWidget.wall.defaultCollection` points to the intended collection; monitor/workspace overrides are checked separately.
- Seelen settings-change/resource-change events are observed and the selected wallpaper widget is deployed.
- If using the original engine, the Seelen app named pipe `\\.\pipe\seelen-ui-<session>` and service pipe `\\.\pipe\seelen-ui-service-<session>` respond to a liveness probe. The pipe names and 3-second timeout are defined in `libs/slu-ipc/src/app.rs`, `service.rs`, and `common.rs`; they are not currently exposed by ThemeStudio.
- If using the ThemeStudio host path, the wallpaper HWND has WorkerW as parent, its style/extended style is correct, its virtual-screen rectangle is correct, and image/video load/play/error events are recorded. Native desktop verification is currently false in policy.

Rollback should restore the pre-activation settings snapshot through Seelen’s settings API or the same lock-aware save semantics, then verify the exact old IDs and widget flags. Only after settings restoration should the transaction unload/delete resources whose path and ID match the transaction. If a resource is bundled, do not delete it. If a resource path or hash no longer matches, preserve it and report a manual-intervention condition. Because CLI unload does not restore settings, “unload succeeded” alone must never be reported as “rollback succeeded.”

## Engine/runtime distribution and missing dependencies

The vendored Seelen package is version `2.8.6` and defines three binaries: `seelen-ui`, `slu`, and `slu-service`. The source package exposes `build:ui`, `build:lib`, and `dev` (`cargo build && tauri dev`), and its Tauri config bundles static resources and the `seelen-ui.uri` deep-link scheme. The recovered ThemeStudio release does not contain any of those binaries or their static runtime resources ([20_sources.md:430-466](20_sources.md:430)).

The exact source/runtime pairing is now clear. The recovered vendor snapshot is pinned to upstream commit `faaf24498e2040b613e6f68c405bc5047cd0df97`; the official release listing identifies that commit as a signed Nightly build, while stable Seelen UI v2.8.6 is a different signed commit `079c385`. Therefore:

- To preserve the recovered source, use the official Nightly artifact whose release metadata and asset hashes identify commit `faaf244`, or build exactly from `faaf244`. The Nightly workflow generates timestamped versions such as `2.8.6-nightly.<timestamp>`, x64/ARM64 binaries, NSIS/MSIX bundles, `static/**/*`, `SHA256SUMS`, and `SHA256SUMS.sig`. The `nightly` tag moves, so record the commit and hashes.
- To use the stable official release, use `Seelen UI_2.8.6_x64-setup.exe` or `Seelen UI_2.8.6_x64-setup-fixed.exe` (and the matching ARM64 file) together with source commit `079c385`, then treat the stable source as a separate vendor revision. Do not pair stable 079c385 binaries with the recovered faaf244 source.

The official release workflow builds `x86_64-pc-windows-msvc` and `aarch64-pc-windows-msvc`, emits signed `.exe`/`.dll` plus `static` resources and checksums, and bundles both normal and fixed-runtime installers ([20_sources.md:500-579](20_sources.md:500)). The fixed package is the safer reproducibility choice for this task; it includes the WebView2 runtime selected by Seelen’s `SetFixedRuntime.ps1` pipeline. ThemeStudio’s own WebView2 SDK/runtime packaging is separate, so record both runtime versions and avoid silently mixing a Seelen Tauri runtime with ThemeStudio’s host runtime.

The stable x64 MSIX was downloaded and expanded read-only as a payload inspection substitute for the opaque NSIS setup executable. It contains `seelen-ui.exe` (54,952,232 bytes), `slu.exe` (8,181,760 bytes), `slu-service.exe` (3,288,872 bytes), `sluhk.dll`, the entire `static/` tree, `AppxManifest.xml`, `AppxBlockMap.xml`, `AppxSignature.p7x`, `SHA256SUMS`, and `SHA256SUMS.sig`. Package SHA-256 is `5A21FA2D96B3021F3ED33D210ED7B8FEA50FD7C5189D0D65D3E6B95352F08B41`; the package signature verifies against the Microsoft Marketplace CA certificate. The fixed NSIS installer itself is also downloaded and verified: SHA-256 `E9CBE8BC836AA20943DE7D1FD148CBC8A1F2085C4314AC2953F9C509B4E3F200`, Authenticode `Valid`, SignPath Foundation signer. Payload details are in [20_sources.md:589-627](20_sources.md:589).
The embedded `SHA256SUMS.sig` is retained for later verification with the project’s signing key; this pass records the file and package/Authenticode signatures but does not claim independent rsign verification without the corresponding public-key tool/material.

The exact v2.8.6 command context is safe to reason about without launching it: `slu.exe resource load/unload ...` normalizes relative paths, sends an `AppMessage::Cli` over the Seelen named pipe, and exits 0 only after the IPC send succeeds; if Seelen is not running, it prints the error and exits 1. `slu-service.exe` is different: its startup path probes the app pipe and launches Seelen UI when absent, so it must not be invoked for a read-only check. The stable source archive and exact control flow are persisted under [source-079c385](source-079c385/Seelen-UI-079c38584d48ef02e800d6f596bbef97bd00e327) and summarized at [20_sources.md:632-685](20_sources.md:632).

Materially missing dependencies for a real activation are:

- A built and legally distributable Seelen engine bundle (`seelen-ui.exe`, `slu.exe`, `slu-service.exe`, static resources, and license/AGPL notices).
- A source/runtime pairing decision: recovered `faaf244` + matching Nightly artifact, or stable `079c385` + stable v2.8.6 installer; the two cannot be mixed.
- A controlled start/stop/liveness contract for the Seelen main instance and service; ThemeStudio’s current backend bridge cannot substitute for Seelen IPC.
- A Seelen settings/resource adapter that reads the actual Seelen app-data path and preserves split files/unknown settings.
- A Dock/toolbar activation adapter that sets only `byWidget["@seelen/weg"].enabled = true` and `byWidget["@seelen/fancy-toolbar"].enabled = true`, preserves their existing geometry, and verifies `byWidget["@seelen/window-manager"].enabled = false` plus no unintended launcher/widget entries.
- A transaction journal for settings/resource hashes, readback verification, and rollback.
- Native wallpaper verification on the target Windows shell, including WorkerW recreation, multi-monitor/mixed-DPI geometry, Explorer restart behavior, video playback, and pause policy.
- If the full engine is not shipped, a second WebView2 wallpaper host, WorkerW P/Invoke, controlled media URL mapping, and a lifecycle implementation around the reused Seelen media components.

The current evidence supports implementation planning and exact source reuse. It does not support claiming that real desktop wallpaper or any Seelen component is active in the 0.1.1 installer.
