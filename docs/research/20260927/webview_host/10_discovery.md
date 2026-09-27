# Microsoft.Web.WebView2 host discovery

Scope: official-source check for the standalone Windows desktop `theme-studio` host. This file records discovery checkpoints only; no SDK or software was downloaded or installed.

**Time**: 2026-09-27, 14:11:20 +08:00
**Source**: https://www.nuget.org/packages/Microsoft.Web.WebView2
**Method**: query-search (via `web__run`, official NuGet Gallery)
**Confidence**: high
**Insight**: The official NuGet Gallery page identifies `Microsoft.Web.WebView2` as the Microsoft-owned package and shows `1.0.4191.47` as the current stable release in the search snapshot; `1.0.4255-prerelease` is newer but prerelease. The page reports the stable release was updated 2026-08-28.

# Relevant extracted content

> NuGet Gallery | Microsoft.Web.WebView2 1.0.4191.47
>
> Version table: `1.0.4255-prerelease` (9/11/2026), `1.0.4191.47` (8/28/2026), followed by older releases.
>
> Owners: Microsoft; webview.

---

**Time**: 2026-09-27, 14:11:20 +08:00
**Source**: https://github.com/MicrosoftDocs/edge-developer/blob/main/microsoft-edge/webview2/concepts/distribution.md
**Method**: query-search (via `web__run`, official MicrosoftDocs repository)
**Confidence**: high
**Insight**: Microsoft’s distribution guidance states that managed apps require the WebView2 .NET Core assembly plus the WPF/WinForms-specific assembly, and that `WebView2Loader.dll` is native and architecture-specific. For x64-only deployment, use the x64 loader under `runtimes\win-x64\native`; AnyCPU requires all architecture variants.

# Relevant extracted content

> For .NET managed apps, include `Microsoft.Web.WebView2.Core.dll` and the WPF/WinForms-specific assembly (`Microsoft.Web.WebView2.Winforms.dll` or `Microsoft.Web.WebView2.WPF.dll`).
>
> `WebView2Loader.dll` is a native and architecture-specific binary. The example managed layout contains `runtimes\win-arm64\native\WebView2Loader.dll`, `runtimes\win-x64\native\WebView2Loader.dll`, and `runtimes\win-x86\native\WebView2Loader.dll`.
>
> A managed AnyCPU app needs the x86, x64, and arm64 loader flavors; a fixed x64 process needs the matching x64 flavor.

---

**Time**: 2026-09-27, 14:11:20 +08:00
**Source**: https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.4191.47
**Method**: query-search (via `web__run`, official NuGet Gallery)
**Confidence**: high
**Insight**: The stable package page gives the exact version and states that the package is compatible with all .NET Framework versions; its computed compatibility table explicitly includes `net462` and later framework targets. It also describes the package as necessary for Win32 C/C++, WPF, and WinForms applications.

# Relevant extracted content

> `Microsoft.Web.WebView2 1.0.4191.47`
>
> “.NET Framework This package is compatible with all versions of .NET Framework.”
>
> Computed target frameworks include `net462`, `net463`, `net47`, `net471`, `net472`, `net48`, and `net481`.
>
> “This package is necessary for Win32 C/C++, WPF, and WinForms applications.”

---

**Time**: 2026-09-27, 14:11:20 +08:00
**Source**: https://github.com/MicrosoftDocs/edge-developer/blob/main/microsoft-edge/webview2/how-to/machine-setup.md
**Method**: query-search (via `web__run`, official MicrosoftDocs repository)
**Confidence**: high
**Insight**: Microsoft’s setup guidance recommends a Release WebView2 SDK version for getting started and identifies the SDK as the NuGet package `Microsoft.Web.WebView2`; the package can be selected from NuGet Package Manager. This supports pinning the stable version above rather than using the prerelease line.

# Relevant extracted content

> “The Microsoft.Web.WebView2 SDK is available in Release and Prerelease versions. To get started, a Release version is recommended.”
>
> The SDK is installed as the `Microsoft.Web.WebView2` NuGet package.

---

**Time**: 2026-09-27, 14:12:02 +08:00
**Source**: https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.4191.47
**Method**: browser-rendered (via `web__run` open; official NuGet Gallery)
**Confidence**: high
**Insight**: The rendered package page confirms the exact stable package version, `.NET Framework` compatibility, explicit `net462` compatibility, WinForms applicability, and the official PackageReference form. It also exposes the official “Download package” link, which resolves to the versioned NuGet package URL recorded below.

# Relevant extracted content

> Lines 1–5: `Microsoft.Web.WebView2 1.0.4191.47`; “.NET Framework This package is compatible with all versions of .NET Framework.”
>
> Lines 128–133: the package is necessary for Win32 C/C++, WPF, and WinForms; computed compatibility includes `net462` and later .NET Framework targets; `native` is compatible.
>
> Lines 40–47: `<PackageReference Include="Microsoft.Web.WebView2" Version="1.0.4191.47" />`.
>
> Lines 186–190 and 222–226: stable `1.0.4191.47` is listed below prerelease `1.0.4255-prerelease`; stable page last updated 2026-08-28; Download package is 8.83 MB.

---

**Time**: 2026-09-27, 14:12:33 +08:00
**Source**: https://api.nuget.org/v3/registration5-gz-semver2/microsoft.web.webview2/1.0.4191.47.json
**Method**: browser-rendered (via `web__run` open; retried once)
**Confidence**: low
**Insight**: The NuGet registration JSON endpoint was not accessible through the configured web retrieval tool on two attempts, so no registration payload was used as evidence. Per the task’s ownership constraint, this failure checkpoint is the equivalent fallback entry in this file; no separate fallback file was created. The package page remains the authoritative source for the version and compatibility claims.

# Relevant extracted content

> `web__run` returned `Internal Error` and reported that the URL was not accessible; the same URL was retried once with the same result.

---

**Time**: 2026-09-27, 14:12:52 +08:00
**Source**: https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/index.json
**Method**: browser-rendered (via `web__run` open; official NuGet v3 flat-container API)
**Confidence**: high
**Insight**: The official NuGet v3 version index lists `1.0.4191.47` as the newest stable version visible on the endpoint; the only later entry is `1.0.4255-prerelease`. The stable package download can therefore be addressed through NuGet’s versioned package endpoint.

# Relevant extracted content

> Lines 131–154 list the recent versions in order, ending with `1.0.4191.47` and then `1.0.4255-prerelease`.
>
> Stable package URL pattern for this package/version: `https://www.nuget.org/api/v2/package/Microsoft.Web.WebView2/1.0.4191.47`.
>
> Equivalent flat-container package URL pattern: `https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/1.0.4191.47/microsoft.web.webview2.1.0.4191.47.nupkg`.

---

**Time**: 2026-09-27, 14:13:37 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-options/
**Method**: query-search (via `web__run`, official Microsoft Learn)
**Confidence**: high
**Insight**: Microsoft documents that .NET Framework projects use `csc.exe`, which can be invoked from the command line, and that the executable is normally under `Windows\Microsoft.NET\Framework\<Version>` (with `Framework64` on 64-bit systems). This supports using the existing v4.0.30319 compiler as a command-line driver, subject to supplying the needed assembly references.

# Relevant extracted content

> “You can invoke the C# compiler by typing the name of its executable file (csc.exe) at a command prompt.”
>
> “For .NET Framework projects, you can also run csc.exe from the command line.”
>
> The executable is usually in the `Microsoft.NET\Framework\<Version>` folder under the Windows directory; exact location depends on the computer configuration.

---

**Time**: 2026-09-27, 14:13:37 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/framework/migration-guide/reference-assemblies
**Method**: query-search (via `web__run`, official Microsoft Learn)
**Confidence**: high
**Insight**: Microsoft states that a project targeting a specific .NET Framework normally builds against that version's reference assemblies from the developer pack; when unavailable, the Microsoft.NETFramework.ReferenceAssemblies package supplies them. For a bare existing csc.exe host, the relevant implication is that net462 reference assemblies must be present or explicitly supplied to `/reference`.

# Relevant extracted content

> “When you target a particular version of .NET Framework, by default your application is built by using the reference assemblies that are included with that version's developer pack.”
>
> The `Microsoft.NETFramework.ReferenceAssemblies` package can provide reference assemblies when the matching developer pack cannot be installed; the package includes many framework versions and selection is determined by the target framework.

---

**Time**: 2026-09-27, 14:13:37 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.winforms.webview2?view=webview2-dotnet-1.0.3856.49
**Method**: query-search (via `web__run`, official Microsoft Learn API reference)
**Confidence**: high
**Insight**: The WebView2 WinForms API reference identifies the required managed assembly as `Microsoft.Web.WebView2.WinForms.dll` and the control as deriving from `System.Windows.Forms.Control`. This confirms the WinForms-specific managed reference in addition to the WebView2 Core assembly.

# Relevant extracted content

> Assembly: `Microsoft.Web.WebView2.WinForms.dll`.
>
> Definition: `public class WebView2 : System.Windows.Forms.Control, System.ComponentModel.ISupportInitialize`.
>
> The control wraps the WebView2 COM API; explicit initialization uses `EnsureCoreWebView2Async(...)` or setting `Source`.

---

**Time**: 2026-09-27, 14:13:37 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/framework/install/guide-for-developers
**Method**: query-search (via `web__run`, official Microsoft Learn)
**Confidence**: high
**Insight**: Microsoft’s developer-pack guidance says targeting a .NET Framework version uses its reference assemblies; the .NET Framework 4.6.2 developer pack supplies the 4.6.2 reference assemblies. Runtime resolution uses the Global Assembly Cache, while reference assemblies are compile-time inputs.

# Relevant extracted content

> The developer pack for .NET Framework 4.6.2 provides that version’s reference assemblies, language packs, and IntelliSense files.
>
> When targeting a specific .NET Framework version, builds use the corresponding developer pack reference assemblies; at runtime, assemblies are resolved from the Global Assembly Cache rather than reference assemblies.

---

**Time**: 2026-09-27, 14:13:37 +08:00
**Source**: https://learn.microsoft.com/en-us/entra/msal/dotnet/advanced/webview2
**Method**: query-search (via `web__run`, official Microsoft Learn)
**Confidence**: high
**Insight**: Microsoft’s .NET Framework WebView2 troubleshooting note records an architecture-loading limitation: a .NET Framework app may need an explicit `PlatformTarget` of `x64` (or matching x86/AnyCPU arrangement), or a direct WebView2 package reference, to avoid loader/BadImageFormat failures. This is relevant to an x64-only csc-built host.

# Relevant extracted content

> On .NET Framework, WebView2 errors can include `BadImageFormatException` or `DllNotFoundException: Unable to load DLL 'WebView2Loader.dll'`.
>
> Microsoft lists `<PlatformTarget>` values `AnyCPU`, `x86`, or `x64`; x86/x64 must match the WebView2 target on the machine. Another workaround is `AnyCPU` plus a direct reference to the WebView2 NuGet package.

---

**Time**: 2026-09-27, 14:14:12 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-options/
**Method**: browser-rendered (via `web__run` open; official Microsoft Learn)
**Confidence**: high
**Insight**: The rendered documentation directly confirms that .NET Framework projects use `csc.exe`, it can be run from the command line, and its executable is normally under `Microsoft.NET\Framework\<Version>`. Thus an existing `v4.0.30319\csc.exe` is a viable compiler driver for a classic .NET Framework host; actual target/reference availability remains a separate local prerequisite.

# Relevant extracted content

> Lines 50–58: .NET Framework projects use `csc.exe` instead of `dotnet build`, and command-line arguments can be passed to it.
>
> Lines 64–67: invoke `csc.exe` at a command prompt; the executable is usually under `Windows\Microsoft.NET\Framework\<Version>` and multiple framework versions may exist.

---

**Time**: 2026-09-27, 14:14:28 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/framework/migration-guide/reference-assemblies
**Method**: browser-rendered (via `web__run` open; official Microsoft Learn)
**Confidence**: high
**Insight**: Microsoft’s rendered guidance confirms the compile-time distinction: a net462 build needs the matching developer-pack reference assemblies, or the equivalent `Microsoft.NETFramework.ReferenceAssemblies` package if those assemblies are unavailable. The existing csc.exe can therefore be used only when these references are available and passed to the compiler.

# Relevant extracted content

> Lines 30–32: a project targeting a particular .NET Framework version builds against that version’s developer-pack reference assemblies; a NuGet reference-assemblies package is an alternative when the pack cannot be installed.
>
> Lines 35–49: the package is `Microsoft.NETFramework.ReferenceAssemblies`; it contains many framework versions, selected by target framework.
>
> Lines 52–65: a project containing that package must be restored before it can be built.

---

**Time**: 2026-09-27, 14:14:47 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.winforms.webview2?view=webview2-dotnet-1.0.3856.49
**Method**: browser-rendered (via `web__run` open; official Microsoft Learn API reference)
**Confidence**: high
**Insight**: The rendered API page directly identifies `Microsoft.Web.WebView2.WinForms.dll` as the WinForms assembly and shows the `WebView2` control inheriting from `System.Windows.Forms.Control`; it also documents asynchronous initialization. This is the managed WinForms reference needed by the host.

# Relevant extracted content

> Lines 33–40: namespace `Microsoft.Web.WebView2.WinForms`, assembly `Microsoft.Web.WebView2.WinForms.dll`.
>
> Lines 426–433: the control embeds WebView2 and has definition `public class WebView2 : System.Windows.Forms.Control` (also implementing `ISupportInitialize`).
>
> Lines 459–465: `CoreWebView2` is initially null; initialization is asynchronous via `EnsureCoreWebView2Async(...)` or `Source`.

---

**Time**: 2026-09-27, 14:15:15 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution
**Method**: browser-rendered (via `web__run` open; official Microsoft Edge Developer documentation)
**Confidence**: high
**Insight**: Microsoft’s current distribution page provides the exact runtime and file-layout constraints. Managed apps need `Microsoft.Web.WebView2.Core.dll` plus the WinForms-specific `Microsoft.Web.WebView2.WinForms.dll`, and an x64 process needs the matching native `runtimes\win-x64\native\WebView2Loader.dll`. The WebView2 Runtime must also exist on the target machine; the SDK DLLs alone are insufficient.

# Relevant extracted content

> Lines 31 and 68–69: the WebView2 Runtime must be present on the client; some Windows 10 systems may not have it, so deployment should detect/install it.
>
> Lines 248–255: ship `WebView2Loader.dll` matching the app architecture; it is native and architecture-specific. An AnyCPU managed app needs x86, x64, and arm64 variants.
>
> Lines 262–273: managed apps need `Microsoft.Web.WebView2.Core.dll` and the WPF/WinForms-specific assembly, with the example `runtimes\win-x64\native\WebView2Loader.dll` layout.
>
> Lines 60–67: production WebView2 apps use the WebView2 Runtime rather than the installed Microsoft Edge Stable browser channel.

---

**Time**: 2026-09-27, 14:15:39 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/framework/install/guide-for-developers
**Method**: browser-rendered (via `web__run` open; official Microsoft Learn)
**Confidence**: high
**Insight**: The current Microsoft developer guidance lists .NET Framework 4.6.2 as an available developer-pack target and states that its developer pack supplies the corresponding reference assemblies. It also confirms that compile-time references come from the developer pack while runtime assemblies resolve from the GAC; later 4.x versions are in-place updates.

# Relevant extracted content

> Lines 115–122: .NET Framework 4.6.2 is listed with supported Windows platforms.
>
> Lines 174–178 and 185–191: the 4.6.2 developer pack provides that version’s reference assemblies; targeting a version builds against those references, while runtime resolution uses the GAC.
>
> Lines 40–42: .NET Framework 4.5.2, 4.6, and 4.6.1 are unsupported; Microsoft recommends updating deployed runtime to 4.6.2 or later. This leaves 4.6.2 as the lower supported baseline in this scope.

---

**Time**: 2026-09-27, 14:15:56 +08:00
**Source**: https://learn.microsoft.com/en-us/entra/msal/dotnet/advanced/webview2
**Method**: browser-rendered (via `web__run` open; official Microsoft Learn)
**Confidence**: high
**Insight**: Microsoft’s .NET Framework troubleshooting page confirms two practical limits relevant to a raw csc-built host: the WebView2 Runtime must be installed, and architecture mismatches can produce `BadImageFormatException` or `DllNotFoundException` for `WebView2Loader.dll`. It recommends an explicit `PlatformTarget` matching the loader/runtime architecture or a direct WebView2 package reference.

# Relevant extracted content

> Lines 35–39: WebView2 use requires Windows 10+ and an installed WebView2 Runtime.
>
> Lines 88–92: on .NET Framework, architecture/loading failures can occur; set `PlatformTarget` to `AnyCPU`, `x86`, or `x64` (x86/x64 must match), or use `AnyCPU` with a direct WebView2 package reference.

---

**Time**: 2026-09-27, 14:16:29 +08:00
**Source**: https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/1.0.4191.47/microsoft.web.webview2.nuspec
**Method**: extract (via PowerShell `Invoke-WebRequest`, official NuGet v3 flat-container metadata; metadata only, no package download)
**Confidence**: high
**Insight**: The versioned official NuGet `.nuspec` confirms package identity/version `Microsoft.Web.WebView2` `1.0.4191.47`, Microsoft authorship, Win32/WPF/WinForms applicability, and no external NuGet dependency groups beyond the package’s own native/UAP groups. This means the host must explicitly reference the package assemblies and the .NET Framework/WinForms framework references.

# Relevant extracted content

> `<id>Microsoft.Web.WebView2</id>`; `<version>1.0.4191.47</version>`; `<authors>Microsoft</authors>`.
>
> Description: “The WebView2 control enables you to embed web technologies (HTML, CSS, and JavaScript) ... This package is necessary for Win32 C/C++, WPF, and WinForms applications.”
>
> Dependencies contain only `native0.0` and `UAP10.0` groups with no listed dependencies.

---

**Time**: 2026-09-27, 14:16:51 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/
**Method**: query-search (via `web__run`, official Microsoft Edge Developer documentation)
**Confidence**: high
**Insight**: Microsoft’s WebView2 introduction explicitly lists `.NET Framework 4.6.2 or later` among supported programming environments. This is the direct official support statement for the requested net462+ baseline.

# Relevant extracted content

> Supported programming environments include `Win32 C/C++`, `.NET Framework 4.6.2 or later`, `.NET Core 3.1 or later`, `.NET 5 or later`, WinUI 2.0, and WinUI 3.0.

---

**Time**: 2026-09-27, 14:16:51 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/get-started/get-started
**Method**: query-search (via `web__run`, official Microsoft Edge Developer documentation)
**Confidence**: high
**Insight**: Microsoft’s tutorial index identifies a dedicated WinForms Getting Started path: create a C# Windows Forms App (.NET Framework) and install the `Microsoft.Web.WebView2` SDK package for that project. This supports the WinForms host choice independently of the API reference.

# Relevant extracted content

> “Get started with WebView2 in WinForms apps | WinForms_GettingStarted | Use the C# Windows Forms App (.NET Framework) project template to create a WinForms project, then install the Microsoft.Web.WebView2 SDK package for the WinForms project.”

---

**Time**: 2026-09-27, 14:17:12 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/
**Method**: browser-rendered (via `web__run` open; official Microsoft Edge Developer documentation)
**Confidence**: high
**Insight**: The current rendered introduction directly confirms `.NET Framework 4.6.2 or later` as a supported WebView2 programming environment. It also identifies Windows 10/11 support and distinguishes Evergreen and Fixed Version runtime distribution, while leaving runtime presence as a deployment concern.

# Relevant extracted content

> Lines 103–112: supported programming environments include `.NET Framework 4.6.2 or later`.
>
> Lines 71–102: supported Windows client/server versions include Windows 10 and Windows 11 families (with the detailed list on the linked operating-system page).
>
> Lines 66–68: both Evergreen and Fixed Version distribution modes are supported.

---

**Time**: 2026-09-27, 14:17:34 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/get-started/winforms
**Method**: browser-rendered (via `web__run` open; official Microsoft Edge Developer documentation)
**Confidence**: high
**Insight**: Microsoft’s WinForms tutorial explicitly uses the C# Windows Forms App (.NET Framework) template and installs the `Microsoft.Web.WebView2` SDK. The current tutorial’s UI example selects .NET Framework 4.7.2 or later, while the broader WebView2 support page and NuGet package metadata establish net462 as the package/platform baseline; therefore 4.7.2 is a tutorial default, not evidence that net462 is unsupported.

# Relevant extracted content

> Lines 33–38: the tutorial creates a C# Windows Forms App (.NET Framework) and installs the Microsoft.Web.WebView2 SDK package.
>
> Lines 70–85: the project template is `C# Windows Forms App (.NET Framework)` and the tutorial selects `.NET Framework 4.7.2 or later` in the UI.
>
> Lines 103–105 and 114–127: install the `Microsoft.Web.WebView2` SDK via NuGet, with prerelease cleared.
>
> Lines 272–275 and 418–423: the code references `Microsoft.Web.WebView2.Core` and asynchronously calls `EnsureCoreWebView2Async`.
>
> Lines 476–478: distributing the app requires distributing/installing the WebView2 Runtime.

---

**Time**: 2026-09-27, 14:18:23 +08:00
**Source**: https://github.com/MicrosoftEdge/WebView2Samples/blob/main/SampleApps/WebView2WindowsFormsBrowser/BrowserForm.cs
**Method**: query-search (via `web__run`, official MicrosoftEdge WebView2Samples repository)
**Confidence**: high
**Insight**: Microsoft’s official WinForms sample imports `System`, `System.Drawing`, `System.Windows.Forms`, `Microsoft.Web.WebView2.Core`, and `Microsoft.Web.WebView2.WinForms`. For a direct csc build, these correspond to the framework references plus the two WebView2 managed assemblies.

# Relevant extracted content

> The sample source includes `using System;`, `using System.Drawing;`, `using System.Windows.Forms;`, `using Microsoft.Web.WebView2.Core;`, and `using Microsoft.Web.WebView2.WinForms;`.
>
> The sample defines a WinForms `Form` and a `Microsoft.Web.WebView2.WinForms.WebView2` control.

---

**Time**: 2026-09-27, 14:18:45 +08:00
**Source**: https://github.com/MicrosoftEdge/WebView2Samples/blob/main/SampleApps/WebView2WindowsFormsBrowser/BrowserForm.cs
**Method**: browser-rendered (via `web__run` open; official MicrosoftEdge WebView2Samples repository)
**Confidence**: high
**Insight**: The official source page confirms this is Microsoft’s WinForms sample (`BrowserForm.cs`, 1490 lines). The rendered page was used only to verify provenance; the import details were taken from the same page’s indexed source snippet and are independently corroborated by the official API/distribution docs.

# Relevant extracted content

> Lines 115–141 identify the repository as `MicrosoftEdge/WebView2Samples` and the file as `BrowserForm.cs` under `SampleApps/WebView2WindowsFormsBrowser`.
>
> The page’s indexed source content includes imports for `System`, `System.Drawing`, `System.Windows.Forms`, `Microsoft.Web.WebView2.Core`, and `Microsoft.Web.WebView2.WinForms`.

---

**Time**: 2026-09-27, 14:19:02 +08:00
**Source**: https://raw.githubusercontent.com/MicrosoftEdge/WebView2Samples/main/SampleApps/WebView2WindowsFormsBrowser/BrowserForm.cs
**Method**: extract (via `web__run` open raw source; official MicrosoftEdge WebView2Samples repository)
**Confidence**: high
**Insight**: The raw official sample makes the direct csc reference set concrete: its imports span `System`, `System.Drawing`, `System.Windows.Forms`, `Microsoft.Web.WebView2.Core`, and `Microsoft.Web.WebView2.WinForms`. A minimal host may omit unused framework references, but those two WebView2 managed assemblies and `System.Windows.Forms.dll` are required for a WinForms WebView2 control; `System.dll`/`System.Drawing.dll` are needed when the corresponding base types are used.

# Relevant extracted content

> Lines 4–15 import `System`, `System.Drawing`, `System.Windows.Forms`, `Microsoft.Web.WebView2.Core`, and `Microsoft.Web.WebView2.WinForms` (plus optional sample namespaces).
>
> Lines 18–28 use `Form` and `CoreWebView2CreationProperties`/`CoreWebView2` types.
>
> Lines 174–182 use `Microsoft.Web.WebView2.WinForms.WebView2` and its initialization/navigation events.

---

**Time**: 2026-09-27, 14:19:28 +08:00
**Source**: https://raw.githubusercontent.com/MicrosoftEdge/WebView2Feedback/main/specs/LoaderDllFolderPath.md
**Method**: extract (via `web__run` open raw source; official MicrosoftEdge WebView2Feedback specification)
**Confidence**: high
**Insight**: The official loader-path specification confirms that .NET must use the standalone native `WebView2Loader.dll`; it cannot merge that native code into a managed assembly. By default the loader is searched using normal Windows loading rules, and `CoreWebView2Environment.SetLoaderDllFolderPath` can point to a folder containing the matching x64 DLL before other CoreWebView2Environment APIs are called.

# Relevant extracted content

> Lines 1–3: for .NET projects the loader must be a standalone DLL because it is native.
>
> Lines 20–29: an absolute or relative folder can be specified; the folder must contain `WebView2Loader.dll`.
>
> Lines 33–37: the folder must contain a loader matching the current process architecture; relative paths are relative to `Microsoft.Web.WebView2.Core.dll`; missing/unloadable DLLs result in loader failures such as `DllNotFoundException`.

---

**Time**: 2026-09-27, 14:19:49 +08:00
**Source**: https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.4191.47
**Method**: extract (via PowerShell `Invoke-WebRequest` link inspection; official NuGet Gallery HTML only, no package download)
**Confidence**: high
**Insight**: Inspecting the official package page’s link metadata yields the exact versioned download endpoint without downloading the `.nupkg`.

# Relevant extracted content

> Package page link href: `https://www.nuget.org/api/v2/package/Microsoft.Web.WebView2/1.0.4191.47`.

---

**Time**: 2026-09-27, 14:20:25 +08:00
**Source**: https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/1.0.4191.47/microsoft.web.webview2.1.0.4191.47.nupkg (plus the package page’s v2 link)
**Method**: extract (via PowerShell `Invoke-WebRequest -Method Head`; official NuGet endpoints, metadata headers only)
**Confidence**: high
**Insight**: A metadata-only HEAD check confirms the versioned flat-container package URL returns HTTP 200 and an `application/octet-stream` package of 9,259,926 bytes. The NuGet page’s v2 download-link href was also captured, but its HEAD request returned 404 (likely endpoint method/redirect behavior), so the verified direct URL for automation is the flat-container URL.

# Relevant extracted content

> Verified URL: `https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/1.0.4191.47/microsoft.web.webview2.1.0.4191.47.nupkg`.
>
> HEAD result: HTTP `200`; `Content-Type: application/octet-stream`; `Content-Length: 9259926`.
>
> NuGet page href also exposed `https://www.nuget.org/api/v2/package/Microsoft.Web.WebView2/1.0.4191.47`; HEAD on that endpoint returned `404` in this environment, so treat it as the page-provided link rather than the verified automation URL.

---

**Time**: 2026-09-27, 14:20:39 +08:00
**Source**: `C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe` and `C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe`
**Method**: local-inspection (PowerShell `Get-Item`/`VersionInfo`; read-only)
**Confidence**: high
**Insight**: Both existing Windows v4.0.30319-folder compilers are present. Their file/product version is `4.8.9221.0 built by: NET481REL1LAST_25H2`, so the folder name is the .NET Framework compiler location, while the actual compiler binary is from the installed 4.8.1 servicing line. This is sufficient to establish compiler availability, but it does not prove the WebView2 references or net462 reference assemblies are currently installed.

# Relevant extracted content

> `Framework64\v4.0.30319\csc.exe`: exists; FileVersion/ProductVersion `4.8.9221.0 built by: NET481REL1LAST_25H2`.
>
> `Framework\v4.0.30319\csc.exe`: exists; FileVersion/ProductVersion `4.8.9221.0 built by: NET481REL1LAST_25H2`.

---

**Time**: 2026-09-27, 14:22:17 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-options/inputs
**Method**: query-search (via `web__run`, official Microsoft Learn)
**Confidence**: high
**Insight**: Microsoft documents csc’s `/reference` (`-reference`/`-references`) option as the mechanism for importing metadata from specified assembly files. This is the direct command-line mechanism needed to pass the two WebView2 managed DLLs and any framework assemblies not already supplied by `csc.rsp`.

# Relevant extracted content

> The References option is `-reference` or `-references` in csc syntax.
>
> It imports public type information from specified assembly files into the compilation.

---

**Time**: 2026-09-27, 14:22:17 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-options/output
**Method**: query-search (via `web__run`, official Microsoft Learn)
**Confidence**: high
**Insight**: Microsoft documents csc’s `-platform:x64` option and defines x64 as a 64-bit CLR target. For a fixed x64 WebView2 host, this option aligns the process with `runtimes\win-x64\native\WebView2Loader.dll`; `anycpu` would require architecture-aware loader handling.

# Relevant extracted content

> Compiler mapping: `PlatformTarget` → csc.exe `-platform:`.
>
> `x64` compiles the assembly to run by the 64-bit CLR on AMD64/EM64T; `anycpu` is the default and runs according to the host process/OS rules.

---

**Time**: 2026-09-27, 14:22:17 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-options/miscellaneous
**Method**: query-search (via `web__run`, official Microsoft Learn)
**Confidence**: high
**Insight**: Microsoft documents that the .NET Framework compiler uses `csc.rsp`, located beside csc.exe, and that it references assemblies shipped with .NET Framework. This can cover common framework references, but it cannot supply the WebView2 package assemblies; those still need explicit `/reference` paths.

# Relevant extracted content

> `csc.rsp` is located in the same directory as `csc.exe`.
>
> The response file references assemblies shipped with .NET Framework; custom assemblies are added separately through compiler options.

---

**Time**: 2026-09-27, 14:22:41 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-options/inputs
**Method**: browser-rendered (via `web__run` open; official Microsoft Learn)
**Confidence**: high
**Insight**: The rendered documentation confirms csc’s `/reference` (`-reference`/`-references`) option and explains that each specified assembly file contributes public metadata to the compilation. This is the mechanism for explicitly referencing `Microsoft.Web.WebView2.Core.dll` and `Microsoft.Web.WebView2.WinForms.dll` alongside any framework DLLs not already in csc.rsp.

# Relevant extracted content

> Lines 31–38: `References / -reference or -references` imports metadata from specified assembly files.
>
> Lines 40–48: each reference is an assembly-manifest file; multiple references can be supplied separately, and additional search paths can be specified.

---

**Time**: 2026-09-27, 14:22:56 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-options/output
**Method**: browser-rendered (via `web__run` open; official Microsoft Learn)
**Confidence**: high
**Insight**: The rendered C# compiler documentation confirms `-platform:x64` as the csc option for producing a 64-bit CLR-targeted assembly, and `-target:winexe` for a GUI Windows executable. This supports an x64 WebView2 host compiled directly with the existing csc.exe.

# Relevant extracted content

> Lines 31–39 map `PlatformTarget` to csc `-platform:` and `OutputType` to csc `-target:`.
>
> Lines 70–81 define `anycpu`, `x64`, and `x86`; `x64` targets the 64-bit CLR on AMD64/EM64T.
>
> Lines 132–134 define `winexe` as a Windows UI executable and require one `Main` entry point.

---

**Time**: 2026-09-27, 14:23:13 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-options/miscellaneous
**Method**: browser-rendered (via `web__run` open; official Microsoft Learn)
**Confidence**: high
**Insight**: The rendered docs confirm csc’s `csc.rsp` is beside csc.exe and that it references assemblies shipped with .NET Framework. This explains why basic framework references may resolve automatically, but custom WebView2 DLLs still need explicit references or a response file entry.

# Relevant extracted content

> Lines 31–35: csc supports response files and `-noconfig` controls automatic inclusion of `CSC.RSP`.
>
> Lines 48–51: `csc.rsp` is located beside `csc.exe` and can contain compiler options/source files.
>
> Lines 59–65: `csc.rsp` references assemblies shipped with .NET Framework; custom references/options must be supplied separately.

---

