# Explorer white panes research: discovery

Scope: read-only investigation of reliable native drawing paths for Windows 11 build 26200 Explorer white regions: preview pane, unselected navigation items, and other shell panes. Preserve hover/selection visuals. Research is for ThemeStudio 0.6.2; no product code, system state, injection, installation, or downloaded program execution is allowed.

## Discovery checkpoints

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: `vendor/windhawk-mods/mods/explorer-visual-tweaks-dark.wh.cpp` and `explorer-treeitem-tweaker.wh.cpp`
**Method**: local source read (PowerShell `rg`/`Get-Content`)
**Confidence**: high
**Insight**: Existing 0.6.2 candidate source leaves ordinary TreeView state to the original theme, while a separate TreeItem Tweaker provides reliable item resolution and state-specific theme hooks tested through Win11 25H2. Because the field-tested 0.6.1 runtime did not enable this candidate mod, this is an implementation observation rather than a confirmed cause of the user photograph.

# Relevant extracted content

> `explorer-visual-tweaks-dark` passes normal TreeView state through; `explorer-treeitem-tweaker` resolves actual `HTREEITEM` and draws states 2/3/5/6 with GDI+.

---

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://github.com/VitalSkib/readingpane-stripe-removal and https://raw.githubusercontent.com/VitalSkib/readingpane-stripe-removal/main/readingpane-stripe-removal.cpp
**Method**: query-search/browser-rendered (via `web__run`)
**Confidence**: high
**Insight**: A narrowly scoped internal-DUI call-stack suppression exists for Preview Pane artifacts, but its tested builds and hard-coded offsets do not cover Windows 11 build 26200 without fresh verification.

# Relevant extracted content

> The source identifies one DUI object by vtable and a field value, then suppresses only nested `FillRect` calls during that object's `PaintBackground`.

---

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/controls/nm-customdraw-tree-view and https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-erasebkgnd
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: Microsoft’s documented primitives support state-aware TreeView item custom draw and host-window background erasure handling, which are safer boundaries than process-wide FillRect color replacement.

# Relevant extracted content

> TreeView uses `NM_CUSTOMDRAW`/`NMTVCUSTOMDRAW`; `WM_ERASEBKGND` is the class-background fallback and can be handled by a targeted subclass.

---

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://github.com/VitalSkib/explorer-visual-tweaks-dark
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: The upstream README documents a Preview Pane background fix and its limits, while the current raw source must be checked separately because the README claims direct value patching that is not visible in the fetched source.

# Relevant extracted content

> README claims a `DUI70.dll` `DirectUI::Element::PaintBackground` fix and warns that third-party preview handlers may draw their own surfaces.

---

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://github.com/Maplespe/explorerTool
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: ExplorerBgTool is a main ItemView renderer only; its source does not name TreeView item states, Preview Pane hosts, or header/status-row targets.

# Relevant extracted content

> The README and native source focus on `ItemView`, `DirectUIHWND` under `SHELLDLL_DefView`, and `FillRect`/`AlphaBlend`.

---

**Time**: 2026-10-05, local Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/controls/nm-customdraw-tree-view and https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-erasebkgnd
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: Microsoft’s supported primitives are state-aware TreeView custom draw and host-window `WM_ERASEBKGND` handling; both preserve a clear boundary around the actual target HWND/state.

# Relevant extracted content

> TreeView custom draw uses `NM_CUSTOMDRAW`/`NMTVCUSTOMDRAW`; a class background is erased through `WM_ERASEBKGND` and can be replaced by a subclass handler.

---
