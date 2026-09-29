# Source checkpoints

**Time**: 2026-09-28, 21:40:00 +08:00
**Source**: https://learn.microsoft.com/microsoft-edge/webview2/concepts/distribution
**Method**: query-search (via `functions.exec` -> `web__run` search_query; official Microsoft Learn result `turn7search0`)
**Confidence**: high
**Insight**: Microsoft Learn identifies `MicrosoftEdgeWebview2Setup.exe` as the small Evergreen Bootstrapper for online clients, gives the silent command `/silent /install`, and distinguishes it from the full Evergreen Standalone Installer for offline deployment.

# Relevant extracted content

> For online clients, the WebView2 Runtime Bootstrapper is a tiny (approximately 2 MB) installer that downloads and installs the Evergreen Runtime from Microsoft servers matching the device architecture.

> Microsoft gives the command `MicrosoftEdgeWebview2Setup.exe /silent /install` for the online-only workflow and says an elevated process/command prompt produces a per-machine install; otherwise the install is per-user.

> For offline clients, the WebView2 Runtime Standalone Installer is a full installer that installs the Evergreen Runtime in offline environments. Microsoft gives `MicrosoftEdgeWebView2RuntimeInstaller{X64/X86/ARM64}.exe /silent /install` for a silent standalone install.

> Microsoft says the bootstrapper may be linked/downloaded programmatically or packaged with the app, while the standalone installer is included for an entirely offline deployment.

---
**Time**: 2026-09-28, 21:57:08 +08:00
**Source**: https://jrsoftware.org/isdl-verify.php
**Method**: query-search (via functions.exec -> web__run search_query; official Inno Setup result turn13search1)
**Confidence**: high
**Insight**: The official Inno verification page says its installers use Authenticode, GitHub Release Attestations, and the Inno Setup Signature Tool. It identifies the expected Authenticode publisher as Pyrsys B.V. and provides verification commands and assets.

# Relevant extracted content

> Authenticode verification: the publisher name should be Pyrsys B.V. and the signature should be valid.

> GitHub Release Attestation example: `gh release verify-asset <filename> --repo jrsoftware/issrc`.

> The page also provides ISSigTool, public-key, and signature-file links for independent verification.

---
**Time**: 2026-09-28, 21:56:10 +08:00
**Source**: https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe
**Method**: browser-rendered link resolution (via functions.exec -> web__run click on official Inno downloads page, turn15view0)
**Confidence**: high
**Insight**: The official Downloads page's GitHub link resolved to the immutable Inno Setup 6.7.3 installer URL. The binary fetch was intentionally not performed; the web tool reported the exact restricted URL, which is sufficient to record the link without downloading or executing it.

# Relevant extracted content

> Resolved URL: https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe

---
**Time**: 2026-09-28, 21:55:50 +08:00
**Source**: https://jrsoftware.org/isdl.php
**Method**: browser-rendered (via functions.exec -> web__run open, turn14view0)
**Confidence**: high
**Insight**: The official Inno Setup Downloads page lists innosetup-6.7.3.exe, links its GitHub download, dates it 2026-05-26, and states that it is digitally signed with Pyrsys B.V. The page also links official verification instructions.

# Relevant extracted content

> Lines 41-44: Filename innosetup-6.7.3.exe; Download Site GitHub; Date 2026-05-26; Description Inno Setup 6 installer; digitally signed with Pyrsys B.V.; verification instructions linked.

---
**Time**: 2026-09-28, 21:55:20 +08:00
**Source**: https://jrsoftware.org/isdl.php
**Method**: query-search (via functions.exec -> web__run search_query; official Inno Setup result turn13search0)
**Confidence**: high
**Insight**: The official Inno Setup Downloads page identifies innosetup-6.7.3.exe as the Inno Setup 6 installer, dated 2026-05-26, hosted on GitHub, and says the installer is digitally signed with Pyrsys B.V. as publisher.

# Relevant extracted content

> Official page result: Filename innosetup-6.7.3.exe; Download Site GitHub; Date 2026-05-26; Description Inno Setup 6 installer.

> The page says the installer is digitally signed with Pyrsys B.V. as the publisher name and links to verification instructions.

---
**Time**: 2026-09-28, 21:54:48 +08:00
**Source**: https://developer.microsoft.com/en-us/microsoft-edge/webview2/
**Method**: extract (via PowerShell Invoke-WebRequest; HTTP 200, HTML length 60147)
**Confidence**: high
**Insight**: The current portal HTML was fetched successfully, but the Evergreen Bootstrapper URL is supplied by the page's client-side Get the Link flow rather than as a plain server-rendered anchor. The HTML confirms the official portal and Bootstrapper/Standalone labels; the exact URL is recorded by the subsequent browser-rendered checkpoint.

# Relevant extracted content

> Canonical page metadata: https://developer.microsoft.com/en-us/microsoft-edge/webview2

> Server-rendered text includes “Evergreen Bootstrapper,” “The Bootstrapper is a tiny installer that downloads the Evergreen Runtime matching device architecture and installs it locally,” and “Evergreen Standalone Installer.”

---
**Time**: 2026-09-28, 21:53:55 +08:00
**Source**: https://developer.microsoft.com/en-us/microsoft-edge/webview2/
**Method**: browser-rendered (via CUA Edge tab; portal Get the Link flow)
**Confidence**: high
**Insight**: The current Microsoft WebView2 portal's Get the Link flow displayed the official Evergreen Bootstrapper URL exactly as https://go.microsoft.com/fwlink/p/?LinkId=2124703. The page labels the Bootstrapper as a tiny installer that downloads the Evergreen Runtime matching device architecture; the link was revealed after the portal's own license-terms step and no file was downloaded.

# Relevant extracted content

> Portal heading: “Evergreen Bootstrapper.”

> Portal text: “The Bootstrapper is a tiny installer that downloads the Evergreen Runtime matching device architecture and installs it locally. There is also a Link that allows you to programmatically download the Bootstrapper.”

> Revealed Get the Link value: https://go.microsoft.com/fwlink/p/?LinkId=2124703

> Portal heading/text for the alternate: “Evergreen Standalone Installer — A full-blown installer that can install the Evergreen Runtime in offline environment. Available for x86/x64/ARM64.”

---
**Time**: 2026-09-28, 21:39:37 +08:00
**Source**: https://jrsoftware.org/ishelp/topic_runsection.htm
**Method**: browser-rendered (via functions.exec -> web__run open, turn11view0)
**Confidence**: high
**Insight**: The official Inno page confirms that postinstall defaults to runasoriginaluser, while explicit runascurrentuser inherits Setup's credentials, typically full administrative privileges. It also confirms the exact syntax relationship for a shell verb: Verb must be combined with shellexec; an .exe does not require shellexec merely because it is executable.

# Relevant extracted content

> Lines 126-138: runascurrentuser inherits Setup/Uninstall credentials and is the default when postinstall is absent. runasoriginaluser is valid only in [Run], uses the normally non-elevated credentials of the user who initially started Setup, and is the default when postinstall is used. The flags cannot be combined.

> Lines 65-72: Verb specifies the action and must be combined with shellexec; common examples are open and print.

> Lines 155-157: shellexec opens the target through its registered association like Explorer; when used, Setup does not wait by default and waituntilterminated is needed if waiting is required.

> Lines 15-18: shellexec is required when Filename is not a directly executable .exe or .com, so it is not required solely for a direct .exe launch.

---
**Time**: 2026-09-28, 21:39:18 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution
**Method**: browser-rendered (via functions.exec -> web__run open, turn9view0)
**Confidence**: high
**Insight**: Microsoft Learn confirms the exact online Bootstrapper command, its requirement to download the matching Runtime from Microsoft servers, the full Standalone command for offline deployment, and that elevated execution selects per-machine installation. It also states that the Bootstrapper can be packaged with the app, but the online flow still needs Runtime download access.

# Relevant extracted content

> Lines 91-104: For online clients, the Bootstrapper is approximately 2 MB and downloads the Evergreen Runtime from Microsoft servers; for offline clients, the Standalone Installer is a full installer for offline environments. Both support per-machine and per-user installs; elevated execution triggers per-machine installation.

> Lines 125-147: The online-only workflow assumes internet access, downloads the Bootstrapper as needed, and invokes MicrosoftEdgeWebview2Setup.exe /silent /install. The Bootstrapper detects device architecture and installs silently. Microsoft also says the Bootstrapper may be packaged with the app.

> Lines 148-162: The entirely offline workflow packages the Evergreen Standalone Installer and invokes MicrosoftEdgeWebView2RuntimeInstaller{X64/X86/ARM64}.exe /silent /install when needed.

> Lines 108-124: Microsoft documents checking the pv (REG_SZ) WebView2 Runtime registry value or calling GetAvailableCoreWebView2BrowserVersionString before deciding whether installation is needed.

---
