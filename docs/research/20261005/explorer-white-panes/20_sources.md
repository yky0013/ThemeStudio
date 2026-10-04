# Explorer white panes research: source checkpoints

Each source is persisted immediately after read. Local vendor files are marked separately from remote first-party sources.

## Source checkpoint 1 — local Explorer Visual Tweaks Dark source

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: `E:/desktop/windows/ThemeStudio-0.6.2/vendor/windhawk-mods/mods/explorer-visual-tweaks-dark.wh.cpp`
**Method**: local source read (PowerShell `Get-Content`/`rg`, read-only)
**Confidence**: high
**Insight**: The candidate native mod separates DirectUI ItemsView selection, navigation TreeView theme drawing, and Preview Pane host fixes. Its ordinary TreeView state is passed through to the original theme while selected/hover states are custom handled; because this mod was not enabled in the field-tested runtime, that behavior is an implementation observation, not a confirmed field cause.

# Relevant extracted content

> Settings expose `itemsView.customizeItemsView`, `navigationPane.customizeNavigationPane`, and `previewPane.matchDetailsPaneBg` with `previewPaneBgColor` (source lines 48–115).
>
> The DirectUI hook resolves `DirectUI::Element::PaintBackground`, `GetSelected`, `GetMouseFocused`, `GetParent`, and `GetKeyFocusedElement` from `DUI70.dll` (lines 754–797). It draws selection resources with nine-patch `AlphaBlend` and a focus pill (lines 655–744).
>
> `Selection::HandleDrawThemeBackground` filters to TreeView `TVP_TREEITEM` and handles only `TREIS_HOT`, `TREIS_SELECTED`, `TREIS_SELECTEDNOTFOCUS`, and `TREIS_HOTSELECTED` (lines 809–835). All other states, including the ordinary unselected state, call the original `DrawThemeBackground` and can therefore retain the white theme fill.
>
> Preview handling targets `Shell Preview Extension Host`, `Shell Preview Extension Host Previewer`, `RICHEDIT50W`, and the `ReadingPane` theme class (lines 972–1115). It replaces the class background brush during `RegisterClassExW`, returns a custom color from `GetThemeColor` for `ReadingPane` part 1 / `TMT_FILLCOLOR`, and only hooks `GetSysColor`/`CreateWindowExW` for `prevhost.exe` RichEdit (lines 1037–1115). Initialization installs these hooks and creates a solid preview brush; teardown only deletes the brush (lines 1124–1179).

---

## Source checkpoint 2 — local Explorer TreeItem Tweaker source

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: `E:/desktop/windows/ThemeStudio-0.6.2/vendor/windhawk-mods/mods/explorer-treeitem-tweaker.wh.cpp`
**Method**: local source read (PowerShell `Get-Content`/`rg`, read-only)
**Confidence**: high
**Insight**: This is the closest reusable native path for left navigation item backgrounds. It is explicitly documented in the source as tested on Windows 11 23H2–25H2 and resolves each item from cursor/selection/vertical position, then draws rounded GDI+ backgrounds through theme hooks. Its current state map still excludes the ordinary normal background, so it explains the remaining white rows and gives a precise extension point.

# Relevant extracted content

> The source says it customizes Explorer TreeView states Hot, Selected, Selected Not Focus, Hot Selected, and Normal Text, and reports compatibility with Windows 11 23H2 through 25H2 (lines 42–76).
>
> `ResolveItemFromDrawContext` maps state 2 (hot), 6 (hot selected), 3/5 (selected) to an `HTREEITEM`, verifies the item rectangle, and falls back to the visible item at the paint rectangle's vertical midpoint (lines 1910–1946). `GetContentBasedRect` preserves vertical paint coordinates while adjusting horizontal bounds (lines 1949–1977).
>
> `HandleTreeDraw` only obtains a `StateStyle` through `GetStyleForState`, whose switch returns styles for state IDs 2, 3, 5, and 6; state 1 (normal) returns `nullptr` and falls through to the original themed draw (lines 973–983 and 2059–2083). `HookedDrawThemeBackground` and `HookedDrawThemeBackgroundEx` apply the custom state drawing only when `IsTreeViewTheme` and otherwise call the original functions (lines 2085–2105).
>
> The mod installs hooks for `DrawThemeBackground`, `DrawThemeBackgroundEx`, `GetThemeColor`, text drawing, `CreateWindowExW`, and `SendMessageW`, and removes tracked state on unload (lines 2890–3010). This provides a concrete state-preserving architecture for adding normal-row background handling.

---

## Source checkpoint 3 — VitalSkib Explorer Visual Tweaks Dark README

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://github.com/VitalSkib/explorer-visual-tweaks-dark
**Method**: browser-rendered (via `web__run` open; repository README, lines 163–254)
**Confidence**: high
**Insight**: The author's README documents a direct Preview Pane background fix for `explorer.exe` and `prevhost.exe`, says the fix uses `DirectUI::Element::PaintBackground`/DUI70 internals, and warns that preview handlers can draw their own surfaces. It also states class-background assignment requires restarting Explorer/host processes for restoration.

# Relevant extracted content

> The README lists Preview Pane background and plain-text preview as features, with separate target processes `explorer.exe` and `prevhost.exe` (lines 163–186).
>
> It says the Preview Pane fix uses a private `DUI70.dll` hook target resolved by an exact decorated C++ export name and that a future Windows update may change it (lines 231–239). It also notes third-party preview handlers can draw their own background/content/scrollbar, so Explorer's Preview Pane styling may not affect them (lines 236–238).
>
> Preview Pane changes require restarting Explorer and included host applications; the README says complete restoration after disabling depends on restart because the background brush is assigned at window-class registration (lines 224–237).

---

## Source checkpoint 4 — VitalSkib current native source

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/VitalSkib/explorer-visual-tweaks-dark/main/explorer-visual-tweaks-dark.wh.cpp
**Method**: browser-rendered (via `web__run` open; raw source, 1278 lines; exact symbol scan read-only)
**Confidence**: high
**Insight**: The current raw source resolves `DirectUI::Element::PaintBackground`, `GetSelected`, `GetMouseFocused`, `GetParent`, and `GetKeyFocusedElement`, but the hook shown in the source only records the current element and calls the original function with unchanged `backgroundValue`. The README claim that it patches a DirectUI Value color is therefore not visible in this fetched source revision; treat the repository README/source pair as internally inconsistent until a commit/tag is pinned.

# Relevant extracted content

> `ResolveDuiFunctions` looks up the decorated `PaintBackground@Element@DirectUI` export and selection/focus/parent getters (source lines 754–775). The installed hook stores `g_currentPaintElement`, then calls `g_origPaintBackground(element, dc, backgroundValue, rect1, rect2, rect3, rect4)` without changing `backgroundValue` (lines 777–797).
>
> The same source uses `RegisterClassExW` to replace `hbrBackground` for `Shell Preview Extension Host`/`Shell Preview Extension Host Previewer`, `GetThemeColor` for `ReadingPane` part 1 / `TMT_FILLCOLOR`, and `GetSysColor`/`CreateWindowExW` for `RICHEDIT50W` in `prevhost.exe` (lines 972–1179).

---

## Source checkpoint 5 — VitalSkib license

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://github.com/VitalSkib/explorer-visual-tweaks-dark/blob/main/LICENSE
**Method**: browser-rendered (via `web__run` open; GitHub license page)
**Confidence**: high
**Insight**: The remote project advertises an MIT license, so its source can be studied or reused subject to preserving the license notice; this is separate from the current ThemeStudio vendor snapshot's provenance.

# Relevant extracted content

> GitHub identifies the repository resource as “MIT license” (lines 153–160). The README also states the project is licensed under MIT (lines 252–254).

---

## Source checkpoint 6 — Maplespe ExplorerBgTool README

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://github.com/Maplespe/explorerTool/blob/main/README.md
**Method**: browser-rendered (via `web__run` open; official archived repository, lines 115–341)
**Confidence**: high
**Insight**: ExplorerBgTool is explicitly an ItemView image renderer with PNG/JPG, alpha, position, random/per-path selection, and a Windows 10/11 registration workflow, but the README does not claim to paint the Preview Pane or TreeView item backgrounds.

# Relevant extracted content

> The repository is archived/read-only (line 115). It describes “Customize Explorer ItemView background image” and Windows 10/11 examples (lines 192–236), with `posType`, `imgAlpha`, `folder`, and per-path `img=` settings (lines 273–330).
>
> Install/uninstall uses `注册_Register.cmd`/`卸载_Uninstall.cmd` or `regsvr32`/`regsvr32 /u`; invalid images may crash Explorer, and holding `ESC` while opening Explorer skips image loading (lines 243–272 and 331–341).

---

## Source checkpoint 7 — Maplespe ExplorerBgTool native draw path

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/Maplespe/explorerTool/main/ExplorerBgTool/dllmain.cpp
**Method**: browser-rendered (via `web__run` open; raw source, 603 lines)
**Confidence**: high
**Insight**: The native implementation identifies `DirectUIHWND` under `SHELLDLL_DefView`, hooks `CreateWindowExW`/`BeginPaint`/`FillRect`/`CreateCompatibleDC`, and uses GDI+/`AlphaBlend` for the main ItemView. It has no TreeView state resolver, Preview Pane class/host handling, or header/status-row target.

# Relevant extracted content

> `ShouldLoad` limits normal load to `explorer.exe`, unless optional file-dialog extension mode is enabled (lines 154–190). `OnWindowLoad` initializes GDI+ and MinHook hooks the five Win32 APIs (lines 318–356).
>
> `MyCreateWindowExW` records only a `DirectUIHWND` whose parent is `SHELLDLL_DefView`, with `ShellTabWindowClass` or `#32770` above it (lines 385–434). `MyFillRect` computes position/zoom-fill and calls `AlphaBlend` with `imgAlpha` (lines 473–586).

---

## Source checkpoint 8 — Maplespe ExplorerBgTool shell registration

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/Maplespe/explorerTool/main/ExplorerBgTool/ShellLoader.cpp
**Method**: browser-rendered (via `web__run` open; raw source, 287 lines)
**Confidence**: high
**Insight**: Its COM/BHO registration is reversible but broad: HKCR CLSID/InProcServer32, Explorer Browser Helper Objects, and Drive FolderExtensions are created, with matching deletes in `DllUnregisterServer`. This is unrelated to the specific white pane colors and should remain an isolated install/restore option.

# Relevant extracted content

> `DllRegisterServer` writes the CLSID, DLL path, `ThreadingModel=Apartment`, Explorer BHO key, and Drive FolderExtensions key; `DllUnregisterServer` deletes those keys (lines 156–213).

---

## Source checkpoint 9 — Maplespe ExplorerBgTool license

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://github.com/Maplespe/explorerTool/blob/main/LICENSE
**Method**: browser-rendered (via `web__run` open; GitHub license page)
**Confidence**: high
**Insight**: ExplorerBgTool is MIT licensed; any source reuse must retain the copyright and permission notice.

# Relevant extracted content

> GitHub identifies the repository LICENSE as MIT (lines 232–262 in the page rendering), with Maplespe copyright and the standard retain-notice conditions.

---

## Source checkpoint 10 — Win32 class background semantics

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/winmsg/about-window-classes
**Method**: browser-rendered (via `web__run` query-search)
**Confidence**: high
**Insight**: Microsoft documents that a class `hbrBackground` brush fills a client area before drawing and can erase prior pixels; with a NULL class brush, the window must handle `WM_ERASEBKGND` itself. This validates why class-brush replacement can fix Preview Pane white frames, while also explaining why changing a registered class may require recreating/restarting windows.

# Relevant extracted content

> The class background brush prepares the client area and the system sends `WM_ERASEBKGND` when the background should be painted. If `hbrBackground` is NULL, the window must paint its own background on `WM_ERASEBKGND`.

---

## Source checkpoint 11 — Microsoft TreeView custom draw contract

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/controls/nm-customdraw-tree-view
**Method**: browser-rendered (via `web__run` query-search)
**Confidence**: high
**Insight**: The supported TreeView custom-draw contract is a parent `WM_NOTIFY`/`NM_CUSTOMDRAW` path using `NMTVCUSTOMDRAW`; returning `CDRF_SKIPDEFAULT` after drawing suppresses the control's default item drawing. This is reliable only when the parent receives notifications and should be checked against Explorer's current TreeView host before choosing it over the existing `DrawThemeBackground` hook.

# Relevant extracted content

> Microsoft says TreeView sends `NM_CUSTOMDRAW` to its parent via `WM_NOTIFY`, with an `NMTVCUSTOMDRAW` payload. At `CDDS_ITEMPREPAINT`, returning `CDRF_SKIPDEFAULT` means the application drew the item and the control will not draw it.

---

## Source checkpoint 12 — Microsoft window subclass API

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/commctrl/nf-commctrl-setwindowsubclass
**Method**: browser-rendered (via `web__run` query-search)
**Confidence**: high
**Insight**: `SetWindowSubclass` installs a callback identified by window/procedure/ID, and `RemoveWindowSubclass` reverses it. Microsoft explicitly warns that the helper cannot subclass across threads, so Explorer/Preview host callbacks must be installed on each target window's owning thread or through the Windhawk cross-thread helper.

# Relevant extracted content

> The API takes `HWND`, `SUBCLASSPROC`, a caller-defined subclass ID, and `DWORD_PTR` reference data. It returns TRUE on installation and requires `commctrl.h`/Comctl32. The documentation warns that the helper cannot subclass a window across threads.

---

## Source checkpoint 13 — Microsoft WM_ERASEBKGND behavior

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-erasebkgnd
**Method**: browser-rendered (via `web__run` query-search)
**Confidence**: high
**Insight**: A window that handles `WM_ERASEBKGND` should return nonzero; otherwise `DefWindowProc` uses the class background brush and the window remains marked for erasing. This provides a precise Preview Pane fallback path after identifying the actual host HWND.

# Relevant extracted content

> `WM_ERASEBKGND` is sent when a window background must be erased, such as during resize. `DefWindowProc` uses the class brush; a custom handler should return nonzero after erasing the background.

---

## Source checkpoint 14 — Microsoft generic custom draw guidance

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/controls/using-custom-draw
**Method**: browser-rendered (via `web__run` query-search)
**Confidence**: high
**Insight**: Microsoft’s generic custom-draw sequence uses `CDDS_PREPAINT` → `CDRF_NOTIFYITEMDRAW` → `CDDS_ITEMPREPAINT`, where item colors can be set before default drawing. This supports preserving selection/hover by branching on item state rather than painting a whole TreeView with a generic fill.

# Relevant extracted content

> The example requests item notifications from `CDDS_PREPAINT`, then sets item text/background colors during `CDDS_ITEMPREPAINT`.

---

## Source checkpoint 15 — VitalSkib Reading Pane Stripe Removal README

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://github.com/VitalSkib/readingpane-stripe-removal
**Method**: browser-rendered (via `web__run` open; repository README, lines 163–212)
**Confidence**: high
**Insight**: This is a narrowly scoped Preview/Reading Pane workaround that avoids changing a generic `FillRect` color. It identifies one internal DUI element and suppresses only the unwanted fill while that element paints; the author reports testing on 26300.9032 and a report on 26220.9022, not the target 26200 build.

# Relevant extracted content

> The README describes a ~47 px stripe in the Reading/Preview Pane on Windows 11 Insider builds 26300.9032 and 26220.9022 (lines 163–174).
>
> The workaround suppresses the specific background fill identified through internal `DUI70.dll` implementation and warns that the implementation may change after Windows updates (lines 178–180, 210–212). It requires a complete `explorer.exe` restart because DirectUI/Preview Pane state may be cached before the mod loads (lines 181–209).

---

## Source checkpoint 16 — Reading Pane targeted hook source

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/VitalSkib/readingpane-stripe-removal/main/readingpane-stripe-removal.cpp
**Method**: browser-rendered (via `web__run` open; raw source, 87 lines)
**Confidence**: high
**Insight**: The source gives a concrete call-stack-scoped suppression pattern for a Preview Pane internal fill: identify the target `PaintBackground` object by vtable pointer plus `fields[3] == 4`, set a thread-local flag only around the original call, and suppress `FillRect` only while that flag is active.

# Relevant extracted content

> `PaintBackground_hook` checks `fields[0] == g_expectedVtable` and `reinterpret_cast<ULONG_PTR>(fields[3]) == 4`, then sets `g_insideTargetPaint` only for the duration of `PaintBackground_orig` (lines 22–41).
>
> `FillRect_hook` returns `TRUE` only when `g_insideTargetPaint` is set; otherwise it calls the original `FillRect` (lines 43–48). The mod resolves `FillRect` from `user32.dll`, uses hard-coded `dui70.dll` offsets `0xD920` and `0x1037C0`, and installs both hooks with `Wh_SetFunctionHook` (lines 50–82).
>
> The hard-coded offsets are evidence of a build-specific internal hook, not a portable 26200 implementation. The source has an empty `Wh_ModUninit` (lines 84–87), so cleanup/recovery behavior must be handled by Windhawk/process restart rather than copied as-is.

---

## Source checkpoint 17 — Reading Pane stripe workaround README

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://github.com/VitalSkib/readingpane-stripe-removal
**Method**: browser-rendered (via `web__run` open; official author repository, lines 163–212)
**Confidence**: high
**Insight**: A current author-side workaround targets a specific Preview Pane DUI element and suppresses only its fill, with explicit warnings that the method is build-specific and temporary. Its tested builds (26300.9032 and 26220.9022) do not prove compatibility with 26200.

# Relevant extracted content

> The README identifies a Preview/Reading Pane stripe bug on Insider builds 26300.9032 and 26220.9022 and says Microsoft is working on it (lines 163–174).
>
> It suppresses the specific background fill identified through internal `DUI70.dll`, does not rely on stripe size/position/color, and warns that internal implementation may change (lines 178–180). It requires a complete Explorer restart because the state may be cached before the mod loads (lines 181–209).

---

## Source checkpoint 18 — Reading Pane targeted suppression source

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/VitalSkib/readingpane-stripe-removal/main/readingpane-stripe-removal.cpp
**Method**: browser-rendered (via `web__run` open; raw source, 87 lines)
**Confidence**: high
**Insight**: This source gives a reusable, call-stack-scoped pattern for Preview Pane background artifacts: identify an internal DUI object, set a thread-local flag only around its original `PaintBackground`, and suppress `FillRect` only while that flag is active.

# Relevant extracted content

> `PaintBackground_hook` checks `fields[0] == g_expectedVtable` and `fields[3] == 4` before setting `g_insideTargetPaint` for the original call (lines 22–41). `FillRect_hook` returns `TRUE` only under that flag and otherwise calls `FillRect_orig` (lines 43–48).
>
> The mod uses hard-coded `dui70.dll` offsets `0xD920` and `0x1037C0` and installs hooks with `Wh_SetFunctionHook` (lines 50–82). The offsets are build-specific; the empty `Wh_ModUninit` (lines 84–87) is not a complete restoration implementation.

---

## Source checkpoint 19 — current 26200 WinUI compatibility warning

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://github.com/ramensoftware/windows-11-file-explorer-styling-guide/issues/79
**Method**: browser-rendered (via `web__run` open; official styling-guide issue)
**Confidence**: high
**Insight**: An issue reports that Windows 11 25H2 build 26200.8737 caused the File Explorer Styler to fall back to legacy Win32 UI, with the Preview Pane unavailable, and that disabling the mod immediately restored modern Explorer. This is user-reported issue evidence, not a confirmed root cause, but it makes 26200 build gating essential.

# Relevant extracted content

> The report says build 26200.8737 caused the Styler to make Explorer load legacy Win32 UI; expected modern command/address/navigation bars and a working Preview Pane were absent (lines 128–180). It attributes the suspected break to outdated hooks/patterns and says disabling the mod restored normal behavior (lines 181–198).

---

## Source checkpoint 20 — local Explorer Info Bar+ status-row painter

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: `E:/desktop/windows/ThemeStudio-0.6.2/vendor/windhawk-mods/mods/explorer-info-bar.wh.cpp`
**Method**: local source read (PowerShell `rg`/`Get-Content`, read-only)
**Confidence**: high
**Insight**: The existing Info Bar+ source contains a reliable status-row targeting and cleanup pattern: it validates the `SHELLDLL_DefView` descendant and geometry, lets DirectUI finish `WM_PAINT`, then paints the row afterward; unload removes the subclass and invalidates/redraws the row.

# Relevant extracted content

> `FindShellDefViewDescendant`/`RefreshValidatedStatusRow` validates that the `SHELLDLL_DefView` child belongs to the same DirectUI thread/process and computes the row below its mapped bottom (source lines 2242–2400).
>
> `DirectUiSubclassProc` calls `DefSubclassProc` first for `WM_PAINT`, then obtains a DC and calls `PaintFinalInfoBar`, so its overlay is after native buffered painting (lines 6429–6487). `Wh_ModUninit` removes the subclass and invalidates/updates the stored row to clear overlay pixels (lines 6925–6965).
>
> The source samples native row pixels for unselected rows in `PickBackgroundColor` before choosing a fallback app-theme color (lines 4987–5101). This is a reusable theme-background sampling pattern for a status row, but it does not target the Details column header.

---

## Source checkpoint 21 — local header target audit

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: `E:/desktop/windows/ThemeStudio-0.6.2/vendor/windhawk-mods/mods/file-explorer-details-autofit-columns.wh.cpp` and related vendor mods
**Method**: local source search (`rg`, read-only)
**Confidence**: medium
**Insight**: The current vendor utility locates `SysHeader32` only to measure/fit Details columns; no verified source in the searched Explorer mods paints its header background. The classic Treeview mod's “header” is a legacy folder-band header and is unrelated to the modern Details column header.

# Relevant extracted content

> `file-explorer-details-autofit-columns.wh.cpp` finds a `SysHeader32` descendant and uses `HDM_GETITEMCOUNT`/`HDM_GETITEMRECT` for width/overflow calculations (source lines around 1241 and 996–1003), without a header background draw hook.
>
> `classic-explorer-treeview.wh.cpp` documents a gradient “header” for its classic folder band, not the Details view's `SysHeader32`/WinUI column header.

---

## Source checkpoint 22 — 26200 compatibility issue report

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://github.com/ramensoftware/windows-11-file-explorer-styling-guide/issues/79
**Method**: browser-rendered (via `web__run` open; official repository issue, lines 128–198)
**Confidence**: medium
**Insight**: A user report against build 26200.8737 says File Explorer Styler caused modern Explorer to fall back to legacy Win32 UI and the Preview Pane to become unavailable, with disabling the mod restoring normal behavior. It is a compatibility warning, not an independently verified root cause.

# Relevant extracted content

> The issue reports build 26200.8737, loss of modern WinUI command/address/navigation bars, Preview Pane “Preview not available,” and immediate recovery after disabling the mod (lines 128–181). It hypothesizes outdated hooks/patterns (lines 183–198).

---
