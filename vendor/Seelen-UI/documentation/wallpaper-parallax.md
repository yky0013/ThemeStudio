# 壁纸与视差组合

用户于 2026-09-27 同意采用“Seelen 播放图片/视频，复用 Windhawk 运动算法，在同一层内容上加入视差”的方案。本改动按该决定实现，不启动第二套独立壁纸渲染器。

## 已实现

- 使用 Seelen 原有 `ImageWallpaper.svelte` 和 `VideoWallpaper.svelte`，新增共享 `ParallaxLayer.svelte`。图片和视频都通过同一组平移/透视计算显示。
- 从 Windhawk **Parallax Wallpaper 0.9.0** 移植四套预设、浮动死区、临界阻尼弹簧、透视投影和恒定边缘补偿。原数学实现位于 `ramensoftware/windhawk-mods@682a7f72694eb768724bea8ef72b079aedd9c57b/mods/parallax-wallpaper.wh.cpp`，作者 HaVeN80，许可 MIT。
- 新增一页内的图片/视频预览、素材选择、效果开关、预设、强度、倾角、方向和暂停按钮。更改视差参数只调整包裹层，不替换视频元素或调用视频的 load/seek。
- 参数加入组合配置，能够保存草稿及导入导出。导入检查启用状态与 activeThemes 一致；融合视差与独立 `parallax-wallpaper` 模组同时选中时提示冲突。
- 原生壁纸管理器读取既有 `GlobalMouseMove` 和 `GetMousePosition`，按原始物理显示器矩形归一化坐标；沿用 Seelen 的遮挡/性能模式暂停。没有新增 Rust 命令或后端数据结构。
- 使用 Seelen 既有 `activeThemes` / `byTheme` 存储参数，增加内置主题 `@workbench/wallpaper-parallax`。

## 试用

运行项目根目录的 `启动壁纸视差预览.cmd`，或在开发工作台点击“壁纸＋视差”。勾选“开启组合视差”，在画面中移动鼠标。可使用示例图片、示例视频，或选择本地媒体。配置草稿保存参数；临时选择的本地媒体只用于预览，不会被打包进配置。

该页面直接挂载两份原 Seelen 媒体组件，不模拟 Tauri 的文件或系统接口。开发预览用显式的内存 URL/示例文件输入；原生环境保留原来的文件协议转换。

## 算法来源与差异

`libs/ui/shared/wallpaper-parallax/motion.ts` 对应上游的 `Preset`、`Normalized`、`AcceptInput`、`SpringAxis`、`Advance`、`Tilt`、`CoversViewport`、`PerspectiveZoom`、`PerspectiveMatrix`。CSS matrix3d 复用了上游平面投影的系数与矩阵排列。

渲染单位适配为 CSS 像素；没有移植 Windhawk 自身的 D3D11 窗口、图像解码线程、独立 HDR 色彩管理或 GPU 设备恢复。媒体解码和播放继续由 Seelen/WebView 完成。本效果是整层平移/倾斜，不是深度图或多层场景重建。

许可和上游作者说明见 [windhawk-parallax-MIT.txt](licenses/windhawk-parallax-MIT.txt)。原 C++ 源码与固定提交 ZIP 仍保留在相邻源码目录。

## 验证范围

共 18 项当前工作台测试通过，其中新增 8 项验证运动/帧率、死区、长暂停、负坐标屏幕、投影覆盖、配置及互斥条件。原生 Monitor.svelte 和 state.svelte.ts 通过 Svelte 编译检查。

浏览器实测包括：图片跟随运动、视频持续播放时的视差变换、暂停后切换预设保持播放位置、关闭效果恢复 identity/none 变换且视频继续播放、导出参数。

完整 Windows 原生程序尚未编译和运行；真实多屏、混合 DPI、桌面层级、系统全屏暂停及实际功耗需要在原生程序中验证。这里的编译检查不等同于完整 Seelen 工程构建。
