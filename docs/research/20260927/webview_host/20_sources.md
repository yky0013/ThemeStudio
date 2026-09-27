# WebView2 host research checkpoints

## C# 5 / .NET Framework 4.8 normalization

The Microsoft API pages render optional reference parameters as `= default`, but the host target is C# 5. The snippets below use the C# 5-compatible equivalent `= null` for those reference parameters; the API types and overloads are otherwise unchanged. `async`/`await`, `Task`, event handlers, object initializers, and `var` are available in C# 5. These are signatures and policy fragments only, not a complete program.

## Source 1 — CoreWebView2Environment.CreateAsync

**Time**: 2026-09-27, 14:11:37 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2environment.createasync?view=webview2-dotnet-1.0.3650.58
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: `CreateAsync` returns a `Task<CoreWebView2Environment>` and accepts browser executable, user data, and environment options. A caller-supplied `userDataFolder` is the supported isolation point; if omitted, a default `{Executable File Name}.WebView2` folder is created beside compiled code, subject to write permission.

# Relevant extracted content

```csharp
public static System.Threading.Tasks.Task<Microsoft.Web.WebView2.Core.CoreWebView2Environment>
    CreateAsync(
        string browserExecutableFolder = null,
        string userDataFolder = null,
        Microsoft.Web.WebView2.Core.CoreWebView2EnvironmentOptions options = null);
```

Microsoft documents that `browserExecutableFolder` may be a relative or absolute fixed-runtime folder; `null` or empty selects an installed compatible WebView2 Runtime. `userDataFolder` may be absolute or relative to the compiled code. The default is `{Executable File Name}.WebView2` beside the compiled code, and creation fails when the process cannot create it. WebView creation can also fail when the supplied `options` conflict with options of WebViews in a shared browser process.

---

## Source 17 — NewWindow property compatibility constraints

**Time**: 2026-09-27, 14:28:37 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2newwindowrequestedeventargs.newwindow?view=webview2-dotnet-1.0.4191.47
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: When routing a popup into an in-app target WebView, the target must belong to the same `CoreWebView2Environment` and profile as the opener, and it cannot already be navigated. This constrains any secondary-view implementation.

# Relevant extracted content

```csharp
public Microsoft.Web.WebView2.Core.CoreWebView2 NewWindow { get; set; }
```

Microsoft also says settings should be changed before setting `NewWindow`, document-created scripts must be added/completed before setting it, and resource-request handlers that affect the new content are added after setting it.

---

## Source 16 — CapturePreview image format enum

**Time**: 2026-09-27, 14:27:05 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/reference/winrt/microsoft_web_webview2_core/corewebview2capturepreviewimageformat?view=webview2-winrt-1.0.4191.47
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: The preview API's format enum explicitly supports `Png` and `Jpeg`; choosing `Png` gives a lossless, easy-to-inspect acceptance artifact.

# Relevant extracted content

```text
Png  = 0x0  // PNG image format
Jpeg = 0x1  // JPEG image format
```

---

## Source 15 — CapturePreviewAsync as acceptance evidence

**Time**: 2026-09-27, 14:26:32 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.capturepreviewasync?view=webview2-dotnet-1.0.4129.50
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: `CapturePreviewAsync` is supported for a built-in visual acceptance artifact: it writes a rendered WebView image to a caller-provided stream and returns a `Task`. It is valid only after the first `ContentLoading` event; calling it during first `NavigationStarting` fails, and calling it before a later page's `ContentLoading` can capture the page being navigated away from.

# Relevant extracted content

```csharp
public System.Threading.Tasks.Task CapturePreviewAsync(
    Microsoft.Web.WebView2.Core.CoreWebView2CapturePreviewImageFormat imageFormat,
    System.IO.Stream imageStream);
```

The output stream receives the image bytes. Microsoft’s format enum supports `Png` and `Jpeg`; PNG is the clearest deterministic acceptance artifact. Schedule capture from/after `ContentLoading` (or a later point after the page is rendered), then await the returned task and close/flush the stream. This proves the visual page rendered to WebView2, but it does not by itself prove WebView2 initialization, navigation policy, host-message handling, persistence, or business-state correctness.

---

## Source 14 — WinForms CoreWebView2CreationProperties

**Time**: 2026-09-27, 14:25:05 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.winforms.corewebview2creationproperties?view=webview2-dotnet-1.0.3856.49
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: WinForms implicit initialization can be configured with `CoreWebView2CreationProperties`, including `UserDataFolder`, `ProfileName`, and `IsInPrivateModeEnabled`. For complete environment/controller control, Microsoft says to create them explicitly and call `EnsureCoreWebView2Async(environment, controllerOptions)` before setting `Source`.

# Relevant extracted content

```csharp
var properties = new CoreWebView2CreationProperties
{
    UserDataFolder = userDataFolder,
    ProfileName = "ThemeStudio",
    IsInPrivateModeEnabled = false
};
webView.CreationProperties = properties;
```

The documented properties also include `BrowserExecutableFolder`, `Language`, and `AdditionalBrowserArguments`. The class is intended for common customization; if complete control is required, use `CoreWebView2Environment.CreateAsync`, optionally `CreateCoreWebView2ControllerOptions()`, and pass them to `EnsureCoreWebView2Async` before assigning the `Source` property.

---

## Source 13 — Multiple profiles under one UDF

**Time**: 2026-09-27, 14:23:56 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/multi-profile-support
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: Profile separation can be achieved inside one shared UDF: each profile gets a dedicated folder for cookies, preferences, and cached resources, allowing data isolation without launching a separate browser process for every WebView. A profile is selected through controller options.

# Relevant extracted content

Microsoft documents `CoreWebView2Environment.CreateCoreWebView2ControllerOptions()` followed by setting `ProfileName` and optionally `IsInPrivateModeEnabled`; a controller created with those options is associated with that profile, and a missing profile is created automatically.

```csharp
CoreWebView2ControllerOptions options =
    environment.CreateCoreWebView2ControllerOptions();
options.ProfileName = "ThemeStudio";
options.IsInPrivateModeEnabled = false;
```

For WinForms, the equivalent profile inputs are available through `CoreWebView2CreationProperties` (`UserDataFolder`, `ProfileName`, and `IsInPrivateModeEnabled`) when using the control's initialization path, or through the two-argument `EnsureCoreWebView2Async` when creating controller options explicitly. The same article exposes `webView.CoreWebView2.Profile` for reading `ProfileName` and `IsInPrivateModeEnabled` after creation. All controls associated with the same profile share that profile's dedicated folder; use separate profile names for independent browser state inside one app-owned UDF.

---

## Source 12 — Manage user data folders / isolation

**Time**: 2026-09-27, 14:22:48 +08:00
**Source**: https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/user-data-folder
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: A WebView2 user data folder (UDF) stores cookies, permissions, caches, and other browser state. For an unpackaged .NET WinForms app, Microsoft documents passing an explicit writable UDF to `CoreWebView2Environment.CreateAsync`; use one app-owned UDF for controls intended to share a session, or separate UDFs when session data must be isolated.

# Relevant extracted content

The page states that each WebView2 session has exactly one UDF and a UDF can have at most one WebView2 session at a time. Controls using the same UDF share the session. On .NET (WPF/WinForms), the default UDF is beside the executable as `<app>.exe.WebView2`; Microsoft recommends a custom UDF in most installed/unpackaged cases so the runtime has write access, for example under `Environment.SpecialFolder.LocalApplicationData`.

```csharp
var userDataFolder = Path.Combine(
    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
    "ThemeStudio", "WebView2");
var environment = await CoreWebView2Environment.CreateAsync(
    null, userDataFolder, new CoreWebView2EnvironmentOptions());
await webView.EnsureCoreWebView2Async(environment);
```

The example is a minimal adaptation of Microsoft’s documented .NET pattern. The UDF should be writable; network drives are discouraged. To retrieve the effective absolute path after creation, use `CoreWebView2Environment.UserDataFolder`. Do not delete a UDF while its session/processes are active; end the session and wait for browser child processes to exit first. Separate UDFs isolate all profile state but consume more memory/disk and may start additional browser processes.

---

## Source 10 — PermissionRequested event

**Time**: 2026-09-27, 14:21:04 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.permissionrequested?view=webview2-dotnet-1.0.4191.47
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: WebView2 surfaces privileged-resource requests through `PermissionRequested`; the host must make the policy decision synchronously or use a deferral. For a local theme editor, an explicit default deny is appropriate unless a narrowly scoped permission is part of the product contract.

# Relevant extracted content

```csharp
public event EventHandler<
    Microsoft.Web.WebView2.Core.CoreWebView2PermissionRequestedEventArgs>
    PermissionRequested;
```

If no deferral is taken, subsequent page scripts are blocked until the handler returns; if a deferral is taken, they remain blocked until the deferral is completed.

---

## Source 11 — PermissionRequested event args

**Time**: 2026-09-27, 14:21:04 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2permissionrequestedeventargs?view=webview2-dotnet-1.0.4022.49
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: The host can decide using origin `Uri`, `PermissionKind`, and `IsUserInitiated`, set `State`, and control whether the result persists with `SavesInProfile`; `GetDeferral()` supports asynchronous user or policy decisions.

# Relevant extracted content

```csharp
public class CoreWebView2PermissionRequestedEventArgs : EventArgs
{
    public bool Handled { get; set; }
    public bool IsUserInitiated { get; }
    public Microsoft.Web.WebView2.Core.CoreWebView2PermissionKind PermissionKind { get; }
    public bool SavesInProfile { get; set; }
    public Microsoft.Web.WebView2.Core.CoreWebView2PermissionState State { get; set; }
    public string Uri { get; }
    public Microsoft.Web.WebView2.Core.CoreWebView2Deferral GetDeferral();
}
```

Microsoft says `SavesInProfile = false` prevents persistence beyond the current request and allows future events for that origin/permission kind. `State` defaults to `Default` and can be set to the desired permission state.

---

## Source 8 — NewWindowRequested event

**Time**: 2026-09-27, 14:19:38 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.newwindowrequested?view=webview2-dotnet-1.0.4191.47
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: A host can intercept `window.open()`/targeted new-window requests. For a single-window desktop shell, handle the event and set `Handled = true`; otherwise, if neither `Handled` nor `NewWindow` is set, WebView2 opens a popup. A target WebView can be supplied when an in-app secondary window is intended.

# Relevant extracted content

```csharp
public event EventHandler<
    Microsoft.Web.WebView2.Core.CoreWebView2NewWindowRequestedEventArgs>
    NewWindowRequested;
```

Microsoft documents that the app may set `Handled` or pass a target `NewWindow`. If neither is set, target content opens in a popup. Without a deferral, scripts causing the request are blocked until the handler returns; with a deferral, they remain blocked until the deferral completes.

---

## Source 9 — NewWindowRequested event args

**Time**: 2026-09-27, 14:19:38 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2newwindowrequestedeventargs?view=webview2-dotnet-1.0.4129.50
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: The event args provide the requested URI and user-gesture state, plus `Handled`, `NewWindow`, name, origin frame info, window features, and `GetDeferral()`. This supports an explicit allowlist and deterministic popup policy.

# Relevant extracted content

```csharp
public class CoreWebView2NewWindowRequestedEventArgs
    : System.ComponentModel.HandledEventArgs
{
    public bool Handled { get; set; }
    public bool IsUserInitiated { get; }
    public string Uri { get; }
    public Microsoft.Web.WebView2.Core.CoreWebView2 NewWindow { get; set; }
    public Microsoft.Web.WebView2.Core.CoreWebView2Deferral GetDeferral();
}
```

The documented properties also include `Name`, `OriginalSourceFrameInfo`, and `WindowFeatures`. `IsUserInitiated` is true for a gesture such as selecting an anchor with `target`; the event can therefore reject non-user initiated popups or only allow the app's own host.

---

## Source 6 — NavigationStarting event and navigation gate

**Time**: 2026-09-27, 14:17:49 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.navigationstarting?view=webview2-dotnet-1.0.4129.50
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: `NavigationStarting` is the synchronous decision point for top-level URI navigation. Redirects also raise it, and the host may cancel/block the navigation before the handler returns, making it suitable for an allowlist of the app's virtual host and approved schemes.

# Relevant extracted content

```csharp
public event EventHandler<
    Microsoft.Web.WebView2.Core.CoreWebView2NavigationStartingEventArgs>
    NavigationStarting;
```

Microsoft states that redirects raise this event with the same navigation ID and that corresponding navigations may be blocked until all handlers return. The handler should inspect `CoreWebView2NavigationStartingEventArgs.Uri` and set its `Cancel` property for disallowed destinations.

---

## Source 7 — NavigationStarting event args

**Time**: 2026-09-27, 14:17:49 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2navigationstartingeventargs?view=webview2-dotnet-1.0.4129.50
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: The event args expose `Uri`, `Cancel`, `IsRedirected`, `IsUserInitiated`, `NavigationId`, `NavigationKind`, and request headers. `Cancel` is inherited from `CancelEventArgs`, so a C# 5 handler can set `e.Cancel = true` when the URI fails the host's navigation policy.

# Relevant extracted content

```csharp
public class CoreWebView2NavigationStartingEventArgs
    : System.ComponentModel.CancelEventArgs
{
    public bool Cancel { get; set; }
    public string Uri { get; }
    public bool IsRedirected { get; }
    public bool IsUserInitiated { get; }
    public ulong NavigationId { get; }
    public CoreWebView2NavigationKind NavigationKind { get; }
}
```

The documented properties include `AdditionalAllowedFrameAncestors`, `RequestHeaders`, and the navigation identity fields above. The `Cancel` property determines whether the navigation is cancelled.

---

## Source 5 — PostWebMessageAsJson

**Time**: 2026-09-27, 14:16:31 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.postwebmessageasjson?view=webview2-dotnet-1.0.4191.47
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: The host can asynchronously post JSON to the top-level document through `window.chrome.webview` using `PostWebMessageAsJson`; `IsWebMessageEnabled` must be true. A navigation that wins before the asynchronous post is delivered causes the message not to be sent.

# Relevant extracted content

```csharp
public void PostWebMessageAsJson(string webMessageAsJson);

public void PostWebMessageAsJson(
    string webMessageAsJson,
    System.Collections.Generic.List<object> additionalObjects);
```

The first overload posts to the top-level document; page JavaScript listens with `window.chrome.webview.addEventListener("message", handler)`. The message is sent asynchronously, is not sent if navigation occurs first, and requires `CoreWebView2.Settings.IsWebMessageEnabled == true`. The overload accepting `additionalObjects` can expose DOM/file-system handles; Microsoft warns to check the target/source immediately before posting such objects and notes message order with the additional-object API may not be preserved.

---

## Source 4 — WebMessageReceived

**Time**: 2026-09-27, 14:15:43 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.webmessagereceived?view=webview2-dotnet-1.0.4191.47
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: Host-to-page and page-to-host messaging use the WebView2 message bridge. The host event fires only when `IsWebMessageEnabled` is enabled and the top-level page calls `window.chrome.webview.postMessage`; repeated calls from one page preserve order, but ordering across frames or relative to DOM events is not guaranteed.

# Relevant extracted content

```csharp
public event EventHandler<
    Microsoft.Web.WebView2.Core.CoreWebView2WebMessageReceivedEventArgs>
    WebMessageReceived;
```

The event is raised for `window.chrome.webview.postMessage` and `postMessageWithAdditionalObjects` from the top-level document when `IsWebMessageEnabled` is set. `postMessage(object)` values are converted to JSON. Calls from the same page are ordered; calls from multiple frames are not guaranteed to be ordered, and WebMessageReceived is not sequenced with DOM events such as `NewWindowRequested`.

---

## Source 3 — SetVirtualHostNameToFolderMapping

**Time**: 2026-09-27, 14:14:21 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.setvirtualhostnametofoldermapping?view=webview2-dotnet-1.0.3800.47
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: A local app shell can be served from a virtual HTTP(S) host mapped to a folder. Microsoft recommends a reserved/non-real domain and the minimum cross-origin access, normally `Deny` unless another origin must read the resources; a reload may be required after changing the mapping.

# Relevant extracted content

```csharp
public void SetVirtualHostNameToFolderMapping(
    string hostName,
    string folderPath,
    Microsoft.Web.WebView2.Core.CoreWebView2HostResourceAccessKind accessKind);
```

The mapping applies to top-level and iframe navigations, subresources, and dedicated/shared worker scripts (not service-worker scripts). Both absolute and relative folder paths are accepted; relative paths are relative to the app executable folder. Use distinct host names for folders that should remain isolated. Microsoft says to choose host names never used by real sites, with `.example`, `.test`, and `.invalid` listed as reserved choices, and to avoid `.local` because navigation can be delayed. `ClearVirtualHostNameToFolderMapping(string hostName)` removes a mapping. A new mapping may require page reload because existing resource loaders can already be running.

---

## Source 2 — WinForms WebView2.EnsureCoreWebView2Async

**Time**: 2026-09-27, 14:12:52 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.winforms.webview2.ensurecorewebview2async?view=webview2-dotnet-1.0.3405.78
**Method**: extract (via `web__run` open)
**Confidence**: high
**Insight**: The WinForms control exposes an overload taking a pre-created environment and another taking environment plus controller options. Initialization completes through a `Task`; the control's `CoreWebView2` is usable when that task completes. Initialization must be called on the UI thread and must not switch to a different environment after initialization starts.

# Relevant extracted content

```csharp
public System.Threading.Tasks.Task EnsureCoreWebView2Async(
    Microsoft.Web.WebView2.Core.CoreWebView2Environment environment = null);

public System.Threading.Tasks.Task EnsureCoreWebView2Async(
    Microsoft.Web.WebView2.Core.CoreWebView2Environment environment = null,
    Microsoft.Web.WebView2.Core.CoreWebView2ControllerOptions controllerOptions = null);
```

The task represents background initialization; when it completes, `CoreWebView2` is non-null. The `CoreWebView2InitializationCompleted` event is invoked before the task completes or on exceptions. Calling with a different environment after initialization began raises `ArgumentException`; the method is asynchronous but still must be called from the UI thread. Repeated calls with the same parameter return the same task unless previous initialization failed.

---
