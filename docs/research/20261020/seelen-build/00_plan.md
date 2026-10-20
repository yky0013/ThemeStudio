# Seelen-UI 2.8.6 build-environment research

- Date: 2026-10-20 (Asia/Shanghai)
- Scope: prepare a project-local, reproducible Windows build environment for the vendored Seelen-UI 2.8.6 source.
- Delegated boundary: inspect prerequisites, identify installed compilers/SDKs, obtain or prepare portable prerequisites under `ThemeStudio-0.6/.tools/seelen-build`, and record provenance/hashes/blockers.
- Fixed source requirements: `rust-toolchain.toml` requests `nightly-2026-05-22`; the checked-in `Cargo.lock` is authoritative; CI builds `x86_64-pc-windows-msvc`.
- Explicit exclusions: do not edit product sources, `Cargo.lock`, `rust-toolchain.toml`, or frontend lockfiles; do not run a Seelen build; do not install machine-wide software; do not persist process environment changes; do not alter user applications or desktop settings.
- Research root: this folder. Use `10_discovery.md` for local discovery, `20_sources.md` for web/source checkpoints, and `90_synthesis.md` for the final handoff.

## Acceptance criteria

1. Exact Rust channel and project lockfile are recorded with hashes.
2. Existing MSVC/Windows SDK/compiler candidates are checked in bounded paths, including the Windhawk compiler cache.
3. Portable prerequisite feasibility is evidenced from official Rust/Microsoft sources.
4. Any downloaded or extracted files stay below `.tools/seelen-build`, have URL/provenance and SHA-256 recorded, and are usable through explicit environment variables/scripts without machine-wide changes.
5. Remaining blockers are explicit; no claim of successful compilation is made.
