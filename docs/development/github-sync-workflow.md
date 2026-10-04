# GitHub 同步与本地交付流程

用户于 2026-10-05 要求：本项目所有流程同步到 GitHub，本地只保留对应安装包。目标为既有私有仓库 [yky0013/ThemeStudio](https://github.com/yky0013/ThemeStudio)，保持私有状态。

## 每次改动的记录

1. 在开发记录中保存需求、原因、设计选择、修改范围和来源许可证；调研保存在 `docs/research/`。
2. 按改动执行类型检查、前后端测试和必要的原生验证。保存命令、结果及实际验证范围；应用内预览和隔离测试不等于真实 Explorer 的现场验收。
3. 本机打包后计算 SHA-256，保留对应源码及构建/验证资料。`docs/development/validation-<version>/` 保存本次证据。
4. 当前版本源码推送到 `main`；0.5 系列维护在 `maintenance/0.5`。每个版本保留独立 `vX.Y.Z` 标签，不重写既有历史或强推。
5. 通过 `tools/sync-github-release.py` 使用清单创建 draft、上传、核对远端大小和 GitHub SHA-256 digest，再发布。凭据只从既有 Git Credential Manager 读取到内存，不写入源码、清单或日志。
6. 尚缺真实 Explorer 视觉验收的版本发布为 prerelease。发布记录必须列出待验证事项，不能沿用 0.2.0 的历史测试结果冒充新版本结果。
7. 确认分支、标签、发行附件均可从远端恢复后，再清理本地构建树、源码 ZIP、日志和截图；本地交付目录只保留对应当前安装包。其他独立工具及 `%LOCALAPPDATA%/ThemeStudio` 用户数据不属于清理范围。

## 2026-10-04—05 本轮记录

- 原因：0.6.0 的资源管理器预设独立于一键主题，且不绘制主题图片到原生文件列表。
- 实现：去掉三个内置条目及其打包资源；增加图片联动、两处实时预览、可见度调节、原生 GDI 绘制与 XAML 配置、失败回滚和恢复记录。0.5.1 保留七套配套动态素材，0.6.1 保留静态素材和外部动态导入。
- 证据：两个版本各 23 项前端测试；0.6.1 的 96 项后端测试、0.5.1 的 88 项后端测试通过；两个 Windhawk 组件编译及设置往返通过；隔离 GDI 绘制和桌面容器只读预览检查通过。
- 待验收：当前 Windows build 26200 的真实 Explorer 注入/视觉效果，以及安装/卸载完整生命周期。未用管理员权限运行这些测试。
- GitHub 同步：0.6.1 提交到 `main`，0.5.1 提交到 `maintenance/0.5`；为两个修订版发布测试版附件，并将旧 0.5.0、0.6.0 安装包补入历史标签的归档发布。
- `ThemeStudio-<version>-Source.zip` 是 2026-10-04 打包时的完整源码快照；本次后续同步工具、项目约定和发布证据同时保存在 Git 标签对应树中。

## 发布清单示例

清单保存在被 Git 忽略的 `installers/` 或指定暂存目录，不包含认证信息：

```json
{
  "repository": "yky0013/ThemeStudio",
  "tag": "v0.6.1",
  "commit": "对应标签的完整提交 SHA",
  "title": "桌面主题工作室 0.6.1 · 测试版",
  "notes": "本版本变化、验证结果和待验证项目",
  "prerelease": true,
  "realExplorerVisualVerified": false,
  "assets": [{"name": "附件文件名", "path": "本地绝对路径", "bytes": 0, "sha256": "文件哈希"}]
}
```

依次运行 `--stage prepare`、`--stage upload`、`--stage verify`、`--stage publish`。重复上传会先核对已存在附件；同名不同哈希会停止，不自动覆盖已发布内容。旧 `tools/publish-release.ps1` 保留作 0.2.0 历史流程参考，不用于当前版本。
