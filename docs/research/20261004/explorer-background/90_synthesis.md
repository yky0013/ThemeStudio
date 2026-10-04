# Explorer background research: synthesis

研究范围：ThemeStudio（Python backend + C# WebView2 host + Windhawk runtime）需要在 Windows 11 File Explorer 中绘制图片背景，并让文件列表区可见，同时提供深色半透明面板。结论只使用本目录的 `10_discovery.md` 与 `20_sources.md` checkpoint；没有安装、注入、启动或修改系统。

## 可行性结论

`ExplorerBlurMica` 本身不能满足“图片 + 文件列表区”。它公开的设置只有 Blur/Acrylic/Mica、颜色 RGBA、清除地址栏/滚动条/WinUI 背景等字段，没有图片路径、`ImageBrush`、图片透明度或 ItemView 图片配置。它适合作为既有 Mica/Acrylic 后端，不适合作为图片后端。[ExplorerBlurMica README](https://github.com/Maplespe/ExplorerBlurMica/blob/main/README.md)（checkpoint 3/11/16）

真正直接绘制 Explorer 文件列表背景的成熟源码候选是 Maplespe 的 **ExplorerBgTool / explorerTool**。其 README 明确写的是 `Customize Explorer ItemView background image`，支持图片位置、缩放/填充、alpha、随机图片、按路径选择图片，并覆盖 Windows 10/11；源码在 `DirectUIHWND`/`SHELLDLL_DefView` 下的窗口上拦截 `FillRect`，通过 GDI+ 位图和 `AlphaBlend` 绘制。[ExplorerBgTool README](https://github.com/Maplespe/explorerTool/blob/main/README.md)（checkpoint 1）[dllmain.cpp](https://raw.githubusercontent.com/Maplespe/explorerTool/main/ExplorerBgTool/dllmain.cpp)（checkpoint 4）

现代 Win11 WinUI 区域可以由官方 Windhawk File Explorer Styler 补齐：官方 styling guide 给出 `Grid#DetailsViewControlRootGrid` 这个 Details view 根节点，并明确支持 `ImageBrush Stretch="UniformToFill" ImageSource="<image>"`，其中 `<image>` 可以是本地文件路径或 URL。[styling guide](https://github.com/ramensoftware/windows-11-file-explorer-styling-guide)（checkpoint 19）这条路线是 XAML 目标级样式，不能单独证明已经覆盖所有 File Explorer 客户端区域；文件列表宿主在 Win11 25H2 仍可能是 `UIItemsView`/`ItemsView`/`DirectUIHWND`，官方 Windhawk 源码也说明 tabbed Explorer 会把 `SHELLDLL_DefView` 嵌在 DirectUI host 下。[official file-list host source](https://raw.githubusercontent.com/ramensoftware/windhawk-mods/main/mods/explorer-nav-dragover-fix.wh.cpp)（checkpoint 18）

因此，最可行的工程方向是一个混合后端：ExplorerBgTool 的 native ItemView 绘制链覆盖文件列表，再由 Windhawk Styler 的 XAML `ImageBrush`/`WindhawkBlur`/半透明 brush 覆盖 WinUI 面板。这个组合是基于源码结构的实现建议，尚未在 ThemeStudio 目标机器上运行验证；不能把它表述为已经完成的全窗效果。

## 候选对比

| 方案 | 图片背景 | 文件列表区 | Win11 证据 | 安装/卸载与权限 | 许可证与复用判断 |
|---|---|---|---|---|---|
| ExplorerBlurMica | 未发现图片字段；只支持 Blur/Acrylic/Mica 和颜色 | 未证明图片绘制 | README 支持 Win10/11；2.0.1 发布说明提到 Win11 Preview 23H2/24H2 兼容修复 | `register.cmd` / `regsvr32`，管理员；`uninstall.cmd` / `regsvr32 /u`；ESC 紧急绕过 | 根 `LICENSE` 是 GPLv3，而 README/源文件头写 LGPLv3，许可证状态冲突；不应直接复制，且功能不匹配 |
| ExplorerBgTool | 已明确支持 PNG/JPG、alpha、位置、stretch/zoom-fill、随机、按路径 | README 直接称 ItemView；源码绘制 `DirectUIHWND` | README 宣称 Win10/11；当前官方 Windhawk 源码证明 Win11 25H2 仍使用 DirectUI ItemsView host，但实际 paint 命中仍需验证 | COM/BHO DLL；注册写 HKCR/HKLM，需管理员；`DllUnregisterServer` 删除对应键；ESC 可跳过 hook | MIT；保留版权/许可声明即可复用。随附 MinHook 需保留其 BSD 条款 |
| Windhawk File Explorer Styler | `ImageBrush` 可用本地路径/URL；`WindhawkBlur`/AcrylicBrush 可做半透明 XAML brush | 明确有 Details view XAML 根；不覆盖所有 DirectUI/非 WinUI 区域 | 官方 guide 与官方 mod source；mod 当前 GPLv3 | 由 Windhawk 运行 mod；本调研未安装或执行 | GPLv3；适合通过 Windhawk 配置/扩展边界使用，复制代码到 ThemeStudio 前需处理 GPL 义务 |
| Microsoft 官方 API | 没有已验证的自定义 File Explorer 图片背景 API | 无 | Microsoft WinUI issue 明确说 File Explorer 等系统应用目前只有固定 Mica/Acrylic 背景 | 不适用 | 不能作为实现依赖 |

## ExplorerBgTool 的源码实现链

`dllmain.cpp` 的关键字段是 `imgPosMode`、`isRandom`、`isCustom`、`imgAlpha`、`folder` 和 `imageList`。`LoadSettings` 读取 `[image] random/custom/folder/posType/imgAlpha`，枚举 `*.png`/`*.jpg`，用 `BitmapGDI` 缓存图片。[source snapshot](source/dllmain.cpp)（对应 checkpoint 4）

`OnWindowLoad` 初始化 GDI+，再用 MinHook 拦截 `CreateWindowExW`、`DestroyWindow`、`BeginPaint`、`FillRect`、`CreateCompatibleDC`。`MyCreateWindowExW` 只记录父级为 `SHELLDLL_DefView` 的 `DirectUIHWND`，再检查 `ShellTabWindowClass` 或 `#32770` 上层窗口。`MyFillRect` 先调用原始 `FillRect`，然后裁剪 paint rect，计算七种位置模式，创建 `BLENDFUNCTION`，最后调用 `AlphaBlend`。[dllmain.cpp](source/dllmain.cpp) [HookDef.h](source/HookDef.h)

图片加载使用 GDI+ `Bitmap::FromStream`、`SHCreateMemStream`、compatible DC 和 `HBITMAP`；依赖 `GdiPlus.lib`、`Msimg32.lib`、`shlwapi.lib` 和 MinHook。[WinAPI.cpp](source/WinAPI.cpp) [WinAPI.h](source/WinAPI.h) [MinHook.h](source/MinHook.h)

这段源码有两个边界：它支持 `imgAlpha`，但没有独立的“深色面板颜色/模糊半径”字段；原项目也没有证明自带 XAML 面板叠层。因此深色面板应由预合成图片（例如 ThemeStudio 先把黑色 alpha 层合入图像），或后续 native renderer 增加颜色叠层；后者是新实现，不能当作 ExplorerBgTool 已有功能。

## 推荐的 ThemeStudio 适配边界

建议把 Python backend/C# WebView2 host 用作配置与预览层，把实际绘制交给 Windhawk 管理的 native mod：

1. 将 ExplorerBgTool 的 MIT 图像加载、窗口识别、位置计算和 `AlphaBlend` 逻辑作为复用候选；优先移植 renderer，保留 `ShellLoader.cpp` 作为独立 DLL 注册方案的参考。Windhawk 管理的进程内生命周期可以避免 ThemeStudio 自己维护 COM/BHO 注册键，但这一步是未来实现方案，尚未编译或运行。
2. 对 `SHELLDLL_DefView`、`DirectUIHWND`、`UIItemsView`、`ItemsView` 建立运行时日志和 fallback。当前官方源码只证明这些类名存在于目标树，不能保证所有 Win11 build 的 `FillRect` 绘制路径相同。
3. 为 WinUI 区域生成 File Explorer Styler 的 `controlStyles`：Details view root 使用 `Background:=<ImageBrush Stretch="UniformToFill" ImageSource="..." />`；需要暗色时，再为可单独定位的 XAML panel 使用带 alpha 的 `SolidColorBrush` 或 `WindhawkBlur`。每个 target 都要记录“命中/未命中”，不要把 XAML 顶部样式结果当成 ItemView 已覆盖。
4. 卸载路径要在 UI 中可见并可回滚：Windhawk mod disable/unload；若采用独立 ExplorerBgTool DLL，则管理员执行 `regsvr32 /u`，确认 `HKCR\CLSID`、Explorer BHO 和 FolderExtensions 注册键被删除，再重启 Explorer。ExplorerBgTool 的 ESC 绕过逻辑可作为崩溃恢复设计参考。

## 必须保留的风险与验证项

- **Win11 build 风险**：ExplorerBgTool 仓库已归档，README 的“Windows 11”说明来自旧版本；官方当前源码只提供窗口树形态证据，未提供 ExplorerBgTool 在 23H2/24H2/25H2 上的现场结果。必须在目标 build 上逐项验证 Home、Details、large/small icons、list、Gallery、tab、文件选择器和窗口缩放。
- **覆盖范围风险**：ExplorerBgTool README 说的是 ItemView；Windhawk guide 说的是 WinUI targets。两者合并前，需通过窗口树、paint 日志和截图确认导航栏、命令栏、文件列表、空白区、滚动后区域都符合预期。
- **稳定性风险**：作者明确警告无效 PNG/JPG 可能导致 Explorer 崩溃，并提供 ESC 绕过。注册 DLL 直接写 HKLM/HKCR，不能把它当成无权限的纯用户层效果。
- **许可证风险**：ExplorerBgTool 是 MIT；MinHook 的头文件带有 BSD 风格保留条款；Windhawk Styler 是 GPLv3；ExplorerBlurMica 的根 LICENSE 与源头/README 存在 GPLv3/LGPLv3 冲突。若 ThemeStudio 分发二进制或复制源代码，需要在实现前完成许可证审查。
- **未完成验证**：本轮只完成源码/文档调研和文本快照，没有下载 release 二进制、编译 DLL、安装注册、启动 Explorer、注入进程或修改注册表。

## 交付物

- [10_discovery.md](10_discovery.md)：发现阶段 checkpoint。
- [20_sources.md](20_sources.md)：逐源证据、配置字段、函数、依赖、注册/卸载和许可证 checkpoint。
- [source/](source/)：通过 HTTPS 保存的 ExplorerBgTool 纯文本源码快照，无二进制。
- [90_synthesis.md](90_synthesis.md)：本结论、推荐混合架构、证据边界和后续验证矩阵。
