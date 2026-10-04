# Explorer background research: source checkpoints

Each entry records one retrieved first-party source and the exact evidence used for the synthesis.

## Source checkpoint 1 — explorerTool README

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://github.com/Maplespe/explorerTool/blob/main/README.md
**Method**: browser-rendered (via `web__run` open; GitHub page lines 192–341)
**Confidence**: high
**Insight**: The archived Maplespe ExplorerBgTool directly implements custom images in Explorer's ItemView, with position, alpha, random selection, per-folder configuration, and a recovery path if an image crashes Explorer.

# Relevant extracted content

> “Customize Explorer ItemView background image” (lines 204–208).
>
> Windows 11 examples include bottom-right (`posType=3`), center (`posType=4`), and zoom-and-fill (`posType=6`), with `imgAlpha=140` (lines 219–232). The README also shows a Windows 10 entry and optional File Dialog loading (`folderExt=true`) (lines 234–242).
>
> Install: download the Release archive, put images in `image`, run `注册_Register.cmd`, and reopen Explorer. Uninstall: run `卸载_Uninstall.cmd`, or `regsvr32 /u "your path/ExplorerBgTool.dll"` (lines 243–272).
>
> Config fields: `random`, `custom`, `posType` (`0` left top, `1` right top, `2` left bottom, `3` right bottom, `4` center, `5` stretch, `6` zoom and fill), `imgAlpha` (0–255), and an absolute `folder` path (lines 273–304).
>
> Per-path settings use an INI section for a filesystem path or CLSID and an `img=` filename (lines 305–330). Supported formats are PNG and JPG. The author warns invalid images can crash Explorer; holding `ESC` while opening Explorer skips image loading so the tool can be uninstalled or the bad image removed (lines 331–341).

---

## Source checkpoint 2 — explorerTool license

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://github.com/Maplespe/explorerTool/blob/main/LICENSE
**Method**: browser-rendered (via `web__run` open; GitHub page lines 232–262)
**Confidence**: high
**Insight**: ExplorerBgTool is MIT-licensed, allowing reuse, modification, distribution, and sublicensing provided the copyright and permission notice are retained; the warranty is disclaimed.

# Relevant extracted content

> The file identifies the “MIT License” and copyright `(c) 2021 Maplespe` (lines 232–234). It grants rights to use, copy, modify, merge, publish, distribute, sublicense, and sell, subject to retaining the copyright and permission notice (lines 236–249), and provides the software “AS IS” without warranty (lines 251–262).

---

## Source checkpoint 3 — ExplorerBlurMica README

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://github.com/Maplespe/ExplorerBlurMica/blob/main/README.md
**Method**: browser-rendered (via `web__run` open; GitHub page lines 190 onward)
**Confidence**: high
**Insight**: ExplorerBlurMica supplies Explorer window blur/Acrylic/Mica and color blending, including WinUI/Xaml toolbar clearing, but the documented schema has only effect/color/clear flags and no image path or image rendering option.

# Relevant extracted content

> The README describes adding Blur, Acrylic, or Mica to Explorer on Windows 10 and Windows 11 (line 192), with custom blend colors and light/dark adaptation in the effects list.
>
> The documented config uses `effect` (`0=Blur`, `1=Acrylic`, `2=Mica`, `3=Blur(Clear)`, `4=MicaAlt`), `clearAddress`, `clearBarBg`, `clearWinUIBg`, `showLine`, and light/dark RGBA values; no image filename or image brush field is documented.

---

## Source checkpoint 4 — ExplorerBgTool hook implementation

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/Maplespe/explorerTool/main/ExplorerBgTool/dllmain.cpp
**Method**: browser-rendered (via `web__run` open; raw source, 603 lines)
**Confidence**: high
**Insight**: The source confirms a native GDI path that reaches the Explorer ItemView window rather than styling only the XAML command bar. It loads image files into GDI memory, identifies Explorer's `DirectUIHWND` below `SHELLDLL_DefView`, and draws on each `FillRect` call with `AlphaBlend`.

# Relevant extracted content

> Includes `<gdiplus.h>` and links `GdiPlus.lib` and `Msimg32.lib`; includes `MinHook.h`, `ShellLoader.h`, `WinAPI.h`, and `HookDef.h` (lines 17–29).
>
> `Config` has `imgPosMode`, `isRandom`, `isCustom`, `noerror`, `imgAlpha`, `folder`, and an `imageList` of loaded `BitmapGDI` objects (lines 102–126). `LoadSettings` reads `[image] random/custom/folder/posType/imgAlpha` and enumerates `*.png` and `*.jpg` (lines 215–311).
>
> `OnWindowLoad` starts GDI+, initializes MinHook, and hooks `CreateWindowExW`, `DestroyWindow`, `BeginPaint`, `FillRect`, and `CreateCompatibleDC` (lines 318–356).
>
> `MyCreateWindowExW` selects a `DirectUIHWND` whose parent is `SHELLDLL_DefView`, then checks the next parent for `ShellTabWindowClass` or `#32770` before recording the window and selecting a random image (lines 385–434). This is direct evidence of targeting the main Explorer ItemView host in the classic/Win32 tree.
>
> `MyFillRect` clips to the paint rectangle, computes top-left/right/center/stretch/zoom-fill placement, creates `BLENDFUNCTION { AC_SRC_OVER, 0, imgAlpha, AC_SRC_ALPHA }`, and calls `AlphaBlend` with the loaded bitmap memory DC (lines 473–586). It invalidates on size changes for non-top-left modes (lines 487–492).
>
> `GetKeyState(VK_ESCAPE)` causes `OnWindowLoad` to return without loading the hook (lines 318–323), providing the documented emergency recovery behavior.

---

## Source checkpoint 5 — ExplorerBgTool build target

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/Maplespe/explorerTool/main/ExplorerBgTool/ExplorerBgTool.vcxproj
**Method**: browser-rendered (via `web__run` open; raw MSBuild source, 202 lines)
**Confidence**: high
**Insight**: The project builds a native dynamic library for Win32 and x64 with Visual Studio v143, Unicode, and Windows target platform version `10.0`, so the source is structured for a Windows DLL/COM deployment rather than a WebView-only overlay.

# Relevant extracted content

> Project globals set `WindowsTargetPlatformVersion` to `10.0` (lines 20–26). Debug/Release configurations are `DynamicLibrary`, use `PlatformToolset` `v143`, and `CharacterSet` `Unicode` for Win32 and x64 (lines 28–45).

---

## Source checkpoint 6 — ExplorerBgTool shell loader and registration

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/Maplespe/explorerTool/main/ExplorerBgTool/ShellLoader.cpp
**Method**: browser-rendered (via `web__run` open; raw source, 287 lines)
**Confidence**: high
**Insight**: The DLL is a COM `IObjectWithSite`/BHO-style shell extension. Registration writes HKCR CLSID/InProcServer32 and HKLM Explorer BHO and FolderExtensions keys; unregister deletes those keys. This explains the administrator requirement and the reversible uninstall path.

# Relevant extracted content

> The fixed CLSID is `{ED15A97D-FE3E-4CDE-98FF-BC46B02896B0}` (lines 10–14). `CObjectWithSite::SetSite` obtains `IWebBrowser2`, finds `DIID_DWebBrowserEvents2`, and calls `Advise` (lines 54–75); `CIDispatch::Invoke` forwards `DISPID_DOCUMENTCOMPLETE` to `OnDocComplete` (lines 248–267).
>
> `DllRegisterServer` creates `HKCR\CLSID\{...}` and `InProcServer32`, sets the DLL path and `ThreadingModel=Apartment`, creates `HKLM\Software\Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects\{...}`, and creates `HKLM\SOFTWARE\Classes\Drive\shellex\FolderExtensions\{...}` with `DriveMask=255` (lines 156–199).
>
> `DllUnregisterServer` deletes the Explorer BHO, FolderExtensions, InProcServer32, and CLSID keys (lines 202–213).

---

## Source checkpoint 7 — ExplorerBgTool Win32/GDI helpers

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/Maplespe/explorerTool/main/ExplorerBgTool/WinAPI.cpp
**Method**: browser-rendered (via `web__run` open; raw source, 163 lines)
**Confidence**: high
**Insight**: The helper implementation uses Win32 INI APIs, file enumeration, GDI+ Bitmap loading, memory streams, compatible DCs, and `HBITMAP`, which are concrete dependencies for a reusable native backend.

# Relevant extracted content

> It links `shlwapi.lib` and uses `GetPrivateProfileStringW` to read INI values (lines 8–12 and 60–77), `_wfindfirst/_wfindnext` to enumerate files (lines 79–99), and `GetFileAttributesExW` for file sizes (lines 107–123).
>
> `BitmapGDI::BitmapGDI` reads the file into memory, creates an `IStream` with `SHCreateMemStream`, calls `Gdiplus::Bitmap::FromStream`, creates a compatible DC and HBITMAP, and selects the bitmap into the DC (lines 125–152). The destructor deletes the GDI+ bitmap, DC, and HBITMAP (lines 155–162).

---

## Source checkpoint 8 — ExplorerBgTool hook declarations

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://github.com/Maplespe/explorerTool/blob/main/ExplorerBgTool/HookDef.h
**Method**: browser-rendered (via `web__run` open; GitHub source page lines 284–343)
**Confidence**: high
**Insight**: The hook layer uses MinHook detours with typed trampolines for the five Win32 paint/window APIs, which is the smallest source-level surface needed to reproduce the ItemView image draw path.

# Relevant extracted content

> `CreateMHook` wraps `MH_CreateHook` and reports a failure with a message box (lines 301–305). Typed originals are declared for `CreateWindowExW`, `DestroyWindow`, `BeginPaint`, `FillRect`, and `CreateCompatibleDC` (lines 310–329), with corresponding detours exported as `MyCreateWindowExW`, `MyDestroyWindow`, `MyBeginPaint`, `MyFillRect`, and `MyCreateCompatibleDC` (lines 332–342).

---

## Source checkpoint 9 — MinHook dependency/license header

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/Maplespe/explorerTool/main/ExplorerBgTool/MinHook.h
**Method**: browser-rendered (via `web__run` open; raw source, 171 lines)
**Confidence**: high
**Insight**: The repository includes MinHook declarations and its BSD-2-Clause-style redistribution terms in the header, with x86/x64 support. A reimplementation or vendored copy must retain that notice and obtain/verify the accompanying implementation files.

# Relevant extracted content

> The header identifies “MinHook - The Minimalistic API Hooking Library for x64/x86” and permits source/binary redistribution with retained notices and disclaimer (lines 1–25). It rejects non-x86/x64 builds (lines 29–31) and declares `MH_Initialize`, `MH_CreateHook`, `MH_RemoveHook`, and hook enable/disable APIs (lines 88–143).

---

## Source checkpoint 10 — ExplorerBgTool WinAPI declarations

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/Maplespe/explorerTool/main/ExplorerBgTool/WinAPI.h
**Method**: browser-rendered (via `web__run` open; raw source, 61 lines)
**Confidence**: high
**Insight**: The header isolates the reusable helper surface: current DLL directory, file existence, window class lookup, INI reads, file enumeration, filename/size, and a `BitmapGDI` wrapper exposing a memory DC, HBITMAP, size, and GDI+ source bitmap.

# Relevant extracted content

> Declarations include `GetCurDllDir`, `FileIsExist`, `GetWindowClassName`, `GetIniString`, `EnumFiles`, `GetFileName`, and `GetFileSize` (lines 20–47). `BitmapGDI` owns `pMem`, `pBmp`, `Size`, and `Gdiplus::Bitmap* src` (lines 49–60).

---

## Source checkpoint 11 — ExplorerBlurMica README (full config/install)

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://github.com/Maplespe/ExplorerBlurMica/blob/main/README.md?plain=1
**Method**: browser-rendered (via `web__run` open; GitHub page lines 526 onward)
**Confidence**: high
**Insight**: ExplorerBlurMica's documented feature set is limited to blur/Acrylic/Mica, color blending, and clearing Explorer bars/WinUI backgrounds. It has no image file, image brush, alpha image, or ItemView image setting.

# Relevant extracted content

> The README describes Blur/Acrylic/Mica for Explorer on Windows 10/11 and names `LGNU V3`/`COPYING.LESSER` in its license link (lines 526–537). This conflicts with the repository root `LICENSE` fetched separately, which begins with GPL v3; treat the repository license state as unresolved until audited.
>
> Config fields are `effect`, `clearAddress`, `clearBarBg`, `clearWinUIBg`, `showLine`, and light/dark RGBA components. The documented effect values are Blur, Acrylic, Mica, Blur(Clear), and MicaAlt; no image path or ItemView image field appears in the schema.
>
> Installation is an administrator-run `register.cmd`/`regsvr32`; removal is administrator-run `uninstall.cmd`/`regsvr32 /u`, followed by deleting remaining files. The README gives the ESC emergency-open recovery path.
>
> Dependencies are MinHook and CustomTkinter; the GUI is Python (the README's project links name the upstream MinHook and CustomTkinter repositories).

---

## Source checkpoint 12 — ExplorerBlurMica release compatibility

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://github.com/Maplespe/ExplorerBlurMica/releases
**Method**: browser-rendered (via `web__run` open; release page lines 176–196)
**Confidence**: high
**Insight**: The latest release page entry visible in the source is 2.0.1. Its notes claim compatibility fixes for Windows 11 Preview Canary 23H2/24H2 builds and an improved registration/uninstall script, but this is still a blur/Mica project and does not add image backgrounds.

# Relevant extracted content

> Release 2.0.1 is associated with commit `6d746b5` (lines 176–180). The notes state compatibility with Windows 11 Preview Canary 23H2 build 26040 and 24H2 build 26052, StartAllBack compatibility, Mica title bar fixes, MicaAlt (`effect=4`), TreeView/DUI split-line control, and updated registration/uninstall scripts (lines 182–196).

---

## Source checkpoint 13 — ExplorerBlurMica configuration GUI

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://github.com/Maplespe/ExplorerBlurMica/blob/main/program.py
**Method**: browser-rendered (via `web__run` open; GitHub page lines 600–630 and source result)
**Confidence**: high
**Insight**: The Python GUI exposes only clear flags, effect mode, alpha, and RGB values, then writes `src\\config.ini` and launches `register.cmd`/`uninstall.cmd`; it does not accept an image path.

# Relevant extracted content

> The source initializes `clearAddress`, `clearBarBg`, `clearWinUIBg`, `showLine`, `mode`, `alpha`, `r`, `g`, `b`, and labels effect radio buttons Blur/Acrylic/Mica/Clear/Mica Alt (source lines shown in the search/open payload around lines 600–630 and 608–624).
>
> Its `install` function writes `[config] effect`, clear flags, and `[light]/[dark]` RGB/alpha values to `src\\config.ini`, then starts `src\\register.cmd`; `remove` starts `src\\uninstall.cmd` (source result from `turn8search0`).

---

## Source checkpoint 14 — ExplorerBlurMica native project dependencies

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/Maplespe/ExplorerBlurMica/main/ExplorerBlurMica/ExplorerBlurMica.vcxproj
**Method**: browser-rendered (via `web__run` open; raw MSBuild source, 257 lines)
**Confidence**: high
**Insight**: The native DLL targets Win32/x64 and Windows SDK 10.0 with Visual Studio v143, but its build imports several pinned NuGet packages and includes WinUI/XAML diagnostics and DirectUI helpers. This is materially more complex than the image renderer in ExplorerBgTool.

# Relevant extracted content

> Imports include Microsoft.Windows.CppWinRT 2.0.230706.1, WindowsAppSDK 1.4.231115000, Windows SDK BuildTools 10.0.22621.1, VC-LTL 5.0.9, and YY.NuGet.Import.Helper 1.0.0.4 (lines 0–6). The project targets Windows SDK `10.0`, DynamicLibrary, v143, Unicode, and Win32/x64 (lines 25–61).
>
> Source lists include DirectUI, Win32/WinRT helpers, XAML diagnostics, WindowListener, TranslucentImpl, and vendored MinHook files (lines 169–226). Build checks require the listed NuGet props/targets (lines 242–255).

---

## Source checkpoint 15 — ExplorerBlurMica native entry point

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/Maplespe/ExplorerBlurMica/main/ExplorerBlurMica/dllmain.cpp
**Method**: browser-rendered (via `web__run` open; raw source, 11 lines)
**Confidence**: high
**Insight**: The native entry point delegates to `MBox::OnDllMain`; this confirms a DLL injection/loader model but does not expose an image render path.

# Relevant extracted content

> `dllmain.cpp` includes `framework.h` and `module.h`; `DllMain` returns `MBox::OnDllMain(hModule, ul_reason_for_call)` (lines 0–10).

---

## Source checkpoint 16 — ExplorerBlurMica config file

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/Maplespe/ExplorerBlurMica/main/src/config.ini
**Method**: browser-rendered (via `web__run` open; raw source, 16 lines)
**Confidence**: high
**Insight**: The shipped config confirms the entire setting surface: effect and clear flags plus light/dark RGB/A. There is no image path or image rendering setting.

# Relevant extracted content

```ini
[config]
effect=0
clearAddress=false
clearBarBg=false
clearWinUIBg=false
showLine=false
[light]
r=255
g=255
b=255
a=255
[dark]
r=255
g=255
b=255
a=255
```

---

## Source checkpoint 17 — ExplorerBlurMica source license headers

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/Maplespe/ExplorerBlurMica/main/ExplorerBlurMica/DirectUITweaker.h
**Method**: browser-rendered (via `web__run` open; raw source, 71 lines)
**Confidence**: high
**Insight**: The source header identifies ExplorerBlurMica as LGPL v3 or later, while the root `LICENSE` fetched at the same revision is GPL v3. This discrepancy is a concrete reuse/legal blocker until the maintainer's intended license is clarified.

# Relevant extracted content

> The header says it is part of MToolBox and ExplorerBlurMica, and that ExplorerBlurMica is free software under the GNU Lesser General Public License version 3 or later (lines 3–15).

---

## Source checkpoint 18 — current Win11 file-list host evidence

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://raw.githubusercontent.com/ramensoftware/windhawk-mods/main/mods/explorer-nav-dragover-fix.wh.cpp
**Method**: browser-rendered (via `web__run` open; official Windhawk mod source, lines 20–35, 62–109, 418–469)
**Confidence**: high
**Insight**: The current official Windhawk source explicitly identifies the Windows 11 25H2 Details file list as DirectUI ItemsView (`UIItemsView`/`ItemsView`/`DirectUIHWND`) and says tabbed Explorer nests `SHELLDLL_DefView` under DirectUI hosts. This supports using the ExplorerBgTool window/paint hook as a candidate for the file-list content area, while requiring build-by-build validation of which paint calls reach the hook.

# Relevant extracted content

> The mod describes the right-hand main file list as “Details / ItemsView on Win11 25H2” and distinguishes it from classic `SysListView32` (lines 29–35).
>
> Its settings say that on Win11 25H2 Details view “the file list uses DirectUI ItemsView, not SysListView32” (lines 100–109).
>
> `IsExplorerFileContentHost` accepts `SysListView32`, `UIItemsView`, `ItemsView`, and `DirectUIHWND` (lines 418–429), then verifies the root is a `CabinetWClass`/`ExploreWClass` Explorer window (lines 431–436). `FindShellDefViewInCabinet` recursively searches because Win11 tabbed UI nests `SHELLDLL_DefView` under DirectUI hosts (lines 465–469).

---

## Source checkpoint 19 — Windhawk Styler XAML image path

**Time**: 2026-10-04, local Asia/Shanghai
**Source**: https://github.com/ramensoftware/windows-11-file-explorer-styling-guide and https://raw.githubusercontent.com/ramensoftware/windhawk-mods/main/mods/windows-11-file-explorer-styler.wh.cpp
**Method**: browser-rendered (via `web__run` find/open plus direct HTTPS source read for exact source line numbers)
**Confidence**: high
**Insight**: The official Windhawk File Explorer Styler route can set an `ImageBrush` with `Stretch="UniformToFill"` and a local path/URL, and the guide exposes a Details view root target. This is a concrete WinUI file-list background path, but it is a XAML target-level style and must be combined with a native DirectUI path for views/regions outside the target tree.

# Relevant extracted content

> The guide identifies the Details view root as `Grid#DetailsViewControlRootGrid` (lines 357–369 in the GitHub page) and separately documents `Fill:=<ImageBrush Stretch="UniformToFill" ImageSource="<image>" />`, with `<image>` replaced by a URL or local file path (lines 594–601).
>
> The Styler source builds a `ResourceDictionary`/`Style` through `Markup::XamlReader::Load` (source lines 6068–6115), inserts arbitrary XAML setter values when `rule.isXamlValue` is true (lines 6150–6173), and tracks `ImageBrush`/`Image` sources in `SetOrClearValue` (lines 5677–5693). The source also has `ImageCacheFileUri`, converting local filesystem paths to file URIs with `UrlCreateFromPath` (lines 4701–4722).
>
> The Styler source header states GPL v3 (raw source lines 0–11 / current source header around line 2209 in the GitHub rendering). This matters if code is copied into ThemeStudio; configuration generation through Windhawk is a separate integration boundary.

---
