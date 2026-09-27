# 新项目的整合边界与本地改动

本项目从 `docs/source-imports.json` 记录的三个本地 Git 快照导入完整源码，未依靠旧程序窗口或旧 localhost 服务嵌入页面。

## 界面来源

- Seelen 的设置页 `WorkbenchView`、`SettingsBox` CSS、颜色/间距变量、图片/视频与视差组件直接参与本项目构建。
- 从 Seelen `components/navigation/index.tsx` 提取纯展示接口 `NavigationFrame.tsx`，继续使用同目录原导航 CSS；把导航目标变成单页锚点，移除展示层对 Seelen 原生 session/resource API 的强依赖。原生导航源文件保留。
- 从 Windhawk `panel/shared/ModCard.tsx` 提取 `ModCardFrame.tsx`，保留 Card.Meta、ribbon、选择框、底部操作及选中样式。直接调用原 `EllipsisText.tsx` 和 `ModSelectBox.ts`；网络评论、评分、路由及原宿主调用不在卡片展示接口里。
- `src/app/main.tsx` 是新的统一入口；桌面图标、鼠标、壁纸视差、Seelen 资源和 Windhawk 模组依次放在同一页。主界面的来源不等于自动启用对应桌面组件。

## 后端与运行

图标/指针源文件复制到 `components` 内并独立维护，默认数据目录改为 `ThemeStudio`，图片转换继续复用原模块。发布时打包为 `ThemeStudio.Backend.exe`。Windows 宿主只向它发送白名单 JSON 请求，不通过 shell 执行用户字符串。

独立 Windows 主程序采用 WinForms + WebView2 容纳同一前端产物。运行包包含前端、后端、WebView2 SDK DLL 和许可文件；不含旧 EXE、旧 Python venv 或旧 localhost 地址。Node 与 Python 开发环境只用于构建和开发调试。

`tools/dev-server.ts` 仅为同一前端提供浏览器验收环境，默认本机 4327；独立 EXE 使用虚拟域名及 WebMessage/stdin，不开 HTTP 端口。两种入口使用同一个 `src/app/bridge.ts` 客户端接口和同一份后端源码。

完整 Seelen Rust 后台和 Windhawk 注入引擎已保留源码，但未在此发布中编译运行。此时 Windhawk 模组是组合配置，壁纸视差是设置页预览。任务栏选型保持待用户决定。

## 验证说明

本轮源码、TypeScript、Python 测试和打包结果见 `verification.json`。启动新 EXE 的原生验收脚本被自动审批以 `blocked by policy` 拒绝，未给出具体理由；没有换用其他渠道重试该启动动作。独立主窗口的运行仍记为未验证。浏览器共享界面的检查不替代该原生运行检查。
