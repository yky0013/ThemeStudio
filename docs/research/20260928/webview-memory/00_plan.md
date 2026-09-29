# WebView2 memory API source verification plan

## Scope

Verify Microsoft’s official .NET WebView2 API behavior for `CoreWebView2.MemoryUsageTargetLevel` / `CoreWebView2MemoryUsageTargetLevel.Low`, `CoreWebView2.TrySuspendAsync()`, and `CoreWebView2.Resume()`. Record signatures, intended memory/CPU effects, visibility requirements, and limits relevant to the local WebView2 SDK `1.0.4191.47`.

## Constraints

- Read-only inspection and web research; do not install packages, modify ThemeStudio source, or change Windows settings.
- Use at most two substantive Microsoft primary source pages.
- Persist a checkpoint immediately after every fetched source in `20_sources.md`.
- Use the local SDK XML only as a version/signature cross-check; derive the final synthesis from persisted checkpoints and explicitly label local evidence.

## Acceptance criteria

1. Give canonical Microsoft URLs and concise API signatures/usage.
2. Distinguish the low-memory target from true suspension and state `IsVisible == false` requirement for `TrySuspendAsync`.
3. State best-effort behavior, possible disk swapping/performance impact, automatic resume behavior, and the recommendation not to mix the two strategies.
