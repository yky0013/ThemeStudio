# Windhawk activation research

Date: 2026-09-27
Scope: identify a source-grounded way for ThemeStudio to install, enable, disable, and roll back user-selected Windhawk mods from local `.wh.cpp` sources. Research only; no application code, system settings, Windhawk installation, mod compilation, or mod activation was performed.

Questions:

1. Does the upstream CLI accept local `.wh.cpp` files and manage their lifecycle?
2. What exact commands, arguments, return/verification signals, runtime files, storage paths, and permissions are required?
3. How do installed and portable modes differ, and which upstream components should ThemeStudio call rather than reimplement?
4. What release/version provenance and compatibility constraints matter?

Evidence policy:

- Prefer official Windhawk repositories, wiki, release notes, and source files.
- Persist a checkpoint immediately after each fetched web source and local source inspection.
- Separate confirmed behavior from inference and runtime checks still required.
- Preserve the actual local `.wh.cpp` source as the input; do not choose or enable any taskbar/Dock provider.

Artifacts: `10_discovery.md`, `20_sources.md`, and `90_synthesis.md`.
