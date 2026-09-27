//! The low-level keyboard hook `HotkeyCapture` adapter: a `WH_KEYBOARD_LL`
//! hook installed on the calling thread for one capture, pumped by a message
//! loop until the chord is complete and released, or the capture ends without
//! one. The hook runs ahead of the shell's own hotkey dispatch and of any
//! window's `WM_KEYDOWN`, so a chord the shell owns (Win+D) is recorded and
//! acted on by nothing; it takes every key that is not injected while it is
//! installed, which is why it exists only inside one capture and ends on its
//! own.
//!
//! The capture ends when: (a) a non-modifier key went down and every key held
//! since the hook went in has been released, the trailing releases taken too;
//! (b) the foreground window is no longer the one snapshotted at the start (a
//! `SetWinEventHook` on the same thread - a click elsewhere, since the
//! keyboard's own switches are taken); (c) [`CAPTURE_TIMEOUT_MS`] passed, which
//! bounds a capture whose keys another hook ahead of this one is eating as well
//! as a user who walked away; (d) the token was canceled, which posts to the
//! loop. Both hooks are removed by a drop guard on every path.
//!
//! The two hook procedures take no user pointer, so they reach the capture's
//! state through a `thread_local!`: per-thread state on the hook thread, and
//! only for the capture's duration. They do no work but record and post; the
//! loop, outside the procedures, reports the held modifiers and the outcome, so
//! the procedures return in microseconds whatever the caller does with a report
//! and stay inside the `LowLevelHooksTimeout` past which Windows drops a hook.
//! What they read is `KBDLLHOOKSTRUCT.vkCode`, the virtual-key code the stored
//! form carries; the left and right variants of a modifier fold to its word.

use std::cell::RefCell;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};

use windhawk_core_ports::{
    CancelReason, CancelToken, CaptureOutcome, HotkeyCapture, HotkeyModifiers, OsError, os_message,
};
use windows_sys::Win32::Foundation::{HMODULE, HWND, LPARAM, LRESULT, WPARAM};
use windows_sys::Win32::System::LibraryLoader::{
    GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS, GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
    GetModuleHandleExW,
};
use windows_sys::Win32::System::Threading::GetCurrentThreadId;
use windows_sys::Win32::UI::Accessibility::{HWINEVENTHOOK, SetWinEventHook, UnhookWinEvent};
use windows_sys::Win32::UI::Input::KeyboardAndMouse::{
    VK_CONTROL, VK_LCONTROL, VK_LMENU, VK_LSHIFT, VK_LWIN, VK_MENU, VK_RCONTROL, VK_RMENU,
    VK_RSHIFT, VK_RWIN, VK_SHIFT,
};
use windows_sys::Win32::UI::WindowsAndMessaging::{
    CallNextHookEx, DispatchMessageW, EVENT_SYSTEM_FOREGROUND, GetForegroundWindow, GetMessageW,
    HHOOK, KBDLLHOOKSTRUCT, KillTimer, LLKHF_INJECTED, LLKHF_UP, MSG, PM_NOREMOVE, PeekMessageW,
    PostThreadMessageW, SetTimer, SetWindowsHookExW, TranslateMessage, UnhookWindowsHookEx,
    WH_KEYBOARD_LL, WINEVENT_OUTOFCONTEXT, WM_APP, WM_TIMER, WM_USER,
};

use crate::os::last_error;

/// How long a capture waits for a chord before ending as a timeout.
const CAPTURE_TIMEOUT_MS: u32 = 15_000;

/// Posted by the keyboard hook procedure: the held set or the chord changed.
const WM_CAPTURE_KEYS: u32 = WM_APP + 1;
/// Posted by the foreground event procedure: the foreground window changed.
const WM_CAPTURE_FOCUS_LOST: u32 = WM_APP + 2;
/// Posted by the token's cancel hook.
const WM_CAPTURE_CANCEL: u32 = WM_APP + 3;

pub struct WindowsHotkeyCapture;

impl HotkeyCapture for WindowsHotkeyCapture {
    fn capture(
        &self,
        cancel: &CancelToken,
        on_modifiers: &mut dyn FnMut(HotkeyModifiers),
    ) -> Result<CaptureOutcome, OsError> {
        // A thread has no message queue until it asks for one, and the posts
        // the hooks and the cancel make need it to exist; a peek creates it.
        let mut probe = MSG::default();
        // SAFETY: `probe` is a valid MSG for the call to fill; a no-remove peek
        // of a range nothing posts changes nothing.
        unsafe {
            PeekMessageW(
                &mut probe,
                std::ptr::null_mut(),
                WM_USER,
                WM_USER,
                PM_NOREMOVE,
            )
        };

        // Superseded or given up before it started: nothing to install.
        if cancel.is_canceled() {
            return Ok(CaptureOutcome::Canceled(CancelReason::Canceled));
        }

        // SAFETY: both calls read process and thread state and take nothing.
        let (thread_id, foreground) = unsafe { (GetCurrentThreadId(), GetForegroundWindow()) };
        let _state = ThreadState::install(thread_id, foreground);
        let hooks = Hooks::install()?;

        let signal = Arc::new(CancelSignal {
            thread_id,
            active: AtomicBool::new(true),
        });
        let _armed = ArmedSignal(signal.clone());
        cancel.on_cancel(Box::new(move || signal.post()));

        pump(hooks.timer, on_modifiers)
    }
}

/// What the loop learns from the thread-local state after a keyboard event.
struct KeysSnapshot {
    modifiers: HotkeyModifiers,
    complete: bool,
    done: Option<(HotkeyModifiers, u32)>,
}

/// The message loop: runs until the capture ends, dispatching everything that
/// is not the capture's own to the thread's (windowless) default handling.
fn pump(
    timer: usize,
    on_modifiers: &mut dyn FnMut(HotkeyModifiers),
) -> Result<CaptureOutcome, OsError> {
    let mut reported = HotkeyModifiers::default();
    loop {
        let mut msg = MSG::default();
        // SAFETY: `msg` is a valid MSG for the call to fill; a null window
        // takes every message of the thread.
        let got = unsafe { GetMessageW(&mut msg, std::ptr::null_mut(), 0, 0) };
        if got == -1 {
            let code = last_error();
            return Err(OsError::new("GetMessageW", code, os_message(code)));
        }
        if got == 0 {
            // WM_QUIT on a thread of this process's own: nothing here posts it,
            // so whatever did wants the thread gone.
            return Ok(CaptureOutcome::Canceled(CancelReason::Canceled));
        }
        match msg.message {
            WM_CAPTURE_KEYS => {
                let Some(snapshot) = ThreadState::snapshot() else {
                    continue;
                };
                if let Some((modifiers, vk)) = snapshot.done {
                    return Ok(CaptureOutcome::Chord { modifiers, vk });
                }
                if !snapshot.complete && snapshot.modifiers != reported {
                    reported = snapshot.modifiers;
                    on_modifiers(reported);
                }
            }
            WM_CAPTURE_FOCUS_LOST => {
                return Ok(CaptureOutcome::Canceled(CancelReason::FocusLost));
            }
            WM_CAPTURE_CANCEL => return Ok(CaptureOutcome::Canceled(CancelReason::Canceled)),
            WM_TIMER if msg.hwnd.is_null() && msg.wParam == timer => {
                return Ok(CaptureOutcome::Canceled(CancelReason::Timeout));
            }
            _ => {
                // SAFETY: `msg` is the message just retrieved, handed on as the
                // standard loop does.
                unsafe {
                    TranslateMessage(&msg);
                    DispatchMessageW(&msg);
                }
            }
        }
    }
}

/// The two hooks and the deadline timer of one capture, removed together when
/// the capture ends, whichever way.
struct Hooks {
    keyboard: HHOOK,
    foreground: HWINEVENTHOOK,
    timer: usize,
}

impl Hooks {
    fn install() -> Result<Hooks, OsError> {
        let mut hooks = Hooks {
            keyboard: std::ptr::null_mut(),
            foreground: std::ptr::null_mut(),
            timer: 0,
        };
        // SAFETY: the hook procedures are `extern "system"` functions of this
        // crate with the signatures the hook ids call for; a thread id of 0
        // makes both global, which a low-level keyboard hook has to be. The
        // module handle is the one holding the keyboard procedure - this
        // crate's DLL, whichever host loaded it - looked up from its address
        // without a reference taken, so the handle changes nothing about the
        // module's lifetime.
        unsafe {
            let mut module: HMODULE = std::ptr::null_mut();
            GetModuleHandleExW(
                GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS
                    | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                keyboard_proc as *const u16,
                &mut module,
            );
            hooks.keyboard = SetWindowsHookExW(WH_KEYBOARD_LL, Some(keyboard_proc), module, 0);
            if hooks.keyboard.is_null() {
                return Err(os_failure("SetWindowsHookExW"));
            }
            hooks.foreground = SetWinEventHook(
                EVENT_SYSTEM_FOREGROUND,
                EVENT_SYSTEM_FOREGROUND,
                std::ptr::null_mut(),
                Some(foreground_proc),
                0,
                0,
                WINEVENT_OUTOFCONTEXT,
            );
            if hooks.foreground.is_null() {
                return Err(os_failure("SetWinEventHook"));
            }
            // A thread timer (no window): its WM_TIMER lands in the loop above.
            hooks.timer = SetTimer(std::ptr::null_mut(), 0, CAPTURE_TIMEOUT_MS, None);
            if hooks.timer == 0 {
                return Err(os_failure("SetTimer"));
            }
        }
        Ok(hooks)
    }
}

impl Drop for Hooks {
    fn drop(&mut self) {
        // SAFETY: each handle is the one its install call returned on this
        // thread, released exactly once; a null one was never installed.
        unsafe {
            if self.timer != 0 {
                KillTimer(std::ptr::null_mut(), self.timer);
            }
            if !self.foreground.is_null() {
                UnhookWinEvent(self.foreground);
            }
            if !self.keyboard.is_null() {
                UnhookWindowsHookEx(self.keyboard);
            }
        }
    }
}

/// The failure of the named call, with the thread's last error.
fn os_failure(operation: &'static str) -> OsError {
    let code = last_error();
    OsError::new(operation, code, os_message(code))
}

/// What the token's cancel hook posts to. The hook can outlive the capture -
/// it stays registered on the token until the token is canceled, which a
/// session's destroy does long after - so it posts only while the capture is
/// running, never to a thread id the system may have handed to another thread.
struct CancelSignal {
    thread_id: u32,
    active: AtomicBool,
}

impl CancelSignal {
    fn post(&self) {
        if self.active.load(Ordering::SeqCst) {
            // SAFETY: a post to a thread queue takes no pointer; a thread that
            // is gone fails the call harmlessly.
            unsafe { PostThreadMessageW(self.thread_id, WM_CAPTURE_CANCEL, 0, 0) };
        }
    }
}

/// Disarms the cancel signal when the capture returns.
struct ArmedSignal(Arc<CancelSignal>);

impl Drop for ArmedSignal {
    fn drop(&mut self) {
        self.0.active.store(false, Ordering::SeqCst);
    }
}

thread_local! {
    /// The capture running on this thread, while one is.
    static CAPTURE: RefCell<Option<ThreadCapture>> = const { RefCell::new(None) };
}

struct ThreadCapture {
    thread_id: u32,
    /// The foreground window when the capture started.
    foreground: HWND,
    keys: KeyState,
}

/// Puts the capture's state in the thread-local slot and clears it on drop.
struct ThreadState;

impl ThreadState {
    fn install(thread_id: u32, foreground: HWND) -> ThreadState {
        CAPTURE.with(|slot| {
            *slot.borrow_mut() = Some(ThreadCapture {
                thread_id,
                foreground,
                keys: KeyState::default(),
            });
        });
        ThreadState
    }

    /// The keyboard state as the hook procedure last left it; `None` when the
    /// thread runs no capture.
    fn snapshot() -> Option<KeysSnapshot> {
        CAPTURE.with(|slot| {
            let slot = slot.borrow();
            let capture = slot.as_ref()?;
            Some(KeysSnapshot {
                modifiers: capture.keys.modifiers(),
                complete: capture.keys.chord.is_some(),
                done: capture.keys.done(),
            })
        })
    }
}

impl Drop for ThreadState {
    fn drop(&mut self) {
        CAPTURE.with(|slot| *slot.borrow_mut() = None);
    }
}

/// The keyboard hook procedure: records the event in the thread's capture and
/// posts to the loop, taking every event that is not injected. A capture that
/// is not on this thread, or a state a borrow cannot reach, passes the event
/// on rather than failing inside a hook.
unsafe extern "system" fn keyboard_proc(code: i32, wparam: WPARAM, lparam: LPARAM) -> LRESULT {
    if code >= 0 {
        // SAFETY: for a non-negative code the system hands a KBDLLHOOKSTRUCT in
        // `lparam`, valid for the duration of the call.
        let event = unsafe { &*(lparam as *const KBDLLHOOKSTRUCT) };
        // Software input is not the user's hand: neither recorded nor taken.
        if event.flags & LLKHF_INJECTED == 0 {
            let down = event.flags & LLKHF_UP == 0;
            let posted = CAPTURE.with(|slot| {
                let mut slot = slot.try_borrow_mut().ok()?;
                let capture = slot.as_mut()?;
                let changed = if down {
                    capture.keys.key_down(event.vkCode)
                } else {
                    capture.keys.key_up(event.vkCode)
                };
                Some((capture.thread_id, changed))
            });
            if let Some((thread_id, changed)) = posted {
                if changed {
                    // SAFETY: a post to a thread queue takes no pointer.
                    unsafe { PostThreadMessageW(thread_id, WM_CAPTURE_KEYS, 0, 0) };
                }
                return 1;
            }
        }
    }
    // SAFETY: forwarding the event with the arguments it arrived with, as the
    // hook chain requires; the hook handle is not needed for a low-level hook.
    unsafe { CallNextHookEx(std::ptr::null_mut(), code, wparam, lparam) }
}

/// The foreground event procedure: posts to the loop when the foreground
/// window is no longer the one the capture started under.
unsafe extern "system" fn foreground_proc(
    _hook: HWINEVENTHOOK,
    _event: u32,
    hwnd: HWND,
    _id_object: i32,
    _id_child: i32,
    _id_event_thread: u32,
    _event_time: u32,
) {
    let lost = CAPTURE.with(|slot| {
        let slot = slot.try_borrow().ok()?;
        let capture = slot.as_ref()?;
        (capture.foreground != hwnd).then_some(capture.thread_id)
    });
    if let Some(thread_id) = lost {
        // SAFETY: a post to a thread queue takes no pointer.
        unsafe { PostThreadMessageW(thread_id, WM_CAPTURE_FOCUS_LOST, 0, 0) };
    }
}

/// A modifier, folded from the generic code and its left and right variants.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Modifier {
    Ctrl,
    Alt,
    Shift,
    Win,
}

fn modifier_of(vk: u32) -> Option<Modifier> {
    let vk = u16::try_from(vk).ok()?;
    match vk {
        VK_CONTROL | VK_LCONTROL | VK_RCONTROL => Some(Modifier::Ctrl),
        VK_MENU | VK_LMENU | VK_RMENU => Some(Modifier::Alt),
        VK_SHIFT | VK_LSHIFT | VK_RSHIFT => Some(Modifier::Shift),
        VK_LWIN | VK_RWIN => Some(Modifier::Win),
        _ => None,
    }
}

/// The pure bookkeeping of a capture: the keys that went down since the hook
/// went in, and the chord once a non-modifier key did. A key that was down at
/// the start is not held here, so its release changes nothing.
#[derive(Default)]
struct KeyState {
    held: Vec<u32>,
    chord: Option<(HotkeyModifiers, u32)>,
}

impl KeyState {
    /// A key went down. True when the loop has something new to see: a change
    /// of the held set, which a repeat of a held key is not.
    fn key_down(&mut self, vk: u32) -> bool {
        if self.held.contains(&vk) {
            return false;
        }
        self.held.push(vk);
        if self.chord.is_none() && modifier_of(vk).is_none() {
            self.chord = Some((self.modifiers(), vk));
        }
        true
    }

    /// A key went up. True when it was one of the held keys.
    fn key_up(&mut self, vk: u32) -> bool {
        let Some(at) = self.held.iter().position(|held| *held == vk) else {
            return false;
        };
        self.held.remove(at);
        true
    }

    /// The modifiers among the held keys.
    fn modifiers(&self) -> HotkeyModifiers {
        let mut modifiers = HotkeyModifiers::default();
        for held in &self.held {
            match modifier_of(*held) {
                Some(Modifier::Ctrl) => modifiers.ctrl = true,
                Some(Modifier::Alt) => modifiers.alt = true,
                Some(Modifier::Shift) => modifiers.shift = true,
                Some(Modifier::Win) => modifiers.win = true,
                None => {}
            }
        }
        modifiers
    }

    /// The chord, once it is complete and every held key has been released.
    fn done(&self) -> Option<(HotkeyModifiers, u32)> {
        self.chord.filter(|_| self.held.is_empty())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const VK_T: u32 = 84;
    const VK_D: u32 = 68;

    fn held(ctrl: bool, alt: bool, shift: bool, win: bool) -> HotkeyModifiers {
        HotkeyModifiers {
            ctrl,
            alt,
            shift,
            win,
        }
    }

    #[test]
    fn left_and_right_variants_fold_to_their_modifier() {
        for (vk, expected) in [
            (VK_CONTROL, Modifier::Ctrl),
            (VK_LCONTROL, Modifier::Ctrl),
            (VK_RCONTROL, Modifier::Ctrl),
            (VK_MENU, Modifier::Alt),
            (VK_LMENU, Modifier::Alt),
            (VK_RMENU, Modifier::Alt),
            (VK_SHIFT, Modifier::Shift),
            (VK_LSHIFT, Modifier::Shift),
            (VK_RSHIFT, Modifier::Shift),
            (VK_LWIN, Modifier::Win),
            (VK_RWIN, Modifier::Win),
        ] {
            assert_eq!(modifier_of(u32::from(vk)), Some(expected), "vk {vk}");
        }
        assert_eq!(modifier_of(VK_T), None);
        assert_eq!(modifier_of(0x1_0000), None);
    }

    #[test]
    fn a_chord_is_the_modifiers_held_when_its_key_goes_down_and_ends_on_release() {
        let mut keys = KeyState::default();
        assert!(keys.key_down(u32::from(VK_LCONTROL)));
        assert!(keys.key_down(u32::from(VK_RMENU)));
        assert_eq!(keys.modifiers(), held(true, true, false, false));
        assert!(keys.chord.is_none());

        assert!(keys.key_down(VK_T));
        assert_eq!(keys.chord, Some((held(true, true, false, false), VK_T)));
        // Complete but not done: the keys are still down.
        assert_eq!(keys.done(), None);

        // Released in any order; the last release ends it.
        assert!(keys.key_up(VK_T));
        assert!(keys.key_up(u32::from(VK_LCONTROL)));
        assert_eq!(keys.done(), None);
        assert!(keys.key_up(u32::from(VK_RMENU)));
        assert_eq!(keys.done(), Some((held(true, true, false, false), VK_T)));
    }

    #[test]
    fn a_repeat_and_the_release_of_a_key_down_at_the_start_change_nothing() {
        let mut keys = KeyState::default();
        assert!(keys.key_down(u32::from(VK_LWIN)));
        // Auto-repeat of the held key.
        assert!(!keys.key_down(u32::from(VK_LWIN)));
        assert_eq!(keys.held, vec![u32::from(VK_LWIN)]);
        // A key that was down before the hook went in.
        assert!(!keys.key_up(u32::from(VK_LSHIFT)));
        assert_eq!(keys.modifiers(), held(false, false, false, true));
    }

    #[test]
    fn keys_going_down_after_the_chord_keep_it_and_delay_its_end() {
        let mut keys = KeyState::default();
        keys.key_down(u32::from(VK_LWIN));
        keys.key_down(VK_D);
        // A second key while the chord is down: not the chord, but its release
        // is waited for.
        keys.key_down(VK_T);
        keys.key_up(VK_D);
        keys.key_up(u32::from(VK_LWIN));
        assert_eq!(keys.chord, Some((held(false, false, false, true), VK_D)));
        assert_eq!(keys.done(), None);
        keys.key_up(VK_T);
        assert_eq!(keys.done(), Some((held(false, false, false, true), VK_D)));
    }

    #[test]
    fn a_modifier_released_before_the_key_is_not_part_of_the_chord() {
        let mut keys = KeyState::default();
        keys.key_down(u32::from(VK_LSHIFT));
        keys.key_down(u32::from(VK_LCONTROL));
        keys.key_up(u32::from(VK_LSHIFT));
        assert_eq!(keys.modifiers(), held(true, false, false, false));
        keys.key_down(VK_T);
        assert_eq!(keys.chord, Some((held(true, false, false, false), VK_T)));
    }
}
