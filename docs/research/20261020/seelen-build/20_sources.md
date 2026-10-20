# Official source checkpoints

## Checkpoint 1 — rustup installation and project-local homes

- Retrieved: 2026-10-20; source: [The rustup book — Installation](https://rust-lang.github.io/rustup/installation/index.html?highlight=Comple)
- Evidence: rustup installs `rustc`, `cargo`, and `rustup` under Cargo's `bin`; on Windows the default is `%USERPROFILE%\\.cargo\\bin` (lines 17–23).
- Evidence: `CARGO_HOME` and `RUSTUP_HOME` can be set before running `rustup-init`; `RUSTUP_HOME` stores toolchains/configuration and `CARGO_HOME` stores Cargo cache files (lines 24–27).
- Application: set both variables only in a project-local launcher/process when installing and using Rust; do not modify persistent PATH or machine/user environment.
- Retrieval note: browser result `turn1view0`; persisted immediately after fetch.

## Checkpoint 2 — MSVC ABI prerequisite

- Retrieved: 2026-10-20; source: [The rustup book — Windows](https://rust-lang.github.io/rustup/devel/installation/windows.html)
- Evidence: Windows has MSVC and GNU ABIs; MSVC Rust is appropriate for Visual Studio interoperation (lines 14–15).
- Evidence: when targeting MSVC, Rust additionally requires a Visual Studio installation so `rustc` can use its linker and libraries (line 16).
- Evidence: the GNU ABI avoids that exact Visual Studio prerequisite for basic use, but many crates still require a full MSYS2/MinGW setup (lines 18–18); this is not an equivalent substitute for the source's `x86_64-pc-windows-msvc` CI target.
- Evidence: the default Windows Rust host/target is MSVC and `x86_64-pc-windows-msvc` is an explicit supported target (lines 19–36).
- Application: prepare the MSVC-targeted Rust toolchain plus a Microsoft linker/SDK; do not silently switch the product to GNU.
- Retrieval note: browser result `turn2view0`; persisted immediately after fetch.

## Checkpoint 3 — official rustup-init download and checksum endpoint

- Retrieved: 2026-10-20; source: [The rustup book — Other installation methods](https://rust-lang.github.io/rustup/installation/other)
- Evidence: Windows should use `rustup-init.exe` for the OS target, with `x86_64-pc-windows-msvc` for this x64 host (lines 15–17).
- Evidence: the manual download pattern is `https://static.rust-lang.org/rustup/dist/{target-tuple}/rustup-init[.exe]`; `.sha256` may be appended to the link for the SHA-256 checksum (lines 63–65 and 152–154).
- Planned URL: `https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe`.
- Application: download the official bootstrapper into `.tools/seelen-build/downloads`, verify its companion checksum, then install with project-local `CARGO_HOME`/`RUSTUP_HOME` and `--no-modify-path`.
- Retrieval note: browser result `turn3view0`; persisted immediately after fetch.

## Checkpoint 4 — Microsoft C++ command-line tool requirements

- Retrieved: 2026-10-20; source: [Use the Microsoft C++ Build Tools from the command line](https://learn.microsoft.com/en-us/cpp/build/building-on-the-command-line?view=msvc-160)
- Evidence: Microsoft offers the C++ Build Tools as a standalone package without the Visual Studio IDE (lines 30–38).
- Evidence: the Desktop development with C++ workload supplies the compiler toolset and optional SDK/toolsets (lines 37–39).
- Evidence: MSVC tools include compilers/linkers and matching libraries/headers; command files set architecture, SDK, and toolset environment (lines 45–50).
- Evidence: the command-line environment uses `PATH`, `TMP`, `INCLUDE`, `LIB`, and `LIBPATH`; Microsoft advises using the generated developer command files and does not recommend setting these permanently in Windows environment (lines 53–56).
- Evidence: `cl.exe` compiles/links and `link.exe` links native outputs (lines 195–205).
- Application: the build launcher should capture a process-local developer environment; persistent PATH/environment writes are unnecessary and excluded.
- Limitation: this page describes an installer-backed Visual Studio Build Tools installation. It does not establish that the MSVC compiler/SDK can be legally or technically run as a simple extracted ZIP; that question remains a blocker for a strictly project-local setup.
- Retrieval note: browser result `turn4view0`; persisted immediately after fetch.

## Checkpoint 5 — Visual Studio offline layout is still installer-backed

- Retrieved: 2026-10-20; source: [Create an offline installation of Visual Studio](https://learn.microsoft.com/en-us/visualstudio/install/create-an-offline-installation-of-visual-studio?view=visualstudio)
- Evidence: a local layout can download C++ workload packages, and Microsoft gives `--add Microsoft.VisualStudio.Workload.NativeDesktop --includeRecommended --includeOptional --lang en-US` as the C++ example (lines 50–80).
- Evidence: creating the local layout requires an administrator command prompt (lines 52–58); a complete layout is at least 45 GB (lines 62–72), exceeding the available E: space for a full layout.
- Evidence: installing from a layout records its path in `C:\ProgramData\Microsoft\VisualStudio\Packages\_Instances\<InstanceID>\state.json` (lines 83–96), which is machine-level state.
- Application: do not run the Visual Studio installer/layout in this subtask because the requested boundary forbids admin/machine-wide changes. The source supports a later user-authorized installation route if the parent decides to relax that constraint.
- Retrieval note: browser result `turn5view0`; persisted immediately after fetch.

## Checkpoint 6 — current Windows SDK download channels

- Retrieved: 2026-10-20; source: [Windows SDK downloads](https://learn.microsoft.com/en-us/windows/apps/windows-sdk/downloads)
- Evidence: Microsoft publishes supported Windows SDK Installer and ISO links and also exposes Windows SDK NuGet packages (lines 30–34).
- Evidence: the current page lists Windows 11 SDK families `10.0.28000.*` and `10.0.26100.*`; latest visible 26100 servicing release is `10.0.26100.9457` (lines 69–75).
- Application: prefer the 26100 SDK family for this Windows 11 build and avoid relying on the incomplete installed `Windows Kits\10` tree. The SDK version is a compatibility choice; the source does not pin a specific SDK version.
- Retrieval note: browser result `turn7view0`; persisted immediately after fetch.

## Checkpoint 7 — exact official SDK installer URL and extraction route

- Retrieved: 2026-10-20; source: [Microsoft GDK documentation: Extracting the Windows SDK setup payload](https://learn.microsoft.com/en-us/gaming/gdk/docs/gdk-dev/console-dev/usingwithoutinstall/extract-setup-payload?view=gdk-2604)
- Evidence: Microsoft documents extracting Windows SDK headers/libraries for a build process without installing the full SDK, intended for advanced users (lines 31–39 and 83–85).
- Evidence: the documented route downloads `winsdksetup.exe`, runs `winsdksetup.exe /layout <folder>` to obtain MSI payloads, then extracts each MSI with `msiexec.exe /a ... TARGETDIR=<folder>` (lines 92–108 and 113–132); an ISO contains the same MSI payloads (lines 99–102).
- Evidence: the extracted `Windows Kits\10` folder is the build-system reference tree (lines 107–112). Microsoft warns extraction paths should be kept under 45 characters to avoid long-path failures (lines 103–105).
- Exact current 26100 installer URL obtained by following the official downloads page's latest 26100 Installer link: `https://download.microsoft.com/download/46742ab5-6592-4968-a793-129e7f3bc55a/KIT_BUNDLE_WINDOWSSDK_MEDIACREATION/winsdksetup.exe`.
- Application: a project-local SDK extraction is technically feasible without registry/ProgramData installation; keep download/layout/extract paths short below `.tools/seelen-build` and record hashes. This supplies headers/libs/RC tools but still does not supply MSVC `cl.exe`/linker.
- Retrieval note: browser result `turn12view0`; link-follow result `turn14view0` (redirect URL above); persisted immediately after fetch.

## Checkpoint 8 — Deno portable binary

- Retrieved: 2026-10-20; source: [Deno releases](https://github.com/denoland/deno/releases)
- Evidence: the official repository currently shows `v2.9.7` as the latest release (retrieval result summary).
- Evidence: each release publishes `deno-x86_64-pc-windows-msvc.zip` and a matching `.sha256sum` asset; the v2.9.7 x64 Windows archive was verified from its companion file.
- Application: download a versioned Deno x64 zip into `.tools/seelen-build/downloads`, verify the companion checksum, extract only `deno.exe`, and expose it through the project-local launcher. Avoid `deno install` or persistent PATH changes.
- Retrieval note: browser result `turn16search0`; persisted immediately after fetch.

## Checkpoint 12 — Deno v2.9.7 downloaded and verified

- Official archive URL: `https://github.com/denoland/deno/releases/download/v2.9.7/deno-x86_64-pc-windows-msvc.zip`
- Companion checksum URL: `https://github.com/denoland/deno/releases/download/v2.9.7/deno-x86_64-pc-windows-msvc.zip.sha256sum`
- Local archive: `.tools/seelen-build/downloads/deno-v2.9.7-x86_64-pc-windows-msvc.zip` (42,630,221 bytes).
- SHA-256: `A0C3101B4158D1DFB7D6A78A7BF0F3DE80C96BB423C152BEEC8BEB22786F2238`; it equals the companion file's `Hash` value.
- Extracted executable: `.tools/seelen-build/deno/deno.exe` (97,462,048 bytes), `deno 2.9.7 (stable, release, x86_64-pc-windows-msvc)`; executable SHA-256 `E020F3E232BD16E33768DEE528E5983349C962952051CED0A5D58AD42F5D9B33`.
- Download note: the first PowerShell fetch of the small checksum file ended with an unexpected EOF; `curl.exe` through the existing process-local proxy fetched it successfully. The archive itself fetched successfully.

## Checkpoint 13 — portable MSVC extraction approach

- Retrieved: 2026-10-20; source: [mmozeiko portable-msvc.py gist](https://gist.github.com/mmozeiko/7f3162ec2988e81e56d5c4e22cde9977) (search result also surfaced a maintained fork at `0017031/4a0e6d86cdf23908c147bffc21de2ddc`).
- Evidence: the script is designed to download standalone 64-bit MSVC compiler/linker/tools plus Windows SDK headers/libraries into a portable folder without installing Visual Studio; it exposes `--show-versions`, `--msvc-version`, and `--sdk-version` selection.
- Evidence: the script's default Visual Studio channel is `https://aka.ms/vs/17/release/channel`; the result describes a minimal native desktop set without UWP/Store/WinRT payloads.
- Application: this is the best remaining route for project-local `cl.exe`/`link.exe`/MSVC CRT and can be run with `--target=x64 --host=x64 --accept-license` into `.tools/seelen-build/msvc` after auditing the exact script and manifest URLs.
- Provenance limitation: this is a third-party script, not a Microsoft distribution. The script's downloaded packages and hashes must be recorded; no code from it is trusted without inspection.
- Retrieval note: browser result `turn20search0` (fork), `turn20search8` (upstream gist comments), and `turn20search6` (portable tool description); persisted immediately after fetch.

## Checkpoint 14 — CMake portable binary

- Retrieved: 2026-10-20; sources: [CMake official download page](https://cmake.org/download/) and [Kitware CMake v4.4.4 release](https://github.com/Kitware/CMake/releases/tag/v4.4.4).
- Evidence: the official download page publishes a Windows x64 ZIP (`cmake-4.4.4-windows-x86_64.zip`) and SHA-256 summary; no installer is required for the ZIP route.
- Official archive URL: `https://github.com/Kitware/CMake/releases/download/v4.4.4/cmake-4.4.4-windows-x86_64.zip`.
- Release SHA-256 from the release metadata: `BACE36E94B31C68AB6FA295F26DFA11219E0701CF7C94B0284A7D1CB13DAC536`.
- Application: download/extract CMake under `.tools/seelen-build/cmake`, prepend its `bin` only in the process environment, and set `CMAKE`/`CMAKE_GENERATOR` only if the crate requires them. This avoids machine-wide CMake installation.
- Retrieval note: browser results `turn23search0`, `turn23search1`, and `turn23search7`; persisted immediately after fetch.

## Checkpoint 15 — CMake and SDK link-library artifacts verified

- Downloaded official CMake v4.4.4 archive to `.tools/seelen-build/downloads/cmake-4.4.4-windows-x86_64.zip` (54,400,562 bytes); SHA-256 equals the official value `BACE36E94B31C68AB6FA295F26DFA11219E0701CF7C94B0284A7D1CB13DAC536`.
- Extracted CMake under `.tools/seelen-build/cmake/cmake-4.4.4-windows-x86_64`; `cmake.exe --version` reports `4.4.4`.
- Extracted official Windows SDK `Windows SDK for Windows Store Apps Libs-x86_en-us.msi` into the project-local SDK root after proof showed the Desktop Libs MSI alone omitted core import libraries. The x64 SDK `um` directory now contains `kernel32.Lib`, `ntdll.lib`, `UserEnv.Lib`, and `WS2_32.Lib`.
- The environment JSON's `LIB` points to this same x64 `um` directory plus x64 UCRT; this is the path parent should reuse for the native proof.

## Checkpoint 16 — NASM requirement and official portable archive

- Local `aws-lc-sys 0.42.0` documentation confirms that Windows x86/x86-64 builds require NASM unless the crate's `prebuilt-nasm` feature is enabled; the current dependency graph uses `aws-lc-rs` defaults and does not enable that feature.
- Official source: [NASM project page](https://nasm.us/) lists stable NASM `3.02` (2026-06-29). The official directory lists an executable-only x64 ZIP: `https://www.nasm.us/pub/nasm/releasebuilds/3.02/win64/nasm-3.02-win64.zip`.
- The official directory does not publish a companion SHA-256 file; record the local SHA-256 and URL as provenance, and retain the archive under `.tools/seelen-build/downloads`.
- Application: extract `nasm.exe` under `.tools/seelen-build/nasm` and expose it only through the process-local `PATH`/`NASM` environment. No machine-wide install is needed.
- Retrieval note: browser results `turn24search1`, `turn24search4`, and `turn25view0`; local crate requirement read from the fetched cargo source and persisted immediately after source review.

## Checkpoint 9 — Deno manual-download instructions

- Retrieved: 2026-10-20; source: [Deno installation — manual download](https://github.com/denoland/docs/blob/main/runtime/getting_started/installation.md)
- Evidence: Deno documents manual installation by downloading a release zip; for Windows x86_64 the asset is `deno-x86_64-pc-windows-msvc.zip`, and every asset has a matching `.sha256sum` file.
- Application: use the versioned GitHub release asset and checksum file, extract `deno.exe` under `.tools/seelen-build/deno`, and call it explicitly from a local launcher.
- Retrieval note: browser result `turn16search1`; persisted immediately after fetch.

## Checkpoint 10 — rustup-init downloaded and verified

- Retrieved/downloaded: 2026-10-20; official URL: `https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe`
- Companion checksum URL: `https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe.sha256`
- Local files: `.tools/seelen-build/downloads/rustup-init.exe` (12,721,664 bytes) and `.sha256` (65 bytes).
- SHA-256: `6F4BEF66261261FCB43131BE8720BAB817D403A09EDEC7455C371974B90BDB7E`.
- Verification: local SHA-256 equals the official companion checksum (case-insensitive); Authenticode status was `NotSigned`, so the checksum is the recorded integrity evidence.
- Next action: run this bootstrapper with process-local `CARGO_HOME`/`RUSTUP_HOME`, `--profile minimal`, `--default-toolchain nightly-2026-05-22`, and `--no-modify-path`.

## Checkpoint 11 — exact nightly manifest and local Rust result

- Official manifest URL: `https://static.rust-lang.org/dist/2026-05-22/channel-rust-nightly.toml`; companion checksum URL appends `.sha256`.
- Manifest SHA-256 verified locally: `904B259E0C838741DE7A50525C9FC359D12332C71EE236AD51C07598DB6544C0`.
- The manifest identifies Rust `1.97.0-nightly (e96c36b6f 2026-05-21)` for the requested date; the project-local rustup installation reports the same commit and host.
- Download/install needed the process-local proxy `http://127.0.0.1:7890`; direct Rustup networking timed out while PowerShell web requests succeeded. This proxy detail belongs in the launcher/checkpoint and should not be persisted globally.
- Result: the fixed nightly toolchain is prepared and hash-checked under `.tools/seelen-build`; MSVC/SDK remains the only build-environment blocker.
