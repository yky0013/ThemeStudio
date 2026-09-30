# Windows 11 File Explorer Styler: compatibility and background scope

**Status**: Research-only, completed 2026-10-01. No production code, Windhawk state, Explorer state, or system setting was changed.

## Compatibility conclusion

The upstream guide's explicit platform boundary is **Windows 11**. Its exact wording is: “This is a collection of commonly requested file explorer styling customizations for Windows 11. It is intended to be used with the Windows 11 File Explorer Styler Windhawk mod.” The guide does not declare a specific `22H2`, `23H2`, or `24H2` minimum. The pinned source likewise has no explicit Windows-build gate; it identifies Windhawk mod version `1.6`, targets `explorer.exe`, uses `x86-64`, and expects a WinUI 3 Explorer tree.

The pinned source's window-material options are narrower than the broad Windows 11 wording. It hooks `DwmSetWindowAttribute` and sets `DWMWA_SYSTEMBACKDROP_TYPE`; Microsoft's API documentation says that attribute is supported starting with **Windows 11 Build 22621**. Therefore:

- Treat Windows 11 with a compatible WinUI 3 Explorer visual tree as the base styling target.
- Treat the source's Acrylic/Mica/Mica Alt **window-backdrop path** as requiring Windows 11 Build 22621 or later.
- Do not claim Windows 10 support or a precise minimum for every XAML style from these sources. The guide and source do not establish it, and older Windows 11 builds may expose different Explorer trees.

Evidence: [upstream guide](https://github.com/ramensoftware/windows-11-file-explorer-styling-guide), [pinned source](./20_sources.md#pinned-themestudio-source), and [Microsoft DWM availability](https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute). Retrieval details and exact excerpts are in [20_sources.md](./20_sources.md).

## Actual styling scope

The guide documents named **WinUI/XAML** targets, separated by region:

| Region | Upstream target(s) | Practical interpretation |
| --- | --- | --- |
| Tabs | `TabViewItem...`, `Grid#TabContainer...` | Tab text/background/visibility and tab controls |
| Navigation header | `Grid#NavigationBarControlGrid` | Navigation bar surface |
| Command header | `FileExplorerExtensions.CommandBarControl_Wave1 > Grid`, `Grid#CommandBarControlRootGrid`, `CommandBar#FileExplorerCommandBar` | Command bar surface |
| Details/content | `Grid#DetailsViewControlRootGrid` | WinUI details-view root/container background |
| Thumbnail area | `StackPanel#DetailsViewThumbnail` | Thumbnail background/overlay area |
| Home | `Grid#HomeViewRootGrid` | Home page root |
| Gallery | `FileExplorerExtensions.GalleryViewControl#GalleryViewControl > Grid`, `Grid#GalleryRootGrid` | Gallery page roots |

The pinned source matches these XAML targets and separately classifies the top-level `CabinetWClass` window as File Explorer for DWM backdrop changes. A repository search of the pinned file found no `SysListView32`, `SHELLDLL_DefView`, `DirectUI`, `ShellView`, or other native file-list hook. The evidence therefore supports a **WinUI details-container** background claim. It does not support claiming that the underlying native file-list renderer itself is painted by this mod. If the native list remains opaque on a particular build, making the parent `Grid#DetailsViewControlRootGrid` transparent will not guarantee wallpaper visibility through the list; that requires live validation of that build's visual tree.

## Wallpaper/image limitation

The guide allows an image brush as an XAML value:

```text
Fill:=<ImageBrush Stretch="UniformToFill" ImageSource="<image>" />
```

`<image>` may be an image, URL, or local file path. The pinned source assembles XAML `<Style>` setters and parses them with `Microsoft.UI.Xaml.Markup.XamlReader::Load`, so the syntax is compatible with the pinned implementation's setter path. This is a brush assigned to a matched XAML `Background`/`Fill` property. It is not a wallpaper engine, WorkerW host, video renderer, per-monitor wallpaper selector, or automatic reader of the current desktop wallpaper.

The source only tracks `http`/`https` `BitmapImage.UriSource` values for retry after network recovery. Local paths are not network-retried. The image must therefore be reachable and valid when Explorer/XAML loads the style; path quoting/escaping and file availability remain runtime concerns. DWM Acrylic/Mica/Mica Alt are system backdrop materials, not arbitrary wallpaper-image compositing. The source's `entireWindow` region extends the DWM frame and the mod documentation limits that full-window application to dark mode; the default region is the Explorer frame only.

## Applicable presets

The pinned source integrates these relevant candidates:

| Preset / route | What it covers | Fit for an image-backed Explorer concept |
| --- | --- | --- |
| `Translucent Explorer11` | Clears command/navigation/Home/Gallery/details XAML backgrounds and selects Acrylic for the Explorer frame | Best starting preset for showing a desktop/backdrop through transparent XAML areas; it does not itself load a chosen wallpaper image |
| `MicaBar` | Mica-themed command bar; command bar background is transparent | Header-focused only; no details-view image claim |
| `MicaTabless` | Tabless layout with transparent navigation/details root and adjusted rows | Useful clean-header/content baseline; still no image source by itself |
| `OS26 Liquid Glass` | `WindhawkBlur` on details, Home, and Gallery roots with margins/corners | Frosted content panels; blur of what is behind the window, not a selected wallpaper file |
| Custom `controlStyles` | Apply `ImageBrush` to `Grid#DetailsViewControlRootGrid`; optionally Home/Gallery roots and transparent thumbnail child | Only route evidenced for a literal image file; native list coverage remains unverified |

For a narrow header-only request, use `MicaBar` or the guide's navigation/command targets. For a literal file-backed content image, start from a transparent preset such as `Translucent Explorer11` and add a custom `ImageBrush` rule to the details root, then validate the actual Explorer build. No built-in preset in the pinned source is an automatic “use current desktop wallpaper as file-list background” switch.

## Caveats to surface in the product

- Windhawk's XAML diagnostics has a single-consumer constraint. The pinned source documents conflicts with tools such as ExplorerBlurMica and offers Alert/Block/Allow handling.
- Theme settings and source availability are not proof of runtime injection or successful rendering. A live check must separately confirm Windhawk enabled/loaded state, Explorer target-tree matches, image load, and whether the native file list is opaque.
- The upstream guide's live `main` page showed short commit `fe8f72c` on Sep 27, 2026 (GMT+8) during this run; a GitHub API confirmation was rate-limited (HTTP 403), so that short hash is page-observed metadata only.
