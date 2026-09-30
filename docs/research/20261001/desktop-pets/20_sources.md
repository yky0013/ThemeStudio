# 页面与仓库抓取检查点

**Time**: 2026-10-01
**Source**: https://www.google.com/search?q=ThemeStudio+desktop+pet+Wuthering+Waves
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: low
**Insight**: 搜索结果未发现 ThemeStudio 或鸣潮桌宠的可核验一手来源；页面主要返回无关结果。该页面只作为发现失败记录，不支持任何主题来源结论。

# Relevant extracted content

> 页面标题为 “ThemeStudio desktop pet Wuthering Waves - Google 搜索”；可见结果主要为 Internet Archive、DSH verification、音乐链接等，与桌宠或 ThemeStudio 主题无关。

---
**Time**: 2026-10-01
**Source**: `E:\desktop\windows\ThemeStudio-0.6.0\README.md` and `E:\desktop\windows\ThemeStudio-0.6.0\src\app\templates.tsx`
**Method**: extract (via PowerShell `Get-Content`; local project source)
**Confidence**: high
**Insight**: 该次读取的 README/`templates.tsx` 快照显示 ThemeStudio 运行时为 Windows .NET Framework 4.8 + Microsoft Edge WebView2 Runtime，主题包界面支持 `.tspack`/`.zip`，内置动态版是 AI 同人插画的缓慢运镜。该快照早于本轮主项目新增的桌宠 EXE 导入/启动改动，不能用来判断当前代码是否已支持第三方桌宠运行；本条只保留包格式与运行库证据。

# Relevant extracted content

> README：运行需 Windows 的 .NET Framework 4.8 和 Microsoft Edge WebView2 Runtime；目标为 Windows 10 2004 / 19041+、Intel/AMD 64 位。

> README：0.4.0 起支持导入 `.tspack`/`.zip` 完整主题数据包；0.3.1 支持 GIF、动态 WebP、APNG 在关闭视差时保持动画，但主题包文档/当前校验对静态壁纸字段仍要求静态图片，动态壁纸字段使用 MP4。

> `src/app/templates.tsx` 脚注：支持 `.tspack` / `.zip` 完整主题数据包；内置动态版是 AI 同人插画的缓慢运镜与柔光动效。

> 读取时的 `templates.apply` UI 行为只报告壁纸、17 种鼠标状态和匹配桌面快捷方式图标；由于主项目随后已加入桌宠 EXE 导入/启动改动，本条不作为当前功能缺失结论。

---
**Time**: 2026-10-01
**Source**: `E:\desktop\windows\ThemeStudio-0.6.0\docs\theme-pack-format.md`
**Method**: extract (via PowerShell `Get-Content`; local project source)
**Confidence**: high
**Insight**: 按所读 ThemeStudio v1 主题包文档，`.tspack`/`.zip` 需在根目录含 `theme.json`（schemaVersion 1），资源路径为包内相对路径；该包格式本身是数据型桌面外观包，允许壁纸/可选 MP4/ICO/CUR/ANI/JSON 等素材，不把外部桌宠运行时文件变成可直接执行的主题包。主项目新增的桌宠 EXE 导入/启动属于另行改动，本条只判断第三方原生包不能直接冒充 `.tspack`。

# Relevant extracted content

> “导出的 `.tspack` 是标准 ZIP，包含壁纸、动态视频（如有）、鼠标、图标和 `theme.json`”；解压后 `theme.json` 与素材必须位于压缩包根目录，不能外面再套一层文件夹。

> 最小套装包含 `theme.json` + `wallpaper.jpg`；`schemaVersion: 1`，`id` 为小写字母/数字/连字符，`version` 为三段数字。素材路径均为包内相对路径。

> 包限制：最多 512 MB；解压总量最多 1 GB；最多 2048 项；单图最多 32 MB/4000 万像素；不支持脚本、EXE、DLL、外部绝对路径、加密压缩包或符号链接。

> 该版主题包文档写明数据包只包含外观素材，不包含快捷方式目标、系统备份、账户数据或可执行模组；Windows `.themepack`/`.deskthemepack` 也不属于此格式。当前桌宠 EXE 功能应以主项目最新实现和其专门说明为准。

---
**Time**: 2026-10-01
**Source**: `E:\desktop\windows\ThemeStudio-0.6.0\components\icon-workbench\theme_packages.py`
**Method**: extract (via PowerShell `Get-Content`; local project source)
**Confidence**: high
**Insight**: 该次读取的 v1 包导入实现仅接受 `.zip`/`.tspack`，解压到临时目录后要求根目录存在 `theme.json`，校验 `schemaVersion=1`、壁纸/缩略图、可选 MP4、完整 17 状态指针、ICO 图标和所有包内路径；数据包不得含链接、特殊文件、加密文件或未允许扩展名。它证明第三方桌宠的原生 ZIP/EXE/角色目录不能直接冒充 v1 `.tspack`；桌宠 EXE 新功能应按主项目最新代码的专门导入路径处理。

# Relevant extracted content

> `DATA_TYPES = IMAGE_TYPES | {'.ico', '.cur', '.ani', '.mp4', '.txt', '.json'}`；导入源扩展名限定 `.zip`/`.tspack`。

> 根目录缺少 `theme.json` 时抛出： “数据包根目录缺少 theme.json。普通 Windows .themepack 不适用于本应用。”

> manifest 必须 `schemaVersion == 1`；`cursors` 非空时必须完整提供 `ROLE_KEYS` 的 17 个状态；图标数量最多 100，关键词 1–30 个。

> 校验拒绝链接、特殊文件、加密压缩包、重复文件名、不安全路径、超大档案和不支持扩展名；文件最终复制到 `%LOCALAPPDATA%\\ThemeStudio\\theme-packs` 资产库。

---
**Time**: 2026-10-01
**Source**: https://bluearchive.nexon.com/
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for official rights entry
**Insight**: Blue Archive official Nexon page is reachable but displays a regional service restriction; footer states © NEXON Korea Corporation. It serves as official publisher/rights reference only; no desktop pet or ThemeStudio package was exposed. Community Shiroko DSH plugin must remain labeled unofficial with separate asset rights.

# Relevant extracted content

> Browser title: “블루 아카이브”; URL `https://bluearchive.nexon.com/`.

> Page message: “This game is not serviced in the country you are connected to.” Footer: “© NEXON Korea Corporation All Rights Reserved.”

> 页面未提供桌宠下载、素材授权或 ThemeStudio 导入说明。

---
**Time**: 2026-10-01
**Source**: https://www.chiikawaofficial.com/
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for official franchise entry
**Insight**: Chiikawa official site明确介绍 Chiikawa、Hachiware、Usagi 及其作者/插画家 Nagano，提供官方角色页与社交入口；页面未提供桌宠/桌面应用下载或可自由再分发素材。社区 Codex/Windows 桌宠应标记为非官方并保留 Nagano/权利方声明。

# Relevant extracted content

> Browser title: “chiikawa official”; URL `https://www.chiikawaofficial.com/`.

> “What started as a social media manga created by the illustrator Nagano ... Chiikawa, along with best friends Hachiware and Usagi ...”; official page links characters and social account `@Chiikawa.official`.

> 页面提供 characters/home/about/social/terms/privacy/contact，但未出现桌宠安装包或主题包导入说明。

---
**Time**: 2026-10-01
**Source**: https://www.arknights.global/
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: 明日方舟官方全球站可访问，导航含 HOME、CHARACTER、NEWS、DISCOVER、GAMEPLAY、COMIC、GALLERY 及官方社媒链接；本次入口未见桌宠下载、模型包授权或 ThemeStudio 导入说明。桌宠来源应标记为社区 ArkPets/Ark-Models，而非官方桌宠。

# Relevant extracted content

> Browser title: “Arknights”; URL `https://www.arknights.global/`; page exposes official social links including @ArknightsEN、ArknightsGlobal、官方 Discord、Yostar Store。

> 页面未出现桌宠、桌面应用或可导入主题资源说明。

---
**Time**: 2026-10-01
**Source**: https://pgr.kurogame.net/
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: 战双国际站官方入口可访问，页脚标注 KURO TECHNOLOGY（HONG KONG）CO., LTD. 对站内图像、文本、音频、视频拥有权利并禁止未授权使用/复制；本次页面没有桌宠或主题包下载。因此任何战双同人桌宠素材都应先做权利审查，不能从官方站点推导可再分发授权。

# Relevant extracted content

> Browser title: “Punishing: Gray Raven”; URL `https://pgr.kurogame.net/`.

> Footer: “All rights of images, texts, audio, videos, etc. published on this website belong to KURO TECHNOLOGY (HONG KONG) CO., LTD. Unauthorized use or copying is strictly prohibited.”

> 页面未呈现桌宠安装包/开发者资源包/ThemeStudio 导入格式。

---
**Time**: 2026-10-01
**Source**: https://www.identityvgame.com/
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: 第五人格官方入口页面标题为 “Identity V Official Website”，页脚标注 Joker Studio、NetEase 的版权；本次页面未提供桌宠或 ThemeStudio 资源。已核验园丁桌宠仓库明确声明与网易/第五人格官方无关。

# Relevant extracted content

> Browser title: “Identity V Official Website”; URL `https://www.identityvgame.com/`.

> Footer: “©Joker Studio ©2020 NetEaseInc. All Rights Reserved”.

> 页面未出现桌宠安装包、资源包或导入说明。

---
**Time**: 2026-10-01
**Source**: https://genshin.hoyoverse.com/en/
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: medium
**Insight**: 直接访问该 HoYoverse 域名的标题显示为当前原神活动页 “A Rekviem for the Underworld”；页面首先出现 Cookie 提示，未进一步展开内容。它可作为原神官方站点入口，但本次页面状态未提供桌宠下载或 ThemeStudio 素材授权证据。

# Relevant extracted content

> URL: `https://genshin.hoyoverse.com/en/`; browser title: “A Rekviem for the Underworld”.

> 页面可见 Cookie 提示；未看到桌宠、桌面应用或可导入主题包信息。

---
**Time**: 2026-10-01
**Source**: https://hsr.hoyoverse.com/en-us/
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: HoYoverse 官方星穹铁道域名可访问，页面标题为 “Honkai: Star Rail official site — The brand-new Version 4.6 ... is now online!”。本次入口页只确认官方品牌/游戏站点，未发现桌宠下载或 ThemeStudio 资源授权。

# Relevant extracted content

> URL: `https://hsr.hoyoverse.com/en-us/`; browser title explicitly includes “Honkai: Star Rail official site”.

> 页面未呈现桌宠安装包、开发者资源包或 ThemeStudio 导入说明。

---
**Time**: 2026-10-01
**Source**: https://zenless.hoyoverse.com/en-us/
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: HoYoverse 官方绝区零域名可访问，标题为 “Zenless Zone Zero Official Website - Version 3.2 ... Is Now Live!”。该入口确认官方品牌来源，但本次页面没有桌宠/ThemeStudio 下载或授权内容；绝区零桌宠证据来自前述社区仓库。

# Relevant extracted content

> URL: `https://zenless.hoyoverse.com/en-us/`; browser title explicitly includes “Zenless Zone Zero Official Website”.

> 页面未呈现桌宠安装包、社区资源许可或 ThemeStudio 导入说明。

---
**Time**: 2026-10-01
**Source**: https://wutheringwaves.kurogames.com/en/
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: 这是《鸣潮》发行方 KURO GAMES 的官方网站入口，页面标题为 “Wuthering Waves Official Website”，页脚明确显示 “Copyright ©KURO GAMES. ALL RIGHTS RESERVED.”。它可作为角色/商标权利方的官方入口，但当前页面只呈现游戏官网/服务条款等内容，未提供可核验的桌宠下载或 ThemeStudio 素材授权；因此不能标记为官方桌宠来源。

# Relevant extracted content

> Browser title: “Wuthering Waves Official Website”; resolved URL: `https://wutheringwaves.kurogames.com/en/`.

> Page footer: “Copyright ©KURO GAMES. ALL RIGHTS RESERVED.”; contact `wutheringwaves_ensupport@kurogames.com`; Privacy Policy and Terms of Service links are on the same official domain.

> 页面可见内容为游戏介绍、年龄/服务提示、官方社群入口与平台商标声明；未出现桌宠、桌面应用、开发者素材包或 ThemeStudio 导入格式。

> 结论边界：可确认官方品牌入口与权利方，不可据此推断存在官方桌宠或允许将官网素材打包再分发。

---
**Time**: 2026-10-01
**Source**: https://github.com/search?q=pgr+desktop+pet&type=repositories
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for this exact GitHub query only
**Insight**: GitHub 对 PGR 简称 `pgr desktop pet` 仍返回 0 个仓库；战双主题暂记为“未找到可核验 GitHub 桌宠来源”，需要其他渠道或更宽泛检索。

# Relevant extracted content

> GitHub search result count: 0.

---
**Time**: 2026-10-01
**Source**: https://github.com/search?q=punishing+gray+raven+desktop+pet&type=repositories
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for this exact GitHub query only
**Insight**: GitHub 精确搜索“punishing gray raven desktop pet”返回 0 个仓库；目前没有找到可核验的战双桌宠 GitHub 来源。需继续用 PGR/战双/帕弥什别名或其他平台检索，不能将 0 结果外推为全球不存在。

# Relevant extracted content

> GitHub search result count: 0; page says “Your search did not match any repositories.”

---
**Time**: 2026-10-01
**Source**: https://github.com/mldhao/dsh-blue-archive-shiroko
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: 这是蔚蓝档案白子同人桌宠与 DSH Web 插件一体的来源，面向 DeepSeek Harness 而不是 ThemeStudio。推荐安装 GitHub Release `dsh-blue-archive-shiroko-0.6.0.tgz`，通过 `dsh plugin --profile web add` 添加，需已安装运行中的 DSH Web、现代 Chromium 浏览器；桌宠图像嵌入插件 JavaScript，默认可替换 `assets/shiroko-custom.webp` 并同步 `PET_IMAGE`。代码 MIT，但角色/图片不在 MIT 范围，项目仅供学习/个人定制/同人交流。

# Relevant extracted content

> 项目说明：面向 DeepSeek Harness Web 客户端的非官方同人插件；提供蔚蓝档案风格 UI 与可拖动、抚摸、同步回复、余额查询的白子桌宠；与 NEXON/Yostar/Blue Archive/OpenAI 无隶属、授权或合作。代码 MIT，角色名称/形象/用户图片不在 MIT 范围。

> 环境：已安装并运行 DeepSeek Harness/DSH，启用 DSH Web 客户端；余额功能需要有效 `DEEPSEEK_API_KEY`；需要 Chromium/Chrome/Edge 等现代浏览器。

> 安装包：从 GitHub Releases 下载 `dsh-blue-archive-shiroko-0.6.0.tgz`，执行 `dsh plugin --profile web add "...tgz"`，完全重启 DSH Web 后 Ctrl+F5。

> 资产：默认桌宠图 `assets/shiroko-custom.webp`；插件运行图像还内嵌在 `lib/client.js` 的 `PET_IMAGE`，替换图像必须同步更新。仓库没有声明 ThemeStudio `.tspack` 支持。

> 许可边界：源代码 MIT；角色、名称和图片素材不属于 MIT；README 建议仅学习、个人定制和同人交流。

> 兼容性判断：DSH `.tgz` 插件 + WebP 资源，不是 ThemeStudio `theme.json`/`.tspack`；不能直接导入 ThemeStudio。

---
**Time**: 2026-10-01
**Source**: https://github.com/search?q=blue+archive+desktop+pet&type=repositories
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for discovery, pending repository verification
**Insight**: GitHub 搜到两个蔚蓝档案桌宠候选：`mldhao/dsh-blue-archive-shiroko`（DSH 主题 + 砂狼白子桌面伴侣，JavaScript，1 star）和 `YixuAn-13/codex-pet-collection`（Codex CLI/CC-Haha，包含玛丽 Mari 两套 9 状态精灵桌宠，0 stars）。需直接读仓库确认包格式、运行时与资产声明。

# Relevant extracted content

> `mldhao/dsh-blue-archive-shiroko`：Blue Archive-inspired DSH theme with a Shiroko desktop companion, Codex-style reply bubbles, petting effects, completion chime；JavaScript；1 star。

> `YixuAn-13/codex-pet-collection`：animated desktop pets for Codex CLI & CC-Haha，Blue Archive Mari sprite pets（Idol & Gym ver.）、9-state animations；0 stars，9 days ago。

---
**Time**: 2026-10-01
**Source**: https://github.com/search?q=milkmocha+desktop+pet&type=repositories
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for this exact GitHub query only
**Insight**: GitHub 对 `milkmocha desktop pet`（不带空格）同样返回 0 个仓库；Milk Mocha 主题目前没有找到可核验 GitHub 桌宠来源。继续检索应使用其他平台/拼写，不能把该结果当作全球不存在证明。

# Relevant extracted content

> GitHub search result count: 0.

---
**Time**: 2026-10-01
**Source**: https://github.com/search?q=%22milk+mocha%22+desktop+pet&type=repositories
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for this exact GitHub query only
**Insight**: GitHub 对精确短语 “milk mocha” desktop pet 返回 0 个仓库。该结果不能证明没有 Milk & Mocha 桌宠；它只说明该精确短语下未找到 GitHub repository，需要其他拼写/平台或官方社媒进一步检索。

# Relevant extracted content

> GitHub search result count: 0; page says “Your search did not match any repositories.”

---
**Time**: 2026-10-01
**Source**: https://github.com/frobel0520/chiikawa-desktop-pets
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: 这是一个 Windows 原生桌面宠物同人仓库，使用 Electron 透明置顶窗口，三个 Chiikawa 角色各有 8 格行走循环；源码运行 `npm.cmd install` + `npm.cmd start`，可用 `npm.cmd run dist` 生成 `dist/Chiikawa Desktop Pets 1.0.0.exe` 便携程序。README 明确是个人非官方项目，角色版权归 Nagano/权利方；当前 README 还提醒只重整文档、未重新核验运行行为。它是独立 Electron EXE，不是 ThemeStudio 包格式。

# Relevant extracted content

> 功能：透明、置顶、无框窗口；吉伊卡哇、小八猫、乌萨奇各自 8 格步行循环；可拖曳，透明区点击穿透；30 FPS。

> 源码运行：双击 `Launch Chiikawa Desktop Pets.vbs`，或 `npm.cmd install`、`npm.cmd start`。

> 便携构建：`npm.cmd run dist`，产物 `dist/Chiikawa Desktop Pets 1.0.0.exe`。

> 项目结构：Electron `electron-main.js`/`preload.js`；`desktop.html/.css/.js` 桌宠逻辑；`assets/` 三角色步行动画；`tools/` Python 切图对齐脚本。

> 许可证/来源： “Unofficial fan project for personal use. Chiikawa characters belong to Nagano and their rights holders.” README 未显示可将角色素材自由再分发的开源授权。

> 运行证据边界：README 的 known limitations 明确当前 PR 只整理文档、没有重新核验运行行为；因此只能确认仓库给出的构建/运行说明，不能把在线搜索页面当作已运行验证。

> 兼容性判断：独立 Electron/portable EXE + PNG 资源，不是 ThemeStudio `.tspack`，不能直接导入。

---
**Time**: 2026-10-01
**Source**: https://github.com/hyc1228/chiikawa-codex-pet
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: 这是可核验的 Chiikawa/乌萨奇/小八非官方 Codex v2 桌宠合集，三个角色各有 ZIP 包，内容仅为 `pet.json` + `spritesheet.webp`，复制到 `~/.codex/pets/<id>/` 后重启 Codex。该仓库明确为 Nagano 角色的非官方、由网络参考图经 ChatGPT 重绘的个人非商业适配，角色美术不视为开源。它还记录了与 agent-pet/Tauri 桌宠的兼容边界：上游只接受 v1 8×9 精灵图，本仓库 v2 为 8×11/1536×2288，需要补丁。它不是 ThemeStudio `.tspack`。

# Relevant extracted content

> 仓库提供角色包：`chiikawa/pet.json + spritesheet.webp`、`usagi/...`、`hachiware/...`；单角色 ZIP 与三角色完整 ZIP 均列出。

> Codex 安装：将角色文件夹复制到 `~/.codex/pets/`，完全退出并重启 Codex，在桌宠设置选择；每个角色文件夹只有 `pet.json` 和 `spritesheet.webp`。

> Codex v2 图集：11 行动画、16 个鼠标视线方向；与 agent-pet 上游 v1（8×9、1536×1872）不兼容；仓库提供 `patches/agent-pet/0001-support-v2-spritesheets.patch` 等补丁，按编号应用后才可使用 agent-pet。

> agent-pet 构建：前置 Node.js 18+、Rust 和平台构建工具；`npm install` + `npm run tauri build`。Windows 用户级目录为 `%APPDATA%\\agent-pet\\pets\\`，仓库内置 `pets/` 目录更可靠。

> 素材声明：素材来源为 Nagano；参考图片从网络下载并由 ChatGPT 根据关键词重绘；项目是非官方、个人非商业适配，与权利人无从属/背书关系，角色美术不应视为开源。

> 兼容性判断：Codex v2 `pet.json`/WebP 精灵图和 agent-pet 补丁不是 ThemeStudio `theme.json`/`.tspack`; 需要独立转换和审查，不能直接导入。

---
**Time**: 2026-10-01
**Source**: https://github.com/search?q=chiikawa+desktop+pet&type=repositories
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for discovery, pending repository verification
**Insight**: GitHub 搜索到 15 个 Chiikawa 桌宠候选。强候选包括 `hyc1228/chiikawa-codex-pet`（Codex v2，Python，7 stars）、`gitChara-dot/Yaha-Pet`（Python）、`WayneYe912/OhMyChiikawa`（macOS JavaScript）、`DAOjun0690/ChiikawaDesktopPet`（C#）、`Mono303/chiikawa-desktop-pet`（Electron + GIF）、`frobel0520/chiikawa-desktop-pets`（Windows 上方行走的 Python 桌宠）、以及 `zhyuh777/chiikawa-pet`（Tauri v2）。需要逐个读取页面才能确认运行方式/许可。

# Relevant extracted content

> 结果数：15。`hyc1228/chiikawa-codex-pet` 描述为 “Unofficial Chiikawa, Usagi, and Hachiware desktop pets for Codex v2”，Python，7 stars，24 days ago。

> `Mono303/chiikawa-desktop-pet` 描述为 Electron 的透明置顶 GIF 角色；`frobel0520/chiikawa-desktop-pets` 描述为在 Windows 任务栏上方行走的三个动画桌宠；`zhyuh777/chiikawa-pet` 描述为 Tauri v2、带待办/学习/升级系统的 Chiikawa 桌宠。

---
**Time**: 2026-10-01
**Source**: https://github.com/iisland2008/identity-v-gardener-desktop-pet
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: 这是《第五人格》园丁（艾玛·伍兹）非官方同人桌宠，目标是 macOS 的 Codex 状态联动；README 给出 Electron/npm 开发与 macOS DMG/ZIP 打包流程，没有 Windows 运行方式。它监听 Codex 会话生命周期事件（只解析 `task_started`、`task_complete`、`turn_aborted` 和时间，不读对话正文），因此不能直接作为 Windows ThemeStudio 桌宠运行时或 `.tspack` 导入。项目未显示开源许可证，声明素材/代码按发布者另行许可。

# Relevant extracted content

> README： “一款使用原创 Q 版素材制作的《第五人格》园丁（艾玛·伍兹）同人桌宠。”

> 功能：拖动帽子、点击随机台词；监听 Codex 会话生命周期，状态包括任务进行中/任务完成/待机；只解析 `task_started`、`task_complete`、`turn_aborted` 三种事件及时间，不读取对话正文。

> 运行/打包：本地 `npm install`、`npm start`；`npm run dist:mac` 生成 macOS `release/` 下 Apple Silicon arm64 DMG 和 ZIP。页面没有 Windows 安装/构建指引。

> 同人声明：项目“为非官方同人作品，与网易游戏及《第五人格》官方无关”；角色及世界观归权利人；桌宠插画和程序代码按发布者另行声明的许可使用；不得冒充官方或用于未经授权的商业用途。

> 兼容性判断：macOS Electron/Codex 联动项目，不是 ThemeStudio `.tspack`，无证据支持 Windows 运行或 ThemeStudio 直接导入。

---
**Time**: 2026-10-01
**Source**: https://github.com/search?q=identity+v+desktop+pet&type=repositories
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for discovery, pending repository verification
**Insight**: GitHub 精确搜索到 1 个第五人格桌宠候选：`iisland2008/identity-v-gardener-desktop-pet`，描述为“第五人格园丁艾玛·伍兹非官方 Codex 状态联动桌宠”，JavaScript，搜索页显示 0 stars、19 days ago 更新。其描述已明确非官方；需直接读取 README 以确认包格式与导入路径。

# Relevant extracted content

> Search result count: 1. Candidate: `iisland2008/identity-v-gardener-desktop-pet`; description “第五人格园丁艾玛·伍兹非官方 Codex 状态联动桌宠”; language JavaScript; 0 stars; updated 19 days ago.

---
**Time**: 2026-10-01
**Source**: https://github.com/isHarryh/Ark-Models
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: Ark-Models 是 ArkPets 配套的明日方舟 Spine 模型库，README 明确格式与运行要求：Spine Runtime v3.8，模型通常由 `.atlas`、`.skel` 与 `.png` 组成，模型分目录并由 `models_data.json` 索引；完整仓库 ZIP 约 1 GB，也可单模型下载。素材版权归上海鹰角网络有限公司，禁止商用。该格式明显不同于 ThemeStudio 的图标/壁纸主题包。

# Relevant extracted content

> 仓库内容：`models`（干员基建小人）、`models_enemies`（敌人战斗小人）、`models_illust`（动态立绘）；由 ArkUnpacker 提取。

> 格式说明：明日方舟 Spine 模型需要 Spine Runtime v3.8；一套模型通常包含 `.atlas`、`.skel`、`.png`；每个模型独立子目录；`models_data.json` 记录具体信息。

> 下载：完整压缩包约 1 GB；支持按需下载单个模型；Git 浅克隆命令也在 README 中给出。

> 版权声明： “本仓库中所有素材其版权归属上海鹰角网络有限公司所有。不得用于商业用途，不得损害版权方的利益。”

> 兼容性判断：Spine 模型资源需 ArkPets/Spine v3.8 运行时；不支持直接作为 ThemeStudio `.tspack`、GIF 或 PNG 单图主题导入。

---
**Time**: 2026-10-01
**Source**: https://github.com/isHarryh/Ark-Pets
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: ArkPets 是目前最成熟的明日方舟桌宠来源之一：公开 GitHub 项目、GPL-3、Windows 7+，官方项目页与模型库分离。安装器 `ArkPets-Setup.exe` 启动后需在启动器“模型库管理”下载模型；也支持从 Ark-Models 手动下载模型 ZIP，在“导入压缩包”中导入。另有免安装 ZIP 和 JDK17 可运行的 JAR。它使用游戏角色 Spine 模型/项目专有模型库，不是 ThemeStudio `.tspack`，也不是普通 GIF。

# Relevant extracted content

> 项目简介： “Arknights Desktop Pets | 明日方舟桌宠 (ArkPets)”，功能包括将《明日方舟》角色模型作为桌宠启动、启动器浏览模型/设置、模拟基建/敌方小人、平面重力、托盘菜单和开机自启。

> 使用：仅支持 Windows 7 及以上；下载 `ArkPets-Setup.exe`，安装后打开启动器；首次使用在“模型库管理”点击“下载模型”，再检索角色并点击“启动”。

> 模型导入：若软件内下载失败，可从 `https://github.com/isHarryh/Ark-Models` 手动下载模型压缩包，在“模型库管理”点击“导入压缩包”。页面也提供 zip 免安装版；存在 JDK17 时可直接运行 jar（无开机自启）。

> 许可证：README 明确基于 GPL3，源代码/版权声明需保留作者说明和原协议；角色模型/游戏素材仍须按相应权利人及模型库声明处理。

> 兼容性判断：ArkPets 的模型 ZIP/Spine 资源由 ArkPets 启动器导入；不能直接作为 ThemeStudio `.tspack`、普通 GIF 或 `theme.json` 导入。

---
**Time**: 2026-10-01
**Source**: https://github.com/search?q=arknights+desktop+pet&type=repositories
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for discovery, pending repository verification
**Insight**: GitHub 搜索到 30 个明日方舟桌宠相关仓库，强候选包括 `isHarryh/Ark-Pets`（ArkPets，Java/LibGDX/Spine，1107 stars，4 天前更新）、`Wyuio-0/DesktopPet`（Python，双端，5 stars）、`csz111182/Arknights-Desktop-Pet`（JavaScript，支持令/遥/阿米娅切换，3 stars，2 天前更新）、`JNGKZbird/Arknights-Angelina-Pet-YuYuan`（多平台 Spine 运行时，3 stars）。搜索结果只做发现，需以仓库 README/许可证/交付文件为准。

# Relevant extracted content

> 结果数量：30。`isHarryh/Ark-Pets` 描述为 “Arknights Desktop Pets | 明日方舟桌宠 (ArkPets)”，Java，LibGDX/Spine 标签，1107 stars，4 days ago。

> 其他候选：`Wyuio-0/DesktopPet` 为“明日方舟双端桌宠”（Python）；`csz111182/Arknights-Desktop-Pet` 为非官方明日方舟桌宠，支持角色切换/语音/移动/DeepSeek，JavaScript；`JNGKZbird/Arknights-Angelina-Pet-YuYuan` 描述为 Windows/鸿蒙/安卓多端并自研 Spine 3.8 运行时。

---
**Time**: 2026-10-01
**Source**: https://github.com/xiyan1314/daifeiyu-desktop-pet
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: 这是一个绝区零风格同人桌宠（性格参考希希芙/“啥子蛇”），基于 PySide6 + Python 3.10，MIT 开源；Windows 绿色版以 ZIP 分发，内含微软签名 `pythonw.exe` 与运行库，双击 `启动桌宠.vbs`，也可源码运行。它支持导入 PNG/JPG/BMP/WebP，视频/GIF 会自动抽帧成多帧动画，数据保存在 `roles/`、`audio/` 等程序目录文件中。该导入能力属于大肥鱼程序自身，不能把这些资源直接视为 ThemeStudio `.tspack`。

# Relevant extracted content

> README：Windows 桌面宠物，基于 PySide6（Qt6）+ Python 3.10，MIT 开源；透明无边框置顶窗口，可拖动、投喂、聊天等。

> 免安装绿色版：从 Releases 下载 `daifeiyu-desktop-pet.zip`，解压 `大肥鱼桌宠_绿色版` 文件夹，双击 `启动桌宠.vbs`；绿色版使用微软签名的 `pythonw.exe` + 完整运行库，无需 Python。

> 角色导入：右键“角色”→“导入角色”，支持 PNG/JPG/BMP/WebP；1–8 个形态；多选图片可做帧序列，选择视频或 GIF 可自动抽帧（视频 3–20 帧、GIF 3–24 帧）；角色库保存在 `roles/` + `roles.json`，音频在 `audio/` + `audio.json`。

> 项目声明：MIT 许可证。README 说性格参考绝区零希希芙，页面未声称官方授权；应按同人内容审查角色素材来源。

> 兼容性判断：可导入格式是程序内角色资源（PNG/JPG/BMP/WebP/GIF/视频），不是 ThemeStudio 包格式。ThemeStudio 若要采用，应重新打包为自身 `theme.json` + 资源目录，不能直接导入该 ZIP。

---
**Time**: 2026-10-01
**Source**: https://github.com/YYKIG/codex_pet_Angels_of_Delusion
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: 这是可核验的《绝区零》同人桌宠包，面向 Codex v2 桌宠运行时而非 ThemeStudio。仓库提供三个 ZIP 包，安装时把各包内的 `pet.json` 和 `spritesheet.webp` 复制到 `%USERPROFILE%\\.codex\\pets\\<宠物 ID>\\`，完全退出并重启 Codex；图集规范为 `spriteVersionNumber: 2`、8×11、单格 192×208、透明 WebP。仓库代码标注 MIT，但角色/联动素材权利归原作者/权利人，README 限于个人学习、技术研究和非商业展示。

# Relevant extracted content

> README：三个可独立安装的 Codex v2 桌宠包：`packages/Nangong_Yu-codex-pet/`、`packages/Aria-codex-pet/`、`packages/Sunna-codex-pet/`；参考《绝区零》× KFC「天使降临 美味 On Air」联动舞台服和官方 Q 版小人。

> 下载文件：`dist/Nangong_Yu-codex-pet.zip`、`dist/Aria-codex-pet.zip`、`dist/Sunna-codex-pet.zip`。

> 安装：将包内 `pet.json` 与 `spritesheet.webp` 复制到 `%USERPROFILE%\\.codex\\pets\\<宠物 ID>\\`，ID 为 `Nangong_Yu`、`Aria`、`Sunna`，复制后完全退出并重启 Codex。

> 图集：`spriteVersionNumber: 2`; 8 列 × 11 行; 单格 192 × 208; 图集 1536 × 2288; 透明 WebP。

> 权利说明：角色及联动素材版权归原作者与权利人所有；项目仅用于个人学习、技术研究和非商业桌面展示。GitHub 页面显示仓库 LICENSE 为 MIT，但该代码许可证不自动覆盖角色美术/联动素材。

> 兼容性判断：这是 Codex v2 `pet.json`/spritesheet 目录格式，不是 ThemeStudio `.tspack`/`.zip`；不能直接导入 ThemeStudio，除非编写转换器并完成权利审查。

---
**Time**: 2026-10-01
**Source**: https://github.com/search?q=zenless+zone+zero+desktop+pet&type=repositories
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for discovery, pending repository verification
**Insight**: GitHub 搜索到两个绝区零相关候选：`YYKIG/codex_pet_Angels_of_Delusion`（Python；天使恶魔三人组）和 `xiyan1314/daifeiyu-desktop-pet`（PySide6；README 描述为绝区零风格的大肥鱼桌宠）。搜索页本身不确认官方性、许可证或可导入格式。

# Relevant extracted content

> `YYKIG/codex_pet_Angels_of_Delusion` 描述为 “Codex desktop pets for Zenless Zone Zero's Angels of Delusion trio”，搜索结果显示 Python、1 star。

> `xiyan1314/daifeiyu-desktop-pet` 描述为 PySide6 桌面宠物，双形态帧动画、投喂、戳戳链、DeepSeek AI 对话，性格参考绝区零希希芙；搜索结果显示 Python、0 stars，最近更新约 1 小时前。

---
**Time**: 2026-10-01
**Source**: https://github.com/Morgan0425/hsr-yinyuejun-desktop-pet
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: 找到可核验的《崩坏：星穹铁道》饮月君同人桌宠，提供 Windows ZIP + `Start-YinyueJun-Pet.bat`，基于 Windows PowerShell 5.1 与 WPF，无需 Python 或其他运行库；macOS 另有 AppKit ZIP。README 明确为非官方个人项目且仓库未附加开源许可证，因此只能作为作者自有分发的候选来源，不能将其直接重分发或并入 ThemeStudio。

# Relevant extracted content

> README：原生 macOS 透明桌面宠物，同时提供 Windows 10/11 PowerShell + WPF 版本；“均不包含联网、生图或销售功能”。

> Windows 安装：从 GitHub Releases 下载 `饮月君桌宠-Windows.zip`，解压整个文件夹，双击 `Start-YinyueJun-Pet.bat`；“Windows 版使用系统自带的 Windows PowerShell 5.1 与 WPF，无需安装 Python 或其他运行库”。

> 源码/素材：仓库保存 9 张 4×4 原始精灵图；构建时生成 128 张连续动画帧和 1 张闭眼静态图。项目结构包含 `WindowsPet/`、`SourceSheets/`、`tools/process_sprites.py` 与 Windows 打包脚本。

> 权利声明： “本项目为非官方个人桌宠项目。角色与美术相关权利归各自权利人所有；仓库目前未附加开源许可证。”

> 兼容性判断：交付是独立 Windows ZIP/WPF 宠物，不是 ThemeStudio `.tspack`，也不是单个 GIF；需按作者 ZIP+BAT 运行或重新制作 ThemeStudio 主题资源，不能直接导入。

---
**Time**: 2026-10-01
**Source**: https://github.com/search?q=hsr+desktop+pet&type=repositories
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for discovery, pending repository verification
**Insight**: Abbreviation search `hsr desktop pet` returned one public candidate, `Morgan0425/hsr-yinyuejun-desktop-pet`, updated 22 days before the search page was rendered. The result does not state license, packaging, or runtime; those must be read from the repository page.

# Relevant extracted content

> GitHub search result count: 1. Repository: `Morgan0425/hsr-yinyuejun-desktop-pet`; language label Objective-C; result page shows 2 stars and “Updated 22 days ago”.

---
**Time**: 2026-10-01
**Source**: https://github.com/search?q=honkai+star+rail+desktop+pet&type=repositories
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for this query result only
**Insight**: GitHub repository search returned 0 repositories for the exact “honkai star rail desktop pet” query. This is only a discovery limitation; it does not prove that no community pet exists elsewhere (e.g., other terms, platforms, or asset-only sources).

# Relevant extracted content

> Search result count shown by GitHub: 0; page says “Your search did not match any repositories.”

---
**Time**: 2026-10-01
**Source**: https://github.com/ChaozhongLiu/DyberPet
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: 当前 DyberPet 是 PySide6 桌宠框架，README 标注最新 v0.10.3 Windows 已有 EXE 发布；角色、物品、迷你宠物可通过 MOD 扩展，页面明确说“JSON 配置即可上手创作”，并提供素材合集与开发文档。它是可承载多主题角色的独立运行时，但其角色目录规范与 ThemeStudio `.tspack` schema 不同，需做适配/转换，不能直接导入。

# Relevant extracted content

> README：桌宠系统包含动画、交互、养成、任务、商店与迷你宠物；“MOD 生态：角色、道具、音效、迷你宠物均可自由扩展与创作”；“JSON 配置即可上手创作”。

> README：最新版本 v0.10.3，Windows 版本已打包发布；Windows 用户“将 Release 下载至本地，双击 EXE 文件即可”。源码运行区仅开放到 v0.6.7，需 Python 3.9.18、PySide6 6.5.2、PySide6-Fluent-Widgets 1.5.4 等依赖并运行 `run_DyberPet.py`。

> README：素材与模组合集 `docs/collection.md` 收录已有角色、物品模组和迷你宠物及下载链接，并“欢迎下载并通过 App 导入”。

> 素材开发文档 `docs/art_dev.md`：角色放在 `res/role/PETNAME/`，包括 `pet_conf.json`、`act_conf.json`、可选 `msg_conf.json`、`action/` PNG 帧、可选 `note/` 与 `info/`。透明 PNG 帧按同一前缀加 `_0.png`, `_1.png` 顺序命名；动作与尺寸/速度/锚点由 JSON 配置控制。

> 运行时/格式判断：该仓库的“角色文件夹 + JSON + PNG/WAV 等素材”是 DyberPet 原生 MOD 目录格式；没有证据表明它接受 ThemeStudio `.tspack` 或普通 GIF 直接导入。对 ThemeStudio 只能作为外部运行时或转换目标，需另行生成 ThemeStudio `theme.json`/资源布局。

---
**Time**: 2026-10-01
**Source**: https://github.com/ChaozhongLiu/DyberPet_GenshinImpact
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: 这是可核验的原神同人桌宠来源，但仓库 README 明确已停止维护，原神版本已合并到新版 DyberPet；旧仓库提供 Windows EXE、源码 ZIP 和角色文件夹迁移提示。其作者声明米哈游素材版权归米哈游、不得商用，动作/拆分来自 B 站作者并要求注明出处；项目本身遵循 GPL v3。不能把该 EXE 或角色文件夹直接当成 ThemeStudio `.tspack`。

# Relevant extracted content

> “本仓库已停止维护，请前往新版 DyberPet”；“现在只需携带角色文件夹，即可迁移到新版 DyberPet”。

> Windows 使用方式：下载仓库 ZIP，解压后双击 `呆啵宠物-原神.exe`；程序不能离开文件夹，可创建快捷方式。页面同时提供源码仓库和旧版 `main.zip` 链接。

> 版权声明：宠物素材版权归米哈游所属，请勿商用；素材拆分和动作设计来自 B 站作者，转载/使用须注明出处；DyberPet 遵循 GPL v3。

> 页面指向新版框架：https://github.com/ChaozhongLiu/DyberPet 。新版需另行读取其当前 README/发行物，旧仓库不能代表新版当前安装格式。

---
**Time**: 2026-10-01
**Source**: https://github.com/search?q=genshin+desktop+pet&type=repositories
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high for discovery, low for implementation details until repository pages are read
**Insight**: GitHub repository search returned five public candidates: `ChaozhongLiu/DyberPet_GenshinImpact`, `GMCY2020/DesktopPet-Simple`, `Alex-jam-lab/Genshin-Impact-AI`, `TransientS1/Desktop-Pet`, and `szbszb547-shenzhen/Genshin-Impact-snow-queen-desktop-pet`. The results themselves do not establish official status or import compatibility; candidate pages require direct verification.

# Relevant extracted content

> Search result count: 5. Visible descriptions include “Genshin Impact Desktop Cyber Pet built with DyberPet” for `ChaozhongLiu/DyberPet_GenshinImpact`; “Genshin Impact Nahida Live2D desktop pet and chat application” for `Alex-jam-lab/Genshin-Impact-AI`; and “原神至冬女皇二创 · Windows 桌面宠物（PySide6）” for `szbszb547-shenzhen/Genshin-Impact-snow-queen-desktop-pet`.

---
**Time**: 2026-10-01
**Source**: https://github.com/KennyXiang/PhrolovaDeskPet
**Method**: browser-rendered (via Codex in-app browser/CUA)
**Confidence**: high
**Insight**: GitHub 公共仓库提供一个非官方《鸣潮》弗洛洛桌宠，明确为 PyQt5 应用，使用多个 PNG 状态图（静止、奔跑等），运行命令为 `python Deskpet.py`，需要 Python 3.8+ 和 PyQt5 依赖；README 明确声明是粉丝作品、非 Kuro Games 官方或背书。它是独立运行项目/源码，不是 ThemeStudio `.tspack`，不能直接作为 ThemeStudio 主题包导入。

# Relevant extracted content

> “A lightweight AI-powered desktop pet built with PyQt5, featuring a fan-made chibi version of Phrolova from Wuthering Waves.”

> Requirements: “Python 3.8 or later”; macOS / Windows / Linux. Run: `python Deskpet.py`; install dependencies: `pip install -r requirements.txt`.

> Animation assets: `images/fll_still.png`, `images/fll_run_1.png`, `images/fll_run_2.png`.

> Disclaimer: “This project is an unofficial fan-made work and is not affiliated with, sponsored by, or endorsed by Kuro Games.”

> Repository page exposes a GPL-3.0 license link; the README additionally limits intended use to learning, personal experimentation, and non-commercial use. Treat those statements as repository-specific caveats and review the actual asset provenance before redistribution.

---
