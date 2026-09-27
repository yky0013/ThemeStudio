# Third-party components

## Cursor Palette

`cursor_adapter.py` adapts the cursor roles/aliases, preset manifest reader and
current-user registry protocol from [DoomSalat/Cursor-Palette](https://github.com/DoomSalat/Cursor-Palette)
(local fork: `../Cursor-Palette/`, upstream release v2.3.6 / source version 2.3.5).

Copyright (c) 2026 Capitan Salat. MIT license; full notice in
`licenses/Cursor-Palette.txt` and included in the executable bundle and distribution.
The existing Cursor Palette data is read-only in this application. New resources,
presets and durable recovery records use the workbench data directory.

The shared-handle ownership and reload flags were checked against Microsoft Learn:
[DestroyCursor](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-destroycursor),
[LoadImageW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-loadimagew),
[SystemParametersInfoW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-systemparametersinfow).

## Lively Wallpaper

Lively v2.2.1.0 remains a separately installed, unmodified wallpaper engine. This
application invokes its automation CLI and reads local metadata; the Lively
binary/source is not linked into ThemeWorkbench.exe. Its original license and
source remain under `../wallpaper-workbench/` and `../Lively-Wallpaper/`.

## Image converter

The existing local `../image-to-ico/converter.py` module is bundled unchanged via
PyInstaller's module search path, rather than opening the separate converter UI.
Pillow, pywin32 and Python/PyInstaller components retain their respective upstream
licenses in the packaging environment.
