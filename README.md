# 桌面主题工作室 · Theme Studio

一个独立的 Windows 主题项目。主设置界面在 Seelen UI 的结构和组件上开发，模组区使用 Windhawk 的卡片、选择和标题组件，加入真实 Windows 桌面快捷方式与 17 状态鼠标设置。所有日常设置在同一页，通过左侧导航定位。

## 启动

双击本目录 `启动.cmd`，或运行 `release/ThemeStudio/ThemeStudio.exe`。请保留整个发布目录。程序自带图标/指针后端，无需先打开旧工作台，也不调用旧预览服务。运行需 Windows 的 .NET Framework 4.8 和 Microsoft Edge WebView2 Runtime；构建机器已具备这些系统组件。

新项目数据保存在 `%LOCALAPPDATA%/ThemeStudio`；原工作台数据保持原位。关闭主窗口会关闭它启动的后端进程。

当前状态：EXE 已构建，浏览器中的共享界面已验证；原生 EXE 的启动验收被自动审批拦截，因此尚未确认原生窗口运行。详见 `docs/verification.json`。

## 已接入

- 桌面快捷方式：读取真实桌面列表，普通 PNG/JPG/WebP/BMP/GIF/TIFF/ICO 直接替换 .lnk/.url 图标；内部自动生成多尺寸 ICO，无独立转换工具；应用前备份，支持恢复和冲突检查。
- 全局鼠标：17 种状态、CUR/ANI、文件夹匹配、方案保存、大小和恢复。部分应用自行绘制的光标不跟随系统设置。
- 壁纸＋视差：复用 Seelen 图片/视频组件和移植的 Windhawk 运动算法；当前在设置页预览，真实桌面播放引擎仍待完整接入。
- Windhawk 模组：使用本地 644 个模组的实际源码解析元数据和预设，并用 Windhawk 卡片界面选择组合；当前保存配置，不把选择视为已经安装/执行模组。
- Seelen 资源：主题与图标包组合配置。完整 Seelen 原生桌面组件仍保留源码，尚未在此发布中编译和启动。

任务栏/Dock 等重叠能力仍由用户决定提供者，见 `config/feature-policy.json`。不会因使用某一套设置界面而自动启用其全部桌面组件。

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
| `config/` | 选型决策、构建依赖锁定信息 |
| `docs/` | 来源清单、改动说明、验证证据 |

## 构建

首次运行 `tools/setup.ps1`，准备当前项目的 npm、Python 依赖和固定 WebView2 SDK。SDK 版本、官方下载地址与 SHA-256 位于 `config/webview2-sdk.json`，校验后解压到 `.cache/webview2`。

```powershell
npm.cmd run check
npm.cmd test
npm.cmd run build
.\tools\package.ps1 -SkipFrontend
```

开发调试：运行 `tools/start-dev.ps1`，只在本机 4327 端口启动新项目的服务。发布 EXE 使用内嵌 WebView2 和自己的后端，不需要 Node/Python 开发环境。

## 来源与许可

来源导入清单：`docs/source-imports.json`、`docs/desktop-source-imports.json`。固定上游源码、作者声明和各自许可证保存在 `vendor/` 与 `licenses/`。新整合代码采用 AGPL-3.0-or-later；Windhawk 宿主及模组的原许可证仍分别适用，不能将全部模组统一视为 MIT。Microsoft WebView2 SDK 的许可和 notice 随发布目录附带。

该项目是基于这些源码的独立衍生项目，不是 Seelen 或 Windhawk 的官方发行版。原目录和旧入口保留，后续整合开发在本目录进行。
