# Windhawk shell and PowerShell audit

- Scope: read-only inventory of runtime PowerShell references in `vendor/windhawk-mods/mods` and C++ sources under `vendor/windhawk` for ThemeStudio 0.6.
- Required classification:
  - **A**: internal hardcoded PowerShell implementing a mod function; candidate for native replacement.
  - **B**: explicit user-selected terminal or user-authored PowerShell/script execution; preserve for compatibility.
  - **C**: comments, examples, sample settings, documentation, identifiers, or visual matching data only.
- Deliverables: exact file/line references, action/function summary, native Win32/COM replacement candidates for A, and source-based acceptance tests that do not toggle network state, create services, or change the desktop.
- Method: inspect local sources first; persist each local source finding in `10_discovery.md`; verify uncertain Win32/COM signatures from primary Microsoft documentation and persist each fetched source in `20_sources.md`; write a disk-grounded synthesis in `90_synthesis.md`.
- Constraints: no product source changes, no live network toggles, no service creation, no desktop mutation, preserve unrelated working-tree changes.
