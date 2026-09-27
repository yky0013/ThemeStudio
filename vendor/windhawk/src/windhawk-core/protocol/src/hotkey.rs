//! DTOs of `captureHotkey`, the one-chord keyboard capture behind a `hotkey`
//! mod setting's badge. Takes no params; an async command whose progress
//! carries the modifiers held and whose completion carries the chord in the
//! stored form, or the reason there is none.

use serde::{Deserialize, Serialize};

/// The modifier keys held, each folded from its left and right variants.
#[derive(Serialize, Deserialize, Debug, Clone, Copy, PartialEq, Eq, Default)]
#[serde(rename_all = "camelCase")]
pub struct HotkeyModifiers {
    pub ctrl: bool,
    pub alt: bool,
    pub shift: bool,
    pub win: bool,
}

/// A `progress` payload of `captureHotkey`: the modifiers held, emitted on
/// every change of that set before the chord completes.
#[derive(Serialize, Deserialize, Debug, Clone, Copy, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct CaptureHotkeyProgress {
    pub modifiers: HotkeyModifiers,
}

/// Why a capture completed with no chord.
#[derive(Serialize, Deserialize, Debug, Clone, Copy, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub enum HotkeyCaptureCanceled {
    /// Canceled through `WhCoreCancel`, or superseded by a newer capture.
    Canceled,
    /// The foreground window changed under the capture.
    FocusLost,
    /// The capture's deadline passed with no chord completed.
    Timeout,
}

/// The completion of `captureHotkey`: `hotkey` is the chord in the stored form
/// (`[ctrl+][alt+][shift+][win+]<vk>`, as in `ctrl+alt+84`), or `null` with
/// `canceled` naming why there is none.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct CaptureHotkeyResult {
    pub hotkey: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub canceled: Option<HotkeyCaptureCanceled>,
}
