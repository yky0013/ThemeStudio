# 0.4.0 source sync and workspace cleanup

The user requested pushing the complete current local source to the existing GitHub repository, then clearing `E:\desktop\windows` so only the latest installer remains.

This snapshot includes the 0.3.0 templates and memory/package improvements, 0.3.1 motion wallpaper and desktop modes, and 0.4.0 portable theme packs and application updates. It retains the upstream source trees, licenses, original/generated assets, dependency locks, build tools, tests, and verification reports. The example package is `examples/ThemeStudio-example.tspack`; the native 0.4.0 evidence is under `docs/development/verification-0.4.0`.

Retained local deliverable: `E:\desktop\windows\ThemeStudio-0.4.0-Windows-x64-Setup.exe`.

- Size: 167337062 bytes.
- SHA-256: `d40e3a281930cea430ece9d81b58328f2dc6fd7b34ae9320ed1f48ef539a2c32`.
- Checksum file in the repository: `docs/releases/ThemeStudio-0.4.0-Windows-x64-Setup.exe.sha256`.
- Existing validation: TypeScript check, 21 frontend tests, 61 backend tests, native preview, real installer staging and metadata checks. Actual in-place upgrade was not performed.
- The installer has not been published to GitHub Releases. Pushing source does not change the repository's visibility or make the anonymous update feed available.

Workspace cleanup is gated on a successful source push and matching remote commit. Build caches, local dependencies, extracted runtimes and superseded deliverables can then be removed. User application data outside the workspace is outside this cleanup.

Unrelated mouse/Office maintenance records from the parent workspace are preserved in a verified local archive under the user's `Documents/ThemeStudio-Archives`, without uploading personal system snapshots to the source repository. A local cleanup receipt records the actual resulting commit and retained installer hash.
