# Seelen / Windhawk 源码开发版

当前状态更新（2026-09-27）：开发入口已接入可实际应用的桌面快捷方式图片替换与全局鼠标方案，详见 [desktop-icons-cursors.md](desktop-icons-cursors.md)。此更新优先于下方首轮预览范围记录；完整 Seelen Rust 原生构建仍未验证。

这是在 Seelen 原设置源码中新增的开发模块。主入口为 `/theme_workbench`，沿用 Preact、i18n、Ant Design 和原设置分组 CSS。Windhawk 目录由兄弟仓库的原始 `ModSourceUtils` 解析器生成，当前包含 644 个模组；每个条目记录固定提交的源码链接、文件哈希、许可声明、目标进程和预设选项。

## 本机开发预览

项目根目录双击 `启动源码开发版.cmd`，或者打开 `http://127.0.0.1:4317`。服务仅绑定本机，复用同一个页面组件，不模拟原生 Tauri 接口。

已开发：组合草稿、模组搜索和选择、预设选择、保存并重载、配置导入导出、资源与源码版本校验、页内定位、中英切换、深浅色预览。预览中“应用 Seelen 外观”不可用；导出配置写到 `tools/theme-workbench/exports/`。

原生设置入口有 Seelen 资源读取及保存适配，并复用已有 WidgetConfiguration。重叠组件通过 `workbench-feature-policy.json` 决策后才接入。常规壁纸与视差壁纸已按用户选择分用途保留；任务栏仍待选择。源代码中的这些原生适配尚未完成本机编译与运行验证。

用户已进一步同意将壁纸播放和视差融合。现在可在“壁纸＋视差”中同时播放视频并进行平移/透视，使用的是原 Seelen 媒体组件与移植后的 Windhawk 运动算法。运行上级 `启动壁纸视差预览.cmd` 可定位到这个区域。效果参数随配置导入导出，本地预览媒体不打包进配置。详情见 [wallpaper-parallax.md](wallpaper-parallax.md)。

## 开发命令

```powershell
Set-Location E:\desktop\windows\Seelen-UI\tools\theme-workbench
npm.cmd ci
npm.cmd run check
npm.cmd test
npm.cmd run build
npm.cmd run preview
```

其中 `check` 覆盖新组合模型、视差计算/控制器、设置页面和独立预览；不是整个 Seelen 工程的类型检查。`build` 构建包含原 Seelen 图片/视频组件的浏览器预览，并对原生 Monitor.svelte、state.svelte.ts 与设置适配器做编译/语法检查，不构建 Rust 程序。

完整版仍遵循上游 `AGENTS.md` 的原流程：先准备 Rust `nightly-2026-05-22`、Deno 和 Windows C++ 工具链，生成 core 绑定，再运行 `npm install`、`npm run build:ui`、`cargo check`；需要本地二进制时使用 debug 构建。本轮没有安装或启动两套原生桌面程序。

## 来源与许可证

三个完整源码快照位于项目上级的 `Seelen-UI/`、`windhawk-mods/`、`windhawk/`。`upstream-snapshots/` 保留官方压缩包及 SHA-256；本地 Git 分支为 `theme-workbench`，tag `upstream-snapshot-20260927` 标记导入基线。导入基线提交是本地提交，上游 SHA 另见来源清单。

保留原作者、许可证及源代码声明；新 Seelen 扩展沿用 AGPL。Windhawk 具体模组许可按文件记录，不把模组库中的默认许可规则应用到所有文件和依赖。

完整原生 Seelen 应用集成、Windhawk 编译/安装/启用仍待完成；旧指针与快捷方式后端现已通过本地宿主接入源开发入口。本开发版不将模组选择记录当作系统启用结果。
