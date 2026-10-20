# Standalone Rust Start layout proof

This harness imports the exact product implementation from:

`../../../../../../vendor/runtime-sources/Seelen-UI-2.8.6/src/background/utils/start_layout.rs`

It provides only the `crate::error::Result` surface required by that module. The tests do not
start Seelen, invoke PowerShell, modify Start settings, or call any product/UI code. Windows COM
reads the current user's pinned Start layout and writes only the requested JSON test output.

When the pinned Rust toolchain is available, run from this directory:

```powershell
cargo test --manifest-path .\Cargo.toml --target x86_64-pc-windows-msvc -- --nocapture
```

The byte-equivalence test uses `NATIVE_START_LAYOUT_REFERENCE` when set. Otherwise it looks for
the existing local reference at `..\proof-output\powershell-reference.json`. That personal
machine export is deliberately not part of the harness source or tracked artifacts.
