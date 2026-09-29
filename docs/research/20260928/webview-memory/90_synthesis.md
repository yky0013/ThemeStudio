# WebView2 memory API synthesis

## Verified API surface

The local WebView2 cache is `1.0.4191.47`. Microsoft Learn lists these relevant APIs for that package:

```csharp
public CoreWebView2MemoryUsageTargetLevel MemoryUsageTargetLevel { get; set; }
public Task<bool> TrySuspendAsync();
public void Resume();
```

The first two signatures are shown directly on the fetched Microsoft Learn pages. The local `Microsoft.Web.WebView2.Core.dll` metadata/reflection cross-check confirms the parameterless `void Resume()` signature. In a WinForms app, use the initialized `WebView2.CoreWebView2` object and its controller state.

## Two distinct strategies

Use the target-level strategy when an inactive WebView must keep scripts or network connections alive:

```csharp
core.MemoryUsageTargetLevel = CoreWebView2MemoryUsageTargetLevel.Low;
// when active again
core.MemoryUsageTargetLevel = CoreWebView2MemoryUsageTargetLevel.Normal;
```

`Low` is a desired memory target, not a hard cap or a full suspension. Microsoft says scripts continue to run, `IsVisible` does not need to be false, and the operation is best effort; the setter returns before the change necessarily completes. Some browser-process memory may be swapped to disk, so later script execution can be slower. The app must restore `Normal` itself when active again.

Use the suspend/resume strategy when the WebView is genuinely hidden and pausing page activity is acceptable:

```csharp
controller.IsVisible = false;
bool suspended = await core.TrySuspendAsync();
if (!suspended)
{
    // Browser conditions prevented suspension; keep the WebView usable.
}

// Later, while still invisible, resume explicitly when fresh page activity is needed.
core.Resume();
```

`TrySuspendAsync()` requires `controller.IsVisible == false`; otherwise Microsoft documents a `COMException` with `HRESULT_FROM_WIN32(ERROR_INVALID_STATE)`. On success it pauses script timers and animations, reduces renderer CPU use, and lets Windows reuse renderer memory. It is best effort: a running script can finish first, and the returned `Task<bool>` can be `false` when browser conditions prevent suspension. A suspended WebView resumes automatically when it becomes visible, so an explicit `Resume()` is usually unnecessary at that point. APIs such as `Navigate` can also auto-resume it; check `IsSuspended` when avoiding unexpected resume.

## Implementation decision and limits

Choose one complete pair for a given lifecycle: either `Low` → `Normal`, or `TrySuspendAsync()` → `Resume()`. Microsoft explicitly advises against mixing these strategies. `TrySuspendAsync()` is the stronger CPU/activity reduction and has the invisibility precondition; `Low` is the less disruptive memory hint for an inactive WebView that must continue running scripts or maintaining connections.

These APIs are best effort and do not promise a fixed memory saving. They also do not replace disposal or lifecycle cleanup for a WebView that is permanently closed. The source verification does not measure ThemeStudio’s actual browser processes or prove the application’s existing lifecycle calls.

## Official sources

- [CoreWebView2.MemoryUsageTargetLevel Property](https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.memoryusagetargetlevel?view=webview2-dotnet-1.0.4191.47) — property signature, `Low`/`Normal` behavior, swapping/performance limits, automatic target changes, and no-mixing guidance.
- [CoreWebView2.TrySuspendAsync Method](https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.trysuspendasync?view=webview2-dotnet-1.0.4191.47) — `Task<bool>` signature, invisibility requirement, suspension effects, best-effort/false result, automatic resume, and auto-resume caveats.
