# Primary documentation checkpoints

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/cfgmgr32/nf-cfgmgr32-cm_disable_devnode
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: high
**Insight**: `CM_Disable_DevNode` is a native Configuration Manager operation for disabling a device instance, with `CM_DISABLE_UI_NOT_OK` and optional persistent disable flags.

# Relevant extracted content

> Syntax: `CONFIGRET CM_Disable_DevNode(DEVINST dnDevInst, ULONG ulFlags)`.
>
> The device instance handle is local-machine bound; success is `CR_SUCCESS`; header/library are `cfgmgr32.h`/`Cfgmgr32.lib`.

---

**Time**: 2026-10-20, 18:02:00 +08:00
**Source**: https://learn.microsoft.com/en-us/powershell/module/netadapter/get-netadapter
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: high
**Insight**: `Get-NetAdapter -Physical` is the compatibility target for the helper's read-only WMI query; the PowerShell docs define `-Physical` as selecting physical adapters and default visibility as excluding hidden adapters.

# Relevant extracted content

> `Get-NetAdapter` supports `-Physical` and `-IncludeHidden`; by default only visible adapters are returned.

---

**Time**: 2026-10-20, 18:02:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/netadaptercimprov/enable-msft-netadapter
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: high
**Insight**: The `MSFT_NetAdapter.Enable` method is exposed by the `Root\\StandardCimv2` provider and returns a `uint32` status code; the helper can invoke it through `System.Management` without a PowerShell host.

# Relevant extracted content

> The method enables a network adapter.
>
> Syntax: `uint32 Enable([out] string CmdletOutput)`; namespace `Root\\StandardCimv2`; provider `NetAdapterCim.dll`; minimum client Windows 8.

---

**Time**: 2026-10-20, 18:02:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/netadaptercimprov/disable-msft-netadapter
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: high
**Insight**: The matching `MSFT_NetAdapter.Disable` method has the same `Root\\StandardCimv2` provider and `uint32` return contract.

# Relevant extracted content

> The method disables a network adapter.
>
> Syntax: `uint32 Disable([out] string CmdletOutput)`; namespace `Root\\StandardCimv2`; provider `NetAdapterCim.dll`; minimum client Windows 8.

---

**Time**: 2026-10-20, 18:02:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/desktop/legacy/hh968170%28v%3Dvs.85%29
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: high
**Insight**: The legacy class reference explicitly identifies `HardwareInterface` and `Hidden` as read-only properties of `MSFT_NetAdapter`, matching the helper's finite WQL filter.

# Relevant extracted content

> `HardwareInterface` indicates that the interface is provided by a hardware device.
>
> `Hidden` indicates that the adapter is hidden and does not appear in a user interface.
>
> The class exposes `Enable` and `Disable` methods in `Root\\StandardCimv2`.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/cfgmgr32/nf-cfgmgr32-cm_enable_devnode
**Method**: browser-rendered (via web__run open, official Microsoft Learn)
**Confidence**: high
**Insight**: `CM_Enable_DevNode` is the matching native operation for enabling a device instance.

# Relevant extracted content

> Syntax: `CONFIGRET CM_Enable_DevNode(DEVINST dnDevInst, ULONG ulFlags)`.
>
> `ulFlags` is reserved and must be zero; success is `CR_SUCCESS`; header/library are `cfgmgr32.h`/`Cfgmgr32.lib`.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupdigetclassdevsw
**Method**: browser-rendered (via web__run open, official Microsoft Learn)
**Confidence**: high
**Insight**: SetupAPI can enumerate present devices in the network adapter setup class, providing the device information set needed for native adapter state changes.

# Relevant extracted content

> `SetupDiGetClassDevsW` returns a local device information set.
>
> Microsoft’s example for present network adapters uses `SetupDiGetClassDevs(&GUID_DEVCLASS_NET, NULL, NULL, DIGCF_PRESENT)`; the returned set must be released with `SetupDiDestroyDeviceInfoList`.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupdienumdeviceinfo
**Method**: browser-rendered (via web__run open, official Microsoft Learn)
**Confidence**: high
**Insight**: `SetupDiEnumDeviceInfo` yields each `SP_DEVINFO_DATA`, whose `DevInst` is the device-instance handle passed to Configuration Manager.

# Relevant extracted content

> Syntax: `BOOL SetupDiEnumDeviceInfo(HDEVINFO DeviceInfoSet, DWORD MemberIndex, PSP_DEVINFO_DATA DeviceInfoData)`.
>
> Initialize `SP_DEVINFO_DATA.cbSize`; increment the member index until `ERROR_NO_MORE_ITEMS`.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupdigetdeviceregistrypropertyw
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: high
**Insight**: `SetupDiGetDeviceRegistryPropertyW` retrieves PnP properties for each enumerated device, useful for filtering to physical network adapters and recording diagnostics.

# Relevant extracted content

> Syntax takes `HDEVINFO`, `SP_DEVINFO_DATA`, a property identifier, output buffer, and required-size pointer.
>
> The property is associated with the `SP_DEVINFO_DATA` element in the device information set.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/cfgmgr32/nf-cfgmgr32-cm_disable_devnode
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: high
**Insight**: A native adapter toggle must report `CONFIGRET` per device and must decide whether a persistent disable is intended; the current PowerShell command is a transient toggle.

# Relevant extracted content

> By default, `CM_Disable_DevNode` disables a device only until reboot; `CM_DISABLE_PERSIST` persists from Windows 10 onward.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/setupapi/ns-setupapi-sp_propchange_params
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: high
**Insight**: SetupAPI’s `DIF_PROPERTYCHANGE` path is an alternative native implementation and explicitly distinguishes global versus profile-specific enable/disable state.

# Relevant extracted content

> `SP_PROPCHANGE_PARAMS` carries `DICS_ENABLE`/`DICS_DISABLE` and `DICS_FLAG_GLOBAL` or `DICS_FLAG_CONFIGSPECIFIC`.
>
> Global scope changes the device state in all hardware profiles; the docs refer to `SetupDiCallClassInstaller` for dispatch.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows-hardware/drivers/install/dif-propertychange
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: high
**Insight**: `DIF_PROPERTYCHANGE` is the installer request for enabling, disabling, restarting, or stopping a device and lets class/co-installers participate.

# Relevant extracted content

> The request notifies the installer that device properties are changing.
>
> It is handled by device co-installers or class installers, and is supported on Windows 2000 and later.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupdicallclassinstaller
**Method**: browser-rendered (via web__run open, official Microsoft Learn)
**Confidence**: high
**Insight**: A `DIF_PROPERTYCHANGE` implementation must call `SetupDiCallClassInstaller` and inspect `DI_NEEDREBOOT`/`DI_NEEDRESTART`; the direct CM route avoids installer restart bookkeeping but still needs per-device result handling.

# Relevant extracted content

> Syntax: `BOOL SetupDiCallClassInstaller(DI_FUNCTION InstallFunction, HDEVINFO DeviceInfoSet, PSP_DEVINFO_DATA DeviceInfoData)`.
>
> For some DIF requests the caller must be an administrator; after success, callers should inspect device-install parameters for restart flags.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/shellapi/ns-shellapi-shellexecuteinfoa
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: high
**Insight**: `SHELLEXECUTEINFO` supports the existing UAC/elevation and wait pattern without a PowerShell host.

# Relevant extracted content

> `SEE_MASK_NOCLOSEPROCESS` requests a process handle in `hProcess`, which the caller must close.
>
> `SEE_MASK_NOASYNC` makes the launch operation synchronous; `lpFile`, `lpParameters`, `lpDirectory`, and `nShow` carry the native executable launch.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/shell/launch
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: high
**Insight**: The `runas` ShellExecute verb is the documented way to launch an application as Administrator while retaining the UAC consent prompt.

# Relevant extracted content

> `runas` launches an application as Administrator; UAC prompts for consent or administrator credentials.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-setnamedsecurityinfow
**Method**: browser-rendered (via web__run open, official Microsoft Learn)
**Confidence**: high
**Insight**: The UWP ownership action can be implemented with `SetNamedSecurityInfoW` in an elevated native helper rather than invoking `takeown` through a PowerShell-created cmd process.

# Relevant extracted content

> `SetNamedSecurityInfoW` sets owner, DACL, and other security information on a named NTFS file or directory.
>
> Setting owner requires `WRITE_OWNER` or `SE_TAKE_OWNERSHIP_NAME`; setting a DACL requires `WRITE_DAC` or ownership. Header/library are `aclapi.h`/`Advapi32.lib`.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-setentriesinaclw
**Method**: browser-rendered (via web__run open, official Microsoft Learn)
**Confidence**: high
**Insight**: `SetEntriesInAclW` merges a read grant for the current user into the existing ACL, matching the `icacls ... /grant ...:(R)` part of the current action.

# Relevant extracted content

> Syntax: `DWORD SetEntriesInAclW(ULONG, PEXPLICIT_ACCESS_W, PACL, PACL*)`.
>
> The function accepts a trustee SID/name, supports `GRANT_ACCESS`, and returns a buffer that must be released with `LocalFree`.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getnamedsecurityinfow
**Method**: browser-rendered (via web__run open, official Microsoft Learn)
**Confidence**: high
**Insight**: The existing owner check already uses `GetNamedSecurityInfoW`; a native ACL update can reuse the same descriptor retrieval and then merge a new DACL.

# Relevant extracted content

> `GetNamedSecurityInfoW` returns the owner/DACL and a descriptor buffer that must be freed with `LocalFree`.
>
> Reading owner/DACL requires `READ_CONTROL` or ownership.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/enable-method-in-class-win32-networkadapter
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: high
**Insight**: WMI’s `Win32_NetworkAdapter.Enable` is documented as a management alternative but explicitly warns that administrator access may be required; it is not a preferred no-PowerShell native path for the mod.

# Relevant extracted content

> The method enables a network adapter and returns zero for success.
>
> Microsoft notes that callers without administrator privileges may have difficulty using it.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/windns/
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: medium
**Insight**: The current search of the official `windns.h` index did not expose a public `DnsFlushResolverCache` entry. The reset recommendation should therefore retain `ipconfig /flushdns` as a separate documented command-line dependency or explicitly verify an SDK/runtime export before using that API.

# Relevant extracted content

> The official header index lists DNS query and configuration APIs but did not list `DnsFlushResolverCache`.

---

**Time**: 2026-10-20, 17:18:00 +08:00
**Source**: https://learn.microsoft.com/en-us/windows/win32/network-interfaces
**Method**: query-search (via web__run, official Microsoft Learn)
**Confidence**: high
**Insight**: Network interfaces include both physical PnP-backed and software-only forms; the native enumeration must preserve the current `-Physical` intent instead of disabling every interface indiscriminately.

# Relevant extracted content

> The docs distinguish physical NICs from software-only interfaces such as loopback, teams, and other provider-backed interfaces.

---
