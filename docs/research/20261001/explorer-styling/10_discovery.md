# Discovery log

**Run date**: 2026-10-01 (Asia/Shanghai)
**Question partition**: (1) upstream Windows/version wording, (2) target scope for header/details/native list, (3) image/wallpaper limits, (4) pinned source presets and runtime caveats.

## Sources selected

1. Live upstream GitHub README, browser-rendered: <https://github.com/ramensoftware/windows-11-file-explorer-styling-guide>.
2. Raw upstream README for line-addressable extraction: <https://raw.githubusercontent.com/ramensoftware/windows-11-file-explorer-styling-guide/main/README.md>.
3. ThemeStudio pinned mod source: `ThemeStudio-0.6.0/vendor/windhawk-mods/mods/windows-11-file-explorer-styler.wh.cpp`.
4. Windhawk mod landing page metadata: <https://windhawk.net/mods/windows-11-file-explorer-styler>.
5. Microsoft DWM attribute availability: <https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute>.

## Retrieval notes

- Browser page showed the upstream repository's `main` branch and short latest commit `fe8f72c` dated Sep 27, 2026 (GMT+8). A GitHub API follow-up returned HTTP 403 rate limit, so no API claim is made.
- Network retrieval used the approved local proxy `http://127.0.0.1:7890`; all fetched-page evidence was immediately appended to `20_sources.md` after successful retrieval.
- Local source inspection was read-only. SHA-256: `2F14AF7887F0DD6E767724B02E515BD46D6AF019E9B7068C0F4E5E8A72C69C37`.
- Search of the pinned source found XAML details/header targets and DWM hooks but no `SysListView32`, `SHELLDLL_DefView`, `DirectUI`, `ShellView`, or native file-list hook.
- Microsoft documents `DWMWA_SYSTEMBACKDROP_TYPE` as supported from Windows 11 Build 22621; this is the API used by the source's Acrylic/Mica/Mica Alt backdrop mapping.

## Evidence boundary

The upstream guide is normative for the documented target strings and syntax. The pinned source is normative for what this ThemeStudio snapshot actually carries. Runtime success on a user's exact Windows build, Explorer visual tree, Windhawk engine, and selected file view still requires live validation; this run made no system changes and did not enable the mod.
