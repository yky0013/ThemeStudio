# 结论

`10_header_sources.md` 中的 Microsoft 状态表与 SDK 数字定义解释了排序列白块：`HIS_SORTEDNORMAL` 为 4，不能只处理 `HIS_NORMAL=1`。应同时覆盖图标普通/排序状态，但不误把排序箭头或下拉按钮当作底板。

`20_splitter_sources.md` 中两份上游 Windhawk 代码与本机实际 trace 一致：`PreviewPane` 部件 3/4 对应两条分隔条。该映射属于私有 Explorer 主题实现，所以修复限定为 shell-owned DirectUI + 该主题 + 部件 3/4 + 状态 0；不更改命中测试或泛化处理其他矩形。

本机 Windows 11 build 26200.8037 已复现旧行为并核对修复。现场又验证了表头浅底浅字问题，最终使用透明悬停/按下叠层维持反馈；导航状态仍采用原生渲染。具体实现、测试范围与限制记录在 `docs/development/explorer-header-splitter-update.md`。
