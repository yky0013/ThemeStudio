# 桌面主题工作室 · Theme Studio

一个独立的 Windows 主题项目。主设置界面在 Seelen UI 的结构和组件上开发，模组区使用 Windhawk 的卡片、选择和标题组件，加入真实 Windows 桌面快捷方式与 17 状态鼠标设置。所有日常设置在同一页，通过左侧导航定位。

## 启动

在其他电脑上运行 `installers/ThemeStudio-0.2.0-Windows-x64-Setup.exe`，安装和程序启动都会请求管理员授权，用于公共桌面快捷方式修改及运行组件；安装路径可自行选择。开始菜单提供程序、图文教程和卸载入口，Windows“已安装的应用”也可卸载。开发目录仍可双击 `启动.cmd`，或运行 `release/ThemeStudio/ThemeStudio.exe`。程序自带图标/指针后端，无需先打开旧工作台，也不调用旧预览服务。运行需 Windows 的 .NET Framework 4.8 和 Microsoft Edge WebView2 Runtime；安装包内置微软官方 x64 WebView2 离线运行库，缺失时安装；需要 Windows 10 2004 / 19041 或更新的 Intel / AMD 64 位系统，不面向 ARM。

卸载会保留已应用的外观、素材和备份；要恢复原外观请先在程序内恢复。

新项目数据保存在 `%LOCALAPPDATA%/ThemeStudio`；原工作台数据保持原位。关闭主窗口会关闭图标/指针后端；已经启用的桌面壁纸、Seelen 和 Windhawk 引擎继续运行，可在设置页停用。

当前版本：0.2.0。安装/启动管理员授权、逐项图片对应、真实桌面媒体播放和运行组件启用已接入；本轮的源码、原生运行与安装验证分别记录在 docs/development/。图文教程位于 `docs/guide/index.html`，离线随程序安装。详见 `docs/installer-verification.json`。

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

安装器使用 Inno Setup 6.7.3（放入 `.tools/inno-6.7.3`）；官方运行库下载来源及哈希在 `config/webview2-runtime.json`，运行 `tools/fetch-runtime.ps1` 获取锁定的离线运行库。分发时同时提供匹配源码压缩包，保留许可证及作者声明。
