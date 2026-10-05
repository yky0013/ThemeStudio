# 0.6.4 / 0.5.4：排序列与分隔条背景修复

2026-10-05，用户反馈普通目录和空“音乐”目录仍出现白色“名称”列头及两条竖白线。两个系列使用相同的 Explorer 背景模组，本次同步升级到 1.2.1。

## 原因和处理

旧代码只处理 `HP_HEADERITEM/HIS_NORMAL`，漏掉排序列的 `HIS_SORTEDNORMAL=4`。实际 Explorer 跟踪确认白块来自 `Header/part 1/state 4`；补齐普通、排序、图标及图标排序的空闲状态，并覆盖表头公共空白条。排序箭头、筛选下拉和原始排序交互仍交给系统。

真实绘制跟踪同时定位到 `DirectUIHWND → PreviewPane` 的 part 3/4、state 0：两者分别对应导航/文件与文件/预览之间的 5 像素竖条。现在仅在 shell 自有 DirectUI 中，对该类、部件和状态的实际裁切矩形绘制同坐标背景。不改布局、窗口大小、命中测试或文档预览内容，不把 `CommandModule` 或其他主题部件一起透明化。

现场点击表头时还发现，浅色原生悬停底色与浅色 GDI 标签叠加会使文字变淡。表头悬停/按下改为 32/255 与 64/255 的浅色透明叠层，保留不同强度的操作反馈和文字可读性。导航栏的悬停、选中以及焦点状态继续使用原生绘制。

## 已完成的验证

- 在 Windows 11 25H2、build 26200.8037 的真实 Explorer 中，用隔离 portable Windhawk 配置加载旧模块，复现白色排序列和两条分隔线；跟踪只记录控件类、主题类、部件、状态及矩形，不记录文件名或内容。
- 隔离 Win32 像素回归先对旧版产生失败码 43（sorted idle header）；修复后通过排序/图标状态、空白表头、两侧分隔条、两种主题绘制 API、裁切、半透明操作反馈、导航选中、缓冲 alpha、预览处理器排除及 500 次 GDI 资源寿命检查。
- 修复后的诊断构建在真实 Explorer 中核对普通详细信息列表、空“音乐”目录、空预览、切换排序列与表头悬停；本轮显示范围内的白块/竖白线消失，文字可读。诊断副本只增加绘制跟踪，背景实现与交付源码一致。
- 每轮现场测试后禁用模块、正常退出隔离 Windhawk；核对模块已从 Explorer 卸载，ThemeStudio 原配置指纹未变。测试未安装新主程序，也未启用 XAML Explorer Styler，因此顶栏仅验证恢复，没有宣称整套主题的全窗口兼容性。

现场证据与回归日志见对应 `validation-0.6.4/` 和版本 verification JSON。绘制 trace 使用 UTF-16LE。本次未完成安装/卸载生命周期回归、独立 0.5 分支现场注入、所有主题及其他 Windows build 验收，两个发行继续标为 prerelease。

## 复核资料

状态定义见 [Microsoft Parts and States](https://learn.microsoft.com/en-us/windows/win32/controls/parts-and-states)；本机实测和上游主题模块的交叉依据见 `docs/research/20261005/explorer-header-splitter/`。`PreviewPane` 是 Explorer 私有主题类别，后续 Windows 更新需要复核。

复测工具 `tools/qa-explorer-surfaces.py` 的顺序为 `prepare`、`start --image <现有已验证BMP>`、`stop`。必须执行 stop 并核对 restored.json；该工具仅供明确安排的本机原生绘制 QA，不应在普通应用启动时执行。
