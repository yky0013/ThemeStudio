# Local SDK cross-check

**Time**: 2026-09-28, 21:40:10 +08:00
**Source**: `E:\desktop\windows\ThemeStudio\.cache\webview2\lib\net462\Microsoft.Web.WebView2.Core.dll` and `Microsoft.Web.WebView2.Core.xml`
**Method**: read-only local XML inspection plus .NET reflection; package cache identifies WebView2 `1.0.4191.47`
**Confidence**: high for the local binary’s public metadata

The local `net462` WebView2 assembly exposes:

```text
CoreWebView2.MemoryUsageTargetLevel : CoreWebView2MemoryUsageTargetLevel { get; set; }
CoreWebView2.TrySuspendAsync()      : Task<bool>
CoreWebView2.Resume()               : void
```

The bundled XML remarks match the Microsoft Learn pages: `Low` is best effort; `TrySuspendAsync` requires `CoreWebView2Controller.IsVisible == false`; `Resume` may be called while invisible; visibility automatically resumes a suspended WebView; and mixing the target-level and suspend/resume strategies is discouraged.

This is a local compatibility cross-check, not an additional web source.
