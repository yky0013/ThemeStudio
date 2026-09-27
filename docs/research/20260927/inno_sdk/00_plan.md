# Inno Setup 6.7.3 compiler payload research

**Scope**: Find and verify an official, immutable Inno Setup 6.7.3 compiler source for ThemeStudio-dev. Download only into this folder, extract a portable payload containing `ISCC.exe`, its required files, and language data, and record provenance and hashes. Do not install software, touch the registry, compile the application, or write outside this research folder.

**Consumer expectation**: `ThemeStudio-dev/tools/build-installer.ps1` invokes `.tools/inno-6.7.3/ISCC.exe`.

**Acceptance checks**:

- Official source URL and exact version 6.7.3 are documented.
- Downloaded artifact has a recorded SHA-256 and, where available, official signature evidence.
- Portable extraction contains `ISCC.exe`, required runtime files, and language files; no Windows installation is performed.
- `ISCC.exe /?` or equivalent version/help output is captured as evidence.
- A final synthesis points to all local evidence files and states any limitations.

**Source policy**: Prefer the official Inno Setup website and JRSoftware-hosted files. Treat mirrors or search snippets as discovery hints only unless the official source confirms them.

