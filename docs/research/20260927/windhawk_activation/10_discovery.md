# Discovery checkpoints

## 2026-09-27 — official upstream candidates

Queries:

- `site:github.com/ramensoftware/windhawk Windhawk CLI install mod enable disable source`
- `site:github.com/ramensoftware/windhawk windhawk.exe command line mod compiler`
- `site:docs.windhawk.net Windhawk install mods command line local source`
- `site:github.com/ramensoftware/windhawk-mods .wh.cpp Windhawk mod source`

Official results inspected:

1. `https://github.com/ramensoftware/windhawk/blob/main/src/windhawk-core/cli/src/args.rs` — CLI command tree and arguments.
2. `https://github.com/ramensoftware/windhawk/blob/main/src/windhawk-core/cli/src/commands/mods/install.rs` — local-source install pipeline.
3. `https://github.com/ramensoftware/windhawk/blob/main/src/windhawk-core/cli/src/commands/mods/lifecycle.rs` — enable/disable/remove behavior.
4. `https://github.com/ramensoftware/windhawk/releases/tag/2.0.0-alpha.6` — release/version feature provenance.
5. `https://github.com/ramensoftware/windhawk/issues/1050` — official permission/elevation behavior evidence.
6. `https://github.com/ramensoftware/windhawk/wiki/Creating-a-new-mod` — `.wh.cpp` metadata and compiler rules.
7. `https://github.com/ramensoftware/windhawk-mods` — official source collection policy.

Status: discovery complete. Exact source behavior and storage paths were then checked in the recovered local snapshot and recorded in `20_sources.md`.
