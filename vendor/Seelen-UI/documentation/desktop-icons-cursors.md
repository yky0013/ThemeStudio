# 桌面快捷方式与鼠标指针接回同一页面

2026-09-27 用户确认：把旧版鼠标和图标功能加入新工作台；常见图片转 ICO 内置，不再显示独立转换步骤。

## 已能使用

运行项目根目录 `启动源码开发版.cmd`，在同页「桌面图标」选择快捷方式和图片，点击替换。PNG、JPG/JPEG、WebP、BMP、GIF、TIF/TIFF 和已有 ICO 均可使用。动态图取第一帧，保留 EXIF 方向，默认完整保留图片、透明补齐正方形，自动生成 16/24/32/48/64/128/256 多尺寸图标。32 MB 文件、4000 万像素上限沿用原转换器。

「鼠标指针」支持原有 17 种全局状态、当前系统方案、Windows 默认、已有 Cursor Palette 方案、CUR/ANI 导入、文件夹按名称匹配、尺寸、方案保存和撤销。ANI 预览是首帧，应用保留原文件的动画及热点。

新页面的这两区已经通过本机接口实际应用，不是仅保存配置的预览。图片选择和指针编辑是草稿，分别点击应用生效。图片与指针素材保存在 `%LOCALAPPDATA%/DesktopIconWorkbench`，复用旧资源、方案、备份；不要求原图片留在上传位置。当前整页主题 JSON 导出仍只包含 Seelen/Windhawk/壁纸参数；桌面图片资源和指针方案单独持久化在本机库，不宣称已实现完整主题资产打包。

已更新旧单页 `icon-workbench/dist/single-page/ThemeWorkbench.exe`，原 `主题工作台.lnk` / `启动主题工作台.cmd` 继续可用；其中独立转换面板已移除，图片直接进入图标库。

## 实际复用与边界

- `icon-workbench/backend.py`：Windows Shell COM 修改 .lnk；保留 .url 配置；备份、原子替换、目标/参数校验、Shell 刷新、冲突保护和恢复。
- `image-to-ico/converter.py`：直接复用原 `load_image` / `encode_ico`，没有另写图像转换算法。新增 `IconStore.import_image` 将产物导入原持久资源库。
- `icon-workbench/cursor_adapter.py`：保留 Cursor Palette（MIT）17 角色和注册表协议适配；只增加锁内当前状态检查，防止页面旧草稿覆盖外部修改。
- `icon-workbench/desktop_bridge.py`：私有 stdio 适配器，调用以上实际实现；不执行命令字符串。仅已扫描快捷方式和已登记素材 ID 可用于浏览器请求。
- `tools/theme-workbench/desktop-host.ts`：隐藏启动现有 Python 虚拟环境，串行调用 stdio。HTTP 仅监听 127.0.0.1，检查 Host/Origin、同源会话令牌和 JSON 请求；其他网页不能直接写设置。
- `DesktopPanel.tsx`：真实桌面/资源缩略图、搜索、多选、图片直接替换、备份列表、17 角色配置、方案保存和恢复，放在原 View 组件内。

Seelen 图标包不等价于 Windows 桌面快捷方式图标。此次按用户要求恢复旧能力，没有替用户选择任务栏提供者。源开发入口使用 Node + 原 Python 环境；Seelen 的完整 Rust/Tauri 可执行程序仍未构建，原生 Seelen 路由尚未接此 stdio 宿主，不能把这里的验证表述为完整 Seelen 原生版本通过。

桌面替换范围为 .lnk / .url；此电脑、回收站、文件夹、EXE 内部图标不在此模块范围内。公共桌面写权限不足会逐项提示并保留原文件；可用旧版 EXE 现有的管理员重启入口。默认不提升权限，也不重启 Explorer。

## 验证

- TypeScript 检查、20 项前端/协议/视差测试、页面构建通过。
- 37 项 Python 测试通过，新增覆盖 7 类图片、LNK/URL 真文件替换和逐字节恢复、7 档 ICO 尺寸、透明留白、陈旧选择拒绝、文件名/资源 ID 边界、指针导入不写系统及锁内状态保护。
- 浏览器点击实测：选择普通 PNG → 两个真实测试快捷方式批量应用 → 还原；路径、启动参数不变，实际 ICO 已生成。
- 浏览器点击实测：当前实际鼠标方案应用 → 系统快照核对 → 恢复，注册表值、类型、缺失值和大小与测试前完全一致；单独 CUR 导入、保存指针方案可用。
- 原 Tk 单页组件隐藏运行检查：图片导入、17 角色、保存/重开草稿通过，无独立转换区；EXE 已重新构建。
- 测试快捷方式及数据均在隔离目录，用户原快捷方式未改；实际系统鼠标的短暂测试已恢复。

证据：项目根目录 `docs/adoption/seelen-windhawk/desktop-verification.json` 与 `qa/desktop-integration/`。本轮旧模块源快照和哈希随验证记录保存，以补充其不在 Seelen Git 仓库内的来源链。
