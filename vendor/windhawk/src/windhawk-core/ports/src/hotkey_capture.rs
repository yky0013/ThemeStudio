//! The hotkey capture port: one keyboard chord recorded from the user's next
//! key presses, behind `captureHotkey`. The adapter owns the capture's policy
//! (what it takes, how it ends); the service relays the held modifiers as
//! progress and turns the outcome into the stored form.

use crate::cancel::CancelToken;
use crate::os_error::OsError;

/// The modifier keys held, each folded from its left and right variants.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct HotkeyModifiers {
    pub ctrl: bool,
    pub alt: bool,
    pub shift: bool,
    pub win: bool,
}

/// Why a capture ended with no chord.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CancelReason {
    /// The token was canceled: the caller gave up, or a newer capture took
    /// over.
    Canceled,
    /// The foreground window changed under the capture (a click elsewhere).
    FocusLost,
    /// The capture's own deadline passed with no chord completed.
    Timeout,
}

/// How a capture ended.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CaptureOutcome {
    /// A chord: the modifiers held when a non-modifier key went down, and that
    /// key's virtual-key code.
    Chord {
        modifiers: HotkeyModifiers,
        vk: u32,
    },
    Canceled(CancelReason),
}

pub trait HotkeyCapture: Send + Sync {
    /// Record the next chord the user presses, blocking on the calling thread
    /// for the capture's duration. `on_modifiers` is called on every change of
    /// the held modifier set before the chord completes; `cancel` ends the
    /// capture early with [`CancelReason::Canceled`]. An error is a capture
    /// that could not start at all.
    fn capture(
        &self,
        cancel: &CancelToken,
        on_modifiers: &mut dyn FnMut(HotkeyModifiers),
    ) -> Result<CaptureOutcome, OsError>;
}
