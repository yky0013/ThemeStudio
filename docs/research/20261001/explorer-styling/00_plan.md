# Explorer styling compatibility research

**Date**: 2026-10-01 (Asia/Shanghai)
**Scope**: Verify the upstream Windows 11 File Explorer Styler guide and the pinned Windhawk source used by ThemeStudio-0.6.0. Resolve the explicit Windows requirement, the actual XAML/native scope of background styling, wallpaper/image limitations, and applicable presets.
**Sources**:

- Upstream guide: https://github.com/ramensoftware/windows-11-file-explorer-styling-guide
- Pinned source: `ThemeStudio-0.6.0/vendor/windhawk-mods/mods/windows-11-file-explorer-styler.wh.cpp`
- Upstream mod landing page for metadata cross-check: https://windhawk.net/mods/windows-11-file-explorer-styler

**Boundaries**: Read-only inspection and research artifacts only. Do not edit production code, install/enable Windhawk, alter Explorer, or change system settings.

**Acceptance criteria**:

1. Quote the upstream guide's Windows version wording and intended mod relationship.
2. Identify guide targets for header/toolbar regions and the details/file-list region, distinguishing XAML target scope from any unaddressed native surface.
3. Verify image/background syntax and practical limitations for a wallpaper-backed preset.
4. Record the pinned source version, architecture/process target, built-in presets, and any source-level caveats.
5. Synthesize applicable presets and confidence/caveats with traceable citations to `20_sources.md`.
