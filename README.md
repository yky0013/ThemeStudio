# 桌面主题工作室 · Theme Studio

## 0.6.4 排序列与分隔条修复

修复“名称”排序列白块、文件区两侧白色分隔条及表头悬停浅底浅字；真实 Explorer 本机核对通过。说明与边界见 [修订记录](docs/development/explorer-header-splitter-update.md)。安装/卸载及跨 Windows build 回归待完成，仍为 prerelease。

## 0.6.3 空预览与普通区域背景修订

补齐原生 Explorer 外层容器、缓冲画布、透明提示文字和滚动条路径，保留选中/悬停状态；修复独立天选姬恢复入口。详见 [修订说明](docs/development/transparent-surfaces-update.md)。真实 Explorer 现场视觉验收待完成，本版为 prerelease。

## 0.6.2 统一应用与两级恢复

修正 Explorer 导航栏普通背景和预览窗格白色填充；整套外观集中到一个应用入口，增加独立初始外观恢复，保留恢复上一次。实现与验证见 [修订说明](docs/development/unified-appearance-update.md) 和 [验证记录](docs/development/verification-0.6.2.json)。Explorer 现场注入验收仍待完成，发布标为测试版。

项目开发、调研、验证及交付同步见 [GitHub 同步流程](docs/development/github-sync-workflow.md)。[0.6.1 发布](https://github.com/yky0013/ThemeStudio/releases/tag/v0.6.1) · [0.5.1 发布](https://github.com/yky0013/ThemeStudio/releases/tag/v0.5.1)。

## 0.6.1 资源管理器图片主题修订

移除绝区零、明日方舟、蔚蓝档案三个内置套装；增加主题与资源管理器图片背景联动、实时预览及恢复功能。详见 `docs/development/explorer-image-update.md`。

一个独立的 Windows 主题项目。主设置界面在 Seelen UI 的结构和组件上开发，模组区使用 Windhawk 的卡片、选择和标题组件，加入真实 Windows 桌面快捷方式与 17 状态鼠标设置。所有日常设置在同一页，通过左侧导航定位。

## 0.6.0 资源管理器、桌宠与直接导入

- 新增独立资源管理器入口：16 个本地源码预设，应用前记录设置，支持恢复；不会停用其他已启用模组。本版入口限定 Windows 11 build 22621+，实际效果依 Windows 控件树而异，不承诺角色壁纸铺满文件列表。
- 新增桌宠库：导入已解压或已安装桌宠的 EXE 主程序，保存路径和文件校验值；用户点击后通过 Explorer 启动，不自动运行。保留整个原桌宠文件夹，模型包需由对应引擎导入。
- 内置十套主题改为静态壁纸，移除十段配套 MP4；用户仍可直接导入 GIF、动态 WebP、图片和视频，或导入带动态版的主题数据包。套装素材版本升为 2.1.0。
- 0.5.0 原文件完整保留；Git 标签 v0.5.0 对应从已验证增量源码恢复的累计改动。新版本另存为 0.6.0，不自动安装或启动。
- 桌宠来源与外观范围调研：`docs/research/20261001/`；验证范围与限制：`docs/development/0.6.0-changes.md`。

## 0.5.0 角色套装与原厂指针

- 按原有 10 套主题重制 120 款角色图标和 170 个鼠标状态；每个指针包含 32/48/64/96 像素版本及对应点击位置。
- 鼠标布局参考本机天选姬的角色加功能符号，预览可查看完整套装。角色素材由内置 imagegen 生成，原始提示词与图集保存在 assets/character-art。
- 检测到本机 ASUS TX 原厂文件时，鼠标区域显示恢复按钮；恢复前备份，支持撤销。没有这些本机文件时不显示该按钮，也不会用 Windows 默认冒充原厂。
- 原厂 OEM 美术文件不随安装包分发。安装、打开、预览保留原桌面；图标和鼠标仍需主动勾选后应用。

## 启动

在其他电脑上运行 `installers/ThemeStudio-0.6.1-Windows-x64-Setup.exe`，安装和程序启动都会请求管理员授权，用于公共桌面快捷方式修改及运行组件；安装路径可自行选择。开始菜单提供程序、图文教程和卸载入口，Windows“已安装的应用”也可卸载。开发目录仍可双击 `启动.cmd`，或运行 `release/ThemeStudio-0.6.1/ThemeStudio.exe`。程序自带图标/指针后端，无需先打开旧工作台，也不调用旧预览服务。运行需 Windows 的 .NET Framework 4.8 和 Microsoft Edge WebView2 Runtime；精简安装包内置微软官方 WebView2 引导安装器，仅在缺失运行库时联网下载；需要 Windows 10 2004 / 19041 或更新的 Intel / AMD 64 位系统，不面向 ARM。

卸载会保留已应用的外观、素材和备份；要恢复原外观请先在程序内恢复。

新项目数据保存在 `%LOCALAPPDATA%/ThemeStudio`；原工作台数据保持原位。关闭主窗口会关闭图标/指针后端；已经启用的桌面壁纸、Seelen 和 Windhawk 引擎继续运行，可在设置页停用。

当前版本：0.6.1。支持导入完整主题数据包和应用更新；图文教程位于 `docs/guide/index.html`，离线随程序安装。该版本的实现与验证记录见 `docs/development/0.4.0-changes.md` 和 `docs/development/0.4.0-verification.json`。

## 0.4.1 修复

- 安装和升级只部署程序，不自动启动程序或启停桌面引擎，保留用户原主题。
- 打开程序、刷新状态和预览只读取当前桌面；旧 Windhawk 配置不会因状态查询而被重新初始化。
- 一键应用默认只更换壁纸，鼠标指针与桌面图标必须主动勾选。
- 安装包使用明确的程序目录清单，不混入开发环境的演示数据或用户缓存。

## 0.4.0 新增

- 导入 `.tspack` / `.zip` 主题数据包后，套装直接加入一键主题库；支持完整套装导出、预览、静态或动态壁纸和配件应用。
- 数据包会校验素材、限制解压范围和大小；同包去重、新版本更新同一套装，保留历史资源供恢复使用。
- “应用更新”支持检查 GitHub 正式版本、显示说明、下载与取消、SHA-256 校验，以及启动安装向导；也可选择本地安装 EXE 与同目录 `.exe.sha256` 进行离线更新。
- 当前发布源匿名访问为 404，在线更新会说明不可用。后续需提供公开正式发布源；本次未发布安装包或更改仓库可见性。
- 数据包制作说明：[theme-pack-format.md](docs/theme-pack-format.md)。安装器构建自动生成配套 `.exe.sha256`。

## 0.3.1 新增

- 历史 0.3.1–0.5.0 的 10 套默认主题内置 1080p、12 秒静音循环 MP4（0.6.0 已移除这些配套视频），可选择静态或动态版本，预览支持播放/暂停。动态版由原插画生成缓慢运镜和柔光效果，并非角色动作视频。
- Windows 原生任务栏与 Mac 风格（Seelen 悬浮 Dock + 顶部工具栏）可独立切换；记住用户选择，应用其他组合时继续遵守。
- GIF、动态 WebP、APNG 在关闭视差时仍保持动画，支持暂停和继续。
- 动态模板与静态模板之间可恢复，播放失败时回滚模板；变更记录保存在本机。
- 验证记录见 `docs/development/0.3.1-verification.json`。

## 0.3.0 新增

- 10 套一键主题、配套壁纸/17 状态指针/12 款图标，应用前备份并支持恢复。
- 修复本地壁纸图片与视频的预览加载。
- 静态壁纸免后台播放器，设置窗口最小化时暂停渲染，非可见内容延迟加载。
- 新应用图标与精简安装包；保留模组编译能力。
- 验证与边界见 `docs/development/0.3.0-changes.md` 和 `docs/development/0.3.0-verification.json`。

## 已接入

- 桌面快捷方式：读取真实桌面列表，普通 PNG/JPG/WebP/BMP/GIF/TIFF/ICO 直接替换 .lnk/.url 图标；内部自动生成多尺寸 ICO，无独立转换工具；应用前备份，支持恢复和冲突检查。
- 全局鼠标：17 种状态、CUR/ANI、文件夹匹配、方案保存、大小和恢复。部分应用自行绘制的光标不跟随系统设置。
- 壁纸＋视差：复用 Seelen 图片/视频组件和移植的 Windhawk 运动算法；已接入真实 WorkerW 桌面背景层，支持图片/视频、全局鼠标视差、暂停、继续和停止恢复。
- Windhawk 模组：使用本地 644 个模组的实际源码解析元数据和预设，并用 Windhawk 卡片界面选择组合；调用匹配版本的原 CLI 实际编译本地源码、安装、启用和停用；界面分别报告启用状态与实际目标进程载入状态。
- Seelen 资源：用户已选择 Seelen Dock 和工具栏，接入官方稳定运行包的启用/停用及 Bubbles 主题应用；窗口管理器保持关闭。

任务栏/Dock 已由用户选择 Seelen，Windhawk 任务栏模组不会重复启用。其他重叠能力继续由用户选择，见 `config/feature-policy.json`。不会因使用某一套设置界面而自动启用其全部桌面组件。

## 源码结构

| 目录 | 职责 |
|---|---|
| `src/app/` | 新项目入口、产品界面、原生消息客户端 |
| `src/host/` | Windows 主窗口、WebView2、私有 stdio 后端连接 |
| `components/icon-workbench/` | 原图标/指针后端的项目内副本 |
| `components/image-to-ico/` | 内置图片转换器 |
| `vendor/Seelen-UI/` | 完整 Seelen 源码及已有整合，含新增导航展示接口 |
| `vendor/windhawk/` | 完整 Windhawk 源码，含提取的模组卡片展示接口 |
| `vendor/windhawk-mods/` | 完整固定版本模组源码与原解析器 |
| `vendor/runtime-sources/Seelen-UI-2.8.6/` | 官方运行包的完整匹配源码，与已有 UI/媒体组件版本分别追溯 |
| `config/` | 选型决策、构建依赖和运行包锁定信息 |
| `docs/` | 来源清单、改动说明、验证证据 |

## 构建

首次运行 `tools/setup.ps1`，准备当前项目的 npm、Python 依赖和固定 WebView2 SDK。SDK 版本、官方下载地址与 SHA-256 位于 `config/webview2-sdk.json`，校验后解压到 `.cache/webview2`。

```powershell
npm.cmd run check
npm.cmd test
npm.cmd run build
.\tools\package.ps1 -SkipFrontend
.\tools\build-installer.ps1 -SkipPackage
```

开发调试：运行 `tools/start-dev.ps1`，只在本机 4327 端口启动新项目的服务。发布 EXE 使用内嵌 WebView2 和自己的后端，不需要 Node/Python 开发环境。

## 来源与许可

来源导入清单：`docs/source-imports.json`、`docs/desktop-source-imports.json`。固定上游源码、作者声明和各自许可证保存在 `vendor/` 与 `licenses/`。新整合代码采用 AGPL-3.0-or-later；Windhawk 宿主及模组的原许可证仍分别适用，不能将全部模组统一视为 MIT。Microsoft WebView2 SDK 的许可和 notice 随发布目录附带。

该项目是基于这些源码的独立衍生项目，不是 Seelen 或 Windhawk 的官方发行版。后续开发可以直接克隆本仓库；构建和运行不依赖旧工作区。

源码及安装包发布于 [yky0013/ThemeStudio](https://github.com/yky0013/ThemeStudio)。[v0.1.1 发布页](https://github.com/yky0013/ThemeStudio/releases/tag/v0.1.1) 保存与安装包匹配的源码、旧工作区源码和 Git 元数据、清理前项目数据，以及 SHA-256 校验记录。旧开发入口、运行环境和本机数据按用户要求清理，清理证据见 `docs/handoff/`。

安装器使用 Inno Setup 6.7.3（放入 `.tools/inno-6.7.3`）；0.3.0 精简安装包的官方引导安装器来源及哈希在 `config/webview2-bootstrapper.json`，运行 `tools/fetch-bootstrapper.ps1` 准备。`config/webview2-runtime.json` 保留历史完整离线运行库信息。分发时同时提供匹配源码压缩包，保留许可证及作者声明。本仓库保存对应版本源码、素材、测试和验证记录；安装包、构建时源码归档与校验文件同步至 GitHub Releases。
