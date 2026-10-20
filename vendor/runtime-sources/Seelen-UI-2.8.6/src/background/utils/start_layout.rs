use std::{
    ffi::c_void,
    os::windows::ffi::OsStrExt,
    path::{Path, PathBuf},
    thread,
};

use windows::{
    Win32::{
        Foundation::RPC_E_CHANGED_MODE,
        System::Com::{
            CLSCTX_INPROC_SERVER, COINIT_APARTMENTTHREADED, CoCreateInstance, CoInitializeEx,
            CoUninitialize,
        },
    },
    core::{GUID, HRESULT, Interface, PCWSTR},
};

use crate::error::Result;

/// The StartLayout PowerShell cmdlet is a thin wrapper around this internal COM class.
///
/// The contract is not part of the public Windows SDK. It is retained here because the
/// installed `Microsoft.Windows.StartLayout.Commands` assembly describes the interface and
/// the registered CLSID resolves to `StartTileData.dll` on supported Windows 11 builds.
#[allow(non_upper_case_globals)]
const CLSID_StartLayoutCmdlet: GUID = GUID::from_u128(0x75ab852c_0441_46d4_a205_ef0a33f98255);

windows_core::imp::define_interface!(
    IStartLayoutCmdlet,
    IStartLayoutCmdlet_Vtbl,
    0x0bac4102_61e9_48a5_93dd_d295aba65369
);

windows_core::imp::interface_hierarchy!(IStartLayoutCmdlet, windows_core::IUnknown);

#[allow(non_snake_case)]
impl IStartLayoutCmdlet {
    /// Export the current user's Windows 11 Start pinned list in the default JSON form.
    ///
    /// This is the vtable slot used by `Export-StartLayout -Path ...`; the following slots
    /// intentionally remain in the same order as the installed managed interface.
    pub unsafe fn ExportStartLayout(&self, pszFilePath: PCWSTR) -> windows::core::Result<()> {
        unsafe {
            (Interface::vtable(self).ExportStartLayout)(Interface::as_raw(self), pszFilePath).ok()
        }
    }

    #[allow(dead_code)]
    pub unsafe fn ExportStartLayoutWithDesktopApplicationIDs(
        &self,
        pszFilePath: PCWSTR,
    ) -> windows::core::Result<()> {
        unsafe {
            (Interface::vtable(self).ExportStartLayoutWithDesktopApplicationIDs)(
                Interface::as_raw(self),
                pszFilePath,
            )
            .ok()
        }
    }

    #[allow(dead_code)]
    pub unsafe fn ValidateLayoutFile(&self, pszFilePath: PCWSTR) -> windows::core::Result<()> {
        unsafe {
            (Interface::vtable(self).ValidateLayoutFile)(Interface::as_raw(self), pszFilePath).ok()
        }
    }

    #[allow(dead_code)]
    pub unsafe fn ExportEdgeAssets(&self, pszFilePath: PCWSTR) -> windows::core::Result<()> {
        unsafe {
            (Interface::vtable(self).ExportEdgeAssets)(Interface::as_raw(self), pszFilePath).ok()
        }
    }
}

#[repr(C)]
#[doc(hidden)]
#[allow(non_snake_case, non_camel_case_types)]
pub struct IStartLayoutCmdlet_Vtbl {
    pub base__: ::windows::core::IUnknown_Vtbl,
    pub ExportStartLayout:
        unsafe extern "system" fn(this: *mut c_void, pszFilePath: PCWSTR) -> HRESULT,
    pub ExportStartLayoutWithDesktopApplicationIDs:
        unsafe extern "system" fn(this: *mut c_void, pszFilePath: PCWSTR) -> HRESULT,
    pub ValidateLayoutFile:
        unsafe extern "system" fn(this: *mut c_void, pszFilePath: PCWSTR) -> HRESULT,
    pub ExportEdgeAssets:
        unsafe extern "system" fn(this: *mut c_void, pszFilePath: PCWSTR) -> HRESULT,
}

struct ComApartment {
    initialized: bool,
}

impl ComApartment {
    fn initialize() -> Result<Self> {
        let result = unsafe { CoInitializeEx(None, COINIT_APARTMENTTHREADED) };
        if result == RPC_E_CHANGED_MODE {
            return Err(
                "Start layout export requires a dedicated single-threaded COM apartment".into(),
            );
        }
        result.ok()?;
        Ok(Self { initialized: true })
    }
}

impl Drop for ComApartment {
    fn drop(&mut self) {
        if self.initialized {
            unsafe { CoUninitialize() };
        }
    }
}

fn absolute_output_path(path: &Path) -> Result<PathBuf> {
    Ok(std::path::absolute(path)?)
}

fn export_on_sta(output_path: PathBuf) -> Result<()> {
    let _apartment = ComApartment::initialize()?;
    let mut wide_path: Vec<u16> = output_path.as_os_str().encode_wide().collect();
    wide_path.push(0);

    let start_layout: IStartLayoutCmdlet =
        unsafe { CoCreateInstance(&CLSID_StartLayoutCmdlet, None, CLSCTX_INPROC_SERVER)? };
    unsafe { start_layout.ExportStartLayout(PCWSTR(wide_path.as_ptr()))? };
    Ok(())
}

/// Export the current user's Windows 11 Start pinned list without starting PowerShell.
///
/// The COM object is created and released on a short-lived dedicated STA thread. Joining the
/// thread guarantees that the interface pointer is released before this function returns and
/// that `CoUninitialize` runs after the COM object has been dropped.
pub fn export_start_layout(path: &Path) -> Result<()> {
    let output_path = absolute_output_path(path)?;
    let thread = thread::Builder::new()
        .name("SLU - native-start-layout".to_string())
        .spawn(move || export_on_sta(output_path))?;

    match thread.join() {
        Ok(result) => result,
        Err(_) => Err("Native Start layout export thread panicked".into()),
    }
}
