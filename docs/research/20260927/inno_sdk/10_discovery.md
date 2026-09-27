# Discovery checkpoints

**Time**: 2026-09-27, Asia/Shanghai
**Source**: query-search: `Inno Setup 6.7.3 official download JRSoftware` and related JRSoftware queries
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: Official JRSoftware pages identify Inno Setup 6.7.3 as released on 2026-05-26. The current home page says download links were updated on 2026-03-02 to immutable GitHub releases, so the old guessed `files.jrsoftware.org/is/6/...` pattern should not be trusted without page confirmation.

# Relevant extracted content

> `https://jrsoftware.org/files/is6-whatsnew.htm` — revision history shows `6.7.3 (2026-05-26)`.
>
> `https://jrsoftware.org/` — What's New says `March 2, 2026 - Updated Inno Setup download links to use immutable releases on GitHub` and `May 26, 2026 - Inno Setup 6.7.3 released.`
>
> `https://jrsoftware.org/isdl-old.php` — old downloads page says prior 6.x versions are available as immutable GitHub releases.

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: query-search: `site:jrsoftware.org/ishelp portable installer /PORTABLE Inno Setup`
**Method**: query-search (via `web__run`)
**Confidence**: medium
**Insight**: The official search results confirm that `/PORTABLE=1` is a documented Inno Setup installer mode and point to the official miscellaneous notes page; the exact no-registry behavior should be confirmed by inspecting the installer’s own help output and post-run filesystem/registry evidence.

# Relevant extracted content

> Official result `Miscellaneous Notes` says Inno Setup installers accept `/PORTABLE=1`, causing the installer to install to the desktop by default and not create an uninstaller or Add/Remove Programs entry.

---
