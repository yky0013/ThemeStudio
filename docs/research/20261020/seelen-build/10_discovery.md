# Local discovery checkpoints

## 2026-10-20 17:xx CST — source and repository baseline

- Source root: `E:\desktop\windows\ThemeStudio-0.6\vendor\runtime-sources\Seelen-UI-2.8.6`
- Source instructions read: `AGENTS.md` (complete). It requires quick Rust feedback (`cargo check`), and the release workflow uses `cargo build --release -p sluhk` followed by `npx tauri build --ci --verbose --no-bundle --target x86_64-pc-windows-msvc`.
- Fixed toolchain: `rust-toolchain.toml` contains `channel = "nightly-2026-05-22"`.
- `rust-toolchain.toml` SHA-256: `E5B547ABE2A7546C20FFAC39AD53F0E4C518767FE4767F82BC5B0FAA688D0FE3`
- `Cargo.lock` SHA-256: `3B75AC49406422E6DB2AEE0B06B46C9D36279E75DC693CAF7B35E6BE1F48ACD6`
- Source `package-lock.json` SHA-256 (recorded for no-edit guard): `F2966CA42613F2269C84334C22AB9FAFFC6E81F64A79A30F59F3C4F420F142D4`
- Source Git HEAD: `b692673878190524ef11501075fd084411348154`.
- The source checkout already has unrelated parent-worktree changes outside the vendored source; this subtask does not touch them.

## 2026-10-20 17:xx CST — process and installed-tool baseline

- OS: Windows 11 Home Chinese, build `26200`, x64; CPU reports 16 logical processors; total visible memory `16,037,112 KiB`, free at check `2,857,112 KiB`; E: free `27,967,049,728` bytes.
- `cargo`, `rustc`, `rustup`, `cl`, `link`, `rc`, `vswhere`, and `deno` are absent from the current process command resolution.
- Node is available at the required path: `C:\Program Files\nodejs\node.exe` version `v24.18.0`; npm `11.16.0`.
- Process environment has no `CARGO_HOME`, `RUSTUP_HOME`, `VCINSTALLDIR`, `VCToolsInstallDir`, `WindowsSdkDir`, `WindowsSDKVersion`, `LIB`, `INCLUDE`, or `LIBCLANG_PATH` values.
- No default Visual Studio directories were found at `C:\Program Files\Microsoft Visual Studio` or `C:\Program Files (x86)\Microsoft Visual Studio`.
- `C:\Program Files (x86)\Windows Kits\10` exists but contains only `Catalogs`, `Debuggers`, and `Windows Performance Toolkit` at the inspected level; the compiler SDK `Include`, `Lib`, and normal `bin` trees are absent.
- The existing Windhawk cache `E:\desktop\windows\ThemeStudio-0.6\.cache\runtimes\windhawk\Compiler` contains MinGW target trees and `clang-20.exe`, `clang++.exe`, `clangd.exe`, and `ld.lld.exe`, plus GNU import libraries. It contains no `cl.exe`, `link.exe`, `rc.exe`, `clang-cl.exe`, or Rust binaries. This is insufficient evidence for the source's MSVC target.
- No `cl.exe`, `link.exe`, `rc.exe`, `llvm-lib.exe`, `clang-cl.exe`, `vswhere.exe`, `rustc.exe`, `cargo.exe`, or `rustup.exe` were found in the bounded searches under `E:\desktop\windows`, `E:\desktop\ThemeStudio`, `C:\Users\yky\AppData\Local`, `C:\Users\yky\AppData\Roaming`, `C:\Program Files`, or `C:\Program Files (x86)` (except Git's unrelated `C:\Program Files\Git\usr\bin\link.exe`).

## 2026-10-20 17:xx CST — preparation boundary

- Created empty project-local preparation directory: `E:\desktop\windows\ThemeStudio-0.6\.tools\seelen-build`.
- Created research directory: `E:\desktop\windows\ThemeStudio-0.6\docs\research\20261020\seelen-build`.
- No product source, lockfile, user application, desktop setting, persistent PATH, or machine-wide installation was changed.

## 2026-10-20 16:44 CST — rustup bootstrap network retry

- `rustup-init.exe` was launched with project-local `CARGO_HOME`/`RUSTUP_HOME`, `--default-toolchain nightly-2026-05-22`, `--default-host x86_64-pc-windows-msvc`, `--profile minimal`, and `--no-modify-path`.
- First attempt failed while downloading `channel-rust-nightly.toml.sha256` with a TCP timeout. A second attempt without the process's configured proxy remained stuck; it was stopped after verifying the PID path was the project-local bootstrapper.
- `Invoke-WebRequest` could fetch the same official static Rust URL successfully. The machine has an enabled user Internet Settings proxy `127.0.0.1:7890`, while WinHTTP is direct and no proxy environment variables were present. The next retry will pass `HTTP_PROXY`/`HTTPS_PROXY` only to rustup's child process.

## 2026-10-20 16:46 CST — project-local Rust toolchain ready

- A retry with process-local `HTTP_PROXY`, `HTTPS_PROXY`, and `ALL_PROXY` set to `http://127.0.0.1:7890` succeeded. No persistent environment variables were written.
- `rustup-home`: `E:\desktop\windows\ThemeStudio-0.6\.tools\seelen-build\rustup-home`
- `cargo-home`: `E:\desktop\windows\ThemeStudio-0.6\.tools\seelen-build\cargo-home`
- Installed toolchain: `nightly-2026-05-22-x86_64-pc-windows-msvc` (active/default).
- `rustc -Vv`: `rustc 1.97.0-nightly (e96c36b6f 2026-05-21)`, host `x86_64-pc-windows-msvc`, LLVM `22.1.6`.
- `cargo -V`: `cargo 1.97.0-nightly (4d1f98451 2026-05-15)`.
- Installed components: `cargo-x86_64-pc-windows-msvc`, `rust-std-x86_64-pc-windows-msvc`, `rustc-x86_64-pc-windows-msvc`; `rust-lld.exe` is present under the target sysroot's `lib\rustlib\x86_64-pc-windows-msvc\bin`.
- The nightly channel manifest was downloaded from `https://static.rust-lang.org/dist/2026-05-22/channel-rust-nightly.toml` and verified against its `.sha256`: `904B259E0C838741DE7A50525C9FC359D12332C71EE236AD51C07598DB6544C0`.
- Rustup emitted `warn: installing msvc toolchain without its prerequisites`; Rust itself is ready, but MSVC linker/SDK prerequisites are still unresolved.

## 2026-10-20 16:48 CST — project-local Deno ready

- Downloaded official Deno v2.9.7 x64 Windows archive to `.tools\seelen-build\downloads`.
- Archive SHA-256: `A0C3101B4158D1DFB7D6A78A7BF0F3DE80C96BB423C152BEEC8BEB22786F2238`; verified against the official `.sha256sum` file.
- Extracted only `deno.exe` to `.tools\seelen-build\deno\deno.exe`; version reports `deno 2.9.7 (stable, release, x86_64-pc-windows-msvc)`, V8 `15.0.245.2-rusty`, TypeScript `6.0.3`.
- No Deno PATH or installer state was changed.

## 2026-10-20 17:03 CST — portable MSVC and complete x64 SDK link libraries

- `portable-msvc.py` is running in `.tools\\seelen-build\\msvc-fetch` and has materialized the x64 MSVC root:
  `msvc-fetch\\vs2022_17.14\\VC\\Tools\\MSVC\\14.44.35207`.
- Verified compiler tools without compiling Seelen: `cl.exe` reports MSVC `19.44.35229` for x64; `link.exe`, `lib.exe`, `ml64.exe`, and `cvtres.exe` are present.
- The script downloads official Visual Studio channel payloads with per-payload SHA-256 checks, but it is still finishing optional packages; parent may use the x64 root now.
- CMake was downloaded from the official Kitware v4.4.4 Windows x64 ZIP and verified: archive SHA-256 `BACE36E94B31C68AB6FA295F26DFA11219E0701CF7C94B0284A7D1CB13DAC536`; `cmake --version` reports `4.4.4`.
- Parent proof initially lacked `kernel32.lib`, `ntdll.lib`, `userenv.lib`, and `WS2_32.lib` because the Windows SDK `Desktop Libs x64` MSI does not contain the core Store/Win32 import set alone. Extracted the official `Windows SDK for Windows Store Apps Libs-x86_en-us.msi` to the same project-local SDK root; x64 `kernel32.Lib` (311,908 bytes), `ntdll.lib` (517,236), `UserEnv.Lib` (19,480), and `WS2_32.Lib` (263,492) are now present under `Lib\\10.0.26100.0\\um\\x64`.
- `build-env.json` now includes process-only MSVC, SDK, Rust, Deno, CMake, `CC/CXX/AR/LINK/RC/MT`, `INCLUDE`, `LIB`, and `PATH` values; no persistent environment was changed.

## 2026-10-20 17:08 CST — AWS-LC native prerequisite

- Cargo registry source `aws-lc-sys-0.42.0` documents that Windows x64 assembly requires NASM unless the `prebuilt-nasm` feature is enabled. The source dependency graph uses `aws-lc-rs` defaults and does not select that feature, so a real NASM executable is prepared.
- Downloaded official NASM 3.02 x64 ZIP from `https://www.nasm.us/pub/nasm/releasebuilds/3.02/win64/nasm-3.02-win64.zip` (641,314 bytes); local SHA-256 `161D0BFAFF53C2F9E9F3E69FD0672323EBABAFD1268976A5CEC11BE92A19AEE7`. The official directory has no companion checksum file.
- Extracted `.tools\\seelen-build\\nasm\\nasm-3.02\\nasm.exe`; version reports `NASM version 3.02 compiled on Jun 28 2026`; executable SHA-256 `04EC2385879F7E1C45DBE76C4020970555DE48EEB97C23F59620EDE061328F51`.
- `build-env.json` exposes `NASM` and sets `AWS_LC_SYS_PREBUILT_NASM=0` so the child build uses the verified assembler.

## 2026-10-20 17:12 CST — Win32 header/import smoke link passed

- The first C smoke attempt exposed one more SDK package split: `windows.h` was present but `winapifamily.h` was missing. Extracted the official `Windows SDK for Windows Store Apps Headers OnecoreUap-x86_en-us.msi` into the same project-local SDK root; `shared\\winapifamily.h` is now present.
- A previous smoke link failed with `LNK1107` because `LINK` was incorrectly set to the linker executable path; MSVC treats `LINK` as option text. Removed that variable from `build-env.json`; the executable remains discoverable through the process-local PATH.
- Final standalone smoke compile/link (outside Seelen source) passed with `cl.exe` and `link.exe`: `.tools\\seelen-build\\smoke\\smoke6.exe`, 108,032 bytes, SHA-256 `A3B293A325F9C33170D866BEEF68B3C9DB73D434EEB89412A1312AFA589B9B0E`.
- The smoke program includes `<windows.h>` and calls `GetTickCount`, proving the x64 MSVC compiler, CRT, Windows SDK headers, `kernel32.Lib`, and linker can cooperate in a child-only environment.
- The shared SDK header used by the smoke compile is `shared\\winapifamily.h`, SHA-256 `BDA507D14F2E40023D344CB943CBD98AF26DE8A47F3B0F5FAC694D2025711AF1`.

## 2026-10-20 17:14 CST — final environment handoff state

- Final project-local MSVC root: `E:\desktop\windows\ThemeStudio-0.6\.tools\seelen-build\msvc-fetch\vs2022_17.14\VC\Tools\MSVC\14.44.35207`; x64 `cl.exe` reports `19.44.35229`, and x64 `link.exe`/`lib.exe` are present.
- Final SDK root used for the handoff: `E:\desktop\windows\ThemeStudio-0.6\.tools\seelen-build\sdk-extracted\Windows Kits\10`, version `10.0.26100.0`. It contains x64 `rc.exe`, `mt.exe`, `windows.h`, `shared\\winapifamily.h`, UCRT libs, and core x64 import libs (`kernel32.Lib`, `ntdll.lib`, `UserEnv.Lib`, `WS2_32.Lib`).
- Final native prerequisites: CMake `4.4.4`, NASM `3.02`, Node `v24.18.0`, Deno `2.9.7`, Rust `1.97.0-nightly` from the pinned nightly date.
- `build-env.json` and `build-env.py` are the reusable child-process handoff. They set `CARGO_HOME`, `RUSTUP_HOME`, `RUSTUP_TOOLCHAIN`, `INCLUDE`, `LIB`, `LIBPATH`, `CC`, `CXX`, `AR`, `RC`, `MT`, `CMAKE`, `NASM`, `AWS_LC_SYS_PREBUILT_NASM=0`, and `CARGO_TARGET_X86_64_PC_WINDOWS_MSVC_LINKER=rust-lld.exe`; they do not set `LINK` to an executable path.
- `build-env.py --run cl ...` compiled and linked the standalone Windows smoke program successfully; no Seelen source or product build was compiled by this subtask.
- Remaining parent action: rerun the parent native Rust proof and then perform the requested Seelen build. The environment subtask has no unresolved compiler/SDK blocker.

## 2026-10-20 17:45 CST — read-only final release progress check

- Main release compiler: PID `64992`, project-local `rustc.exe`, started `17:27:40`, still alive/responding. Its command is the final `seelen_ui` crate with `--emit=dep-info,link`, `-C opt-level=z`, `-C lto`, `-C codegen-units=1`, target `x86_64-pc-windows-msvc`, and `-C linker=rust-lld.exe`.
- Parent process is cargo PID `11636`; no child linker process is present in this snapshot, so rustc is still in its own codegen/LTO phase rather than waiting on a detached linker.
- Progress evidence: `seelen_ui.d` (48,746,648 bytes) was written at `17:45:42`; the seelen-ui fingerprint output was also updated at the same time. Earlier Tauri codegen assets were written at `17:38:00–17:38:02`.
- A 16-second read-only counter window measured rustc CPU average `39.86%` (min `4.59%`, max `88.87%`), CPU time increase `7.016 s`, read throughput average about `52,951 B/s`, write throughput average about `2,983,338 B/s` (max `23,866,705 B/s`), private memory increase `316,862,464` bytes, and working-set increase `414,638,080` bytes. This is active progress, not a stalled zero-activity wait.
- Current process snapshot: private memory `2,665,558,016` bytes, working set `1,638,490,112` bytes, virtual size `7,379,333,120` bytes, four threads, 582 handles. System free physical memory was `1,901,008 KiB` and free virtual memory `6,421,168 KiB`.
- Relevant source note: `src/background/tauri_context.rs` explicitly isolates `tauri::generate_context!()` because of macro build slowness. The release profile's full LTO and one codegen unit make this final crate's long, memory-heavy phase expected.
- Assessment: no intervention is warranted. Do not suspend/kill/dump or alter the build. Avoid launching other memory-heavy work while this phase completes; reassess only if CPU/IO and generated-file timestamps remain unchanged for a sustained interval.
