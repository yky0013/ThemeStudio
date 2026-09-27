# Inno Setup 6.7.3 compiler payload — synthesis

## Result

An official, usable Inno Setup 6.7.3 compiler payload is present at:

`E:\desktop\windows\ThemeStudio-dev\docs\research\20260927\inno_sdk\inno-6.7.3\`

The parent build workflow can use the contents of this folder as `.tools\inno-6.7.3\`; the expected entry point is `ISCC.exe`.

## Provenance

- Official downloads page: <https://jrsoftware.org/isdl.php>
- Immutable release tag: <https://github.com/jrsoftware/issrc/releases/tag/is-6_7_3>
- Exact installer URL: <https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe>
- Exact release: Inno Setup 6.7.3, published 2026-05-26.
- GitHub API asset size: `10,592,232` bytes.
- GitHub API SHA-256: `9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732`.
- Local installer SHA-256: `9C73C3BAE7ED48D44112A0F48E66742C00090BDB5BEF71D9D3C056C66E97B732` (matches).
- Release page states the release is immutable and the tag/commit are verified under Martijn Laan’s GPG key `E2DD568CF6098F6A`.

## Verification

- Installer Authenticode: `Valid`; signer `Pyrsys B.V.`; certificate thumbprint `E0AB19C8D38CBF9C44709925122A7A02F8C70CB7`.
- Installer `.issig`: verified by official `ISSigTool.exe` with `def02.ispublickey`, result `innosetup-6.7.3.exe: OK`.
- Downloaded release `ISSigTool.exe`: Authenticode `Valid` and verified with `def01.ispublickey`, result `ISSigTool.exe: OK`.
- In the extracted payload, all 17 `.issig` companions passed verification with the official `def01`/`def02` keys; see `payload-signature-check.json`.
- All 20 extracted `.exe`/`.dll` files report valid Authenticode signatures.
- Full 119-file SHA-256 manifest: `payload-manifest.json`.

## Payload contents

The portable folder contains 119 files (28,932,337 bytes), including:

- `ISCC.exe` and `ISCmplr.dll`;
- `ISPP.dll`, `isscint.dll`, 7-Zip/LZMA/BZip/Zlib support DLLs and tools;
- `Default.isl` plus 29 language files under `Languages\`;
- `license.txt`, signed setup payloads, examples, and documentation.

`license.txt` is the bundled “Inno Setup License”, 1,521 bytes, SHA-256 `2E5346868C2A18434489824E11D65C3031620F792FEFC415D05F19CD441ABF5C`.

Running `ISCC.exe /?` produced the expected `Inno Setup 6 Command-Line Compiler` banner and usage text. It did not compile any application script. The help output is saved as `iscc-help.txt`; the binary returned exit code 1 on this help path.

## Portable extraction method and state checks

The official installer was run only in portable mode with `/PORTABLE=1 /VERYSILENT /CURRENTUSER /NORESTART /NOICONS /DIR=<owned-folder>`. The installer log (`portable-extraction.log`) records Setup version 6.7.3, no administrative install mode, a successful run, and no restart. The temporary setup directory was absent after completion. Read-only checks after extraction found no `HKCU\Software\Jordan Russell\Inno Setup` key and no Inno Setup uninstall entry in the checked HKCU/HKLM locations; no system installation was left behind.

The supplied `innoextract` 1.9 could not parse the 6.7.3 installer (`Unexpected setup loader revision: 2`), so the official portable mode was used. No application code was changed and no application build was run.

## Local evidence map

- `00_plan.md`: scope and acceptance criteria.
- `10_discovery.md`: search checkpoints.
- `20_sources.md`: official page/API checkpoints and extracted claims.
- `30_download.md`: download, extraction, hash, signature, and help checkpoints.
- `innosetup-6.7.3.exe`, `.issig`, `ISSigTool.exe`, `def01.ispublickey`, `def02.ispublickey`: source and verification artifacts.
- `inno-6.7.3\`: portable compiler folder.
- `portable-extraction.log`, `iscc-help.txt`, `issigtool-installer-verify.txt`, `issigtool-tool-verify.txt`, `payload-signature-check.json`, `payload-manifest.json`: reproducible local evidence.

