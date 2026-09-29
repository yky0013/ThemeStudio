# Compact installer: WebView2 prerequisite and elevated post-install launch

## Verified WebView2 deployment choice

Microsoft’s primary deployment page is [Distribute your app and the WebView2 Runtime](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution). Its official download portal is [Download the WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/). The portal’s current **Get the Link** flow resolved to the Evergreen Bootstrapper URL `https://go.microsoft.com/fwlink/p/?LinkId=2124703` on 2026-09-28. Use that official link (or re-resolve it from the portal when refreshing the package); no binary was downloaded during this check.

For Inno build tooling, the official [Inno Setup Downloads](https://jrsoftware.org/isdl.php) page lists `innosetup-6.7.3.exe` dated 2026-05-26. Its GitHub link resolves to `https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe`. The page states that the installer is digitally signed with publisher name `Pyrsys B.V.`; the official [verification instructions](https://jrsoftware.org/isdl-verify.php) describe Authenticode, GitHub Release Attestations, and ISSigTool checks. No installer was downloaded or executed during this check.

For an online installer, package or download the small `MicrosoftEdgeWebview2Setup.exe` Bootstrapper, then invoke:

```text
MicrosoftEdgeWebview2Setup.exe /silent /install
```

Microsoft states that this Bootstrapper downloads the matching Evergreen Runtime from Microsoft servers and detects the device architecture. Therefore the target needs internet access to obtain the Runtime unless the Runtime is already present. Packaging the Bootstrapper inside the compact installer avoids needing internet access to obtain the small Bootstrapper itself, but it does not make the Runtime download offline.

For an entirely offline deployment, Microsoft directs the installer to include the full architecture-specific Evergreen Standalone Installer and invoke:

```text
MicrosoftEdgeWebView2RuntimeInstaller{X64/X86/ARM64}.exe /silent /install
```

Choose the architecture-specific filename that matches the package. Microsoft’s page also says that elevated execution produces a per-machine Runtime installation; an unelevated invocation produces a per-user installation. If the compact installer is intended to install a machine-wide prerequisite, the prerequisite entry must run from an elevated Setup process.

Before invoking either installer, the compact installer can follow Microsoft’s documented detection step: inspect the WebView2 `pv (REG_SZ)` registry value or call `GetAvailableCoreWebView2BrowserVersionString`. Skip the prerequisite when a valid Runtime is already present.

## Signature verification recommendation

The cited WebView2 deployment page specifies the source portal and deployment commands but does not prescribe an Authenticode verification command. Treat signature verification as a local packaging control: before embedding or executing the downloaded Bootstrapper/Standalone EXE, run PowerShell `Get-AuthenticodeSignature`, require `Status` to be `Valid`, and inspect that the signer is the expected Microsoft publisher. Record the verified file hash and signer in the build manifest. Do not infer trust from the filename alone. This is an operational recommendation, not a claim that Microsoft Learn’s cited page itself mandates that exact check.

Example read-only check:

```powershell
$sig = Get-AuthenticodeSignature -LiteralPath .\MicrosoftEdgeWebview2Setup.exe
$sig.Status
$sig.SignerCertificate.Subject
```

Do not install or execute a file whose signature status or signer does not meet the project’s expected policy.

## Inno Setup fix for the required-admin main EXE

The official [Inno Setup `[Run]` and `[UninstallRun]` documentation](https://jrsoftware.org/ishelp/topic_runsection.htm) states that `postinstall` defaults to `runasoriginaluser`, which uses the normally non-elevated credentials of the user who initially started Setup. It states that explicit `runascurrentuser` makes the child inherit Setup’s credentials, typically full administrative privileges. The two flags cannot be combined.

Given the supplied local facts—main EXE marked `requireAdministrator` and a `postinstall` launch through `runasoriginaluser` producing `CreateProcess failed 740`—the smallest conditional source change is to append `runascurrentuser` to that existing `[Run]` entry, preserving the current flags:

```ini
[Run]
Filename: "{app}\ThemeStudio.exe"; Flags: postinstall nowait skipifsilent unchecked runascurrentuser
```

The exact existing flags must be inspected before editing; the line above is a shape example, not a claim about the package’s current source. If the entry already has explicit `runascurrentuser`, no launch flag change is needed. If Setup itself is not elevated, inheriting Setup credentials may still be insufficient for a required-admin child.

The same Inno page says `Verb` must be combined with `shellexec`, and that `shellexec` opens a target through the registered shell association. It does not list `runas` among its examples; it gives `open` and `print`. A shell-based alternative can therefore be tested only conditionally as:

```ini
Filename: "{app}\ThemeStudio.exe"; Verb: "runas"; Flags: shellexec ...
```

Here `...` means the package’s existing compatible flags; it must not be guessed. An `.exe` does not require `shellexec` merely because it is an executable, and adding `shellexec` changes waiting behavior: Inno does not wait by default, so add `waituntilterminated` only if the package must wait. For this reported 740 case, investigate explicit `runascurrentuser` first; use the `shellexec` + `Verb: "runas"` form only if shell elevation is an intentional tested behavior.

## Decision boundary

For a compact online installer, package the Bootstrapper and use `/silent /install` only when Runtime download access is acceptable. For an offline installer, package the matching Standalone Installer and use the same silent switch pair. Validate the prerequisite signature before execution, detect an existing Runtime first, and make the required-admin app’s `[Run]` launch explicit with `runascurrentuser` after confirming the actual source flags. No installer was run and no application or package files were changed during this documentation check.

## Audit trail

The source payloads and fetched line references are saved in [`20_sources.md`](20_sources.md). Microsoft evidence is recorded from lines 91–104, 125–162 of the browser-rendered page; Inno evidence is recorded from lines 15–18, 65–72, 126–138, and 155–157 of its browser-rendered page.

