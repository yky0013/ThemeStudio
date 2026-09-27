# 安装包实施结论

依据本目录官方来源记录：使用 Inno Setup 6.7.3 构建当前用户安装包，保留目标路径页面、开始菜单程序/教程/卸载入口和 Windows 卸载登记。Inno 6.7.3 不接受较新帮助页中的 SetupArchitecture 指令；采用其受支持的 ArchitecturesAllowed / ArchitecturesInstallIn64BitMode 构建承载 x64 程序的安装器。

发行目标限制为 Intel/AMD x64 Windows 10 2004 / 19041 及以上与 Windows 11。包内包含微软官方 Evergreen Standalone x64 Runtime，下载固定 CDN 文件并记录 SHA-256 和有效 Microsoft 签名；检测 HKCU/HKLM 的官方 pv 注册项，仅缺失时调用 /silent /install，并以再次检测结果为准。不猜测特定数字退出码的含义，不强制重启，也不卸载共享 Runtime。

应用素材和备份位于 LOCALAPPDATA/ThemeStudio，卸载不设置额外清除该目录的规则。图文教程使用原生应用、隔离示例快捷方式和真实安装向导截图，离线随程序部署。87 项运行/打包组件的许可声明随包保留；匹配源码归档随安装包提供。

本机已实测自定义中文与空格路径安装、原生启动、教程入口、开始菜单和卸载登记、卸载后程序与快捷方式移除及用户数据保留。缺少 Runtime 的全新系统分支与第二台实机尚未测试。最终浏览器页面检查因 Computer Use 无法确认当前 URL 而停止，后续仅进行了文件封装与静态验证。详情见 ../../../installer-verification.json。
