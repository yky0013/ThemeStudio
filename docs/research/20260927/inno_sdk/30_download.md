# Download and extraction checkpoints

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe
**Method**: native PowerShell `Invoke-WebRequest` into the owned folder
**Confidence**: high
**Insight**: The downloaded installer is exactly the GitHub immutable-release asset advertised by JRSoftware. Its size and SHA-256 match the GitHub API digest, and Windows Authenticode verifies it with publisher Pyrsys B.V.

# Relevant extracted content

- Local path: `innosetup-6.7.3.exe`
- Size: `10,592,232` bytes
- SHA-256: `9C73C3BAE7ED48D44112A0F48E66742C00090BDB5BEF71D9D3C056C66E97B732`
- Expected API digest: `9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732`
- Authenticode: `Valid`; status message `Signature verified.`
- Signer subject: `CN=Pyrsys B.V., O=Pyrsys B.V., S=Noord-Holland, C=NL`
- Signer certificate thumbprint: `E0AB19C8D38CBF9C44709925122A7A02F8C70CB7`

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: portable payload executable/DLL signature scan
**Method**: local PowerShell `Get-AuthenticodeSignature`
**Confidence**: high
**Insight**: Every executable and DLL in the extracted payload (20 files, including compiler and compression support binaries) reports a valid Authenticode signature; no unsigned or invalid executable/DLL was found.

# Relevant extracted content

- Scanned: `20` `.exe`/`.dll` files
- Valid: `20`
- Other statuses: `0`
- The payload’s `ISCC.exe` and support libraries therefore have both valid Authenticode and, where provided, valid Inno Setup `.issig` signatures.

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: all 17 `.issig` companions in `inno-6.7.3\`
**Method**: local ISSigTool batch verification; results persisted to `payload-signature-check.json`
**Confidence**: high
**Insight**: Every signed payload file discovered in the portable compiler directory passed verification with one of the two official Inno Setup public keys; no signed-file verification failed.

# Relevant extracted content

- Checked: `17`
- Passed: `17`
- Failed: `0`
- Report: `payload-signature-check.json`

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: extracted `inno-6.7.3` payload and its bundled `.issig` files
**Method**: local `ISSigTool.exe` verification with official `def01.ispublickey` and `def02.ispublickey`
**Confidence**: high
**Insight**: All requested compiler-side and setup-support binaries tested passed Inno Setup’s own signature verification. `ISCmplr.dll` and `ISPP.dll` use `def02`; compression/parser and setup payload files use `def01` or `def02` as appropriate.

# Relevant extracted content

Verified with exit code `0`: `ISCmplr.dll`, `ISPP.dll`, `isscint.dll`, `is7z.dll`, `is7zxa.dll`, `is7zxr.dll`, `isbzip.dll`, `isbunzip.dll`, `islzma.dll`, `islzma32.exe`, `islzma64.exe`, `isunzlib.dll`, `iszlib.dll`, `Setup.e32`, `SetupCustomStyle.e32`, `SetupLdr.e32`, and `SetupLdr.e64`.

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: local verification of `innosetup-6.7.3.exe` against its `.issig` using official `def02.ispublickey`
**Method**: local `ISSigTool.exe --key-file=def02.ispublickey verify`
**Confidence**: high
**Insight**: The Inno Setup signature tool accepted the downloaded installer signature, providing cryptographic verification beyond the matching SHA-256 and Authenticode checks.

# Relevant extracted content

> `innosetup-6.7.3.exe: OK`

- Exit code: `0`
- Captured output: `issigtool-installer-verify.txt`

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: local verification of `ISSigTool.exe` against its `.issig` using official `def01.ispublickey`
**Method**: local `ISSigTool.exe --key-file=def01.ispublickey verify`
**Confidence**: high
**Insight**: The downloaded release ISSigTool helper also passed the official signature verification using the key ID specified by its companion `.issig` file.

# Relevant extracted content

> `ISSigTool.exe: OK`

- Exit code: `0`
- Captured output: `issigtool-tool-verify.txt`

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://files.jrsoftware.org/is/misc/def01.ispublickey
**Method**: native PowerShell `Invoke-WebRequest` into the owned folder
**Confidence**: high
**Insight**: The official `def01` key was downloaded for verifying release files whose `.issig` records use the `def01` key ID, including the 6.7.3 ISSigTool asset.

# Relevant extracted content

- Local path: `def01.ispublickey`
- Size: `248` bytes
- SHA-256: `3B0B7E1E478C9AB327746A990512E2B245C9231E88A7FDD60D7874DD439DB562`
- Key ID: `def0147c3bbc17ab99bf7b7a9c2de1390283f38972152418d7c2a4a7d7131a38`
- Public key coordinates recorded in the downloaded file: `public-x e3e943066aff8f28d2219fd71c9ffff4c8d1aa26bc4225434be67180ab5e242d`; `public-y e419041c3f54551e86a1c47f387005cd535dfc9d64339b30d37f9a4f7866b650`.

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: `innosetup-6.7.3.exe` executed with official `/PORTABLE=1` mode
**Method**: native PowerShell `Start-Process` with `/PORTABLE=1 /VERYSILENT /CURRENTUSER /NORESTART /NOICONS /DIR=<owned-folder>`
**Confidence**: high
**Insight**: The official portable mode produced a self-contained compiler directory with 119 files, including `ISCC.exe`, `ISCmplr.dll`, `Default.isl`, 29 language files, compiler support DLLs, signed `.issig` companions, examples, and license text. The installer returned exit code 0. Its log recorded Setup version 6.7.3, no administrative mode, and successful installation only under the owned target; the temporary setup directory was removed afterward.

# Relevant extracted content

- Portable folder: `inno-6.7.3\`
- File count: `119`
- Required payload present: `ISCC.exe`, `ISCmplr.dll`, `Default.isl`, `Languages\` (29 `.isl` files), `license.txt`
- Registry/uninstall read-only checks after extraction: no `HKCU\Software\Jordan Russell\Inno Setup`, no HKCU/HKLM Inno Setup uninstall entry, no 32-bit HKLM uninstall entry
- Setup log: `portable-extraction.log`; key lines include `Setup version: Inno Setup version 6.7.3`, `Administrative install mode: No`, `Install mode root key: HKEY_CURRENT_USER`, `Installation process succeeded.`
- Temporary setup directory `C:\Users\yky\AppData\Local\Temp\is-ENWEDJHWAJ.tmp`: absent after completion

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: `inno-6.7.3\ISCC.exe`
**Method**: local executable help invocation (`ISCC.exe /?`)
**Confidence**: high
**Insight**: The extracted command-line compiler runs and reports the Inno Setup 6 command-line compiler banner and normal usage/options without compiling any application script. The help invocation exits with code 1, which is expected for this binary’s help path; the output confirms the executable is the intended ISCC compiler.

# Relevant extracted content

> `Inno Setup 6 Command-Line Compiler`
>
> `Usage: iscc [options] scriptfile.iss`
>
> `/ ? Show this help screen` (rendered as `/?` in the captured file).

- Captured output: `iscc-help.txt`
- Authenticode: `ISCC.exe` signature status `Valid`, signer `CN=Pyrsys B.V., O=Pyrsys B.V., S=Noord-Holland, C=NL`
- The PE version metadata reports `0.0.0.0`; version identity is therefore taken from the executable’s help banner and installer log, not that metadata field.

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://files.jrsoftware.org/is/misc/def02.ispublickey
**Method**: native PowerShell `Invoke-WebRequest` into the owned folder
**Confidence**: high
**Insight**: The official verification key referenced by JRSoftware was downloaded for ISSigTool verification. Its key ID matches the `def02` key ID embedded in the installer `.issig` file.

# Relevant extracted content

- Local path: `def02.ispublickey`
- Size: `248` bytes
- SHA-256: `32BEA6BCEB4AC7C4E6B3BECDF3FB38DE77378C5E76D494AB907D87CFAB9E597B`
- Key ID: `def020edee3c4835fd54d85eff8b66d4d899b22a777353ca4a114b652e5e7a28`
- Public key coordinates recorded in the downloaded file: `public-x 515dc7d6c16d4a46272ceb3d158c5630a96466ab4d948e72c2029d737c823097`; `public-y f3c21f6b5156c52a35f6f28016ee3e31a3ded60c325b81fb7b1f88c221081a61`.

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/ISSigTool.exe.issig
**Method**: native PowerShell `Invoke-WebRequest` into the owned folder
**Confidence**: high
**Insight**: The release signature file for ISSigTool matches its filename, byte size, and SHA-256, with key ID `def0147c3bbc17ab99bf7b7a9c2de1390283f38972152418d7c2a4a7d7131a38`.

# Relevant extracted content

- Local path: `ISSigTool.exe.issig`
- Size: `368` bytes
- SHA-256: `894B3E4C085FF64978071B3F61738BB16B33741930264D6FE8B9F2ABFAB975E2`
- Signature file payload: `format issig-v2`; `file-name "ISSigTool.exe"`; `file-size 919184`; `file-hash aea490d45665a88c0c832d25647d21c1b87962efedb25668caec05678e0fd7c6`; `key-id def0147c3bbc17ab99bf7b7a9c2de1390283f38972152418d7c2a4a7d7131a38`.

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/ISSigTool.exe
**Method**: native PowerShell `Invoke-WebRequest` into the owned folder
**Confidence**: high
**Insight**: The release’s ISSigTool helper was downloaded for local signature verification. Its size and SHA-256 match the GitHub API, and its Authenticode signature is valid under the same Pyrsys B.V. publisher.

# Relevant extracted content

- Local path: `ISSigTool.exe`
- Size: `919,184` bytes
- SHA-256: `AEA490D45665A88C0C832D25647D21C1B87962EFEDB25668CAEC05678E0FD7C6`
- Authenticode: `Valid`; signer `CN=Pyrsys B.V., O=Pyrsys B.V., S=Noord-Holland, C=NL`

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe.issig
**Method**: native PowerShell `Invoke-WebRequest` into the owned folder
**Confidence**: high
**Insight**: The release signature file matches the installer’s filename, byte size, and SHA-256, and identifies key ID `def020edee3c4835fd54d85eff8b66d4d899b22a777353ca4a114b652e5e7a28`.

# Relevant extracted content

- Local path: `innosetup-6.7.3.exe.issig`
- Size: `376` bytes
- SHA-256: `18DA06B0F8CA6021A42E023EBD02FE10D37A30A43639C08CC8B15363243663A0`
- Signature file payload: `format issig-v2`; `file-name "innosetup-6.7.3.exe"`; `file-size 10592232`; `file-hash 9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732`; `key-id def020edee3c4835fd54d85eff8b66d4d899b22a777353ca4a114b652e5e7a28`.

---
