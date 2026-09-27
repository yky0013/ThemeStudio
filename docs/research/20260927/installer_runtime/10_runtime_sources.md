# WebView2 Evergreen Runtime installer discovery

Scope: official Microsoft-source check for packaging the x64 Evergreen Standalone Installer with the Theme Studio Windows installer. No installer was downloaded or executed. Core-page limit: three unique official pages.

**Time**: 2026-09-27, 14:50:29 +08:00
**Source**: https://developer.microsoft.com/en-us/microsoft-edge/webview2
**Method**: query-search (via `web__run`, official Microsoft Edge Developer download page)
**Confidence**: high
**Insight**: Microsoft’s official download page exposes an Evergreen Standalone Installer choice for x86/x64/ARM64. The x64 link will be inspected without saving or executing the payload to capture the current redirected URL.

# Relevant extracted content

> The page has a “Download the WebView2 Runtime” section with an “Evergreen Standalone Installer” described as a full installer for offline environments and separate x86, x64, and ARM64 choices.

---

**Time**: 2026-09-27, 14:50:29 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution
**Method**: query-search (via `web__run`, official Microsoft Edge Developer documentation)
**Confidence**: high
**Insight**: Microsoft’s distribution guidance covers the required detection registry keys, per-user/per-machine behavior, silent commands, and the approved offline flow of including the Evergreen Standalone Installer in the application installer or updater.

# Relevant extracted content

> The page documents HKLM/HKCU `pv` detection, `MicrosoftEdgeWebView2RuntimeInstaller{X64/X86/ARM64}.exe /silent /install`, and the sequence: download standalone installer, include it in the app installer/updater, detect existing Runtime, then install only when missing.

---

**Time**: 2026-09-27, 14:50:29 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/samples/wv2deploymentvsinstallersample
**Method**: query-search (via `web__run`, official Microsoft Edge WebView2 deployment sample)
**Confidence**: high
**Insight**: Microsoft’s official installer sample explicitly allows packaging `MicrosoftEdgeWebView2RuntimeInstallerX64.exe` with the app and directs the outer setup project to use `Commands Reboot="Defer"`; it also requires changing the filename for non-x64 targets.

# Relevant extracted content

> The sample demonstrates three approaches, including packaging the Evergreen WebView2 Runtime Standalone Installer with the app.
>
> For the standalone approach, `product.xml` includes `MicrosoftEdgeWebView2RuntimeInstallerX64.exe` and the command section uses `Reboot="Defer"`.

---

**Time**: 2026-09-27, 14:53:16 +08:00
**Source**: https://developer.microsoft.com/en-us/microsoft-edge/webview2
**Method**: browser-rendered + redirect extraction (via `web__run` and metadata-only PowerShell/`curl.exe -I -L`; official Microsoft Edge Developer page; no installer body downloaded)
**Confidence**: high
**Insight**: The rendered official page states that the Evergreen Standalone Installer is a full installer for offline environments and offers x86/x64/ARM64. Its official page component exposes the x64 short link `https://go.microsoft.com/fwlink/?linkid=2124701`; following redirects with headers only currently resolves to the CDN URL below.

# Relevant extracted content

> Page lines 40–42: “Download the WebView2 Runtime” section for application distribution.
>
> Page lines 55–63: Evergreen Standalone Installer is a full offline installer, with x86, x64, and ARM64 choices.
>
> The page’s official component asset was `https://edgecdn-embza6g8cacagcbn.z01.azurefd.net/shared/edgeweb/_nuxt/BIbVQZ4U.js`; its `BlockWebView2` code maps the x64 button to the short link above.
>
> Current x64 short link from the page’s official `BlockWebView2` component: `https://go.microsoft.com/fwlink/?linkid=2124701`.
>
> Header-only redirect chain (`curl.exe -sS -I -L --max-redirs 10`) on 2026-09-27:
>
> `302 Location: https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/06fb6ad8-1976-4e78-9ceb-3ae170edebde/MicrosoftEdgeWebView2RuntimeInstallerX64.exe`
>
> Final response: `200 OK`, `Content-Type: application/octet-stream`, `Content-Length: 212213456`, `Last-Modified: Thu, 24 Sep 2026 19:32:25 GMT`.

---

**Time**: 2026-09-27, 14:53:16 +08:00
**Source**: https://go.microsoft.com/fwlink/?linkid=2124701
**Method**: extract (metadata-only `curl.exe -I -L`; official Microsoft redirect endpoint; no installer body downloaded)
**Confidence**: high
**Insight**: The x64 redirect endpoint is currently usable as the stable official entry point, while the CDN URL is the concrete versioned payload URL observed today. The CDN URL should be recorded with retrieval time and refreshed before a future release because Evergreen content changes.

# Relevant extracted content

> Redirect target: `https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/06fb6ad8-1976-4e78-9ceb-3ae170edebde/MicrosoftEdgeWebView2RuntimeInstallerX64.exe`.
>
> The request used HEAD-only headers and followed the 302; no installer bytes were saved or executed.

---

**Time**: 2026-09-27, 14:53:39 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution
**Method**: browser-rendered (via `web__run` open; official Microsoft Edge Developer documentation)
**Confidence**: high
**Insight**: Microsoft’s current distribution page supplies the full implementation rules: detect `pv` in the documented HKLM/HKCU keys, include the standalone installer in the app installer/updater, run `/silent /install` only when missing, and distinguish per-machine versus per-user installation by elevation. It also documents restart behavior for Evergreen updates and says a running app continues using the previous Runtime until references are released or the app restarts.

# Relevant extracted content

> Lines 31 and 68–69: WebView2 Runtime must be present; detect/install before creating WebView2.
>
> Lines 99–105: standalone installer is the offline option; it may be included in an app installer/updater; elevated execution gives per-machine installation, otherwise per-user.
>
> Lines 110–124: inspect `pv (REG_SZ)` and require a value greater than `0.0.0.0`.
>
> On 64-bit Windows:
>
> `HKLM\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}`
>
> `HKCU\Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}`
>
> On 32-bit Windows, HKLM omits `WOW6432Node`; HKCU is the same path.
>
> Lines 157–162: standalone silent command is `MicrosoftEdgeWebView2RuntimeInstaller{X64/X86/ARM64}.exe /silent /install`.
>
> Lines 163–167: an updated Evergreen Runtime is used after the app restarts or releases old WebView2 environment references; `NewBrowserVersionAvailable` can trigger a restart prompt/workflow.

---

**Time**: 2026-09-27, 14:54:00 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/samples/wv2deploymentvsinstallersample
**Method**: browser-rendered (via `web__run` open; official Microsoft Edge WebView2 deployment sample)
**Confidence**: high
**Insight**: Microsoft’s official installer sample explicitly approves chaining the Evergreen Standalone Installer with an app installer. For x64, include `MicrosoftEdgeWebView2RuntimeInstallerX64.exe` as a package file and set the outer installer’s command section to `Reboot="Defer"`; change the filename for non-x64 architectures.

# Relevant extracted content

> Lines 31–44: the sample creates a Setup Project and demonstrates packaging the Evergreen WebView2 Runtime Standalone Installer with the app.
>
> Lines 82–86: x64 standalone package file is `MicrosoftEdgeWebView2RuntimeInstallerX64.exe`.
>
> Lines 114–124: uncomment the standalone package file and point `<Commands Reboot="Defer">` `PackageFile` at it; change the filename for non-x64 devices.
>
> Lines 127–132: download the Bootstrapper or Standalone Installer from the official WebView2 page and place it in the package source folder before building the setup project.

---

## Derived implementation notes

These notes are derived only from the seven checkpoints above; they are not an additional source.

### Current x64 payload

Use the official entry point `https://go.microsoft.com/fwlink/?linkid=2124701`. On 2026-09-27, header-only redirect resolution produced:

`https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/06fb6ad8-1976-4e78-9ceb-3ae170edebde/MicrosoftEdgeWebView2RuntimeInstallerX64.exe`

The CDN URL is time-sensitive Evergreen content. Keep the short official entry point and record a fresh redirect/hash during each release preparation; do not assume the GUID remains unchanged.

### Runtime detection

Read the `pv` `REG_SZ` value and accept the Runtime as present only when at least one key exists with a version greater than `0.0.0.0`:

- 64-bit Windows: `HKLM\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}` and `HKCU\Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}`.
- 32-bit Windows: `HKLM\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}` and the same HKCU path.

Missing key, `null`, empty string, or `0.0.0.0` means “not installed”. After the installer exits, re-read the same keys and require a valid positive version before continuing the Theme Studio installation.

### Offline install flow

Bundle `MicrosoftEdgeWebView2RuntimeInstallerX64.exe` inside the Theme Studio installer. At prerequisite time: detect the Runtime, run the bundled file only when missing, wait for process completion, re-check `pv`, and then continue the application installation. Invoke it as:

```text
MicrosoftEdgeWebView2RuntimeInstallerX64.exe /silent /install
```

Elevated execution requests a per-machine install; a non-elevated process installs per-user. A per-user installation can be replaced by a per-machine installation when a per-machine Microsoft Edge Updater is present.

### Exit code and restart handling

The three selected official pages do not publish a numeric exit-code table for the Evergreen Standalone Installer. The installer wrapper should therefore record the raw process exit code, avoid hardcoding `3010`, `1641`, or another reboot code without separate validation, and use the post-install `pv` check as the authoritative prerequisite result. Treat a nonzero code or a missing/invalid `pv` after completion as a runtime-install failure and retain the installer log/context.

For the outer setup, use the official sample’s `Reboot="Defer"` behavior. Evergreen updates become active for a running app only after old WebView2 environment references are released or the app restarts; Theme Studio should close/restart its own WebView2 host when required and should not force a machine reboot merely because the Runtime installer was chained.

The Evergreen Runtime is shared by multiple apps, so the Theme Studio uninstaller should leave the shared WebView2 Runtime installed.

