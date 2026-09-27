# Discovery checkpoints — Seelen activation

**Time**: 2026-09-27, 17:40:00 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/blob/master/src/static/widgets/wallpaper-manager/metadata.yml (`turn4search0`)
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: Built-in wallpaper manager is a first-class resource with ID `@seelen/wallpaper-manager`, internal loader, desktop preset, and wallpaper next/previous commands.

# Relevant extracted content

> `id: "@seelen/wallpaper-manager"`; `loader: Internal`; `preset: Desktop`; `command: ["wallpaper", "next"]`.

---

**Time**: 2026-09-27, 17:40:05 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/blob/master/libs/core/src/state/settings/mod.rs (`turn4search1`)
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: Core settings expose `active_themes`, `active_icon_packs`, wallpaper collections, per-wallpaper settings, and a wallpaper widget `enabled` flag/default collection; defaults include `@default/theme` and `@system/icon-pack`.

# Relevant extracted content

> `pub active_themes: Vec<ThemeId>`; `pub active_icon_packs: Vec<IconPackId>`; `pub by_wallpaper`; `pub wallpaper_collections`; `active_themes: vec!["@default/theme"]`; `active_icon_packs: vec!["@system/icon-pack"]`.

---

**Time**: 2026-09-27, 17:40:10 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/releases (`turn4search3`)
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: Official releases are versioned and signed; the release line includes wallpaper behavior fixes, so a ThemeStudio engine integration must pin/report a concrete Seelen version/commit.

# Relevant extracted content

> The search result showed Seelen UI v2.8.4 and a wallpaper flicker/fade fix.

---

**Time**: 2026-09-27, 17:40:15 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/blob/master/src/background/state/infrastructure.rs (`turn4search4`)
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: Seelen's command layer exposes settings read/write and native wallpaper get/set; its wallpaper picker accepts supported image/video types and stores imported files under the common user-wallpaper directory.

# Relevant extracted content

> `state_get_settings`; `state_write_settings`; `get_native_shell_wallpaper`; `set_native_shell_wallpaper`; `state_request_wallpaper_addition` using `Wallpaper::SUPPORTED_VIDEOS` and `SUPPORTED_IMAGES`.

---

**Time**: 2026-09-27, 17:40:20 +08:00
**Source**: https://seelen.io/docs/resource-guidelines (`turn27view1`)
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: Official resource guidance lists themes, widgets, plugins, icon packs, and wallpapers and documents `slu resource load/unload` for a running Seelen instance.

# Relevant extracted content

> “Resource kinds” include Theme, Widget, Plugin, IconPack, Wallpaper.
>
> `slu resource load <kind> <path>`; `slu resource unload <kind> <path>`.

---

**Time**: 2026-09-27, 17:40:25 +08:00
**Source**: https://seelen.io/resources (`turn26view3`)
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: Official marketplace separates resource categories and lists wallpapers, icon packs, widgets, themes, and a Desktop Media Player widget, supporting explicit resource-kind selection.

# Relevant extracted content

> Marketplace examples include “Acheron Black Hole” wallpaper, “Windows 11 Start Icon” icon pack, and “Desktop Media Player” widget.

---

**Time**: 2026-09-27, 17:40:30 +08:00
**Source**: https://github.com/eythaann/Seelen-UI/blob/master/AGENTS.md (`turn4search8`)
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: Upstream repository identifies FEATURES.md, resource guidelines, built-in resource folders, and the `slu` CLI as source-of-truth locations.

# Relevant extracted content

> Built-in resources are under `src/static/widgets/`, `src/static/themes/`, and `src/static/plugins/`; `slu resource load` is the documented live-load workflow.

---
