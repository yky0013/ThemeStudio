# 应用更新接入依据

结论来自同目录 `10_discovery.md`、`20_sources.md` 和 `21_installer_sources.md` 的官方来源记录。

GitHub `releases/latest` 排除 draft 与 prerelease，资产元数据可提供文件名、大小、下载 URL 及 SHA-256 digest。客户端固定读取 ThemeStudio 的正式版本、按三段数字比较版本，优先使用 digest；缺失时读取同发布内校验文件。匿名访问 ThemeStudio 的 release 与仓库接口当前均为 404，不能宣称现有公开在线升级链路已经可用。离线更新覆盖这一交付边界。

来源：[GitHub release API](https://docs.github.com/en/rest/releases/releases#get-the-latest-release)、[GitHub release assets](https://docs.github.com/en/rest/releases/assets#get-a-release-asset)。

Inno Setup 的同一 AppId 与默认 UsePreviousAppDir 支持识别原安装目录，`/DIR` 可显式传入当前目录。保持 `CloseApplications=yes`、`RestartApplications=no`，由安装向导完成文件替换并提示重新启动；本版添加配对 AppMutex，避免主窗口仍运行时继续覆盖。用户素材保存在程序目录之外。

来源：[AppId](https://jrsoftware.org/ishelp/topic_setup_appid.htm)、[UsePreviousAppDir](https://jrsoftware.org/ishelp/topic_setup_usepreviousappdir.htm)、[命令行参数](https://jrsoftware.org/ishelp/topic_setupcmdline.htm)、[AppMutex](https://jrsoftware.org/ishelp/topic_setup_appmutex.htm)。

公开源的实际下载升级、非 ASCII 目录的真实覆盖安装与运行组件占用处理需要单独端到端实测，官方文档不替代本机验证。
