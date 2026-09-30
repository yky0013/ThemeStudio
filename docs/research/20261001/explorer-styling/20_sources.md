# Source checkpoints

## Upstream GitHub guide (browser-rendered)

**Time**: 2026-10-01, 00:38:00 +08:00
**Source**: https://github.com/ramensoftware/windows-11-file-explorer-styling-guide
**Method**: browser-rendered (via `mcp__cua_repl` in Codex In-app Browser)
**Confidence**: high
**Insight**: The live upstream README describes a collection of styling customizations for Windows 11 and says it is intended for the Windows 11 File Explorer Styler Windhawk mod. The table of contents and rendered sections expose separate controls for tabs, navigation bar, command bar, details view, Home, and Gallery, plus an “Image as color” technique.

# Relevant extracted content

> “This is a collection of commonly requested file explorer styling customizations for Windows 11. It is intended to be used with the Windows 11 File Explorer Styler Windhawk mod.”

> “After installing the mod, open its Settings tab and adjust the styles according to your preferences.”

> “Details view background” target: `Grid#DetailsViewControlRootGrid`.

> “Navigation bar background” target: `Grid#NavigationBarControlGrid`; “Command bar background” targets include `FileExplorerExtensions.CommandBarControl_Wave1 > Grid, Grid#CommandBarControlRootGrid` and `CommandBar#FileExplorerCommandBar`.

> “The background can also be an image” with `Fill:=<ImageBrush Stretch="UniformToFill" ImageSource="<image>" />`; replace `<image>` with an image, URL, or local file path.

> The rendered repository page showed branch `main`, latest commit `fe8f72c` (Sep 27, 2026, GMT+8) at retrieval time. GitHub API confirmation was attempted but returned HTTP 403 rate limit, so the short commit identifier is recorded as page-observed metadata rather than API-verified.

---

## Microsoft DWM API availability cross-check

**Time**: 2026-10-01, 00:44:10 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute
**Method**: extract (PowerShell `Invoke-WebRequest` through `http://127.0.0.1:7890`, then local line extract)
**Confidence**: high
**Insight**: The pinned source hooks `DwmSetWindowAttribute` for `DWMWA_SYSTEMBACKDROP_TYPE`; Microsoft documents that attribute as supported starting with Windows 11 Build 22621. This gives a concrete floor for the source's Acrylic/Mica/Mica Alt window-backdrop path, while the README's broad compatibility wording remains simply “Windows 11.”

# Relevant extracted content

Source was saved transiently as `C:\Users\yky\AppData\Local\Temp\dwmwindowattribute-20261001.html`.

> Microsoft page entry for `DWMWA_SYSTEMBACKDROP_TYPE`: “This value is supported starting with Windows 11 Build 22621.”

> Microsoft page entries for `DWMWA_USE_HOSTBACKDROPBRUSH`, immersive dark mode, corner preference, and border/caption/text attributes state Windows 11 Build 22000; the source's system-backdrop hook specifically uses the Build 22621-gated attribute.

---

## Upstream README raw text (line-addressable extract)

**Time**: 2026-10-01, 00:40:00 +08:00
**Source**: https://raw.githubusercontent.com/ramensoftware/windows-11-file-explorer-styling-guide/main/README.md
**Method**: extract (PowerShell `Invoke-WebRequest` through `http://127.0.0.1:7890`, then local line extract)
**Confidence**: high
**Insight**: The raw README confirms exact line-addressable wording and the target split: Explorer frame height covers tabs/address/command bars; details view and thumbnail have separate XAML targets; Home and Gallery are separate targets. The guide offers image brush syntax but does not claim a native file-list API or wallpaper integration beyond setting an XAML brush value.

# Relevant extracted content

Source was saved transiently as `C:\Users\yky\AppData\Local\Temp\explorer-styling-readme-20261001.md` for line-addressable inspection. Relevant lines:

> Lines 47-62: Introduction identifies Windows 11, the Windhawk mod, installation via the mod settings, and links to other Windhawk guides.

> Lines 109-113: Explorer frame container includes tabs, address bar, and command bar; height is adjustable in mod settings.

> Lines 183-209: Navigation Bar and Command Bar have separate targets; command bar targets are `FileExplorerExtensions.CommandBarControl_Wave1 > Grid, Grid#CommandBarControlRootGrid` and `CommandBar#FileExplorerCommandBar`.

> Lines 211-233: Details view background target is `Grid#DetailsViewControlRootGrid`; thumbnail background target is `StackPanel#DetailsViewThumbnail`.

> Lines 235-260: Home page target is `Grid#HomeViewRootGrid`; Gallery targets are `FileExplorerExtensions.GalleryViewControl#GalleryViewControl > Grid` and its `Grid#GalleryRootGrid` child.

> Lines 480-488: Image background is expressed as `Fill:=<ImageBrush Stretch="UniformToFill" ImageSource="<image>" />`; `<image>` may be an image, URL, or local file path.

---

## Pinned ThemeStudio source

**Time**: 2026-10-01, 00:41:50 +08:00
**Source**: `E:\desktop\windows\ThemeStudio-0.6.0\vendor\windhawk-mods\mods\windows-11-file-explorer-styler.wh.cpp` (SHA-256 `2F14AF7887F0DD6E767724B02E515BD46D6AF019E9B7068C0F4E5E8A72C69C37`)
**Method**: extract (PowerShell `rg`/line read; read-only)
**Confidence**: high
**Insight**: The pinned mod is Windhawk mod version 1.6, x86-64, injected into `explorer.exe`; it styles XAML/WinUI controls through XAML diagnostics. It exposes built-in themes and translucent background effects, including a frame-only versus entire-window choice, but the source has no explicit minimum Windows build check.

# Relevant extracted content

> Lines 2-12: `@id windows-11-file-explorer-styler`, `@version 1.6`, `@include explorer.exe`, `@architecture x86-64`.

> Lines 111-125: Settings support control styles/resource variables; UWPSpy should target `explorer.exe` with the WinUI 3 target framework; the README guide is the collection of requested customizations.

> Lines 164-181: Styles use `Style=Value` or XAML `Style:=...`; the built-in `WindhawkBlur` brush supports blur/tint properties and fallback behavior when battery saver/transparency settings disable blur.

> Lines 314-330: The mod uses XAML diagnostics; only one diagnostics consumer can be active at a time. `Alert`, `Block`, and `Allow` determine conflicts with programs such as ExplorerBlurMica.

> Lines 344-389: Settings include themes, `backgroundTranslucentEffect` options (`default`, `acrylic`, `mica`, `micaAlt`, `none`), and a region option: frame only (default) or entire window; entire-window application is only supported in dark mode.

> Lines 412-427: `explorerFrameContainerHeight` controls the container including tabs, address bar, and command bar; diagnostics consumer handling may break the mod or another consumer.

---

## Windhawk landing page metadata check

**Time**: 2026-10-01, 00:42:30 +08:00
**Source**: https://windhawk.net/mods/windows-11-file-explorer-styler
**Method**: extract (PowerShell `Invoke-WebRequest` through `http://127.0.0.1:7890`; page metadata)
**Confidence**: medium
**Insight**: The page metadata repeats the mod name and description but does not expose a machine-readable Windows build requirement in the fetched HTML. Treat the GitHub guide's Windows 11 wording and the pinned source's `explorer.exe`/WinUI 3 evidence as the authoritative compatibility boundary.

# Relevant extracted content

> `<meta property="og:title" content="Windows 11 File Explorer Styler - Windhawk" />`

> `<meta property="og:description" content="Customize the File Explorer with themes contributed by others or create your own customizations" />`

> The page loads its content through JavaScript; no explicit `23H2`, `24H2`, or minimum-build declaration was present in the fetched HTML.

---

## Pinned source follow-up: scope, native-list boundary, and image loading

**Time**: 2026-10-01, 00:47:00 +08:00
**Source**: `E:\desktop\windows\ThemeStudio-0.6.0\vendor\windhawk-mods\mods\windows-11-file-explorer-styler.wh.cpp` (same SHA-256 as above)
**Method**: extract (PowerShell `rg`/line read; read-only)
**Confidence**: high
**Insight**: The source's window-level backdrop path is separate from XAML control styling: DWM hooks classify `CabinetWClass` as File Explorer and set system backdrop attributes, while XAML styles target named WinUI controls. The source contains no `SysListView32`, shell-view, DirectUI, or native file-list hook/target; therefore a “file-list wallpaper” claim must be limited to the documented `Grid#DetailsViewControlRootGrid` XAML container unless independently verified on the target Windows build.

# Relevant extracted content

> Lines 8377-8398: `GetTargetWindowType` recognizes `CabinetWClass` as `FileExplorer` and `XamlExplorerHostIslandWindow_WASDK` only for the desktop context menu; other window classes are ignored.

> Lines 8410-8455: `DwmSetWindowAttribute_Hook` maps the setting to `DWMSBT_TRANSIENTWINDOW` (Acrylic), `DWMSBT_MAINWINDOW` (Mica), `DWMSBT_TABBEDWINDOW` (Mica Alt), or `DWMSBT_NONE` for File Explorer windows.

> Lines 8457-8481 and 8483-8530: when the region is `kEntireWindow`, the hook extends the DWM frame with margins `{-1,-1,-1,-1}`; otherwise it leaves the original frame behavior unchanged.

> Lines 4668-4688 and 4733-4743: only `http`/`https` `BitmapImage.UriSource` values are tracked for retry after network recovery; other URI schemes (including local paths) are not network-retried.

> A repository-wide search of the pinned file found only XAML details targets such as `Grid#DetailsViewControlRootGrid` and no `SysListView32`, `SHELLDLL_DefView`, `DirectUI`, `ShellView`, or other native file-list hook. This is a source-scope observation, not a claim that every Windows 11 build uses the same internal tree.

> Lines 465-488: the built-in `Translucent Explorer11` theme clears backgrounds for command/navigation/Home/Gallery/details targets and selects Acrylic; lines 1013-1052 show `MicaTabless` clearing the details root; lines 1054-1072 show `OS26 Liquid Glass` applying `WindhawkBlur` to details/Home/Gallery roots.

---

## Pinned source follow-up: XAML value path

**Time**: 2026-10-01, 00:49:00 +08:00
**Source**: `E:\desktop\windows\ThemeStudio-0.6.0\vendor\windhawk-mods\mods\windows-11-file-explorer-styler.wh.cpp` (same SHA-256 as above)
**Method**: extract (PowerShell line read; read-only)
**Confidence**: high
**Insight**: XAML styles are assembled as a `ResourceDictionary`/`Style` and parsed with `Microsoft.UI.Xaml.Markup.XamlReader::Load`, so the upstream README's `ImageBrush` value is consistent with the pinned implementation's XAML setter path. The image is a brush assigned to a matched XAML property; it is not a separate wallpaper engine or a native list renderer.

# Relevant extracted content

> Lines 5117-5164: `GetStyleFromXamlSetters` builds a XAML `ResourceDictionary` and calls `Markup::XamlReader::Load(xaml)` before returning the parsed `Style`.

> Lines 5183-5223: XAML value rules are emitted as `<Setter>` values and inserted into the style; this is the path used for `Background`/`Fill` brush values.

> Lines 2128-2133: the implementation includes `Microsoft.UI.Xaml.Markup.h`, `Microsoft.UI.Xaml.Media.Imaging.h`, and `Microsoft.UI.Xaml.Media.h`, matching the ImageBrush/BitmapImage path.

---
