# ThemeStudio 桌宠来源目录（2026-10-01）

本目录只纳入本轮直接打开并核验过的官方入口或作者仓库。官方页面用于确认品牌/权利入口；“官方桌宠”必须有官方发布页或官方可下载包才算，本轮没有把任何官方游戏官网当成官方桌宠来源。所有社区项目均保持“非官方”标记。

| ThemeStudio 主题 | 已核验来源与属性 | Windows 交付/运行要求 | 对 ThemeStudio 的直接导入判断 |
|---|---|---|---|
| **鸣潮** | [Kuro 官方入口](https://wutheringwaves.kurogames.com/en/)（官方品牌/权利入口，无桌宠下载）；[PhrolovaDeskPet](https://github.com/KennyXiang/PhrolovaDeskPet)（同人，README 明确非 Kuro 官方，GPL-3 仓库） | 源码 `Deskpet.py`；Python 3.8+、PyQt5；角色 PNG 状态帧（静止/奔跑） | 可作为独立 Python 桌宠研究源；不能把源码/PNG 项目直接当 `.tspack`。**鸣潮官方桌宠本轮未核实**。 |
| **原神** | [HoYoverse 官方入口](https://genshin.hoyoverse.com/en/)（本轮只核实到官方站）；[旧版 DyberPet 原神仓库](https://github.com/ChaozhongLiu/DyberPet_GenshinImpact)（同人、已停止维护、GPL-3；作者声明米哈游素材不得商用）；[DyberPet 当前框架](https://github.com/ChaozhongLiu/DyberPet)（GPL-3，v0.10.3 Windows 发布，支持 MOD） | 旧仓库 Windows `呆啵宠物-原神.exe`；当前框架 Windows Release EXE，源码路线 Python 3.9.18/PySide6 6.5.2 等；角色目录含 `pet_conf.json`、`act_conf.json`、透明 PNG 帧 | 角色目录/EXE 是 DyberPet 自有格式；不能直接作为 ThemeStudio `.tspack`。官方桌宠未核实。 |
| **崩坏：星穹铁道** | [官方入口](https://hsr.hoyoverse.com/en-us/)；[饮月君桌宠](https://github.com/Morgan0425/hsr-yinyuejun-desktop-pet)（非官方个人项目，仓库未附开源许可证） | `饮月君桌宠-Windows.zip`，解压后 `Start-YinyueJun-Pet.bat`；Windows 10/11 PowerShell 5.1 + WPF，无需 Python/其他运行库 | ZIP/BAT 是独立 WPF 桌宠交付，不能作为 `.tspack` 直接运行或导入。 |
| **绝区零** | [官方入口](https://zenless.hoyoverse.com/en-us/)；[Angels of Delusion Codex 宠物包](https://github.com/YYKIG/codex_pet_Angels_of_Delusion)（同人，Codex v2；代码 MIT，角色/联动素材另受权利约束）；[DaFeiYu](https://github.com/xiyan1314/daifeiyu-desktop-pet)（同人，MIT，希希芙风格） | Codex 包为 ZIP 内 `pet.json` + `spritesheet.webp`，复制到 `%USERPROFILE%\\.codex\\pets\\<id>\\` 后重启 Codex；DaFeiYu Windows 绿色 ZIP 含 `pythonw.exe`/运行库，源码 Python 3.10 + PySide6，可在其自身界面导入 PNG/JPG/BMP/WebP、GIF/视频 | 两种格式分别属于 Codex v2 和 DaFeiYu；GIF/图片可被 DaFeiYu 自身导入，但这些包都不能作为 ThemeStudio `.tspack` 直接运行。 |
| **明日方舟** | [官方入口](https://www.arknights.global/)；[ArkPets](https://github.com/isHarryh/Ark-Pets)（社区项目，GPL-3，Windows）；[Ark-Models](https://github.com/isHarryh/Ark-Models)（配套模型库；素材版权归上海鹰角网络有限公司，禁止商用） | ArkPets `ArkPets-Setup.exe`；Windows 7+；首次在模型库管理下载模型，也可导入模型 ZIP；另有 ZIP 免安装/JDK17 JAR。模型通常为 Spine v3.8 的 `.atlas` + `.skel` + `.png` | 模型 ZIP/Spine 资源只能交给 ArkPets/Spine Runtime；不能把模型包、GIF 或单张 PNG 直接当 `.tspack`。 |
| **蔚蓝档案** | [NEXON 官方入口](https://bluearchive.nexon.com/)（本轮页面受地区限制）；[DSH Blue Archive Shiroko](https://github.com/mldhao/dsh-blue-archive-shiroko)（非官方 DSH 插件，代码 MIT；角色/图片不在 MIT） | Release `dsh-blue-archive-shiroko-0.6.0.tgz`；通过 `dsh plugin --profile web add` 安装；需运行 DSH Web、现代 Chromium 浏览器；余额功能另需 `DEEPSEEK_API_KEY` | `.tgz` 是 DSH 插件宿主格式，WebP/内嵌图片需按该项目结构替换；不能作为 ThemeStudio `.tspack` 直接运行。 |
| **战双帕弥什** | [KURO 官方入口](https://pgr.kurogame.net/)；GitHub 精确查询与 `pgr desktop pet` 简称查询均返回 0 | 本轮没有核验到可运行的 Windows 桌宠包或作者仓库 | **未找到可核验来源**。0 结果仅限本轮 GitHub 查询，不代表其他平台不存在；不得补猜下载链接。 |
| **第五人格** | [官方入口](https://www.identityvgame.com/)；[园丁 Codex 桌宠](https://github.com/iisland2008/identity-v-gardener-desktop-pet)（非官方同人，README 声明与网易/官方无关，未显示开源许可证） | Electron/npm；README 仅给 macOS 安装与 arm64 DMG/ZIP 打包；监听 Codex `task_started`/`task_complete`/`turn_aborted`，未给 Windows 运行方式 | macOS Electron/Codex 项目，不具备已核验的 Windows 运行交付；不能作为 `.tspack` 直接运行。 |
| **Chiikawa** | [官方站](https://www.chiikawaofficial.com/)（介绍 Nagano 与 Chiikawa/Hachiware/Usagi，无桌宠下载）；[Codex v2 合集](https://github.com/hyc1228/chiikawa-codex-pet)（非官方、个人非商业，角色图不视为开源）；[Windows Electron 宠物](https://github.com/frobel0520/chiikawa-desktop-pets)（非官方个人项目，当前 README 提醒未重新核验运行行为） | Codex 包为角色 ZIP，`pet.json` + `spritesheet.webp`，复制到 `~/.codex/pets/<id>/` 后重启 Codex；Windows 仓库源码 `npm.cmd install`/`npm.cmd start`，`npm.cmd run dist` 产出 `Chiikawa Desktop Pets 1.0.0.exe` | Codex v2 资源或 Electron portable EXE 均是各自宿主格式；不能作为 `.tspack` 直接运行。Windows 项目虽然有构建命令，但本轮未运行验证。 |
| **Milk Mocha** | GitHub 精确短语与 `milkmocha desktop pet` 查询均返回 0；本轮无可核验官方桌宠或社区仓库 | 无可靠 Windows 包/运行时证据 | **未找到可核验来源**。需要其他拼写、平台或官方社媒检索；本轮不猜测来源。 |

## 兼容性与安全导入预期

本轮核验的第三方交付大多是独立运行时格式：PyQt5/PySide6 角色目录、PowerShell/WPF ZIP、Electron portable EXE、ArkPets 的 Spine 模型 ZIP、Codex `pet.json`/WebP、DSH `.tgz`。这些格式各自依赖宿主程序，不能仅改扩展名或压缩成 ZIP 就变成 ThemeStudio `.tspack`。

已读取的 ThemeStudio v1 主题包文档/导入器要求 `.tspack`/`.zip` 根目录有 `theme.json`（`schemaVersion: 1`）并使用包内相对路径；该证据只用于判断“第三方原生桌宠包不能直接作为 v1 `.tspack` 运行”。主项目本轮另有桌宠 EXE 导入/启动改动，具体可接受格式、权限和启动策略应以主代理当前代码与 QA 为准，本研究未运行任何外部 EXE，也未验证新 importer。

对于后续候选，安全的最小记录应包含：原始仓库 URL、作者/版本、宿主运行时、包内文件清单、SHA-256、素材/角色权利声明、是否允许再分发，以及转换后 ThemeStudio 包的独立 provenance。GIF、WebP 或 PNG 只能证明图像资产格式，不能证明可执行桌宠行为或授权。

## 结论边界

本轮直接核实到的“官方”来源均为游戏官网/品牌权利入口，没有一项页面同时提供可确认的官方桌宠安装包。因此“官方桌宠”对鸣潮、原神、星铁、绝区零、明日方舟、蔚蓝档案、战双、第五人格、Chiikawa、Milk Mocha 均应暂记为“未核实”；社区项目则按上表的非官方、宿主和许可边界使用。
