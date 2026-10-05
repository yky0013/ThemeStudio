# Explorer header / splitter source checkpoints

Scope: read-only investigation of the approximately 4 px white vertical strip between Explorer navigation/list regions and the list/preview region. The target is to distinguish a native theme part from a DirectUI layout/sizer surface. No implementation file or live Explorer state was changed.

## Source checkpoint 1 — Aerexplorer UIFILE replacement (local vendor snapshot)

**Time**: 2026-10-05, 11:59:01 +08:00
**Source**: `E:/desktop/windows/.themestudio-0.6.4-work/vendor/windhawk-mods/mods/aerexplorer.wh.cpp` (lines 256–280, 2128–2177, 3028–3036); upstream `https://github.com/ramensoftware/windhawk-mods/blob/main/mods/aerexplorer.wh.cpp`
**Method**: local source read (PowerShell `Get-Content`/`rg`), with upstream primary-source URL recorded
**Confidence**: high
**Insight**: Explorer's legacy details/preview layout is declared through shell32 UIFILE DirectUI XML. `PreviewBackground` and `ReadingPane` are layout elements; `PreviewPaneSizer` and `ReadingPaneSizer` are separate `Sizer` elements that size their targets. This is not evidence of a `DrawThemeBackground` part for the splitter itself.

# Relevant extracted content

> Lines 259–280 define `<Element resid="FolderLayout" layout="shellborderlayout()">`, `StatusBarModule`, `TemplateBackground id="atom(PreviewContainer)"`, `PreviewBackground id="atom(BackgroundClear)" background="ARGB(0, 0, 0, 0)"`, `PreviewThumbnailModule`, `PreviewMetadataModule`, then `<Sizer id="atom(PreviewPaneSizer)" sizingtarget="atom(PreviewContainer)" ... layoutpos="top" .../>`; the right-side reading pane is a `TemplateBackground id="atom(ReadingPane)" ... layoutpos="right">` followed by `<Sizer id="atom(ReadingPaneSizer)" sizingtarget="atom(ReadingPane)" ... layoutpos="Right"/>`.
>
> The hook around lines 2133–2177 replaces `DUI_LoadUIFileFromResources` only for selected `shell32.dll` UIFILE resource IDs (3, 4, 5, 6, 19, 20, 21). This demonstrates the source controls DirectUI XML layout, not a public window class or documented theme part.
>
> The same XML places `ProperTreeModule` at `layoutpos="Left"` and `ViewHostContainer` at `layoutpos="Client"`; therefore the left navigation/content boundary is a layout boundary with a `Sizer`/theme separator candidate, while the actual item/list content is a sibling region.

---

## Source checkpoint 9 — Microsoft Theme API parts/states documentation

**Time**: 2026-10-05, 12:06:15 +08:00
**Source**: `https://learn.microsoft.com/en-us/windows/win32/controls/parts-and-states` (localized page opened because the English redirect was unavailable)
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: Microsoft documents that `DrawThemeBackground` receives a class-specific part and state, that state 0 means a part has no defined states, and that the published table covers standard classes/parts from `Vsstyle.h`/`Vssym32.h`. `PreviewPane` is absent from that standard table, so its part 3/4 names must be treated as Explorer's private visual-style class map, not a public SDK constant.

# Relevant extracted content

> Microsoft says parts can represent drawn shapes, images, lines, or text areas, and that `stateId=0` is used when no states are defined (page lines 28–35). The standard table includes `REBAR RP_SPLITTER/RP_SPLITTERVERT` and other public parts, but no `PreviewPane` class.

> This supports the narrow interpretation of the QA trace: `PreviewPane` part 3/4 state 0 is a private Explorer theme call observed at runtime. It does not justify substituting public `REBAR RP_SPLITTER` IDs or changing all `DrawThemeBackground` calls.

---

## Source checkpoint 8 — historical PreviewPane class-map corroboration (secondary)

**Time**: 2026-10-05, 12:05:00 +08:00
**Source**: `https://www.vistastylebuilder.com/forum/index.php?action=printpage%3Btopic%3D950.0`
**Method**: browser-rendered (via `web__run` open)
**Confidence**: low
**Insight**: A Windows Style Builder 1.6 class-map changelog explicitly labels `PreviewPane` part 3 as “ProperTree Separator” and part 4 as “ReadingPane Separator”, while part 1 is “Details Background”. This is useful corroboration for the modern trace, but it is a 2010 community-maintained map and cannot by itself prove current Windows 11 build 26200 behavior.

# Relevant extracted content

> The page lists `PreviewPane <1> = Details Background`, `<3> = ProperTree Separator`, `<4> = ReadingPane Separator`, and `<5>–<7> =` text/attribute parts. It separately lists `CommandModule <1> = Background`, `<3> = Button`, `<4> = SplitButtonLeft`, `<5> = SplitButtonRight`, and `<6> = ExpanderGlyph`.

> Treat this as historical naming only. The current build-specific fact comes from the isolated `DirectUIHWND` trace and the two independent current Windhawk source paths above.

---

## Source checkpoint 7 — upstream Aerexplorer page

**Time**: 2026-10-05, 12:04:20 +08:00
**Source**: `https://github.com/ramensoftware/windhawk-mods/blob/main/mods/aerexplorer.wh.cpp`
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: The upstream page confirms the UIFILE replacement source used for the DirectUI layout evidence. The browser page exposes the file and raw-source link; the exact `Sizer` and `PreviewBackground` lines are retained in the local vendor snapshot and checkpoint 1.

# Relevant extracted content

> GitHub identifies the file as `mods/aerexplorer.wh.cpp` in the public `ramensoftware/windhawk-mods` repository. Its local snapshot contains the `DUI_LoadUIFileFromResources` hook and the `PreviewPaneSizer`/`ReadingPaneSizer` XML described above.

---

## Source checkpoint 6 — upstream Win32 UI Modernizer page

**Time**: 2026-10-05, 12:03:45 +08:00
**Source**: `https://github.com/ramensoftware/windhawk-mods/blob/main/mods/win32-ui-modernizer.wh.cpp`
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: The upstream page confirms the navigation-divider implementation is part of the public Windhawk mod source. GitHub could not render the full 3.19 MB file in the browser view, so exact line claims remain grounded in the local vendored snapshot and its recorded source URL.

# Relevant extracted content

> GitHub identifies the file as `mods/win32-ui-modernizer.wh.cpp` under `ramensoftware/windhawk-mods` and links its raw source. The local snapshot supplies the exact `PreviewPane`/`NavPane` part 3/4 branch and the `WindowFromDC`/memory-DC owner comments.

---

## Source checkpoint 5 — upstream Translucent Windows page

**Time**: 2026-10-05, 12:03:10 +08:00
**Source**: `https://github.com/ramensoftware/windhawk-mods/blob/main/mods/translucent-windows.wh.cpp`
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: The upstream repository page confirms the local file is an actual Windhawk mod source under `ramensoftware/windhawk-mods`, rather than an inferred or undocumented snippet. The line-level part/class evidence is preserved in the local vendor copy above so it remains auditable even if the upstream branch changes.

# Relevant extracted content

> GitHub identifies the file as `mods/translucent-windows.wh.cpp` in the public `ramensoftware/windhawk-mods` repository and exposes the raw source. The local snapshot was inspected for the exact `PreviewPane` part 3/4 branch and line renderer.

---

## Source checkpoint 4 — isolated QA baseline paint trace

**Time**: 2026-10-05, 12:02:00 +08:00
**Source**: `E:/desktop/windows/.themestudio-0.6.4-work/docs/development/validation-0.6.4/baseline-paint-trace.tsv`
**Method**: local validation artifact read (PowerShell `Get-Content -Encoding Unicode`); runtime capture was performed by the parent agent in an isolated QA environment and is recorded here as evidence only
**Confidence**: high
**Insight**: The baseline trace contains exactly two full-height five-pixel `PreviewPane` paints on `DirectUIHWND`, both in state 0: `(part 3, state 0, 340,0,345,773)` and `(part 4, state 0, 1421,0,1426,773)`. These rectangles match the two visible vertical white strips and are the strongest current evidence for the narrow fix target.

# Relevant extracted content

```text
DirectUIHWND    PreviewPane    3    0    340,0,345,773
DirectUIHWND    PreviewPane    4    0    1421,0,1426,773
```

> The same trace records `DirectUIHWND` `ShellStatusBarSeparator` part 1/state 0 and `CommandModule` parts 4/state 1–2 in other rectangles, so those calls are distinct from the two full-height PreviewPane separator calls. The trace also records the normal `SysTreeView32`/`TreeView` and scrollbar calls separately.

> The parent agent reports that this trace came from an isolated QA run that reproduced the user's screenshot and was restored afterward. This file itself is read-only evidence; no live Explorer or Windhawk state was touched during this subtask.

---

## Source checkpoint 3 — Win32 UI Modernizer navigation-divider source (local vendor snapshot)

**Time**: 2026-10-05, 12:01:05 +08:00
**Source**: `E:/desktop/windows/.themestudio-0.6.4-work/vendor/windhawk-mods/mods/win32-ui-modernizer.wh.cpp` (lines 17787–17803, 17939–17960, 17999–18086, 19658–19695, 20906–20925); upstream `https://github.com/ramensoftware/windhawk-mods/blob/main/mods/win32-ui-modernizer.wh.cpp`
**Method**: local source read (PowerShell `Get-Content`/`rg`), with upstream primary-source URL recorded
**Confidence**: high
**Insight**: A second independent renderer removes or redraws the Explorer navigation divider only when the theme class is `PreviewPane` or `NavPane` and the part is 3 or 4. It resolves the paint owner from `WindowFromDC`, with a memory-DC fallback, and uses `NamespaceTreeControl` only to validate the Explorer root. This strongly supports using the observed `DirectUIHWND` paint owner and a narrowly scoped `PreviewPane` part 3/4, rather than globally changing all DirectUI or all white fills.

# Relevant extracted content

> The mod documents that the divider theme part repaints on position changes and that DirectUI may paint it through a memory DC owned by a different internal HWND (lines 17787–17791 and 17999–18002).
>
> `NavDividerTrackAndGetHwnd` first calls `WindowFromDC(hdc)` and falls back to a thread-local paint HWND, then records the divider center x on that HWND (lines 18052–18086). This is consistent with the observed `DirectUIHWND` trace and warns against assuming a dedicated splitter HWND.
>
> The theme hook checks `(iPartId == 3 || iPartId == 4)` and then accepts only `cls == L"PreviewPane" || cls == L"NavPane"` (lines 19658–19695). It either skips the divider or fills exactly the divider rect plus a one-pixel horizontal expansion. The same source treats `PreviewPane` part 1 as a pane background elsewhere (lines 20906–20925), separating the divider from the background part.
>
> The mod's settings describe this as the Explorer navigation divider and a WinUI-style pane splitter. That wording is descriptive project code, not a Microsoft public API guarantee; retain the part IDs as source-backed evidence and the class-map stability as build-dependent.

---

## Source checkpoint 2 — Translucent Windows theme-hook source (local vendor snapshot)

**Time**: 2026-10-05, 12:00:30 +08:00
**Source**: `E:/desktop/windows/.themestudio-0.6.4-work/vendor/windhawk-mods/mods/translucent-windows.wh.cpp` (lines 824–835, 3896–3931, 4731–4740, 4997–5006, 5027–5035, 5044–5055); upstream `https://github.com/ramensoftware/windhawk-mods/blob/main/mods/translucent-windows.wh.cpp`
**Method**: local source read (PowerShell `Get-Content`/`rg`), with upstream primary-source URL recorded
**Confidence**: high
**Insight**: An independent Windhawk theme renderer identifies `PreviewPane` by `GetThemeClass` and treats part IDs 3 and 4 as the Preview Pane separators. It draws a cached 3×3 one-pixel line for either part and routes the call from `DrawThemeBackgroundEx`; the same source treats PreviewPane part 1 as the pane background. This is direct code evidence for the splitter part IDs, although it does not prove Microsoft’s internal class map is stable across all Windows builds.

# Relevant extracted content

> `GetThemeClass` resolves the theme class through the undocumented ordinal 74 export of `uxtheme.dll` (lines 824–835). The renderer then enters the `PreviewPane` branch at lines 4997–5006.
>
> `PaintPreviewPaneSeparator` accepts only `iPartId == 3 || iPartId == 4` (lines 3896–3907), shifts the destination one pixel, and draws a cached 3×3 line. `CachePreviewPaneSeparator` creates a 3×3 DIB and draws a one-pixel vertical line (lines 3910–3931). This matches a narrow vertical divider/splitter paint rect, not a full pane background.
>
> In the same `DrawThemeBackgroundEx` hook, `PreviewPane` part 1 is handled as the background surface (lines 5044–5055), while `CommandModule` is a separate theme class with its own button/split-button/location part handling (lines 5027–5035). Thus a `CommandModule` trace should not be used as evidence for the PreviewPane splitter.
>
> The source's `GetThemeColor` hook independently recognizes `PreviewPane` parts 5, 6, and 7 for fill/text colors (lines 1421–1427), reinforcing that parts 3/4 are special separator parts while 1 and 5–7 serve other pane roles.

---

## Narrowest evidence-backed repair boundary

**Confirmed for the current QA run**

- The two white strips are `DirectUIHWND` theme calls with `ThemeClass = PreviewPane`, `part = 3/4`, `state = 0`, and full-height five-pixel rectangles. The trace is in `docs/development/validation-0.6.4/baseline-paint-trace.tsv`.
- Two independent current Windhawk sources identify `PreviewPane` parts 3 and 4 as divider/separator paints and keep part 1 as a pane background. `CommandModule` is a separate theme class for command buttons/split buttons.
- Aerexplorer's shell32 DirectUI XML identifies `PreviewPaneSizer`/`ReadingPaneSizer` as sizing elements, which explains why the separator is a DirectUI/theme paint call rather than a normal `SysTreeView32` or scrollbar.

**Recommended narrow boundary**

In the existing `DrawThemeBackground` and `DrawThemeBackgroundEx` replacement path, add one predicate equivalent to:

```text
IsShellDirectUI(window)
&& ThemeClassIs(theme, "PreviewPane")
&& (part == 3 || part == 4)
&& state == 0
```

For that predicate only, paint the clipped `rect` through the existing `PaintImage` path and return success. Preserve the existing `part == 1` PreviewPane background handling, and leave `CommandModule`, `Header`, `Status`, TreeView selection/hover states, and all other DirectUI paints on their current paths. Use the actual paint rectangle; do not hard-code the 5 px width or move/resize the pane. This preserves native hit testing and sizing because the change is paint-only.

**Limits and open evidence**

- `PreviewPane` and its numeric parts are Explorer's private visual-style class map, not public `Vsstyle.h`/`Vssym32.h` constants. `REBAR RP_SPLITTER` is a different public class and should not be substituted.
- The independent source paths and the QA trace agree on build-specific behavior, but no Microsoft public source documents `PreviewPane` part 3/4. Revalidate the predicate after a Windows build change.
- The historical Style Builder map is corroboration only; it is not current Windows 11 runtime evidence.
