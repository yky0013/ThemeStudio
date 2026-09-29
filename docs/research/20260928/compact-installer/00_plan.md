# Plan: compact installer prerequisites and launch

## Scope

Verify, from at most two primary official sources, the WebView2 Evergreen Bootstrapper/Standalone deployment commands and network assumptions, plus the Inno Setup `[Run]` behavior relevant to a required-admin application launched after installation.

## Fixed inputs

- Bootstrapper file: `MicrosoftEdgeWebview2Setup.exe`.
- Reported app behavior: the existing main EXE has a `requireAdministrator` manifest; an Inno post-install launch using the original-user path produced `CreateProcess failed 740`.
- The parent agent is rebuilding a smaller installer while preserving app functionality.

## Boundaries

- No installs, app edits, or package builds in this subtask.
- Use no more than two official sources: Microsoft Learn WebView2 deployment documentation and Inno Setup help.
- Treat the Inno recommendation as conditional on the actual `[Run]` entry and existing flags.
- Persist a source checkpoint immediately after each search/page fetch.

## Deliverable

Produce `90_synthesis.md` with exact URLs, commands, network/offline distinction, a signature-verification recommendation, and the smallest conditional Inno launch adjustment.

