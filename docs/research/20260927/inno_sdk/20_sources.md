# Source checkpoints

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://jrsoftware.org/
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: JRSoftware’s official home page confirms the 6.7.3 release date and states that its Inno Setup download links were changed to immutable GitHub releases on 2026-03-02.

# Relevant extracted content

> `May 26, 2026 - Inno Setup 6.7.3 released.`
>
> `March 2, 2026 - Updated Inno Setup download links to use immutable releases on GitHub.`

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://jrsoftware.org/ishelp/topic_technotes.htm
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: JRSoftware officially documents the installer’s `/PORTABLE=1` mode. It defaults the destination to the desktop and does not create an uninstaller or an Add/Remove Programs entry; the documented example also uses `/silent /currentuser`.

# Relevant extracted content

> `Inno Setup's own installers accept an additional /PORTABLE=1 command-line parameter to enable portable mode which causes the installers to install to the desktop by default and to not create an uninstaller nor an entry in the Add/Remove Programs Control Panel applet.`
>
> Example: `/portable=1 /silent /currentuser`.

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://api.github.com/repos/jrsoftware/issrc/releases/tags/is-6_7_3
**Method**: extract (native PowerShell `Invoke-RestMethod`, official GitHub API)
**Confidence**: high
**Insight**: GitHub’s release API confirms tag `is-6_7_3`, release name `Inno Setup 6.7.3`, publication time `2026-05-26T16:27:57Z`, and provides the installer’s exact asset digest `sha256:9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732` plus the matching `.issig` asset and ISSigTool assets.

# Relevant extracted content

| Asset | Size | SHA-256 digest |
|---|---:|---|
| `innosetup-6.7.3.exe` | 10,592,232 bytes | `9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732` |
| `innosetup-6.7.3.exe.issig` | 376 bytes | `18da06b0f8ca6021a42e023ebd02fe10d37a30a43639c08cc8b15363243663a0` |
| `ISSigTool.exe` | 919,184 bytes | `aea490d45665a88c0c832d25647d21c1b87962efedb25668caec05678e0fd7c6` |
| `ISSigTool.exe.issig` | 368 bytes | `894b3e4c085ff64978071b3f61738bb16b33741930264d6fe8b9f2abfab975e2` |

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://api.github.com/repos/jrsoftware/issrc/releases/tags/is-6_7_3
**Method**: browser-rendered API attempt (via `web__run` open)
**Confidence**: low for payload, high for URL identity
**Insight**: The web research connector cannot access the GitHub API endpoint. Native PowerShell retrieval is required for exact asset metadata; this does not alter the official URL or release identity already established.

# Relevant extracted content

> `URL ... is not accessible via this tool.`

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://github.com/jrsoftware/issrc/releases/tag/is-6_7_3
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: The release page labels Inno Setup 6.7.3 as an immutable release, shows tag `is-6_7_3`, and reports the tag and release commit as signed and verified by Martijn Laan (GPG key ID `E2DD568CF6098F6A`). The web renderer did not load the asset list, so the GitHub API will be queried locally for asset metadata and digest.

# Relevant extracted content

> `Immutable release. Only release title and notes can be modified.`
>
> `This tag was signed with the committer’s verified signature.` — Martijn Laan, GPG key ID `E2DD568CF6098F6A`.
>
> `Assets 8` (asset list failed to render in the browser fetch).

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://jrsoftware.org/isdl-verify.php
**Method**: browser-rendered (via `web__run` click from official downloads page)
**Confidence**: high
**Insight**: JRSoftware documents three independent verification methods. For immutable GitHub release assets, GitHub Release Attestations can be checked with `gh release verify-asset`; the installer’s Authenticode publisher should be `Pyrsys B.V.`; and the Inno Setup Signature Tool can verify matching `.issig` files using `def02.ispublickey`. The page also warns that hashes alone detect corruption/tampering but do not replace full verification.

# Relevant extracted content

> Authenticode: a valid signature should show publisher name `Pyrsys B.V.`.
>
> GitHub release attestation: `gh release verify-asset <filename> --repo jrsoftware/issrc`.
>
> Inno Setup Signature Tool: `issigtool --key-file=def02.ispublickey verify <filenames>`; matching `.issig` files are required. `def02.ispublickey` is used for installers and files that change each release such as `ISCmplr.dll`, `Setup.e32`, and `Setup.e64`.

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe
**Method**: browser-rendered link extraction (via `web__run` click from the official download page)
**Confidence**: high
**Insight**: The official page’s GitHub link resolves to the immutable release asset URL for tag `is-6_7_3`. The web fetcher refused to download the binary as a restricted URL, so the URL was recorded for native PowerShell retrieval and later hash verification.

# Relevant extracted content

> `Failed to fetch https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe: Failed to fetch restricted URL`.
>
> The failed fetch itself exposes the exact immutable asset URL linked by `https://jrsoftware.org/isdl.php`.

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://jrsoftware.org/isdl.php
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: The official downloads page names the exact installer `innosetup-6.7.3.exe`, dates it 2026-05-26, links the download to GitHub, and states it is digitally signed with Pyrsys B.V. as publisher. This is the authoritative path for the immutable release artifact.

# Relevant extracted content

> `Filename ... innosetup-6.7.3.exe ... Download Site GitHub ... 2026-05-26 ... Inno Setup 6 installer`.
>
> `The installer is digitally signed with Pyrsys B.V. as the publisher name` and the page links `Verification instructions`.

---

**Time**: 2026-09-27, Asia/Shanghai
**Source**: https://jrsoftware.org/files/is6-whatsnew.htm
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: The official revision history identifies the exact target as Inno Setup 6.7.3, released 2026-05-26, and records the 6.7.3 compiler/ISPP changes.

# Relevant extracted content

> `Inno Setup 6.7` and `6.7.3 (2026-05-26)`.
>
> 6.7.3 includes a fix for user-defined ISPP functions with no parameters and adds the predefined variable `SysPath`; the page links the official license text.

---

## 2026-09-27T20:27:00+08:00 - installer elevation directive

- URL: https://jrsoftware.org/ishelp/topic_setup_privilegesrequired.htm
- Retrieval: native web fetch of the official Inno Setup reference.
- Outcome: `PrivilegesRequired=admin` requests elevation when installation starts and always runs the actual setup in administrative install mode. `lowest` does not request elevation.
- Local observation: the outer compiled setup bootstrap manifest says `asInvoker`; the application manifest says `requireAdministrator`. The setup directive, administrative installer logs/registration, and actual elevation behavior must be checked separately from the bootstrap manifest.
- Decision: retain the original Inno Setup bootstrap and its supported admin directive; do not patch the compiled executable. The earlier check expecting an elevated outer bootstrap manifest was too strict and is replaced by separate recorded checks.
