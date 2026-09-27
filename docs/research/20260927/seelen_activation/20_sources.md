# Source checkpoints — Seelen activation

## Local recovered ThemeStudio/Seelen source

**Time**: 2026-09-27, 18:35:00 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\src\ui\react\settings\modules\themeWorkbench\infra\index.tsx:25-68`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: The recovered native workbench already contains the exact settings apply path: read current settings through `StateGetSettings`, preserve unrelated fields, normalize base theme/icon IDs, write through `StateWriteSettings`, and expose only policy-adopted widget settings.

# Relevant extracted content

```tsx
const current = await invoke(SeelenCommand.StateGetSettings, { path: null });
const next = {
  ...current,
  activeThemes: ["@default/theme", ...recipe.seelen.activeThemes.filter((id) => id !== "@default/theme")],
  activeIconPacks: ["@system/icon-pack", ...recipe.seelen.activeIconPacks.filter((id) => id !== "@system/icon-pack")],
  byTheme: recipe.wallpaperParallax ? { ...current.byTheme, [PARALLAX_THEME_ID]: toThemeVariables(recipe.wallpaperParallax) } : current.byTheme,
};
await invoke(SeelenCommand.StateWriteSettings, { settings: next });
```

The same file calls `adoptedSeelenComponents(policy)` and renders `WidgetConfiguration` only for IDs returned by that policy.

---

**Time**: 2026-09-27, 18:35:05 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\src\ui\react\settings\modules\themeWorkbench\domain\model.ts:26-109`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: ThemeStudio recipe format is explicit and bounded: `schemaVersion: 1`, `seelen.activeThemes`, `seelen.activeIconPacks`, optional wallpaper parallax, and Windhawk drafts. Dependency checks verify resource IDs and source hashes before native apply.

# Relevant extracted content

```ts
export interface ThemeRecipe {
  schemaVersion: 1;
  name: string;
  seelen: { activeThemes: string[]; activeIconPacks: string[] };
  windhawk: ModDraft[];
  wallpaperParallax?: ParallaxSettings;
}
```

`parseRecipe` rejects duplicate IDs, oversized recipes, malformed values, and mismatched `wallpaperParallax.enabled` versus `activeThemes`.

---

**Time**: 2026-09-27, 18:35:10 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\src\ui\react\settings\modules\themeWorkbench\domain\adoption.ts:1-13` and `config\feature-policy.json:1-95`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: Current policy selects wallpaper provider `both` with standard image/video through Seelen and parallax algorithms in the shared Seelen media layer; taskbar remains `awaiting_user`, Start/launcher and desktop widgets are outside scope. The policy adapter therefore returns only `@seelen/wallpaper-manager` for the settled wallpaper choice.

# Relevant extracted content

```ts
if (wallpaper.status === "chosen_by_user" && ["seelen", "both"].includes(wallpaper.provider || ""))
  result.push("@seelen/wallpaper-manager");
if (taskbar.status === "chosen_by_user" && taskbar.provider === "seelen")
  result.push("@seelen/weg", "@seelen/fancy-toolbar");
```

Policy fields include `standardImageVideo: "seelen"`, `mouseParallax: "windhawk_algorithms_in_seelen_media_layer"`, `startBothStockRenderers: false`, and `nativeDesktopVerified: false`.

---

**Time**: 2026-09-27, 18:35:15 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\src\background\resources\mod.rs:45-192,247-381`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: Seelen's `ResourceManager` is the authoritative loader/activation implementation. It loads themes, widgets, plugins, wallpapers, and icon packs; loads user resources from dedicated directories; and `enable_resource` mutates only the relevant settings field.

# Relevant extracted content

- Resource directories: bundled/user themes, bundled/user widgets, bundled/user plugins, user wallpapers, user icon packs, and user sound packs (`get_entries_for_type`, lines 247–265).
- `load` accepts a folder, metadata file, `.yaml/.yml/.json/.jsonc`, or `.slu` via `SluResource::load`; direct image/video wallpaper files are copied into `user_wallpapers_path()/date_based_hex_id()` and returned as a generated ID (lines 126–164).
- `enable_resource(Theme, id)` optionally resets shared-style themes to `@default/theme` then appends the theme; `IconPack` appends the ID; `Widget` calls `set_widget_enabled(id, true)`; `Wallpaper` creates a hidden one-wallpaper collection and sets `by_widget.wall.default_collection` (lines 315–379).
- `load` returns `Option<ResourceId>`; system icon pack and deprecated themes produce no activatable ID, so callers must treat `None` as “loaded but no enable action”.

---

**Time**: 2026-09-27, 18:35:20 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\src\background\resources\cli.rs:1-29` and `libs\slu-ipc\src\commands.rs:89-173`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: The supported CLI path is `slu resource load|unload <kind> <path>`; load/unload run in the main Seelen instance, emit the updated resource list, and load calls `enable_resource` after registration. Supported kinds include `theme`, `widget`, `plugin`, `icon-pack`, `wallpaper`, and `sound-pack`.

# Relevant extracted content

```text
slu resource load theme <path>
slu resource load icon-pack <path>
slu resource load wallpaper <file-or-folder>
slu resource unload theme <same-path>
```

`ResourceSubCommand::Load` and `Unload` are `MainInstance`; `Bundle` and `Translate` are direct operations. `ResourceManagerCli` maps each CLI kind to the internal `ResourceKind` enum.

---

**Time**: 2026-09-27, 18:35:25 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\libs\core\src\state\settings\mod.rs:363-414,455-629,631-715,718-740`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: The persisted settings schema is `settings.json` with camelCase keys. `Settings::load` also reads sibling `<stem>_shortcuts.json` and `<stem>_by_app.yml`; `Settings::save` writes those split files. Sanitize always prepends the base theme and system icon pack, deduplicates, and reconciles widget settings.

# Relevant extracted content

- `SeelenWallSettings` has `enabled`, `interval`, `randomize`, `default_collection`, `multimonitor_behaviour`, `use_accent_color`, and `coverage_pause_threshold`; defaults are enabled, 300 seconds, per-monitor, and threshold 0.8.
- `Settings` fields include `active_themes`, `active_icon_packs`, `by_widget`, `by_theme`, `by_wallpaper`, `wallpaper_collections`, and `monitors_v3`.
- Defaults: `active_themes = ["@default/theme"]`, `active_icon_packs = ["@system/icon-pack"]`.
- `sanitize()` inserts `@default/theme` and `@system/icon-pack` at index 0, then deduplicates.
- `Settings::load(path)` opens the JSON with a shared lock, migrates wallpaper data, sanitizes, and returns settings; `save(path)` writes the main JSON without split fields, then writes shortcuts and by-app siblings.
- `is_widget_enabled`/`set_widget_enabled` delegate to `by_widget`.

---

**Time**: 2026-09-27, 18:35:30 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\libs\core\src\state\settings\by_widget.rs:17-95`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: Widget activation is independent and field-addressable. Built-in IDs map to typed settings, while third-party IDs live in `byWidget.others`; `set_enabled` changes only the selected widget. Seelen system widgets cannot be disabled during sanitize.

# Relevant extracted content

```text
byWidget["@seelen/weg"]                 -> weg.enabled
byWidget["@seelen/fancy-toolbar"]       -> fancy_toolbar.enabled
byWidget["@seelen/window-manager"]      -> wm.enabled
byWidget["@seelen/wallpaper-manager"]   -> wall.enabled
byWidget.others[widgetId].enabled        -> external widget
```

`is_enabled` defaults absent `@seelen/*` widgets to enabled; external widgets default disabled until an explicit entry is written.

---

**Time**: 2026-09-27, 18:35:35 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\src\background\state\application\settings.rs:29-41,131-135` and `src\background\utils\constants.rs:41-75,99-145`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: The live settings path is resolved by Tauri's app-data directory, not by ThemeStudio's `%LOCALAPPDATA%\ThemeStudio`. In the recovered Seelen source the file is `<Seelen app data>\settings.json`; user resources are sibling `themes`, `plugins`, `widgets`, `wallpapers`, and `iconpacks` directories, with generated system icons in the app cache.

# Relevant extracted content

```text
settings       = data_dir\settings.json
iconpacks      = data_dir\iconpacks
user_themes    = data_dir\themes
user_plugins   = data_dir\plugins
widgets        = data_dir\widgets
wallpapers     = data_dir\wallpapers
system_icons   = cache_dir\gen-icon-pack
```

`AppSettings::read_settings()` loads that path; `write_settings()` calls `Settings::save(SEELEN_COMMON.settings_path())` and then emits settings/reconciles widgets/window manager.

---

**Time**: 2026-09-27, 18:35:40 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\libs\core\src\resource\interface.rs:16-148` and `resource\metadata.rs:14-85`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: Resource registration accepts folders with a recognized metadata entrypoint, YAML/JSON files, or `.slu` bundles. The loader stores the exact path, filename, modified time, bundled flag, and optional remote metadata, which provides status/provenance evidence.

# Relevant extracted content

- `SluResource::load_ext` resolves a folder entrypoint, loads, sets `metadata.internal.path`, `filename`, and `written_at`, then sanitizes and validates.
- `.slu` loading checks that the embedded resource kind matches the requested type and stores `metadata.internal.remote`.
- `ResourceMetadata.internal` contains `path`, `filename`, `bundled`, `written_at`, and `remote`.
- `SluResource::save` writes back to the original `.yml/.yaml/.json/.jsonc/.slu` path; `delete` removes the resource path.

---

**Time**: 2026-09-27, 18:35:45 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\src\background\resources\commands.rs:23-123` and `resources\emitters.rs:23-145`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: Readback and rollback status can be based on resource lists and settings events: handlers expose current themes, widgets, plugins, wallpapers, and icon packs; remove only drops non-bundled resources; emitters publish `State*Changed` and reconcile widget deployments after changes.

# Relevant extracted content

- `state_get_themes`, `state_get_icon_packs`, `state_get_wallpapers`, and `state_get_widgets` return `RESOURCES` snapshots.
- `remove_resource(id, kind)` filters by ID and `!metadata.internal.bundled`, deletes the exact path, and emits a kind-changed event.
- `emit_kind_changed` dispatches `StateThemesChanged`, `StateIconPacksChanged`, `StateWallpapersChanged`, or widget/plugin events; widget changes call `WIDGET_MANAGER.reconcile()`.

---

**Time**: 2026-09-27, 18:35:50 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\libs\core\src\state\settings\by_widget.rs:53-85`, `src\background\resources\mod.rs:315-379`, `src\background\widgets\manager.rs:67-119`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: Individual component activation does not require enabling every Seelen provider. Theme/icon activation touches only active ID lists; widget activation touches one `byWidget` entry; widget manager reconciles and creates deployments only for enabled IDs. Therefore taskbar/Dock can remain untouched while wallpaper manager is enabled.

# Relevant extracted content

- `enable_resource(Widget, id)` calls `set_widget_enabled(id, true)` only for that ID.
- `WidgetManager::reconcile()` removes deleted resources, skips disabled IDs, and deploys only enabled resources.
- `adoptedSeelenComponents` in recovered ThemeStudio currently returns wallpaper manager only under the settled policy.

---

**Time**: 2026-09-27, 18:35:55 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\src\background\widgets\wallpaper_manager\mod.rs:23-117` and `handlers.rs:8-41`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: Seelen contains the requested upstream WorkerW desktop-parent implementation. It detects existing WorkerW layouts before sending Explorer's 0x052C spawn message, sets child/window styles, reparents the WebView window to WorkerW, sizes it to the virtual screen, and falls back to absolute positioning if WorkerW cannot be found.

# Relevant extracted content

```text
FindWindowA("Progman")
PostMessageW(progman, 0x052C, WPARAM(0xD), LPARAM(0x1))
FindWindowExA(..., "SHELLDLL_DefView", ...)
FindWindowExA(..., "WorkerW", ...)
SetWindowLongPtrW(hwnd, GWL_STYLE, WS_CHILDWINDOW | ...)
SetWindowLongPtrW(hwnd, GWL_EXSTYLE, remove WS_EX_APPWINDOW/WS_EX_WINDOWEDGE)
SetParent(hwnd, worker_w)
```

`set_as_wallpaper` computes `WindowsApi::virtual_screen_rect()`, uses a relative `0..virtual width/height` rectangle after reparenting, otherwise uses the absolute virtual-screen rectangle, and logs rather than fails if desktop refresh causes WorkerW rebuild.

---

**Time**: 2026-09-27, 18:36:00 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\src\ui\svelte\wallpaper-manager\index.ts:1-35`, `state.svelte.ts:21-185`, `modules\Monitor\Monitor.svelte:111-167`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: The native wallpaper widget invokes `SetAsWallpaper` before the widget is marked ready, subscribes to global mouse position and settings/resource events, computes monitor-relative rectangles, and renders one or two media slots per monitor with parallax and pause/mute policy.

# Relevant extracted content

- `index.ts` calls `Widget.self.init`, `setResizable(false)`, then `invoke(SeelenCommand.SetAsWallpaper)` before mounting the app.
- `state.svelte.ts` reads `byWidget["@seelen/wallpaper-manager"]`, `byWallpaper`, `monitorsV3`, and current virtual-desktop wallpapers; it subscribes to `GlobalMouseMove`, `StateSettingsChanged`, and other state events.
- `Monitor.svelte` uses `position: fixed`, monitor-relative left/top/width/height, optional `scale(monitor.scaleFactor)`, and wraps `Wallpaper` in `ParallaxLayer`.

---

**Time**: 2026-09-27, 18:36:05 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\libs\ui\svelte\components\Wallpaper\Wallpaper.svelte:39-70`, `components\ImageWallpaper.svelte:1-32`, `components\VideoWallpaper.svelte:27-216`, `ParallaxPreview.svelte:1-37`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: Seelen's media layer selects image/video/themed wallpaper by `WallpaperKind`; image and video elements are full-viewport and video includes playback recovery, pause, reload, seek preservation, and stall handling. ThemeStudio's local `ParallaxPreview` already adds a `sourceOverride` escape hatch so browser/WebView2 previews can bypass Tauri `convertFileSrc`.

# Relevant extracted content

- `Wallpaper.svelte` dispatches `ImageWallpaper` for images and `VideoWallpaper` for videos, with overlay and paused-message support.
- Image source normally uses `convertFileSrc(definition.metadata.path + "\\" + definition.filename)`.
- Video source uses the same path conversion and has recovery timers, `load()`/seek restoration, pause/play control, and cleanup on destroy.
- `ParallaxPreview.svelte` passes a synthetic definition and direct `sourceOverride` URL to the same Seelen image/video components; this is the most reusable path for ThemeStudio's existing WebView2 media layer.

---

**Time**: 2026-09-27, 18:36:10 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\src\host\ThemeStudio.cs:1-240`, `src\app\bridge.ts:1-42`, `docs\integration.md`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: Current ThemeStudio host has a single UI WebView2 and a private WebMessage→stdio backend bridge; it does not yet create a WorkerW child window, run Seelen, or expose Seelen IPC. The host already has the primitives needed for a second dedicated wallpaper WebView2, but real desktop playback and native verification remain missing.

# Relevant extracted content

- `StudioWindow` owns one `WebView2`, maps `app.theme-studio.invalid` to `wwwroot`, and uses `CoreWebView2.WebMessageReceived` for whitelisted desktop operations.
- `operations` currently contains icon/cursor/state/recipe operations only; no Seelen settings/resource operation exists.
- `StartBackend()` launches bundled `backend\ThemeStudio.Backend.exe` over redirected stdin/stdout; it does not launch `slu` or a Seelen engine.
- `docs/integration.md` and README explicitly state that Seelen Rust background and Windhawk injection engines are retained as source but not compiled/run in the 0.1.1 release.

---

**Time**: 2026-09-27, 18:36:15 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\docs\source-imports.json`, `vendor\upstream-snapshots\seelen-source.json`, `config\webview2-runtime.json`, `config\webview2-sdk.json`, `tools\fetch-runtime.ps1`, `tools\package.ps1`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: The recovered project pins Seelen source provenance to upstream commit `faaf24498e2040b613e6f68c405bc5047cd0df97`, records archive hashes, and separately pins WebView2 SDK 1.0.4191.47 plus a Microsoft-signed Evergreen Standalone Runtime installer version 1.3.271.7. This does not provide a Seelen runtime binary: a Seelen engine build/distribution is still a required dependency.

# Relevant extracted content

```json
{ "Repository": "eythaann/Seelen-UI", "Commit": "faaf24498e2040b613e6f68c405bc5047cd0df97", "SHA256": "1BA4C8133E73DC5CBDF2FB89025AEBCDAFAF0B61C760AE8F3F6716EEAB21BEDB" }
```

`package.ps1` copies WebView2 DLLs and `WebView2Loader.dll` into the release, compiles the WinForms host, and bundles the Python backend. No Seelen Rust build or `slu.exe`/`seelen-ui.exe` is emitted.

---

## Official upstream web checkpoints

**Time**: 2026-09-27, 18:36:20 +08:00
**Source**: https://seelen.io/docs/resource-guidelines (official Seelen documentation; `turn27view1`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: Official documentation confirms resource kinds and the live CLI workflow. `slu resource load` registers a resource in a running Seelen instance, `unload` reverses the same path, and the session-only nature is explicit; permanent install is through settings.

# Relevant extracted content

> Resource kinds: `Theme`, `Widget`, `Plugin`, `IconPack`, `Wallpaper`.
>
> `slu resource load <kind> <path>` and `slu resource unload <kind> <path>`.
>
> “The resource is registered immediately and available in Seelen UI settings without restarting the app. Seelen UI must be running for this command to work.”
>
> “Loaded resources are registered for the current session. After restarting Seelen UI you will need to load them again, or install them permanently through the settings panel.”

---

**Time**: 2026-09-27, 18:36:25 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/blob/faaf24498e2040b613e6f68c405bc5047cd0df97/src/background/resources/mod.rs (`turn18view0`–`turn18view2`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: The fixed upstream commit confirms the local loader findings: direct image/video wallpaper paths are copied into Seelen's user wallpaper store; user resources are scanned by kind; and `enable_resource` is the implementation behind the marketplace “Enable” action.

# Relevant extracted content

> `ResourceKind::Wallpaper` accepts supported image/video extensions and calls `Wallpaper::create_from_file` under `user_wallpapers_path()`.
>
> `ResourceKind::Theme`, `Widget`, `Plugin`, `Wallpaper`, and `IconPack` map to their respective resource maps; system icon pack has no activatable ID.
>
> `enable_resource` is documented as “the same way the ‘Enable’ button does after installing a resource”.

---

**Time**: 2026-09-27, 18:36:30 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/blob/faaf24498e2040b613e6f68c405bc5047cd0df97/libs/slu-ipc/src/commands.rs (`turn24view0`–`turn24view1`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: The fixed upstream CLI defines `ResourceSubCommand::{Load,Unload,Bundle,Translate}`, maps `ClapResourceKind` to all six resource kinds, and explicitly classifies load/unload as main-instance operations. This is the command contract ThemeStudio should call when a Seelen runtime is present.

# Relevant extracted content

> `Load { kind: ClapResourceKind, path: PathBuf }`
>
> `Unload { kind: ClapResourceKind, path: PathBuf }`
>
> `Load`/`Unload` use `CommandExecutionMode::MainInstance`; `Bundle`/`Translate` are direct.

---

**Time**: 2026-09-27, 18:36:35 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/blob/faaf24498e2040b613e6f68c405bc5047cd0df97/src/background/widgets/wallpaper_manager/mod.rs and `/handlers.rs` (`turn19view0`–`turn17view0`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: The official upstream implementation provides a direct reuse blueprint for a .NET WebView2 host: detect/create WorkerW, remove conflicting top-level styles, `SetParent` the wallpaper WebView, size to the virtual screen, and fall back to absolute placement with a desktop refresh warning path.

# Relevant extracted content

> `FindWindowA("Progman")`, `PostMessageW(..., 0x052C, ...)`, `FindWindowExA(..., "SHELLDLL_DefView", ...)`, and `FindWindowExA(..., "WorkerW", ...)`.
>
> `SetWindowLongPtrW` applies `WS_CHILDWINDOW`, removes `WS_CLIPSIBLINGS`, `WS_EX_APPWINDOW`, and `WS_EX_WINDOWEDGE`, then `SetParent(hwnd, worker_w)`.
>
> `set_as_wallpaper` sizes to the virtual screen and logs a fallback if the WorkerW hierarchy is unavailable.

---

**Time**: 2026-09-27, 18:36:40 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/releases (`turn26view2`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: Official release history shows Seelen versions are signed and behavior can change between releases; current release page includes v2.8.6, v2.8.5, and v2.8.4. ThemeStudio must pin and report the actual Seelen engine version/commit used for activation and wallpaper testing.

# Relevant extracted content

> v2.8.6 release commit `079c385` is shown as signed/verified.
>
> v2.8.4 release commit `7870b82` is shown as signed/verified and includes a media-player seekable progress enhancement.

---

**Time**: 2026-09-27, 18:36:45 +08:00
**Source**: https://seelen.io/resources (`turn26view3`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: The official marketplace distinguishes themes, icon packs, wallpapers, widgets, and plugins and lists a Desktop Media Player widget, confirming that resource kind/ID selection should remain explicit rather than bundling all components into one provider switch.

# Relevant extracted content

> The marketplace lists “Windows 11 Start Icon” as an IconPack, “Acheron Black Hole” and “Hypnotic Eyes” as Wallpapers, and “Desktop Media Player” as a Widget.

---

## Microsoft official WebView2 checkpoints

**Time**: 2026-09-27, 18:36:50 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/reference/winrt/microsoft_web_webview2_core/corewebview2 (`turn10search0`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: WebView2 supports a virtual-host-to-folder mapping for local files, but Microsoft's documentation warns that media files through this mapping can be slow. This is a viable fallback for mapping Seelen media into the existing host, but a dedicated local media scheme or copied WebView2-accessible folder should be benchmarked for video.

# Relevant extracted content

> `SetVirtualHostNameToFolderMapping(hostName, folderPath, accessKind)` maps a local folder to HTTP/HTTPS URLs in the WebView.
>
> “Due to a current implementation limitation, media files accessed using virtual host name can be very slow to load.”
>
> Use the minimal cross-origin access necessary; `Deny`/`DenyCors` are available.

---

**Time**: 2026-09-27, 18:36:55 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2environment.createasync (`turn10search2`) and https://learn.microsoft.com/microsoft-edge/webview2/concepts/distribution (`turn10search5`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: A .NET host can choose the runtime folder with `CoreWebView2Environment.CreateAsync(browserExecutableFolder, userDataFolder, options)`. Microsoft distinguishes Evergreen (automatic updates, recommended for most apps) from Fixed Version (predictable offline/air-gapped behavior); the host must report which mode is used and pin the chosen runtime if reproducibility matters.

# Relevant extracted content

> `browserExecutableFolder` points to a fixed WebView2 runtime folder; null/empty uses an installed runtime.
>
> Fixed Version gives exact API/runtime control but requires shipping and updating the runtime; Evergreen updates automatically.

---

**Time**: 2026-09-27, 18:37:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/webview2 (`turn10search3`) and https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/user-data-folder (`turn10search4`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: Microsoft recommends an explicit writable WebView2 user-data folder for desktop apps and provides runtime availability detection. ThemeStudio already uses `%LOCALAPPDATA%\ThemeStudio\webview`; a second wallpaper WebView must use a separate or coordinated profile path and remain writable.

# Relevant extracted content

> `CoreWebView2Environment.GetAvailableBrowserVersionString()` can detect missing runtime.
>
> `CoreWebView2Environment.CreateAsync(..., userDataFolder: ...)` lets the app choose a writable UDF.
>
> WebView2 stores profile data in an app-specific UDF and the app is responsible for its lifecycle.

---

**Time**: 2026-09-27, 18:37:05 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\src\Cargo.toml:1-35`, `Cargo.toml:1-75`, `src\tauri.conf.json`, `scripts\SetFixedRuntime.ps1`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: The vendored Seelen engine is a real three-binary Rust/Tauri package: `seelen-ui`, `slu`, and `slu-service`, version `2.8.6`, with a `custom-protocol` feature for production builds. Its Tauri bundle is configured for NSIS and the source includes a separate fixed WebView2 runtime setup script; ThemeStudio currently does not execute this build or ship these binaries.

# Relevant extracted content

```text
[package] name = "seelen-ui" version = "2.8.6"
[[bin]] name = "seelen-ui" path = "background/main.rs"
[[bin]] name = "slu" path = "slu/main.rs"
[[bin]] name = "slu-service" path = "service/main.rs"
custom-protocol = ["tauri/custom-protocol"]
```

`src/tauri.conf.json` bundles static resources and uses the `seelen-ui.uri` deep-link scheme. `scripts/SetFixedRuntime.ps1` downloads a versioned WebView2 fixed-runtime CAB and adds `webviewInstallMode.type = fixedRuntime` to the Tauri config.

---

**Time**: 2026-09-27, 18:37:10 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\package.json:scripts`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: The vendored Seelen package exposes `build:ui`, `build:lib`, `dev` (`cargo build && tauri dev`), and `@tauri-apps/cli` scripts. The source confirms a build path exists, but no built Seelen binaries are present in ThemeStudio's release package.

# Relevant extracted content

```json
"build:ui": "tsx scripts/build.ts",
"build:lib": "cd ./libs/core && deno task build && cd ../..",
"dev": "cargo build && tauri dev"
```

---

**Time**: 2026-09-27, 18:37:15 +08:00
**Source**: `E:\desktop\windows\.recovery\source\ThemeStudio-0.1.1\vendor\Seelen-UI\libs\core\src\state\settings\mod.rs:154-220,230-360`
**Method**: extract (read-only local source)
**Confidence**: high
**Insight**: Seelen Dock/toolbar and window manager are separate settings. `SeelenWegSettings.enabled` defaults true, `FancyToolbarSettings.enabled` defaults true, while `WindowManagerSettings.enabled` defaults false. The newly selected taskbar route therefore needs only the first two flags enabled and must preserve/force the window manager flag false unless separately chosen.

# Relevant extracted content

```text
byWidget["@seelen/weg"].enabled            -> SeelenWegSettings.enabled (default true)
byWidget["@seelen/fancy-toolbar"].enabled -> FancyToolbarSettings.enabled (default true)
byWidget["@seelen/window-manager"].enabled -> WindowManagerSettings.enabled (default false)
```

`SeelenWegSettings` also owns Dock/Taskbar mode, position, size, padding, margins, and visibility; these are independent taskbar settings and should be read/preserved unless the user specifies values.

---

**Time**: 2026-09-27, 18:37:20 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/releases (`turn30view0`, `turn31view0`, `turn31view1`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: Official release/source matching is not interchangeable: the recovered local snapshot is upstream commit `faaf244`, which the official release page identifies as the signed Seelen UI Nightly commit; stable v2.8.6 is a different signed commit `079c385`. Use a Nightly artifact matching `faaf244` or build exactly from `faaf244`; do not pair the recovered source with stable v2.8.6 binaries.

# Relevant extracted content

> Release list shows “Seelen UI Nightly” at commit `faaf244` and “Seelen UI v2.8.6” at commit `079c385`.
>
> Stable v2.8.6 notes include Dock/toolbar transitions and high-DPI edge-triggering fixes; these are source changes after the recovered `faaf244` snapshot.
>
> The Nightly page is a pre-release and reports signed commit metadata; its asset list is separate from the stable release.

---

**Time**: 2026-09-27, 18:37:25 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/blob/079c385/.github/workflows/release.yml (`turn35view0`–`turn35view3`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: The official release workflow identifies the exact distributable pieces and target architecture. It builds signed binaries for `x86_64-pc-windows-msvc` and `aarch64-pc-windows-msvc`, uploads `static/**/*`, all `.exe`/`.dll`, `SHA256SUMS`, `SHA256SUMS.sig`, and `seelen_ui.pdb`, then bundles normal and fixed-runtime NSIS installers plus MSIX.

# Relevant extracted content

```text
npx tauri build --ci --verbose --no-bundle --target <target>
target/<target>/release/static/**/*
target/<target>/release/*.exe
target/<target>/release/*.dll
target/<target>/release/SHA256SUMS
target/<target>/release/SHA256SUMS.sig
```

The workflow creates signed-binaries artifacts by target, then bundles `Seelen UI_<version>_<arch>-setup.exe` and `Seelen UI_<version>_<arch>-setup-fixed.exe`; the fixed bundle uses `scripts/SetFixedRuntime.ps1`. The workflow source at `faaf244` has the same pipeline shape and is the relevant build recipe for the recovered snapshot.

---

**Time**: 2026-09-27, 18:37:30 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/blob/faaf24498e2040b613e6f68c405bc5047cd0df97/src/tauri.conf.json (`turn34view0`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: The matching source config bundles static resources, enables the Tauri asset protocol for `$APPDATA`/`$LOCALDATA` and image formats, targets NSIS, and registers the `seelen-ui.uri` deep-link. These runtime resources are part of the engine distribution; copying only `seelen-ui.exe`, `slu.exe`, and `slu-service.exe` is insufficient.

# Relevant extracted content

> `bundle.resources.static = "static"`
>
> Asset protocol scope includes `$APPDATA/**/*`, `$LOCALDATA/**/*`, and image formats.
>
> Bundle target is `nsis`; file association is `.slu`; desktop deep-link scheme is `seelen-ui.uri`.

---

**Time**: 2026-09-27, 18:37:35 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/blob/faaf24498e2040b613e6f68c405bc5047cd0df97/.github/workflows/nightly.yml (`turn36view0`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: The official Nightly workflow is the correct distribution provenance for the recovered `faaf244` source. It force-updates the `nightly` tag, generates a timestamped `2.8.6-nightly.<timestamp>` version, builds x64/ARM64 binaries with `npx tauri build --ci --verbose --no-bundle`, bundles NSIS/MSIX artifacts, and uploads `bundles/**/*` to the Nightly release.

# Relevant extracted content

```text
target: x86_64-pc-windows-msvc | aarch64-pc-windows-msvc
npx tauri build --ci --verbose --no-bundle --target <target>
Seelen UI_${VERSION}_x64-setup.exe
Seelen UI_${VERSION}_arm64-setup.exe
```

The workflow also uploads `static/**/*`, all `.exe`/`.dll`, `SHA256SUMS`, `SHA256SUMS.sig`, and `seelen_ui.pdb` into per-target binary artifacts before bundling. Because the `nightly` tag moves, a consumer must record the release commit and asset hashes; the tag alone is not immutable.

---

**Time**: 2026-09-27, 18:37:40 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/blob/079c385/.github/workflows/release.yml (`turn35view0`–`turn35view3`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: The stable release workflow gives the exact official x64 distribution file names and matching source commit. Stable v2.8.6 commit `079c385` produces normal and fixed-runtime installers named `Seelen UI_2.8.6_x64-setup.exe` and `Seelen UI_2.8.6_x64-setup-fixed.exe` (plus ARM64 variants), and signs the binary/hash artifacts.

# Relevant extracted content

> Stable release workflow builds `x86_64-pc-windows-msvc` and `aarch64-pc-windows-msvc`.
>
> It uploads `target/<target>/release/static/**/*`, `*.exe`, `*.dll`, `SHA256SUMS`, `SHA256SUMS.sig`, and `seelen_ui.pdb`.
>
> The bundle stage creates `Seelen UI_<version>_<arch>-setup.exe` and the fixed-runtime `Seelen UI_<version>_<arch>-setup-fixed.exe`.

Stable v2.8.6 binaries must be paired with source commit `079c385`; they must not be paired with the recovered `faaf244` vendor snapshot.

---

**Time**: 2026-09-27, 18:37:45 +08:00
**Source**: https://docs.rs/tauri/latest/tauri/path/struct.PathResolver.html (`turn37search0`) and https://v2.tauri.app/plugin/file-system/ (`turn37search2`)
**Method**: browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: Tauri’s `app_data_dir()` resolves to `data_dir/<bundle_identifier>`; on Windows `data_dir` is the Roaming AppData folder. With Seelen identifier `com.seelen.seelen-ui`, the settings/resource root for the normal unpackaged/NSIS app is `%APPDATA%\com.seelen.seelen-ui`, while logs/cache use separate local/cache roots. This resolves the prior `<Seelen app data>` ambiguity.

# Relevant extracted content

> Tauri `data_dir` on Windows resolves to `{FOLDERID_RoamingAppData}`.
>
> `app_data_dir()` resolves to `data_dir/<bundle_identifier>`.
>
> Seelen’s `src/tauri.conf.json` identifier is `com.seelen.seelen-ui`.

Thus the normal settings path is `%APPDATA%\com.seelen.seelen-ui\settings.json`; user themes/plugins/widgets/wallpapers/iconpacks are sibling directories under that root. For MSIX, the runtime may be package-redirected/virtualized; use the live `app_data_dir()` result or query the running engine rather than hard-code the unpackaged path.

---

**Time**: 2026-09-27, 18:00:00 +08:00
**Source**: https://api.github.com/repos/eythaann/Seelen-UI/releases/tags/v2.8.6
**Method**: extract (official GitHub Releases API via PowerShell `Invoke-RestMethod`; read-only metadata)
**Confidence**: high
**Insight**: Stable v2.8.6 release metadata identifies immutable asset URLs and sizes. The x64 fixed-runtime installer is `Seelen.UI_2.8.6_x64-setup-fixed.exe` (255,532,712 bytes); the normal x64 installer is `Seelen.UI_2.8.6_x64-setup.exe` (46,541,128 bytes). The release was published 2026-09-18 and is separate from source commit `faaf244`.

# Relevant extracted content

```text
release tag: v2.8.6
published: 2026-09-18T01:23:17Z
stable source commit shown on official release page: 079c385
x64 fixed URL: https://github.com/eythaann/Seelen-UI/releases/download/v2.8.6/Seelen.UI_2.8.6_x64-setup-fixed.exe
x64 fixed size: 255532712 bytes
x64 normal URL: https://github.com/eythaann/Seelen-UI/releases/download/v2.8.6/Seelen.UI_2.8.6_x64-setup.exe
x64 normal size: 46541128 bytes
```

The same release lists x64/ARM64 MSIX and fixed/normal NSIS setup assets plus `latest.json`. Asset URLs and sizes were captured before downloading; downloaded hashes/signatures are recorded in the follow-up checkpoints below.

---

**Time**: 2026-09-27, 18:05:00 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/releases/download/v2.8.6/Seelen.UI_2.8.6_x64-setup-fixed.exe
**Method**: extract (downloaded official release asset with PowerShell `Invoke-WebRequest`; no execution)
**Confidence**: high
**Insight**: The downloaded stable fixed-runtime x64 installer exactly matches the official API metadata size (255,532,712 bytes). Its SHA-256 is `E9CBE8BC836AA20943DE7D1FD148CBC8A1F2085C4314AC2953F9C509B4E3F200`; Windows Authenticode verification is `Valid` with signer `CN=SignPath Foundation, O=SignPath Foundation`.

# Relevant extracted content

```text
local asset: docs/research/20260927/seelen_activation/assets/Seelen.UI_2.8.6_x64-setup-fixed.exe
size: 255532712
sha256: E9CBE8BC836AA20943DE7D1FD148CBC8A1F2085C4314AC2953F9C509B4E3F200
authenticode: Valid; Signature verified.
signer: CN=SignPath Foundation, O=SignPath Foundation, L=Lewes, S=Delaware, C=US
thumbprint: CAFB2E571C130176611DA4E1F9363D45B596264F
```

The installer was only downloaded and inspected; it was not opened, installed, or started.

---

**Time**: 2026-09-27, 18:15:00 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/releases/download/v2.8.6/Seelen.UI_2.8.6.0_x64.Msix
**Method**: extract (downloaded official MSIX asset with PowerShell `Invoke-WebRequest`; expanded as ZIP without installation)
**Confidence**: high
**Insight**: The stable x64 MSIX is an inspectable distributable containing the complete Seelen engine payload. It contains `seelen-ui.exe`, `slu.exe`, `slu-service.exe`, `sluhk.dll`, `static/`, `AppxManifest.xml`, `AppxBlockMap.xml`, `AppxSignature.p7x`, `SHA256SUMS`, and `SHA256SUMS.sig`.

# Relevant extracted content

```text
asset: Seelen.UI_2.8.6.0_x64.Msix
size: 42287368 bytes
sha256: 5A21FA2D96B3021F3ED33D210ED7B8FEA50FD7C5189D0D65D3E6B95352F08B41
package signature: Valid; CN=7E60225C-94CB-4B2E-B17F-0159A11074CB; issuer Microsoft Marketplace CA G 022
```

Extracted root payload:

```text
seelen-ui.exe    54952232 bytes  SHA256 5E03F93B15C24247075722D16EAF0301EB3F5517A9BBAFC7EA5AF30083E7176F
slu.exe           8181760 bytes  SHA256 DE2362D20F73E7A885D0E6E1FC6049510841DB92D6EBB384BB1B2D71905711AF
slu-service.exe   3288872 bytes  SHA256 F55CC6EAD12F5B67B3207795A163D217B1ADA4AC1D0CA206C08E7BE227793E2D
sluhk.dll          204576 bytes  SHA256 A27FB0308BD65B71F4672B909781D6922C3C736B736716A5A156FE1702437BED
```

`seelen-ui.exe`, `slu-service.exe`, and `sluhk.dll` have valid SignPath Authenticode signatures. `slu.exe` is not individually Authenticode-signed in the extracted filesystem, but it is covered by the signed MSIX package (`AppxSignature.p7x`/`AppxBlockMap.xml`). `AppxManifest.xml` declares the three executables as the main app, `slu.exe` CLI alias, and `slu-service.exe` service alias. The package was only downloaded/expanded; no executable was launched.

---

**Time**: 2026-09-27, 18:16:00 +08:00
**Source**: `assets/Seelen.UI_2.8.6_x64-setup-fixed.exe` extraction attempt
**Method**: extract (read-only utility diagnostics; no installer execution)
**Confidence**: high
**Insight**: The fixed NSIS setup executable was not directly unpacked by the available portable `7za`/`7zr` or Innoextract tools; Innoextract correctly reported that it is not an Inno Setup installer. The official x64 MSIX from the same v2.8.6 release was used for payload inspection instead, avoiding installer startup.

# Relevant extracted content

```text
7za/7zr: Cannot open file as archive (NSIS plugin unavailable in extracted console build)
innoextract: Not a supported Inno Setup installer
payload source used: official Seelen.UI_2.8.6.0_x64.Msix
```

---

**Time**: 2026-09-27, 18:07:00 +08:00
**Source**: https://constexpr.org/innoextract/ and https://constexpr.org/innoextract/files/innoextract-1.9/ (`turn38search0`, `turn38search1`)
**Method**: query-search (official innoextract site via `web__run`)
**Confidence**: high
**Insight**: The official innoextract project documents extraction of Inno Setup installers without running setup and provides a Windows binary archive. It is used only as a read-only extraction utility; no Seelen installer process is executed.

# Relevant extracted content

> “innoextract allows to extract such installers without running the actual setup executable under Windows or using Wine.”
>
> Official Windows archive: `innoextract-1.9-windows.zip`.

---

**Time**: 2026-09-27, 18:20:00 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/archive/079c38584d48ef02e800d6f596bbef97bd00e327.zip
**Method**: extract (downloaded official source archive with PowerShell `Invoke-WebRequest`; expanded with `Expand-Archive`; read-only inspection)
**Confidence**: high
**Insight**: The matching stable v2.8.6 source archive is persisted separately from the recovered/vendor source. Archive SHA-256 is `5E3255D79BBF2481EDBB8726D2AB030F2F67FBD701F933D019954DEEDB06765B`. Key CLI/settings/path/WorkerW files are present under `source-079c385/Seelen-UI-079c38584d48ef02e800d6f596bbef97bd00e327`.

# Relevant extracted content

```text
archive: assets/Seelen-UI-079c385-source.zip
archive SHA256: 5E3255D79BBF2481EDBB8726D2AB030F2F67FBD701F933D019954DEEDB06765B
matching source root: source-079c385/Seelen-UI-079c38584d48ef02e800d6f596bbef97bd00e327
```

The stable archive’s `src/Cargo.toml` declares `seelen-ui`, `slu`, and `slu-service` version `2.8.6`; `src/tauri.conf.json` has identifier `com.seelen.seelen-ui`; and the stable `resources/cli.rs`, `libs/slu-ipc/src/commands.rs`, `libs/core/src/state/settings/mod.rs`, `src/background/utils/constants.rs`, and `wallpaper_manager/mod.rs` match the previously inspected recovered vendor files byte-for-byte. Stable `wallpaper_manager/handlers.rs` differs only in the generated-command annotation (`#[tauri::command(async)]`) versus the recovered vendor’s generated-handler implementation.

---

**Time**: 2026-09-27, 18:27:00 +08:00
**Source**: `assets/msix-x64-2/seelen-ui.exe`, `slu.exe`, `slu-service.exe` (Windows `FileVersionInfo`, read-only)
**Method**: extract (read-only PE version metadata; no process launch)
**Confidence**: high
**Insight**: The extracted stable MSIX payload’s three executable files report FileVersion/ProductVersion `2.8.6`, ProductName `Seelen UI`, and Company `Seelen`, confirming that the payload is the stable v2.8.6 engine/CLI/service set.

# Relevant extracted content

```text
seelen-ui.exe    FileVersion=2.8.6 ProductVersion=2.8.6 ProductName=Seelen UI Company=Seelen
slu.exe           FileVersion=2.8.6 ProductVersion=2.8.6 ProductName=Seelen UI Company=Seelen
slu-service.exe   FileVersion=2.8.6 ProductVersion=2.8.6 ProductName=Seelen UI Company=Seelen
```

---

**Time**: 2026-09-27, 18:25:00 +08:00
**Source**: `source-079c385/Seelen-UI-079c38584d48ef02e800d6f596bbef97bd00e327/src/slu/main.rs:13-66`, `src/slu/resources.rs:13-20`, `libs/slu-ipc/src/commands.rs:14-18,134-173`
**Method**: extract (read-only stable source archive)
**Confidence**: high
**Insight**: v2.8.6 `slu.exe` has two execution contexts. `resource load`/`unload` are `MainInstance` commands and only send an IPC message to a running Seelen main instance; `resource bundle`/`translate` are direct commands. `slu.exe` prints errors to stderr and exits 1 on any failure; successful direct/main-instance dispatch returns 0.

# Relevant extracted content

```text
slu resource load theme <path>       -> MainInstance -> AppIpc::send(AppMessage::Cli(...))
slu resource unload icon-pack <path> -> MainInstance -> AppIpc::send(AppMessage::Cli(...))
slu resource bundle theme <path>     -> Direct (no running UI required)
slu resource translate <file>        -> Direct (may write the translation file)
```

The main-instance path normalizes relative `./`, `../`, `.\\`, and `..\\` arguments to absolute paths before IPC. If the Seelen main pipe is unavailable, `AppIpc::send` fails and `slu.exe` exits 1; it does not silently start the engine. `ResourceSubCommand::Load` in the main process loads/registers, emits the resource list, enables the returned ID, and then returns; `Unload` unregisters/emits but does not restore settings.

---

**Time**: 2026-09-27, 18:25:05 +08:00
**Source**: `source-079c385/Seelen-UI-079c38584d48ef02e800d6f596bbef97bd00e327/src/service/main.rs:77-94,123-180`, `src/service/cli/mod.rs`, `src/background/cli/mod.rs:25-107`
**Method**: extract (read-only stable source archive)
**Confidence**: high
**Insight**: `slu-service.exe` is a service host, not a passive CLI helper: on startup it probes the app pipe and calls `launch_seelen_ui()` when the main app is absent, then starts the service/task scheduler. ThemeStudio must not invoke it during a read-only/status check. `seelen-ui.exe`’s legacy console-client path forwards commands to the running instance and exits 0 on successful URI forwarding; command errors exit 1.

# Relevant extracted content

- `slu-service.exe` calls `AppIpc::can_stablish_connection()`; when false it waits for the shell and launches Seelen UI (`launch_seelen_ui()`).
- `slu-service.exe` exits 1 for logger/setup/task-scheduler failures and exits with the service exit code after cleanup.
- `seelen-ui.exe` marks the legacy CLI as deprecated and directs users to `slu`; its `--uri` path sends `AppMessage::OpenUri`, then exits 0 on success or 1 on connection failure.

---

**Time**: 2026-09-27, 18:28:00 +08:00
**Source**: Codex workspace dependency inventory (`mcp__codex_app__load_workspace_dependencies`)
**Method**: extract (bundled dependency inventory; read-only)
**Confidence**: high
**Insight**: Bundled workspace runtimes are available, but no bundled 7-Zip/Inno extraction tool was listed. The extraction utilities used here are retained under the owned `assets` folder.

# Relevant extracted content

```text
bundled Python: C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-923-495-0_26.923.495.0_x64__3k8sg7r9htsxt\dependencies\python\python.exe
bundled Node:   C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-923-495-0_26.923.495.0_x64__3k8sg7r9htsxt\dependencies\node\bin\node.exe
read-only 7-Zip extra used: assets/7zextra/x64/7za.exe
read-only Inno extractor used: assets/innoextract/innoextract.exe
```

---
