# Native Start pinned-list export — synthesis

## Finding

Windows 11 on this host exposes the same export operation through an internal COM server, without starting PowerShell or loading `System.Management.Automation`:

- COM class CLSID: `{75AB852C-0441-46D4-A205-EF0A33F98255}`
- COM server: `C:\Windows\System32\StartTileData.dll`
- COM interface IID: `{0BAC4102-61E9-48A5-93DD-D295ABA65369}`
- Registry threading model: `Both`

The COM ABI is an `IUnknown` interface with this vtable order and `LPCWSTR` path argument:

```text
HRESULT ExportStartLayout(LPCWSTR pszFilePath);
HRESULT ExportStartLayoutWithDesktopApplicationIDs(LPCWSTR pszFilePath);
HRESULT ValidateLayoutFile(LPCWSTR pszFilePath);
HRESULT ExportEdgeAssets(LPCWSTR pszFilePath);
```

Equivalent C# interop used by the proof:

```csharp
[ComImport]
[Guid("75AB852C-0441-46D4-A205-EF0A33F98255")]
internal class StartLayoutCmdletComClass {}

[ComImport]
[Guid("0BAC4102-61E9-48A5-93DD-D295ABA65369")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IStartLayoutCmdlet
{
    void ExportStartLayout([MarshalAs(UnmanagedType.LPWStr)] string pszFilePath);
    void ExportStartLayoutWithDesktopApplicationIDs([MarshalAs(UnmanagedType.LPWStr)] string pszFilePath);
    void ValidateLayoutFile([MarshalAs(UnmanagedType.LPWStr)] string pszFilePath);
    void ExportEdgeAssets([MarshalAs(UnmanagedType.LPWStr)] string pszFilePath);
}
```

Use `ExportStartLayout` to match Seelen's current `Export-StartLayout -Path ...` call. The `WithDesktopApplicationIDs` method is a different output mode and should not be substituted when preserving Seelen's `desktopAppLink` behavior.

## Proof

`native_start_layout_proof.cs` and `run-prototype.cmd` instantiate the COM class and call `ExportStartLayout` directly. The executable has no reference to the StartLayout managed assembly, PowerShell, or `System.Management.Automation`. It reports no PowerShell/automation modules loaded before or after the call.

The proof generated `proof-output/native-com.json` with 15 `pinnedList` entries. The installed cmdlet generated `proof-output/powershell-reference.json` for comparison. Both files are 1,279 bytes, have SHA-256 `2cf9b68592fc643a3f6722f478ce3fe937e4a7d11738157a86df597e3bbd116a`, are byte-for-byte equal, and have equal parsed `pinnedList` arrays. The detailed comparison is in `proof-output/comparison.txt`.

## Support boundary

Microsoft documents the JSON `pinnedList` format and the `Export-StartLayout` cmdlet, including `desktopAppLink` and `packagedAppId`, in [Customize the Start layout for managed Windows devices](https://learn.microsoft.com/en-us/windows/configuration/start/layout), [Customize the Windows 11 Start menu](https://learn.microsoft.com/en-us/windows-hardware/customize/desktop/customize-the-windows-11-start-menu), and [Export-StartLayout](https://learn.microsoft.com/en-us/powershell/module/startlayout/export-startlayout). The exact CLSID, IID, and `StartTileData.dll` contract did not appear in Microsoft Learn or Windows SDK documentation during this search. Treat this as an internal Windows implementation boundary: it is proven on the current Windows build, but it is not a supported public API and may change across Windows updates.

The local managed assembly is useful for discovery only. Its reference list includes `System.Management.Automation`; directly hosting the cmdlet class would therefore violate the no-PowerShell/no-SMA requirement. The COM declarations in the prototype are copied from the assembly's COM metadata (GUIDs, IUnknown interface, method names/order), while the implementation is loaded by COM registration from the native DLL.

## Handoff

The parent agent can replace the Seelen PowerShell invocation with this COM call in the native/Windows integration layer, preserving the existing JSON deserialization and environment-variable expansion. Keep an explicit fallback or version gate because the COM surface is undocumented and build-dependent. Do not call `ProcessStartLayoutPolicy` directly: the PE export is present, but no reliable public signature was found and it was not needed for the working proof.

## Product patch rationale

The requested Seelen source patch now adds `src/background/utils/start_layout.rs`, exposes it from `utils/mod.rs`, and changes `get_native_start_menu` to call `export_start_layout` before the existing file deserialization and environment-variable expansion. The implementation keeps the verified vtable order, converts the requested output to an absolute UTF-16 path, creates the COM object on a dedicated STA thread, and drops the interface before its RAII `CoUninitialize` guard. The old `utils/pwsh.rs` module was removed after a repository-wide search found no remaining callers.

The parent requested only static validation at this stage because the Rust toolchain is unavailable in the current environment. `cargo check` and `cargo fmt --check` were attempted and could not start because `cargo`/`rustc` are not installed or on `PATH`; the standalone C# COM proof remains the runtime evidence. Rust compilation should be run once the pinned nightly toolchain is restored.

## Final validation on 2026-10-20

The pinned Rust toolchain is now available. The exact product Rust module passed all three runtime proof tests: byte-identical layout, Unicode/space paths, and controlled invalid-destination failure. The complete Seelen release and all 27 frontend apps built successfully. CLI-only launches of the three rebuilt executables exited successfully, with no desktop appearance change; live Dock/toolbar activation was not performed. Personal layout JSON remains local and excluded from version control.
