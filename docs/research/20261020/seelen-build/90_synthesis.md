# Seelen-UI 2.8.6 build-environment handoff

## Outcome

The project-local Windows MSVC build environment is prepared under `ThemeStudio-0.6/.tools/seelen-build`. It matches the vendored source's `nightly-2026-05-22` and `x86_64-pc-windows-msvc` requirements, and it has passed a standalone Win32 C compile/link smoke test. No Seelen source, `Cargo.lock`, frontend lockfile, user application, desktop setting, persistent PATH, or machine-wide installer state was changed.

## Fixed source inputs

- Source: `vendor/runtime-sources/Seelen-UI-2.8.6`.
- Rust channel: `nightly-2026-05-22`; `rust-toolchain.toml` SHA-256 `E5B547ABE2A7546C20FFAC39AD53F0E4C518767FE4767F82BC5B0FAA688D0FE3`.
- `Cargo.lock` SHA-256 `3B75AC49406422E6DB2AEE0B06B46C9D36279E75DC693CAF7B35E6BE1F48ACD6`.
- Source Git HEAD observed: `b692673878190524ef11501075fd084411348154`.

## Prepared artifacts

- Rust: project-local `cargo-home`/`rustup-home`; `rustc 1.97.0-nightly (e96c36b6f 2026-05-21)`, Cargo `1.97.0-nightly`, target `x86_64-pc-windows-msvc`, and `rust-lld.exe`. The nightly manifest SHA-256 is `904B259E0C838741DE7A50525C9FC359D12332C71EE236AD51C07598DB6544C0`.
- Deno: v2.9.7 x64 portable executable; archive SHA-256 `A0C3101B4158D1DFB7D6A78A7BF0F3DE80C96BB423C152BEEC8BEB22786F2238`, verified against the official `.sha256sum`.
- MSVC: x64 compiler/linker root `msvc-fetch/vs2022_17.14/VC/Tools/MSVC/14.44.35207`; `cl.exe` reports MSVC 19.44.35229. Official Visual Studio channel and manifest were saved and hashed in `build-env.json`.
- Windows SDK: extracted MSI payloads under `sdk-extracted/Windows Kits/10`, version `10.0.26100.0`. The root contains x64 headers, UCRT/Win32 import libraries, `rc.exe`, and `mt.exe`; the core x64 import set includes `kernel32.Lib`, `ntdll.lib`, `UserEnv.Lib`, and `WS2_32.Lib`.
- CMake: v4.4.4 official x64 ZIP; archive SHA-256 `BACE36E94B31C68AB6FA295F26DFA11219E0701CF7C94B0284A7D1CB13DAC536`.
- NASM: v3.02 official x64 ZIP; archive SHA-256 `161D0BFAFF53C2F9E9F3E69FD0672323EBABAFD1268976A5CEC11BE92A19AEE7`; the official directory has no companion checksum file. `aws-lc-sys` is configured through the child environment to use real NASM (`AWS_LC_SYS_PREBUILT_NASM=0`).

## Reuse

Use `.tools/seelen-build/build-env.json` as the machine-local environment manifest and `.tools/seelen-build/build-env.py` to run a child command. The helper validates required files, sets all paths in the child only, and leaves the parent shell unchanged. It includes `CC`, `CXX`, `AR`, `RC`, `MT`, `CMAKE`, `NASM`, `INCLUDE`, `LIB`, `LIBPATH`, Rust homes/toolchain, and the `rust-lld.exe` linker setting. It intentionally does not set `LINK` to the linker executable because MSVC interprets `LINK` as option text.

The helper adds `HTTP_PROXY`, `HTTPS_PROXY`, and `CARGO_HTTP_PROXY` only to the child when downloads are needed, using the observed local proxy `http://127.0.0.1:7890`; this is not persisted.

## Validation

- `cl.exe /?`, `link.exe /?`, `rc.exe /?`, `cmake --version`, `nasm -v`, `deno --version`, and `rustc -Vv` all executed through the project-local environment.
- The smoke source `.tools/seelen-build/smoke/main.c` includes `<windows.h>` and calls `GetTickCount`. The resulting `.tools/seelen-build/smoke/smoke6.exe` is 108,032 bytes with SHA-256 `A3B293A325F9C33170D866BEEF68B3C9DB73D434EEB89412A1312AFA589B9B0E`.
- The smoke proves that the compiler, CRT, Windows SDK headers, x64 import libraries, and linker cooperate. It does not prove the Seelen application builds or runs; the parent agent owns that build and its functional verification.

## Evidence and limits

Rustup's official documentation supports project-local `CARGO_HOME`/`RUSTUP_HOME` and manual `rustup-init.exe` downloads with `.sha256` verification: [rustup installation](https://rust-lang.github.io/rustup/installation/index.html?highlight=Comple), [Windows ABI requirements](https://rust-lang.github.io/rustup/devel/installation/windows.html), and [manual downloads](https://rust-lang.github.io/rustup/installation/other). Microsoft documents MSVC command-line tools and process-local `PATH`/`INCLUDE`/`LIB` use in [C++ command-line builds](https://learn.microsoft.com/en-us/cpp/build/building-on-the-command-line?view=msvc-160). Microsoft documents Windows SDK MSI extraction without a full install in [GDK extraction guidance](https://learn.microsoft.com/en-us/gaming/gdk/docs/gdk-dev/console-dev/usingwithoutinstall/extract-setup-payload?view=gdk-2604).

The third-party `portable-msvc.py` workflow was inspected and retained only as a downloaded local recipe; the compiler payloads came from the official Visual Studio channel and were SHA-256 checked by the script. The SDK used in the final environment came from Microsoft SDK MSI extraction because the portable script's optional SDK copy did not produce a complete `SourceDir` tree. The final environment has no unresolved compiler/SDK prerequisite blocker.
