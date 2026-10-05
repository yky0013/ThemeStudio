# Explorer Details header visual-style research

Scope: Microsoft official documentation and SDK source for `HEADERPARTS`, `HEADERITEMSTATES`, `HEADERITEMLEFTSTATES`, `HEADERITEMRIGHTSTATES`, and `HEADERSORTARROWSTATES`, with an implementation recommendation that changes only idle background treatment while preserving interaction states and glyph rendering.

## Source checkpoint 1 — Microsoft Learn discovery

**Time**: 2026-10-05, Asia/Shanghai
**Source**: Microsoft Learn search results for `HEADERPARTS`, `HEADERITEMSTATES`, and header visual styles; official URLs surfaced: https://learn.microsoft.com/en-us/windows/win32/controls/using-visual-styles, https://learn.microsoft.com/en-us/windows/win32/controls/header-controls, https://learn.microsoft.com/en-us/windows/win32/controls/header-control-reference
**Method**: query-search (via web-search skill / web.run, domain-filtered Microsoft Learn queries)
**Confidence**: high
**Insight**: The official Learn results establish the relevant path: header controls use visual styles, headers contain column items, and the header reference includes dropdown notifications. The enum-specific pages were not returned by search, so the next checkpoints use their canonical Microsoft Learn URLs and the Microsoft SDK source.

# Relevant extracted content

> `Using Visual Styles with Custom and Owner-Drawn Controls` says visual-style parts are defined in `Vssym32.h`, backgrounds are drawn with `DrawThemeBackground`/`DrawThemeBackgroundEx`, and control text color is application-defined by state.

> `About Header Controls` describes a header as a window above columns, with separate header items and mouse interactions that show an item in a pressed state.

> `Header Control Reference` lists `HDN_DROPDOWN` as the notification sent when a header control's drop-down arrow is clicked.

---

## Source checkpoint 2 — Microsoft Learn Parts and States

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/controls/parts-and-states
**Method**: query-search (via web-search skill / web.run; Microsoft Learn result `Parts and States`)
**Confidence**: high
**Insight**: Microsoft’s canonical parts/states table confirms that `HEADER` exposes `HP_HEADERITEM`, `HP_HEADERITEMLEFT`, `HP_HEADERITEMRIGHT`, `HP_HEADERSORTARROW`, plus `HP_HEADERDROPDOWN` and `HP_HEADERDROPDOWNFILTER`. It lists the full `HIS_*` set, but only three states for left/right pieces and two states for the sort arrow. This supports routing the idle background through the item part while preserving separate arrow/dropdown pieces.

# Relevant extracted content

> The page states that values are defined in `Vsstyle.h` and `Vssym32.h`, and that an image is selected at run time with the 1-based `iStateId` for the relevant part.

| Class | Part | States listed by Microsoft |
|---|---|---|
| `HEADER` | `HP_HEADERDROPDOWN` | `HDDS_HOT`, `HDDS_NORMAL`, `HDDS_SOFTHOT` |
| `HEADER` | `HP_HEADERDROPDOWNFILTER` | `HDDFS_HOT`, `HDDFS_NORMAL`, `HDDFS_SOFTHOT` |
| `HEADER` | `HP_HEADERITEM` | `HIS_HOT`, `HIS_ICONHOT`, `HIS_ICONNORMAL`, `HIS_ICONPRESSED`, `HIS_ICONSORTEDHOT`, `HIS_ICONSORTEDNORMAL`, `HIS_ICONSORTEDPRESSED`, `HIS_NORMAL`, `HIS_PRESSED`, `HIS_SORTEDNORMAL`, `HIS_SORTEDHOT`, `HIS_SORTEDPRESSED` |
| `HEADER` | `HP_HEADERITEMLEFT` | `HILS_HOT`, `HILS_NORMAL`, `HILS_PRESSED` |
| `HEADER` | `HP_HEADERITEMRIGHT` | `HIRS_HOT`, `HIRS_NORMAL`, `HIRS_PRESSED` |
| `HEADER` | `HP_HEADERSORTARROW` | `HSAS_SORTEDDOWN`, `HSAS_SORTEDUP` |

---

## Source checkpoint 3 — Microsoft win32metadata source tree / `vssym32.h`

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://github.com/microsoft/win32metadata/blob/main/generation/WinSDK/RecompiledIdlHeaders/um/vssym32.h
**Method**: extract (via PowerShell `Invoke-WebRequest` against the raw Microsoft GitHub source after querying the repository tree)
**Confidence**: high
**Insight**: The Microsoft repository contains the Windows SDK visual-style headers under `generation/WinSDK/RecompiledIdlHeaders/um`. The current `vssym32.h` is the visual-style property symbol header; the `HEADERPARTS` and header-state enum definitions are in the sibling `vsstyle.h` source checkpoint below, which `vssym32.h` includes.

# Relevant extracted content

> Repository tree result: `generation/WinSDK/RecompiledIdlHeaders/um/vssym32.h` and `.../vsstyle.h` are Microsoft-owned source files. The raw `vssym32.h` begins with the VisualStyle Core Win32/ComCtl32 symbols header guard and includes `VSStyle.h`.

---

## Source checkpoint 4 — Microsoft Windows SDK `vsstyle.h` header enums

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://github.com/microsoft/win32metadata/blob/main/generation/WinSDK/RecompiledIdlHeaders/um/vsstyle.h#L621-L688 (raw: https://raw.githubusercontent.com/microsoft/win32metadata/main/generation/WinSDK/RecompiledIdlHeaders/um/vsstyle.h)
**Method**: extract (via PowerShell `Invoke-WebRequest` against the raw Microsoft GitHub source)
**Confidence**: high
**Insight**: The Microsoft SDK source gives the exact numeric IDs and names. `HP_HEADERITEM` is part 1; `HP_HEADERITEMLEFT`, `HP_HEADERITEMRIGHT`, and `HP_HEADERSORTARROW` are parts 2–4; dropdown/filter/overflow are parts 5–7. `HIS_*` is a 12-state set; left/right pieces each have 3 states; the sort arrow has two direction states; dropdown and dropdown-filter each have Normal, SoftHot, and Hot.

# Relevant extracted content

```text
VSCLASS_HEADER = L"HEADER"

HEADERPARTS
  HP_HEADERITEM          = 1
  HP_HEADERITEMLEFT      = 2
  HP_HEADERITEMRIGHT     = 3
  HP_HEADERSORTARROW     = 4
  HP_HEADERDROPDOWN      = 5
  HP_HEADERDROPDOWNFILTER= 6
  HP_HEADEROVERFLOW      = 7

HEADERITEMSTATES
  HIS_NORMAL             = 1
  HIS_HOT                = 2
  HIS_PRESSED            = 3
  HIS_SORTEDNORMAL       = 4
  HIS_SORTEDHOT          = 5
  HIS_SORTEDPRESSED      = 6
  HIS_ICONNORMAL         = 7
  HIS_ICONHOT            = 8
  HIS_ICONPRESSED        = 9
  HIS_ICONSORTEDNORMAL   = 10
  HIS_ICONSORTEDHOT      = 11
  HIS_ICONSORTEDPRESSED  = 12

HEADERITEMLEFTSTATES:  HILS_NORMAL = 1, HILS_HOT = 2, HILS_PRESSED = 3
HEADERITEMRIGHTSTATES: HIRS_NORMAL = 1, HIRS_HOT = 2, HIRS_PRESSED = 3
HEADERSORTARROWSTATES: HSAS_SORTEDUP = 1, HSAS_SORTEDDOWN = 2
HEADERDROPDOWNSTATES:  HDDS_NORMAL = 1, HDDS_SOFTHOT = 2, HDDS_HOT = 3
HEADERDROPDOWNFILTERSTATES: HDDFS_NORMAL = 1, HDDFS_SOFTHOT = 2, HDDFS_HOT = 3
HEADEROVERFLOWSTATES: HOFS_NORMAL = 1, HOFS_HOT = 2
```

---

## Source checkpoint 5 — Microsoft Learn state-selection semantics

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/controls/parts-and-states
**Method**: browser-rendered (via web-search skill / web.run `open`, lines 30–37 and 119–125)
**Confidence**: high
**Insight**: Microsoft defines a part as a drawable area such as text, shape, image, or line; states select different background images, and `iStateId` is a 1-based index. Therefore an idle-only recolor must change the normal state asset or its painting path while leaving other state IDs and independent parts intact. The page also states that state 0 is only for parts with no defined states, so it is not a safe substitute for a header item’s `HIS_NORMAL`/sorted/icon-normal states.

# Relevant extracted content

Microsoft 说明，多数控件部件包含不同的视觉状态。

Microsoft 将不同状态关联到背景图像，运行时通过从 1 开始的 iStateId 索引选择对应图像。

> The table lists `HEADER` as: `HP_HEADERDROPDOWN` → `HDDS_*`; `HP_HEADERDROPDOWNFILTER` → `HDDFS_*`; `HP_HEADERITEM` → `HIS_*`; `HP_HEADERITEMLEFT` → `HILS_*`; `HP_HEADERITEMRIGHT` → `HIRS_*`; `HP_HEADERSORTARROW` → `HSAS_*`.

---

## Scoped conclusion for ThemeStudio header split

The official numeric mapping is:

| Target | Part/state IDs | Meaning relevant to the requested idle-only change |
|---|---:|---|
| Main header item | `HP_HEADERITEM=1`; `HIS_NORMAL=1`, `HIS_SORTEDNORMAL=4`, `HIS_ICONNORMAL=7`, `HIS_ICONSORTEDNORMAL=10` | Idle item backgrounds for unsorted, sorted, icon, and sorted-icon variants. The `SORTED` and `ICON` qualifiers are independent visual conditions; `HOT`/`PRESSED` variants remain 2/3, 5/6, 8/9, and 11/12. |
| Left edge fragment | `HP_HEADERITEMLEFT=2`; `HILS_NORMAL=1` | Idle left fragment. Keep `HILS_HOT=2` and `HILS_PRESSED=3`. |
| Right edge fragment | `HP_HEADERITEMRIGHT=3`; `HIRS_NORMAL=1` | Idle right fragment. Keep `HIRS_HOT=2` and `HIRS_PRESSED=3`. |
| Sort arrow | `HP_HEADERSORTARROW=4`; `HSAS_SORTEDUP=1`, `HSAS_SORTEDDOWN=2` | Directional sort glyph. Leave this native so arrow shape/contrast stays intact. |
| Dropdown | `HP_HEADERDROPDOWN=5`; `HDDS_NORMAL=1`, `HDDS_SOFTHOT=2`, `HDDS_HOT=3` | Dropdown button normal, soft-hover, and hot states. Preserve all three. |
| Dropdown filter | `HP_HEADERDROPDOWNFILTER=6`; `HDDFS_NORMAL=1`, `HDDFS_SOFTHOT=2`, `HDDFS_HOT=3` | Filter-dropdown equivalent. Preserve all three. |
| Overflow | `HP_HEADEROVERFLOW=7`; `HOFS_NORMAL=1`, `HOFS_HOT=2` | Overflow button normal/hot states. Preserve both. |

Recommendation: apply the idle background replacement only to `HP_HEADERITEM` states `1/4/7/10` and the `HP_HEADERITEMLEFT`/`HP_HEADERITEMRIGHT` normal states `1`, while preserving the native text/glyph drawing and all `HOT`/`PRESSED` state paths. Do not replace `HP_HEADERSORTARROW` or dropdown parts as part of this color change. The supplied Explorer trace records `part 1/state 4` as the white sorted Name header, `part 0/state 1` as the full strip, `part 4/state 1` as the arrow, and `part 5/state 1` as the dropdown; `part 0` is the shared higher-level area described by Microsoft’s state-selection page, not a named `HEADERPARTS` item, so it should remain a separately audited strip target.

Official references: [Parts and States](https://learn.microsoft.com/en-us/windows/win32/controls/parts-and-states), [Microsoft Windows SDK `vsstyle.h`](https://github.com/microsoft/win32metadata/blob/main/generation/WinSDK/RecompiledIdlHeaders/um/vsstyle.h#L621-L688), [Using Visual Styles with Custom and Owner-Drawn Controls](https://learn.microsoft.com/en-us/windows/win32/controls/using-visual-styles), [About Header Controls](https://learn.microsoft.com/en-us/windows/win32/controls/header-controls), and [Header Control Reference](https://learn.microsoft.com/en-us/windows/win32/controls/header-control-reference).

---
