# Source checkpoints

**Time**: 2026-09-28, 21:38:49 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.memoryusagetargetlevel?view=webview2-dotnet-1.0.4191.47
**Method**: browser-rendered (via `functions.exec` → `web__run.open`)
**Confidence**: high
**Insight**: The Microsoft Learn API page for the local SDK version documents the settable `CoreWebView2.MemoryUsageTargetLevel` property and the `Low`/`Normal` strategy. `Low` is a best-effort target that lets scripts and network connections continue; it may swap browser-process memory to disk and affect performance, and the app must restore `Normal` when active. Microsoft recommends choosing either this target-level pair or `TrySuspendAsync()` + `Resume()`, rather than mixing them.

# Relevant extracted content

The page lists the version and C# signature:

> Package: `Microsoft.Web.WebView2 v1.0.4191.47`
>
> `public Microsoft.Web.WebView2.Core.CoreWebView2MemoryUsageTargetLevel MemoryUsageTargetLevel { get; set; }`

The page says:

> “An app may set MemoryUsageTargetLevel to indicate desired memory consumption level of WebView. Scripts will not be impacted and continue to run.”

It states that `Low` is for an inactive app, that setting it does not require `CoreWebView2Controller.IsVisible = false`, and that the operation is best effort and returns before completion. It may cause some browser-process memory to be swapped to disk; a later script can incur performance impact. Returning to `Normal` is not automatic.

The page explicitly recommends selecting either `TrySuspendAsync()` + `Resume()` or `MemoryUsageTargetLevel = Low` + `Normal`, and says mixing them is not advisable. It also states that `TrySuspendAsync()` changes the target to `Low`, while `Resume()` on a suspended WebView changes it back to `Normal`.

Relevant fetched lines: 314, 322–341.

---

**Time**: 2026-09-28, 21:39:38 +08:00
**Source**: https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.trysuspendasync?view=webview2-dotnet-1.0.4191.47
**Method**: browser-rendered (via `functions.exec` → `web__run.open`)
**Confidence**: high
**Insight**: Microsoft documents `TrySuspendAsync()` as `Task<bool>` and requires the WebView controller’s `IsVisible` property to be false; otherwise it throws `COMException` with `HRESULT_FROM_WIN32(ERROR_INVALID_STATE)`. Suspension pauses script timers and animations, minimizes renderer CPU, and makes renderer memory reusable, but is best effort and can return `false` when browser conditions prevent suspension. The WebView auto-resumes when visible; `Resume()` can be called explicitly for an invisible WebView.

# Relevant extracted content

The page lists the package version and C# signature:

> Package: `Microsoft.Web.WebView2 v1.0.4191.47`
>
> `public System.Threading.Tasks.Task<bool> TrySuspendAsync();`

The page’s example awaits the task and checks the Boolean result. Its remarks state:

> “The IsVisible property must be false when the API is called. Otherwise, the API throws COMException with error code of HRESULT_FROM_WIN32(ERROR_INVALID_STATE).”

It further states that suspension pauses WebView script timers and animations, minimizes CPU usage for the associated browser renderer, and allows the operating system to reuse renderer memory. The request is best effort; a running script can finish first, and the async result is `false` when conditions prevent suspension. The WebView resumes automatically when visible, while the app may call `Resume()` and then `TrySuspendAsync()` periodically for an invisible WebView. Some APIs such as `Navigate` can auto-resume it, so `IsSuspended` should be checked when avoiding unexpected resume.

Relevant fetched lines: 370, 409–439.

---
