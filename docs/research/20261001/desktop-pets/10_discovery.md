# 主题级发现摘要（2026-10-01）

本轮优先使用 GitHub repository search 定位可读的一手作者仓库，再回到仓库 README、开发文档与官方品牌站核验运行方式、包格式和权利声明。搜索命中只作为发现线索，具体结论以 `20_sources.md` 中的直接仓库/官方页面检查点为准。

| 主题 | 发现状态 | 可核验的一手来源 | 结论边界 |
|---|---|---|---|
| 鸣潮 | 找到 1 个同人桌宠；官方站点仅为权利入口 | `KennyXiang/PhrolovaDeskPet`；Kuro 官方站 | Phrolova 为 PyQt5 源码桌宠；未核实官方桌宠 |
| 原神 | 找到旧版同人桌宠与通用运行时 | `ChaozhongLiu/DyberPet_GenshinImpact`；`ChaozhongLiu/DyberPet` | 旧仓库已停止维护；素材有米哈游版权声明 |
| 崩坏：星穹铁道 | 找到 1 个饮月君同人桌宠 | `Morgan0425/hsr-yinyuejun-desktop-pet` | Windows ZIP/WPF，仓库未附开源许可证 |
| 绝区零 | 找到 Codex v2 桌宠包与 Windows PySide6 桌宠 | `YYKIG/codex_pet_Angels_of_Delusion`；`xiyan1314/daifeiyu-desktop-pet` | 均为社区项目；格式分别是 Codex v2 与独立 PySide6 角色库 |
| 明日方舟 | 找到成熟 ArkPets + Ark-Models | `isHarryh/Ark-Pets`；`isHarryh/Ark-Models` | Spine v3.8/模型 ZIP 仅供 ArkPets 运行；素材版权归鹰角 |
| 蔚蓝档案 | 找到 DSH 白子桌宠插件 | `mldhao/dsh-blue-archive-shiroko` | `.tgz` 是 DSH 插件；代码 MIT 不覆盖角色/图片 |
| 战双帕弥什 | 未找到 GitHub 精确/简称候选 | PGR 官方入口；两次 GitHub 0 结果 | 仅说明本轮 GitHub 检索未命中，不代表全球没有来源 |
| 第五人格 | 找到 macOS Codex 园丁桌宠 | `iisland2008/identity-v-gardener-desktop-pet` | 非官方、macOS Electron；未见 Windows 运行方式 |
| Chiikawa | 找到 Codex v2 与 Windows Electron | `hyc1228/chiikawa-codex-pet`；`frobel0520/chiikawa-desktop-pets` | 均为非官方；官方站只作为 Nagano/角色权利入口 |
| Milk Mocha | 未找到 GitHub 精确/无空格候选 | 两次 GitHub 0 结果 | 需要其他拼写/平台继续查；本轮不补猜测 |

## 运行时/包格式簇

- **PyQt5/PySide6 + Python**：Phrolova（Python 3.8+、PNG 状态帧）、DyberPet（Windows EXE 或 Python/PySide6 MOD）、DaFeiYu（Python 3.10；绿色 ZIP 带 `pythonw.exe`，角色可导入图片/GIF/视频）。
- **PowerShell/WPF**：饮月君桌宠 Windows ZIP + `Start-YinyueJun-Pet.bat`，依赖 Windows PowerShell 5.1/WPF。
- **Electron/portable EXE**：Chiikawa Windows 仓库，`npm run dist` 生成便携 EXE；第五人格园丁仓库只给 macOS Electron 打包。
- **Spine/ArkPets**：ArkPets 安装器/ZIP/JAR 负责运行，模型包通常为 `.atlas` + `.skel` + `.png`，需 Spine Runtime 3.8。
- **Codex v2 / DSH**：Codex 宠物包为 `pet.json` + `spritesheet.webp`；DSH 白子为 `.tgz` 插件。两者均需各自宿主，不能把 ZIP/TGZ 当作 ThemeStudio 主题包。
