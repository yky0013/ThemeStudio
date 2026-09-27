//! Native Win32 file dialogs. The host owns the archive file I/O of user-data
//! export/import, so export opens a Save picker for the archive it writes and
//! inspect/import an Open picker for the archive it reads; and a `filePath` or
//! `folderPath` mod setting needs a filesystem path, which a file input inside the
//! webview never yields, so its Browse button opens an Open picker here too. All run inside the
//! `wh_ipc` worker: each enters a single-threaded COM apartment, shows an
//! `IFileDialog` parented to the main window, and reports the chosen path, a user
//! cancel, or a shell failure.

use std::ffi::{OsStr, OsString, c_void};
use std::path::{Path, PathBuf};
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

use windows::Win32::Foundation::HWND;
use windows::Win32::System::Com::{
    CLSCTX_INPROC_SERVER, COINIT_APARTMENTTHREADED, COINIT_DISABLE_OLE1DDE, CoCreateInstance,
    CoInitializeEx, CoTaskMemFree, CoUninitialize,
};
use windows::Win32::UI::Shell::Common::COMDLG_FILTERSPEC;
use windows::Win32::UI::Shell::{
    FILEOPENDIALOGOPTIONS, FOS_FILEMUSTEXIST, FOS_FORCEFILESYSTEM, FOS_PATHMUSTEXIST,
    FOS_PICKFOLDERS, FileOpenDialog, FileSaveDialog, IFileDialog, IFileOpenDialog, IFileSaveDialog,
    IShellItem, SHCreateItemFromParsingName, SIGDN_FILESYSPATH,
};
use windows::Win32::UI::WindowsAndMessaging::FindWindowW;
use windows::core::{HRESULT, HSTRING, PCWSTR, PWSTR, w};

use crate::lifecycle::window::MAIN_WINDOW_CLASS;

/// `HRESULT_FROM_WIN32(ERROR_CANCELLED)`: the `IFileDialog::Show` result when the
/// user dismisses the picker - a benign no-op, told apart from a real failure.
const ERROR_CANCELLED_HRESULT: HRESULT = HRESULT(0x8007_04C7u32 as i32);

/// `RPC_E_CHANGED_MODE`: `CoInitializeEx` rejecting STA because the thread is already
/// an MTA. The dialog still works, so we proceed - just without owning the uninit.
const RPC_E_CHANGED_MODE: HRESULT = HRESULT(0x8001_0106u32 as i32);

/// How long the picker waits for [`start_point`] before opening without one.
/// Testing whether a path exists is the first touch of its volume: a reachable
/// share answers in milliseconds, but an unreachable one blocks for the SMB
/// connect timeout (about 40 s measured), and the picker must not stall behind
/// that on a Browse click.
const START_POINT_PROBE_TIMEOUT: Duration = Duration::from_secs(2);

/// What a setting's Browse picker selects: an existing file (`filePath`) or an
/// existing folder (`folderPath`).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PickTarget {
    File,
    Folder,
}

/// The outcome of showing a file dialog.
pub enum DialogOutcome {
    /// The user chose a path.
    Picked(PathBuf),
    /// The user dismissed the dialog (a benign no-op, not an error).
    Canceled,
    /// The dialog could not be shown (a COM/shell failure), with a diagnostic.
    Failed(String),
}

/// The native file dialogs the handlers reach through
/// [`BridgeCtx`](crate::ipc::bridge::BridgeCtx). Injected as a trait so the handlers
/// are headless-testable (a fake returns a canned path or a cancel); the production
/// [`Win32FileDialog`] shows the real pickers. `Send + Sync` so the context that holds
/// it can cross to the `wh_ipc` worker thread.
pub trait FileDialog: Send + Sync {
    /// Show a Save picker for the exported archive, seeded with `default_name`.
    fn save_archive(&self, default_name: &str) -> DialogOutcome;
    /// Show an Open picker for an archive to inspect/import.
    fn open_archive(&self) -> DialogOutcome;
    /// Show an Open picker for any existing file (no type filter) or, for
    /// [`PickTarget::Folder`], an existing folder. `initial` is the setting's
    /// current value: a folder picker starts in it when it is a folder that
    /// exists; otherwise (and for a file picker) the picker starts in its parent
    /// with its name filled in when that parent exists, and wherever the shell
    /// defaults to when nothing exists.
    fn pick_file(&self, target: PickTarget, initial: Option<&Path>) -> DialogOutcome;
}

/// The production dialogs: the native Win32 `IFileSaveDialog` / `IFileOpenDialog`.
pub struct Win32FileDialog;

impl FileDialog for Win32FileDialog {
    fn save_archive(&self, default_name: &str) -> DialogOutcome {
        save_dialog(default_name)
    }
    fn open_archive(&self) -> DialogOutcome {
        open_dialog()
    }
    fn pick_file(&self, target: PickTarget, initial: Option<&Path>) -> DialogOutcome {
        pick_file_dialog(target, initial)
    }
}

/// Show a Save picker for the exported archive, seeded with `default_name`.
fn save_dialog(default_name: &str) -> DialogOutcome {
    let Some(_com) = ComApartment::enter() else {
        return DialogOutcome::Failed("COM initialization failed".to_owned());
    };
    // SAFETY: the standard IFileSaveDialog sequence; the dialog and shell item are
    // released on drop, and the display-name PWSTR is freed by `result_path`.
    unsafe {
        let dialog: IFileSaveDialog =
            match CoCreateInstance(&FileSaveDialog, None, CLSCTX_INPROC_SERVER) {
                Ok(dialog) => dialog,
                Err(e) => return DialogOutcome::Failed(format!("CoCreateInstance: {e}")),
            };
        add_options(&dialog, FILEOPENDIALOGOPTIONS(0));
        let filters = json_filters();
        let _ = dialog.SetFileTypes(&filters);
        let _ = dialog.SetDefaultExtension(w!("json"));
        let _ = dialog.SetFileName(&HSTRING::from(default_name));
        shown(dialog.Show(main_window_owner()), || dialog.GetResult())
    }
}

/// Show an Open picker for an archive to inspect/import.
fn open_dialog() -> DialogOutcome {
    let Some(_com) = ComApartment::enter() else {
        return DialogOutcome::Failed("COM initialization failed".to_owned());
    };
    // SAFETY: the standard IFileOpenDialog sequence; see `save_archive`.
    unsafe {
        let dialog: IFileOpenDialog =
            match CoCreateInstance(&FileOpenDialog, None, CLSCTX_INPROC_SERVER) {
                Ok(dialog) => dialog,
                Err(e) => return DialogOutcome::Failed(format!("CoCreateInstance: {e}")),
            };
        add_options(&dialog, FILEOPENDIALOGOPTIONS(0));
        let filters = json_filters();
        let _ = dialog.SetFileTypes(&filters);
        shown(dialog.Show(main_window_owner()), || dialog.GetResult())
    }
}

/// Show an Open picker for any existing file or folder, started at `initial` where
/// it (or its parent) exists and says so in time (see [`FileDialog::pick_file`]
/// and [`probe_start_point`]).
fn pick_file_dialog(target: PickTarget, initial: Option<&Path>) -> DialogOutcome {
    let Some(_com) = ComApartment::enter() else {
        return DialogOutcome::Failed("COM initialization failed".to_owned());
    };
    // SAFETY: the standard IFileOpenDialog sequence; see `save_archive`.
    unsafe {
        let dialog: IFileOpenDialog =
            match CoCreateInstance(&FileOpenDialog, None, CLSCTX_INPROC_SERVER) {
                Ok(dialog) => dialog,
                Err(e) => return DialogOutcome::Failed(format!("CoCreateInstance: {e}")),
            };
        // No `SetFileTypes`: the setting says nothing about the file's type, so the
        // picker lists everything. The picked file or folder must exist - the value
        // is a path the mod opens.
        add_options(
            &dialog,
            match target {
                PickTarget::File => FOS_FILEMUSTEXIST,
                PickTarget::Folder => FOS_PICKFOLDERS | FOS_PATHMUSTEXIST,
            },
        );
        if let Some((folder, name)) = initial.and_then(|path| probe_start_point(target, path)) {
            // `SetFolder` rather than `SetDefaultFolder`: the current value wins over
            // the folder the shell remembers from the last pick, since it is the path
            // the user is replacing.
            if let Ok(item) = SHCreateItemFromParsingName::<_, _, IShellItem>(
                &HSTRING::from(folder.as_os_str()),
                None,
            ) {
                let _ = dialog.SetFolder(&item);
            }
            if let Some(name) = name {
                let _ = dialog.SetFileName(&HSTRING::from(name.as_os_str()));
            }
        }
        shown(dialog.Show(main_window_owner()), || dialog.GetResult())
    }
}

/// Add `extra` to the dialog's options, and with them `FOS_FORCEFILESYSTEM`: the
/// result is resolved to a filesystem path (`result_path`), which a virtual
/// location - "This PC", "Network", a phone over MTP - does not have, so the
/// shell refuses such a pick itself (the dialog stays open) rather than hand
/// back an item that cannot be resolved.
///
/// # Safety
/// Calls COM methods on `dialog`; safe when it is a live dialog.
unsafe fn add_options(dialog: &IFileDialog, extra: FILEOPENDIALOGOPTIONS) {
    // SAFETY: `dialog` is the live interface this function's contract requires.
    unsafe {
        if let Ok(options) = dialog.GetOptions() {
            let _ = dialog.SetOptions(options | FOS_FORCEFILESYSTEM | extra);
        }
    }
}

/// Where the picker starts for a setting's current value: the folder to open in
/// and the name to fill in. A folder picker opens in the value itself when that is
/// an existing folder; otherwise, for either target, its parent with its name
/// filled in when that parent exists; `None` when neither exists (a value typed by
/// hand, or from another machine), so the picker opens where the shell defaults to.
fn start_point(target: PickTarget, path: &Path) -> Option<(&Path, Option<&OsStr>)> {
    if target == PickTarget::Folder && path.is_dir() {
        return Some((path, None));
    }
    let folder = path.parent().filter(|folder| folder.is_dir())?;
    Some((folder, Some(path.file_name()?)))
}

/// [`start_point`] evaluated on a helper thread and waited for at most
/// [`START_POINT_PROBE_TIMEOUT`]; `None` on timeout, so the picker opens where the
/// shell defaults to, as it does for a value that does not exist. The helper is
/// left to finish on its own: it is blocked in a kernel call with nothing to
/// cancel, and its late answer goes to a dropped receiver.
fn probe_start_point(target: PickTarget, path: &Path) -> Option<(PathBuf, Option<OsString>)> {
    let (tx, rx) = mpsc::channel();
    let path = path.to_path_buf();
    thread::Builder::new()
        .name("wh_dialog_probe".to_owned())
        .spawn(move || {
            let point = start_point(target, &path)
                .map(|(folder, name)| (folder.to_path_buf(), name.map(OsStr::to_os_string)));
            let _ = tx.send(point);
        })
        .ok()?;
    rx.recv_timeout(START_POINT_PROBE_TIMEOUT).ok().flatten()
}

/// Map a dialog `Show` result to the outcome: a cancel HRESULT is [`DialogOutcome::Canceled`],
/// any other error is [`DialogOutcome::Failed`], and success resolves the result item to a
/// filesystem path.
///
/// # Safety
/// `get_result` must call `IFileDialog::GetResult` on the dialog that produced
/// `show`, and is invoked only after a successful `Show`.
unsafe fn shown(
    show: windows::core::Result<()>,
    get_result: impl FnOnce() -> windows::core::Result<IShellItem>,
) -> DialogOutcome {
    match show {
        // SAFETY: `Show` answered Ok, so calling `get_result` is what this
        // function's contract permits, and the item it returns is the live one
        // `result_path` requires.
        Ok(()) => unsafe { result_path(get_result()) },
        Err(e) if e.code() == ERROR_CANCELLED_HRESULT => DialogOutcome::Canceled,
        Err(e) => DialogOutcome::Failed(format!("Show: {e}")),
    }
}

/// Resolve a chosen `IShellItem` to its filesystem path, freeing the display-name
/// buffer the shell allocates.
///
/// # Safety
/// Calls COM methods on `item` and reads/frees the returned `PWSTR`; safe when
/// `item` is a live shell item from a successful `GetResult`.
unsafe fn result_path(item: windows::core::Result<IShellItem>) -> DialogOutcome {
    let item = match item {
        Ok(item) => item,
        Err(e) => return DialogOutcome::Failed(format!("GetResult: {e}")),
    };
    // SAFETY: `item` is the live shell item this function's contract requires,
    // so the COM call is on a valid interface pointer.
    let pwstr: PWSTR = match unsafe { item.GetDisplayName(SIGDN_FILESYSPATH) } {
        Ok(pwstr) => pwstr,
        Err(e) => return DialogOutcome::Failed(format!("GetDisplayName: {e}")),
    };
    // SAFETY: on success GetDisplayName writes a NUL-terminated CoTaskMem string
    // to `pwstr`, which is read here before the free below.
    let path = unsafe { pwstr.to_string() };
    // SAFETY: `pwstr` is the CoTaskMem buffer GetDisplayName just allocated.
    unsafe { CoTaskMemFree(Some(pwstr.0 as *const c_void)) };
    match path {
        Ok(path) => DialogOutcome::Picked(PathBuf::from(path)),
        Err(e) => DialogOutcome::Failed(format!("path decode: {e}")),
    }
}

/// The picker's file-type filter: the archive's `.json`, plus an all-files escape.
fn json_filters() -> [COMDLG_FILTERSPEC; 2] {
    [
        COMDLG_FILTERSPEC {
            pszName: w!("Windhawk user data (*.json)"),
            pszSpec: w!("*.json"),
        },
        COMDLG_FILTERSPEC {
            pszName: w!("All files (*.*)"),
            pszSpec: w!("*.*"),
        },
    ]
}

/// The main window handle to own the modal dialog, or `None` (an ownerless dialog)
/// when the window is not found - so a picker still shows if the lookup fails.
fn main_window_owner() -> Option<HWND> {
    // SAFETY: FindWindowW reads window state; a null window-name matches any title. A
    // missing window is `Err` (a null handle), which `.ok()` turns into `None`.
    unsafe { FindWindowW(&HSTRING::from(MAIN_WINDOW_CLASS), PCWSTR::null()) }.ok()
}

/// A COM apartment held for the lifetime of a dialog. Entering initializes the
/// worker thread as STA (the modal picker needs it); `owned` tracks whether this
/// guard performed the init, so `Drop` balances it - a thread already in an MTA
/// (`RPC_E_CHANGED_MODE`) is used as-is and left untouched.
struct ComApartment {
    owned: bool,
}

impl ComApartment {
    fn enter() -> Option<ComApartment> {
        // SAFETY: CoInitializeEx is always safe to call; STA suits the modal dialog.
        let hr = unsafe { CoInitializeEx(None, COINIT_APARTMENTTHREADED | COINIT_DISABLE_OLE1DDE) };
        if hr.is_ok() {
            Some(ComApartment { owned: true })
        } else if hr == RPC_E_CHANGED_MODE {
            Some(ComApartment { owned: false })
        } else {
            None
        }
    }
}

impl Drop for ComApartment {
    fn drop(&mut self) {
        if self.owned {
            // SAFETY: balanced with the successful CoInitializeEx on this thread.
            unsafe { CoUninitialize() };
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn probe_yields_each_start_point_shape() {
        let temp = tempfile::TempDir::new().unwrap();
        let folder = temp.path();
        let name = OsStr::new("value.txt");
        let file = folder.join(name);

        // A folder picker starts in an existing folder itself.
        let point = probe_start_point(PickTarget::Folder, folder).unwrap();
        assert_eq!(point, (folder.to_path_buf(), None));

        // Either picker starts in an existing parent with the name filled in.
        for target in [PickTarget::File, PickTarget::Folder] {
            let point = probe_start_point(target, &file).unwrap();
            assert_eq!(point, (folder.to_path_buf(), Some(name.to_os_string())));
        }

        // Nothing exists: no start point.
        let orphan = folder.join("missing").join(name);
        assert_eq!(probe_start_point(PickTarget::File, &orphan), None);
    }
}
