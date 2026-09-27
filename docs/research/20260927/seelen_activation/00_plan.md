# Seelen activation research plan — 2026-09-27

## Scope

Research only. Do not install, start, or apply Seelen engines/settings. Do not edit ThemeStudio application code. Owned artifact root: `docs/research/20260927/seelen_activation/`.

## Questions answered

1. Exact Seelen settings/configuration paths and IPC/CLI/resource-manager functions for themes, icon packs, Dock/toolbar, and wallpaper.
2. Individual component activation while preserving the newly selected Seelen Dock/toolbar provider and leaving window manager, launcher, and unrelated widgets disabled.
3. Activation status, rollback, and failure evidence.
4. Engine/runtime distribution and source/version provenance.
5. Upstream WorkerW desktop-parent implementation and reuse of Seelen image/video/parallax media in a .NET WebView2 host.

## Source policy

Official primary sources only: recovered ThemeStudio/Seelen source, fixed upstream Seelen commit, official Seelen docs/releases/workflows, and official Tauri/WebView2 documentation. Every fetched source is persisted in `10_discovery.md` or `20_sources.md`; `90_synthesis.md` is derived from those artifacts.

## Scope update

The parent task later confirmed that the user selected Seelen Dock and toolbar as the taskbar provider. Recommendations therefore enable `@seelen/weg` and `@seelen/fancy-toolbar`, preserve their existing geometry, keep `@seelen/window-manager` disabled, and leave Start/launcher/other widgets unchanged.

The follow-up also requires stable v2.8.6 artifact/source matching. The owned folder now contains the downloaded fixed NSIS installer, x64 MSIX payload expansion, and source archive for commit `079c385`; no installer or Seelen executable was run.
