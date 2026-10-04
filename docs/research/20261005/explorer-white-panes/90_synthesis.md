# Explorer white panes research: synthesis

本轮结论只来自本目录的 checkpoint。现场配置边界必须先固定：父线程已核实 0.6.1 的 `runtime-managed.json` 只启用了 `themestudio-explorer-background` 与 `windows-11-file-explorer-styler`；本目录分析的 `explorer-visual-tweaks-dark`、`explorer-treeitem-tweaker` 等是候选源码，现场并未启用。因此下面关于 normal TreeView 漏处理、Preview class brush 或 DUI hook 的内容都是候选实现观察与可检验推断，不是现场白色区域的已确认根因。

## 最短可执行指引

**导航树未选中背景**：在与当前 `TreeItem Tweaker` 相同的 `uxtheme.dll` hook 中，只命中 `IsTreeViewTheme(hTheme)`、`iPartId == TVP_TREEITEM`（数值 1）和 `iStateId == TREIS_NORMAL`（数值 1）；按现有 `ResolveItemFromDrawContext`/`MakeAdjustedRect` 定位 item。对该状态绘制透明背景并返回 `S_OK` 以露出底图，或绘制主题深色 fallback。`TREIS_HOT`（2）、`TREIS_SELECTED`（3）、`TREIS_SELECTEDNOTFOCUS`（5）、`TREIS_HOTSELECTED`（6）必须保持现有分支和颜色，不能被 normal 分支覆盖；`DrawThemeBackground`、`DrawThemeBackgroundEx` 两个入口都要处理。

**Preview Pane**：优先按本地源码已证明的类名匹配 `Shell Preview Extension Host`、`Shell Preview Extension Host Previewer`；文本预览另有 `RICHEDIT50W`，主题颜色入口是 `ReadingPane` + `partId == 1` + `TMT_FILLCOLOR`。在 `CreateWindowExW` 命中目标 HWND 后，用目标线程的 `SetWindowSubclass`/Windhawk `SetWindowSubclassFromAnyThread` 安装可移除 subclass；仅处理 `WM_ERASEBKGND`（`wParam` 是 HDC，绘制主题/底图色并返回非零），其余消息调用 `DefSubclassProc`，在 `WM_NCDESTROY` 与卸载阶段 `RemoveWindowSubclass`，再 `RedrawWindow` 清除残留。DUI `PaintBackground`/`FillRect` 抑制只在 26200 的 vtable/offset 经过现场符号验证后启用。

## 最可靠的导航树修复边界

作为候选实现观察，`explorer-visual-tweaks-dark.wh.cpp` 的 `Selection::HandleDrawThemeBackground` 只处理 `TREIS_HOT`、`TREIS_SELECTED`、`TREIS_SELECTEDNOTFOCUS`、`TREIS_HOTSELECTED`；对 `TREIS_NORMAL` 等状态，它直接调用 `g_origDrawThemeBackground`。这说明“若启用该候选 mod，normal 行仍可能由原生主题填充”，不能把它归因成现场 0.6.1 的已确认原因。[本地源快照](source/explorer-visual-tweaks-dark.wh.cpp)（checkpoint 1）

更适合复用的是 `explorer-treeitem-tweaker.wh.cpp` 的 TreeView 状态绘制链。它的关键函数是：

- `ResolveItemFromDrawContext(HWND hTree, INT iStateId, const RECT* pRect)`：按 hover 光标、TreeView selection、状态 ID 和绘制矩形解析 `HTREEITEM`。
- `GetContentBasedRect(HDC hdc, INT iStateId, const RECT* pRect)` / `MakeAdjustedRect`：保留当前绘制的垂直位置，只调整背景横向边界。
- `HandleTreeDraw(HDC hdc, INT iPartId, INT iStateId, LPCRECT pRect)`：使用 GDI+ 圆角路径绘制填充/边框。
- `HookedDrawThemeBackground` 与 `HookedDrawThemeBackgroundEx`：只在 TreeView theme、`iPartId == 1` 时接管并返回 `S_OK`。

当前候选 `GetStyleForState` 只返回 2、3、5、6；把 state 1 加入 `NormalState` 是一个可复用的实现扩展点。建议默认 `NormalState.Background.Enabled=true`、`Background.Opacity=0`，这样会抑制原生白色背景而露出已经绘制的图片；如果某个窗口没有图片底图，再把 opacity 设为主题深色。已有 selected/hover 状态保持原值和原分支，避免改变用户现在认可的选中效果。`HandleTreeDraw` 不能在 normal style disabled 时回退原生绘制，否则白色会再次出现；需要用“启用但透明”的样式表达“跳过原生背景”。这仍需在实际启用的两个 mod 配置下验证。[TreeItem Tweaker 源快照](source/explorer-treeitem-tweaker.wh.cpp)（checkpoint 2）

这条路径比 `explorerTool` 的通用 `FillRect` 更可靠，因为它命中 `TreeView` 的具体 `TVP_TREEITEM`/state/rect，并且保留了 hover、selected、selected-not-focus 的分支。Microsoft 的 `NM_CUSTOMDRAW` 也支持父窗口在 `CDDS_ITEMPREPAINT` 中使用 `NMTVCUSTOMDRAW`，返回 `CDRF_SKIPDEFAULT` 来完全接管单项绘制；但 Explorer 是否把导航 TreeView 的通知可靠转交给可控 parent，需要在目标 build 实测。因此现有 `DrawThemeBackground` 路径是首选，`NM_CUSTOMDRAW` 是备用验证路线。[Microsoft TreeView custom draw](https://learn.microsoft.com/en-us/windows/win32/controls/nm-customdraw-tree-view)（checkpoint 11）

`explorer-navigation-pane-tweaks.wh.cpp` 只把 `TVP_TREEITEM` 的 rect/clip 左边界平移来补偿树缩进，保留原 `iStateId` 和原主题绘制；它不解决颜色白底，不应作为颜色后端。[本地源快照](source/explorer-navigation-pane-tweaks.wh.cpp)（checkpoint 1/21）

## Preview Pane 的可靠命中顺序

当前本地 `Preview` 命名空间处理三层：

1. 在 `RegisterClassExW_hook(const WNDCLASSEXW*)` 中匹配 `Shell Preview Extension Host`、`Shell Preview Extension Host Previewer`，替换 `hbrBackground`。
2. 在 `GetThemeColor_hook` 中匹配 `ReadingPane` theme、part 1、`TMT_FILLCOLOR`，返回配置颜色。
3. 只对 `prevhost.exe` 的 `RICHEDIT50W` 子窗口通过 `GetSysColor_hook` 和 `CreateWindowExW_hook` 处理文本预览。

Microsoft 文档说明，类 `hbrBackground` 会在 `WM_ERASEBKGND` 时准备客户端背景；如果 class brush 为 NULL，窗口自身必须处理 `WM_ERASEBKGND`。[About Window Classes](https://learn.microsoft.com/en-us/windows/win32/winmsg/about-window-classes) [WM_ERASEBKGND](https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-erasebkgnd)（checkpoint 10/13）因此现有类注册 hook 对“类尚未注册”有效，但如果 26200 的类已经注册、窗口由另一线程/宿主创建，或者预览 handler 自己绘制白色内容，仍会漏掉。官方 README 也承认第三方 handler 可自行绘制背景/内容。[VitalSkib README](https://github.com/VitalSkib/explorer-visual-tweaks-dark)（checkpoint 3）

可复用的补强顺序是：

- hook `CreateWindowExW`，只匹配上述两个 Preview Host 类名及已确认的 ReadingPane 子窗口；创建后在窗口所属线程安装 `SetWindowSubclass(HWND, SUBCLASSPROC, UINT_PTR, DWORD_PTR)`。
- subclass 中只处理 `WM_ERASEBKGND`，从 `wParam` 取得 HDC，在 client rect 中绘制配置的主题/底图色并返回非零；其余消息调用 `DefSubclassProc`。在 `WM_NCDESTROY` 移除 subclass。Microsoft 明确规定 `SetWindowSubclass` helper 不能跨线程，所以必须使用目标线程安装或 Windhawk 的跨线程 helper。[SetWindowSubclass](https://learn.microsoft.com/en-us/windows/win32/api/commctrl/nf-commctrl-setwindowsubclass)（checkpoint 12）。
- `WM_THEMECHANGED`、`WM_SETTINGCHANGE`、DPI/resize 后重新失效并按当前主题重绘；卸载时移除 subclass、恢复 class brush/brush ownership、`RedrawWindow` 清理残留像素。
- 对仍然白色的 empty state 继续定位实际 child class/`ReadingPane` theme，而不是扩大 `FillRect` hook。第三方 handler 的图像/媒体内容可能仍然白，这是外部 handler 边界。

VitalSkib README 宣称其 `DirectUI::Element::PaintBackground` 会直接修改 `DUI Value` 颜色；但同一仓库当前 raw source 的 hook 只保存 `g_currentPaintElement` 并原样调用 `g_origPaintBackground`，没有修改 `backgroundValue`。该 README/source 不一致必须在采用前钉住 commit 并重新审计。[README](https://github.com/VitalSkib/explorer-visual-tweaks-dark) [当前 raw source](https://raw.githubusercontent.com/VitalSkib/explorer-visual-tweaks-dark/main/explorer-visual-tweaks-dark.wh.cpp)（checkpoint 3/4）。

对于 Preview Pane 内部 stray fill，`readingpane-stripe-removal` 给出更精确的模板：`PaintBackground_hook` 先以 vtable 指针和 `fields[3] == 4` 命中特定 DUI 元素，只在原始 `PaintBackground` 调用期间设置线程标志，`FillRect_hook` 仅在该标志下返回 TRUE。这个模式可以避免全局颜色猜测，但其 `dui70.dll` 偏移 `0xD920`、`0x1037C0` 只对应作者测试的 26220/26300 Insider build；不能直接用于 26200，必须先做 build-specific symbol/offset 验证。其 `Wh_ModUninit` 为空，也不能直接作为完整恢复实现。[README](https://github.com/VitalSkib/readingpane-stripe-removal) [source](https://raw.githubusercontent.com/VitalSkib/readingpane-stripe-removal/main/readingpane-stripe-removal.cpp)（checkpoint 15/16）。

## Status bar、Details header 与 ExplorerBgTool 边界

状态栏可以复用本地 `explorer-info-bar.wh.cpp` 的时序：`RefreshValidatedStatusRow` 找同进程/同线程的 `SHELLDLL_DefView` 并把其 bottom 映射为 status row；`DirectUiSubclassProc` 先让 `DefSubclassProc` 完成所有 native buffered paint，再用 DC 调 `PaintFinalInfoBar`；卸载时移除 subclass 并 `RedrawWindow` 清除覆盖像素。[Info Bar 源快照](source/explorer-info-bar.wh.cpp)（checkpoint 20）这比在 `DirectUIHWND` 上最后一层泛化填充安全，并且 `PickBackgroundColor` 会在未选中行从 native pixels 采样主题色。

本地搜索未找到一个已验证的现代 Details column header 背景 painter。`file-explorer-details-autofit-columns.wh.cpp` 只查找 `SysHeader32`、`HDM_GETITEMCOUNT` 和 `HDM_GETITEMRECT` 来计算列宽；classic Treeview 的 “header” 是旧式 Folder Band，不能当作现代 Details header 证据。（checkpoint 21）因此 header 需要先在 26200 目标窗口上确认 HWND/UIA/XAML 类型，再决定 `SysHeader32` subclass 或 WinUI style；当前不应把它和 TreeView/Preview Pane 共用一个 FillRect hook。

Maplespe ExplorerBgTool 只命中 `DirectUIHWND` 父为 `SHELLDLL_DefView` 的主 ItemView，通过 `MyFillRect` + `AlphaBlend` 绘制图片。它没有 TreeView state resolver、Preview Host 类名、ReadingPane theme、status-row 几何验证或 Details header target。[README](https://github.com/Maplespe/explorerTool/blob/main/README.md) [dllmain.cpp](https://raw.githubusercontent.com/Maplespe/explorerTool/main/ExplorerBgTool/dllmain.cpp)（checkpoint 6/7）因此保留为主文件区底图后端即可，不能用来修复本轮白色 pane。

## 26200 build 门槛与恢复

官方 styling-guide issue #79 报告 build `26200.8737` 上 File Explorer Styler 可能让 Explorer 回退到 legacy Win32 UI、Preview Pane 显示 “Preview not available”，禁用 mod 后立即恢复。它是用户报告而非根因确认，但足以要求 26200 build gating：启用任何 DUI70/XAML private hook 前记录 build/exports/offsets，并提供 Windhawk disable + Explorer restart 的回滚路径。[Issue #79](https://github.com/ramensoftware/windows-11-file-explorer-styling-guide/issues/79)（checkpoint 19/22）

卸载/恢复要覆盖三类状态：

- TreeView：移除 `DrawThemeBackground`/`DrawThemeBackgroundEx` hooks，取消 tracked TreeView state，重绘受影响 item/TreeView；保留现有 selected/hover 状态的恢复。
- Preview：移除窗口 subclass，释放 class brush/临时 GDI brush，恢复或重新注册 class brush，`RedrawWindow`/重启 Explorer 与相关 preview host。微软文档指出 subclass 必须在拥有窗口的线程处理。[SetWindowSubclass](https://learn.microsoft.com/en-us/windows/win32/api/commctrl/nf-commctrl-setwindowsubclass)（checkpoint 12）。
- Status row：按 Info Bar+ 顺序移除 subclass，再 `RedrawWindow` 已验证 row，防止 overlay 残留。

本轮没有安装、编译、注入、运行 DLL 或修改系统；26200 上的命中和偏移仍需后续专门验证。

## 交付物

- [10_discovery.md](10_discovery.md)
- [20_sources.md](20_sources.md)
- [source/](source/)：本地相关 Windhawk 源码与 HTTPS 获取的 VitalSkib/Maplespe 纯文本快照，无二进制。
