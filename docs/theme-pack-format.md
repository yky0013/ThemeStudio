# ThemeStudio 主题数据包 v1

使用者在“一键主题”点击“导入主题数据包”，选择 `.tspack` 或 `.zip`，套装便出现在列表中。先预览，再点击“一键应用”。数据包不会在导入时修改桌面。

最方便的制作方法：打开任意套装的预览，点击“导出完整套装”。导出的 `.tspack` 是标准 ZIP，包含壁纸、动态视频（如有）、鼠标、图标和 `theme.json`。解压后修改素材和清单，再把 **theme.json 与素材文件一起放在压缩包根目录**，压缩成 ZIP 即可导入。不要在外面多套一层文件夹。

## 最小静态套装

```text
my-theme.tspack
├── theme.json
└── wallpaper.jpg
```

```json
{
  "schemaVersion": 1,
  "id": "my-theme",
  "version": "1.0.0",
  "name": "我的桌面",
  "subtitle": "一套自己的桌面配色",
  "author": "素材作者",
  "artwork": "素材来源与授权说明",
  "accent": "#7967c6",
  "pale": "#e6e0f7",
  "wallpaper": "wallpaper.jpg"
}
```

`thumbnail` 可省略，默认显示静态壁纸。所有素材路径都是包内的相对路径，用 `/` 分隔，支持中文文件名。图片支持静态 JPG/JPEG、PNG、WebP、BMP。

## 动态壁纸、图标与鼠标

`animatedWallpaper` 可指定包内 MP4，例如 `wallpaper-motion.mp4`；建议 H.264、1080p、无音轨循环视频。`motionLabel` 是预览说明。MP4 容器校验不能保证任意视频编码都可播放，制作完成后应在预览中确认。必须保留 `wallpaper` 静态图，供静态模式与恢复使用。

图标字段示例：

```json
{
  "icons": {
    "browser": {
      "file": "icons/browser.ico",
      "matches": ["chrome", "edge", "firefox", "浏览器"]
    },
    "notes": {
      "file": "icons/notes.ico",
      "matches": ["notepad", "obsidian", "笔记"]
    }
  }
}
```

图标匹配当前电脑的快捷方式名称，不包含原电脑的绝对路径。匹配到多款图标时，使用清单中的第一款。每个图标需是有效 ICO，并提供 1–30 个名称关键词，最多 100 款。

`cursors` 可整体省略；若提供，必须包含以下 17 个键，分别指向 CUR/ANI 文件：

```json
{
  "cursorSize": 48,
  "cursorPreview": "cursor-preview.png",
  "cursors": {
    "Arrow": "cursors/Arrow.cur",
    "Help": "cursors/Help.cur",
    "AppStarting": "cursors/AppStarting.cur",
    "Wait": "cursors/Wait.cur",
    "Crosshair": "cursors/Crosshair.cur",
    "IBeam": "cursors/IBeam.cur",
    "NWPen": "cursors/NWPen.cur",
    "No": "cursors/No.cur",
    "SizeNS": "cursors/SizeNS.cur",
    "SizeWE": "cursors/SizeWE.cur",
    "SizeNWSE": "cursors/SizeNWSE.cur",
    "SizeNESW": "cursors/SizeNESW.cur",
    "SizeAll": "cursors/SizeAll.cur",
    "UpArrow": "cursors/UpArrow.cur",
    "Hand": "cursors/Hand.cur",
    "Person": "cursors/Person.cur",
    "Pin": "cursors/Pin.cur"
  }
}
```

`cursorSize` 默认为 48，可选 32–256、按 16 递增。`cursorPreview` 是可选的静态预览图。不含鼠标或图标的套装只应用它已有的内容。

## 版本与存储

- `id` 为 1–64 位小写英文字母、数字或连字符，同一套装更新时保持不变。主题版本为三段数字，例如 `1.0.0`、`1.1.0`。
- 完全相同的数据包重复导入会提示“已在套装库中”。修改素材后提高 `version`；新版替换套装卡片，旧素材仍保留供历史恢复使用。不会覆盖内置主题。
- 素材保存在 `%LOCALAPPDATA%\ThemeStudio\theme-packs`，应用升级与卸载默认保留。不要手动删除正在使用的素材或恢复记录。
- 单包最多 512 MB、解压总量最多 1 GB、最多 2048 项，单张图片最多 32 MB / 4000 万像素。不支持脚本、EXE、DLL、外部绝对路径、加密压缩包或符号链接。
- Windows 原生 `.themepack`、`.deskthemepack` 和旧“导出配置”的 `.theme.json` 不属于本数据包格式。
- 包只包含外观素材，不包含快捷方式目标、系统备份、个人账户数据或可执行模组。桌面模式仍由用户单独选择。

分享前确认素材的使用与再分发许可，保留作者和来源说明。
