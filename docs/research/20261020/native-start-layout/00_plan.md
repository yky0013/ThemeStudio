# Native Start layout export research plan

Date: 2026-10-20
Scope: determine whether Windows exposes a supported non-PowerShell path that can export the same Windows 11 Start pinned-list JSON consumed by Seelen's `get_native_start_menu`.

Boundaries:

- Inspect the installed `StartLayout` module and its managed command assembly read-only.
- Inspect Seelen's source only for the input/output contract.
- Use official Windows documentation and other primary technical evidence for API claims.
- Build a read-only proof prototype under this folder only; it must not write Windows settings or modify the desktop configuration.
- Preserve exact uncertainty: a callable managed implementation is not automatically a documented public native API.

Planned artifacts:

- `10_discovery.md`: local module, assembly, source, and runtime observations.
- `20_sources.md`: per-source web/documentation checkpoints.
- `30_prototype.cs` and `run-prototype.ps1`: standalone read-only proof attempt.
- `proof-output/`: captured output and hashes from the proof run.
- `90_synthesis.md`: evidence-backed conclusion, exact signatures, limitations, and handoff.
