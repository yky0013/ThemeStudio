# Web/documentation checkpoints

Research date: 2026-10-20 (local Windows host)

## Source checkpoint 1 — Microsoft Learn: managed-device Start layout

- URL: https://learn.microsoft.com/en-us/windows/configuration/start/layout
- Retrieved via: Microsoft Learn search result (`turn9search0`)
- Evidence: The page documents a Windows 11 `pinnedList` JSON containing `desktopAppLink` and `packagedAppId` entries. It states that exported desktop-app tiles use `DesktopApplicationLinkPath` in the resulting file.
- Relevance: Confirms the JSON shape that Seelen deserializes and the two item forms observed in the local proof output.
- Limitation: This is the supported layout format/documentation; it does not document the internal COM CLSID or interface found locally.

## Source checkpoint 2 — Microsoft Learn: Windows 11 Start menu customization

- URL: https://learn.microsoft.com/en-us/windows-hardware/customize/desktop/customize-the-windows-11-start-menu
- Retrieved via: Microsoft Learn search result (`turn9search1`)
- Evidence: The documented JSON keys include `packagedAppID`, `desktopAppID`, and `desktopAppLink`; `desktopAppLink` is the shortcut path for an unpackaged Win32 app.
- Relevance: Supports interpreting the exported `pinnedList` entries as Windows 11 Start pin identifiers/links.
- Limitation: This documents OEM/layout customization, not a public runtime export API.

## Source checkpoint 3 — Microsoft Learn: Export-StartLayout cmdlet

- URL: https://learn.microsoft.com/en-us/powershell/module/startlayout/export-startlayout
- Retrieved via: Microsoft Learn search result (`turn9search2`)
- Evidence: The documented syntax is `Export-StartLayout [-Path] <String> [-UseDesktopApplicationID]` or the `-LiteralPath` form. The description says it exports the current user's Start tile layout.
- Relevance: Establishes the behavior Seelen currently relies on and the meaning of omitting `-UseDesktopApplicationID`.
- Limitation: The page documents only the PowerShell cmdlet surface; it does not expose the underlying COM contract.

## Source checkpoint 4 — Microsoft Learn: Windows 11 Start layout export instructions

- URL: https://learn.microsoft.com/windows/configuration/customize-start-menu-layout-windows-11
- Retrieved via: Microsoft Learn search result (`turn9search3`)
- Evidence: The page describes exporting Windows 11 Start layout to a JSON file with `Export-StartLayout -Path ...json`; it also distinguishes XML export behavior and JSON pin lists.
- Relevance: Confirms that the current Windows 11 export is JSON and that the no-`UseDesktopApplicationID` form is the JSON path.
- Limitation: No native API signature or COM identifier is documented.

## Source checkpoint 5 — Microsoft Learn: StartLayout module index

- URL: https://learn.microsoft.com/en-us/powershell/module/startlayout/?view=windowsserver2025-ps
- Retrieved via: Microsoft Learn search result (`turn9search5`)
- Evidence: The StartLayout module lists `Export-StartLayout`, `Export-StartLayoutEdgeAssets`, `Get-StartApps`, and `Import-StartLayout`.
- Relevance: Confirms the installed module's public command inventory.
- Limitation: The module index contains no public native/COM API entry for the export operation.

## Source checkpoint 6 — exact internal COM GUID search

- Query: `"0BAC4102-61E9-48A5-93DD-D295ABA65369"`
- Retrieved via: Microsoft/web search (`turn9search*` exact-GUID query)
- Evidence: No Microsoft Learn or Windows SDK API page surfaced for this GUID. The local managed assembly metadata remains the authoritative evidence for this internal interface shape.
- Relevance: Shows the COM boundary is undocumented/internal rather than a discoverable public SDK contract.

## Source checkpoint 7 — native DLL/export search

- Query: `"StartTileData.dll" "ProcessStartLayoutPolicy"`
- Retrieved via: Microsoft/web search (`turn9search*` DLL/export query)
- Evidence: No Microsoft Learn or Windows SDK page surfaced documenting `StartTileData.dll` or `ProcessStartLayoutPolicy` as a supported public API.
- Relevance: The local PE export table is evidence of an implementation DLL, not proof of a supported API contract.

## Source checkpoint 8 — opened Microsoft Learn cmdlet page

- URL: https://learn.microsoft.com/en-us/powershell/module/startlayout/export-startlayout?view=windowsserver2025-ps
- Retrieved via: opened Microsoft Learn result (`turn17view0`), lines 24-56 and 126-128.
- Evidence: The page gives `Export-StartLayout [-Path] <String> [-UseDesktopApplicationID]`; it states that the cmdlet exports the current user's Start tile layout, and that `-UseDesktopApplicationID` changes the output from the default shortcut-link path to DesktopApplicationID.
- Relevance: Directly supports selecting `ExportStartLayout` (without the `WithDesktopApplicationIDs` variant) for byte-compatible Seelen behavior.
- Limitation: The rendered page also says access requires authorization for some sections; the quoted syntax/description/parameter text was available in the fetched page.

## Source checkpoint 9 — opened Microsoft Learn Start layout format page

- URL: https://learn.microsoft.com/en-us/windows/configuration/start/layout
- Retrieved via: opened Microsoft Learn result (`turn18view0`), lines 82-114 and 142-158, with format details at 427-432.
- Evidence: The page states that the Windows 11 JSON export contains a list of pins (`pinnedList`) and shows `desktopAppLink`, `packagedAppId`, and `secondaryTile` entries. It explicitly gives `Export-StartLayout -Path ...LayoutModification.json` for JSON export and explains that `desktopAppLink` carries a shortcut path.
- Relevance: Directly matches the proof output and Seelen's `StartMenuLayout` enum.
- Limitation: The page continues to prescribe PowerShell as the supported export front end; it does not document the internal COM contract.
