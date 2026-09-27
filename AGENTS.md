# 桌面主题工作室 / Theme Studio

此目录为用户要求的新独立项目，沿用父目录的来源优先和重叠功能由用户选型的约定。

- 原始导入版本和许可证见 `docs/source-imports.json` 与 `licenses/`；完整源代码保留在 `vendor/Seelen-UI`、`vendor/windhawk`、`vendor/windhawk-mods`。
- 主界面在 `src/app`，直接使用/适配 Seelen 设置组件和 Windhawk 模组组件；不要重新画一个无行为的演示页。
- 图标与全局 17 状态鼠标后端在 `components/icon-workbench`；普通图片转换器在 `components/image-to-ico`，作为内部步骤。
- 单页设置。重叠能力选择以 `config/feature-policy.json` 为准，任务栏仍待用户选择。
- 新项目的构建/运行必须使用项目内源码、依赖和打包文件，不能指向父目录旧预览服务、Python venv 或旧 EXE。
- 新数据使用 `%LOCALAPPDATA%/ThemeStudio`，不覆盖旧项目数据。应用和恢复必须保存并核对持久记录。
- 保留完整来源声明；分清可用能力、源码能力、未编译引擎、界面预览。
- 子代理仅在用户或适用说明授权时使用；边界清楚的独立工作优先 luna_worker。
