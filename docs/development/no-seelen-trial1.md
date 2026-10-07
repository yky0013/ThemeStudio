# NoSeelen 体验版 1

日期：2026-10-07（Asia/Shanghai）。用户要求：在独立分支移除 Seelen UI 的运行功能，保留其余 ThemeStudio 功能，交付安装包及完整试用清单；体验后再决定主线。

## 分支与范围

- 分支：`experiment/no-seelen-20261007`。
- 基线：ThemeStudio 0.6.4，主线提交 `b692673878190524ef11501075fd084411348154`，基线树 `3551f6d47b15748bed21f4214275f857c68a316b`。
- 移除 Seelen 引擎/服务/运行主题资源、Dock 与顶部栏入口、Mac 桌面切换、Seelen 设置读写及启停/恢复代码。
- 保留原已复用的界面/媒体源码及许可证；并非删除所有来自 Seelen 的源码。壁纸与视差继续使用已有组件。
- 保留鼠标、壁纸、图标、7 套主题、主题包导入导出、资源管理器背景、Windhawk、桌宠入口和统一应用/恢复。
- Windhawk 通用目录不再因 Seelen 任务栏占用而禁止任务栏模块；每项模块仍需实际兼容性验证。两个 Explorer 模块由专用页面管理。

## 安装与数据隔离

- 新 AppId：`2A8C2E70-74B7-4586-B297-88D40A6E4299`。
- 默认目录：`{Program Files}/ThemeStudio-NoSeelen`。
- 用户数据：`%LOCALAPPDATA%/ThemeStudio-NoSeelen`。
- 互斥锁：`Local\ThemeStudio.NoSeelen.Application`。
- 安装到已存在的其他版本目录会被拒绝。安装不自动启动程序或启用外观。
- 不接受主线更新，避免把实验版覆盖为主线。其他 Windhawk 引擎运行时拒绝激活本分支模块。
- 两个版本改变的是同一套 Windows 外观，用户应先恢复再切换体验；数据隔离不代表可以同时叠加修改同一外观。

## 构建与验证

已完成：

- TypeScript 检查通过。
- 27 项前端测试通过；包含安装身份隔离检查。
- 106 项后端测试通过；包含 Seelen 旧请求被拒绝、停机不触碰外部 Seelen、其他 Windhawk 引擎冲突检查、统一应用及恢复测试。
- Preact/Svelte 前端、PyInstaller 后端及 .NET 原生主程序编译通过。
- 主 EXE 的 `requireAdministrator` manifest 已从 PE 资源读取核对；文件版本为 `0.6.4.1`。
- Inno Setup 6.7.3 安装包编译完成。编译器官方文件 SHA-256 与原记录一致，签名有效。
- WebView2 引导器由原官方链接重新获取，微软签名有效；版本 1.3.275.13，固定 SHA-256 更新为 `aa38a8cfce6179b87181609b1c730a29eaf26138fc833af5759e67576770f3a3`。
- 发布目录运行组件只包含 `windhawk`；未发现 `seelen-ui.exe`、`slu.exe`、`slu-service.exe` 或 `sluhk.dll`。
- 浏览器实测 Seelen/Mac 桌面入口为零，Windhawk 状态区仍显示；页面无横向溢出。
- 离线清单包含 97 个主要试用点、645 条模块记录，通用列表可选 643 项。标记与备注刷新后保留；导出/导入功能由本地 JSON 提供。

未完成：

- 原生窗口启动验收被自动审批拒绝。被拒绝的是诊断宿主的只读 `--smoke-dir` 启动，工具返回 `blocked by policy`，未给出更具体的原因。未用其他启动途径绕过拒绝。
- 本次未进行安装/卸载生命周期回归、实际桌面应用、真实 Explorer 视觉验收或全部模组逐项验收。用户在试用清单中记录实际结果。

## 构建重现

1. `tools/setup.ps1` 准备固定前端/Python/WebView2 SDK 依赖。
2. 在 `.tools/inno-6.7.3` 放置原项目规定的 Inno Setup 6.7.3 便携编译器。
3. `tools/prepare-runtimes.ps1` 仅下载并展开固定 Windhawk 分发包。
4. `tools/fetch-bootstrapper.ps1` 下载并检查微软引导器。
5. `tools/build-installer.ps1` 生成 NoSeelen 独立安装包。

`tools/build.ts` 调用 `tools/build-trial-checklist.py`，以当前模块源码目录生成试用页/文本/JSON；生成文件不重复提交，随安装包发布。

Git HTTPS 传输在本机不可用。源码从对应提交的官方 codeload 归档恢复，并以本地导入提交做差异基线；远端实验分支通过 GitHub Git Data API 以真实主线提交为父提交同步。不得把本地导入提交 SHA 冒充远端提交。
