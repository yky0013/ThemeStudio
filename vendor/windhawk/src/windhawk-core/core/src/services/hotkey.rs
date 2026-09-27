//! `captureHotkey`: one keyboard chord recorded through the `HotkeyCapture`
//! port for a `hotkey` mod setting's badge. The port blocks the operation
//! thread for the capture's duration and reports the modifiers held as they
//! change; this service relays those as progress events and completes with
//! the chord in the stored form (`format_hotkey`), or with the reason there
//! is none. It writes no setting: the front-end does, through
//! `setModSettings`, once the user saves.
//!
//! A session runs one capture at a time. The adapter's hook takes every key
//! while it is installed, so two captures at once would each take the other's
//! chord; the newest click wins instead. The slot below holds the token that
//! ends the running capture, and a new `captureHotkey` cancels it at prepare -
//! before either body runs - so the superseded one ends as `canceled` however
//! the two threads interleave.

use std::sync::{Arc, Mutex};

use serde_json::Value;
use windhawk_core_ports::{
    CancelReason, CancelToken, CaptureOutcome, HotkeyCapture, HotkeyModifiers,
};
use windhawk_core_protocol::{
    CaptureHotkeyProgress, CaptureHotkeyResult, HotkeyCaptureCanceled,
    HotkeyModifiers as HotkeyModifiersDto,
};

use crate::error::CoreError;
use crate::runtime::{OpContext, PreparedOp};
use crate::services::wire::to_value_result;
use crate::session::SessionInner;

/// The token of the capture the session is running, if any. Coordination
/// only: it holds no durable state, and the operation's own token still ends
/// the capture on `WhCoreCancel` and on session destroy (the body wires the
/// two together).
#[derive(Default)]
pub struct HotkeyCaptureSlot {
    running: Mutex<Option<Arc<CancelToken>>>,
}

impl HotkeyCaptureSlot {
    /// Put a fresh token in the slot, returning the one it replaces. The
    /// caller cancels that one outside the slot's lock: a cancel runs the
    /// token's hooks on the calling thread.
    fn take_over(&self) -> (Arc<CancelToken>, Option<Arc<CancelToken>>) {
        let token = Arc::new(CancelToken::new());
        let previous = self
            .running
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .replace(token.clone());
        (token, previous)
    }

    /// Empty the slot if it still holds `token`: a capture that ended clears
    /// itself, and leaves a newer one's token alone.
    fn release(&self, token: &Arc<CancelToken>) {
        let mut running = self.running.lock().unwrap_or_else(|e| e.into_inner());
        if running
            .as_ref()
            .is_some_and(|held| Arc::ptr_eq(held, token))
        {
            *running = None;
        }
    }
}

/// `captureHotkey`: end the capture the session is running, if any, and
/// prepare the next one.
pub fn prepare_capture_hotkey(
    session: &Arc<SessionInner>,
    _params: Value,
) -> Result<PreparedOp, CoreError> {
    let port = session.deps().hotkey_capture.clone();
    let slot = session.hotkey_capture_slot();
    let (token, previous) = slot.take_over();
    if let Some(previous) = previous {
        previous.cancel();
    }

    Ok(PreparedOp(Box::new(move |ctx| {
        let result = run_capture(port.as_ref(), &token, ctx);
        slot.release(&token);
        result
    })))
}

fn run_capture(
    port: &dyn HotkeyCapture,
    token: &Arc<CancelToken>,
    ctx: &OpContext,
) -> Result<Value, CoreError> {
    // The operation's cancel (WhCoreCancel, session destroy) ends the capture
    // through the same token a newer capture does.
    let forward = token.clone();
    ctx.cancel_token()
        .on_cancel(Box::new(move || forward.cancel()));

    let mut on_modifiers = |modifiers: HotkeyModifiers| {
        ctx.emit_progress(progress_payload(modifiers));
    };
    let outcome = port.capture(token, &mut on_modifiers).map_err(|e| {
        CoreError::hotkey_capture_unavailable(
            format!("hotkey capture: {}", e.render_operation()),
            e.os_error,
        )
    })?;
    let dto = match outcome {
        CaptureOutcome::Chord { modifiers, vk } => CaptureHotkeyResult {
            hotkey: Some(format_hotkey(modifiers, vk)),
            canceled: None,
        },
        CaptureOutcome::Canceled(reason) => CaptureHotkeyResult {
            hotkey: None,
            canceled: Some(match reason {
                CancelReason::Canceled => HotkeyCaptureCanceled::Canceled,
                CancelReason::FocusLost => HotkeyCaptureCanceled::FocusLost,
                CancelReason::Timeout => HotkeyCaptureCanceled::Timeout,
            }),
        },
    };
    to_value_result("captureHotkey", &dto)
}

fn progress_payload(modifiers: HotkeyModifiers) -> Value {
    let dto = CaptureHotkeyProgress {
        modifiers: HotkeyModifiersDto {
            ctrl: modifiers.ctrl,
            alt: modifiers.alt,
            shift: modifiers.shift,
            win: modifiers.win,
        },
    };
    // Four booleans in a struct: the serialization cannot fail.
    serde_json::to_value(dto).unwrap_or(Value::Null)
}

/// The stored form of a chord: `[ctrl+][alt+][shift+][win+]<vk>`, the
/// modifiers held spelled lowercase in that order, then the virtual-key code
/// in decimal - the spelling a mod reads with `wcsstr` and `_wtoi`.
pub fn format_hotkey(modifiers: HotkeyModifiers, vk: u32) -> String {
    let mut text = String::new();
    for (held, word) in [
        (modifiers.ctrl, "ctrl+"),
        (modifiers.alt, "alt+"),
        (modifiers.shift, "shift+"),
        (modifiers.win, "win+"),
    ] {
        if held {
            text.push_str(word);
        }
    }
    text.push_str(&vk.to_string());
    text
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_stored_form_spells_the_held_modifiers_in_order_then_the_code() {
        let all = HotkeyModifiers {
            ctrl: true,
            alt: true,
            shift: true,
            win: true,
        };
        assert_eq!(format_hotkey(all, 84), "ctrl+alt+shift+win+84");
        assert_eq!(
            format_hotkey(
                HotkeyModifiers {
                    win: true,
                    ..HotkeyModifiers::default()
                },
                68
            ),
            "win+68"
        );
        assert_eq!(format_hotkey(HotkeyModifiers::default(), 116), "116");
    }

    #[test]
    fn a_new_capture_takes_the_slot_and_a_finished_one_leaves_a_newer_alone() {
        let slot = HotkeyCaptureSlot::default();
        let (first, none) = slot.take_over();
        assert!(none.is_none());

        let (second, replaced) = slot.take_over();
        assert!(Arc::ptr_eq(&replaced.expect("the first"), &first));

        // The first ending does not evict the second.
        slot.release(&first);
        let (_, still) = slot.take_over();
        assert!(Arc::ptr_eq(&still.expect("the second"), &second));
    }
}
