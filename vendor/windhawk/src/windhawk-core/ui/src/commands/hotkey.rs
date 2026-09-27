//! The hotkey capture handlers: `captureHotkey`, which starts the core's
//! one-chord capture and relays its events, and `cancelCaptureHotkey`. Like
//! `startUpdate`, the capture is an async command with progress the front-end
//! consumes - the held modifiers, as `hotkeyCaptureProgress` events - so its
//! [`AsyncKind`] carries a progress mapper beside the terminal shaper. The core
//! runs one capture per session and ends the running one when another starts,
//! so the cancel finds the op by command alone, as `cancelUpdate` does.

use serde_json::{Value, json};
use windhawk_core_host::HostError;
use windhawk_core_protocol::OperationEvent;

use crate::ipc::bridge::BridgeCtx;
use crate::ipc::envelope::Envelope;
use crate::ipc::outcome::{AsyncKind, AsyncOp, Outcome, Terminal};
use crate::ipc::reply;
use crate::shape::webview_ipc::{CancelCaptureHotkeyReply, CaptureHotkeyReply, to_wire};

/// `captureHotkey`: start the capture. The reply is the core's completion
/// forwarded - `{ hotkey }`, or `{ hotkey: null, canceled }` - and on a failure
/// `{ hotkey: null }` with the error attached, whether the start was refused
/// synchronously (an older core not knowing the command) or the hook could not
/// be installed; the front-end reads either as the cue for its manual editor.
pub fn capture_hotkey(ctx: &BridgeCtx, _data: &Value) -> Result<Outcome, HostError> {
    match ctx.start_async("captureHotkey", &json!({})) {
        Ok(start) => Ok(Outcome::Async(AsyncOp {
            start,
            kind: AsyncKind {
                terminal: Terminal::Shaped(capture_hotkey_terminal),
                progress: Some(capture_hotkey_progress),
                effect: None,
                records: None,
            },
            context: Value::Null,
        })),
        Err(error) => {
            // The pump attaches an op's terminal error itself; a start that
            // never became an op attaches its own here.
            let mut data = no_capture_reply();
            reply::attach_error(&mut data, &error);
            Ok(Outcome::Reply(data))
        }
    }
}

/// `cancelCaptureHotkey`: signal the in-flight capture. `signaled` is whether an
/// op was found and signaled; the op's own terminal still produces the
/// `captureHotkey` reply, as `canceled`.
pub fn cancel_capture_hotkey(ctx: &BridgeCtx, _data: &Value) -> Result<Outcome, HostError> {
    let signaled = ctx.ops.cancel_by_command("captureHotkey");
    Ok(Outcome::Reply(to_wire(CancelCaptureHotkeyReply {
        signaled,
    })))
}

/// The capture's terminal reply. A completion is forwarded verbatim: its shape
/// is the reply's, and a field the core adds is not dropped. A failure is the
/// bare `{ hotkey: null }`; the error is attached by the pump.
fn capture_hotkey_terminal(outcome: Result<Value, HostError>, _ctx: &Value) -> Value {
    match outcome {
        Ok(completed) => completed,
        Err(_) => no_capture_reply(),
    }
}

/// `{ hotkey: null }`: the reply of a capture that never ran.
fn no_capture_reply() -> Value {
    to_wire(CaptureHotkeyReply {
        hotkey: None,
        canceled: None,
    })
}

/// Map a capture progress event to its front-end event: the `{ modifiers }`
/// payload forwards verbatim as `hotkeyCaptureProgress`. Never handed a
/// terminal event, so it cannot produce a reply.
fn capture_hotkey_progress(event: &OperationEvent) -> Vec<Envelope> {
    match event {
        OperationEvent::Progress { payload } => {
            vec![Envelope::event("hotkeyCaptureProgress", payload.clone())]
        }
        OperationEvent::Installing
        | OperationEvent::Completed { .. }
        | OperationEvent::Failed { .. } => Vec::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use windhawk_core_protocol::{ErrorCode, WireError};

    #[test]
    fn terminal_forwards_a_completion_and_shapes_a_failure_bare() {
        let chord = json!({ "hotkey": "ctrl+alt+116" });
        assert_eq!(
            capture_hotkey_terminal(Ok(chord.clone()), &Value::Null),
            chord
        );

        let canceled = json!({ "hotkey": null, "canceled": "focusLost" });
        assert_eq!(
            capture_hotkey_terminal(Ok(canceled.clone()), &Value::Null),
            canceled
        );

        let err = HostError::wire(WireError::new(
            ErrorCode::HotkeyCaptureUnavailable,
            "no hook",
        ));
        assert_eq!(
            capture_hotkey_terminal(Err(err), &Value::Null),
            json!({ "hotkey": null })
        );
    }

    #[test]
    fn progress_forwards_the_held_modifiers_as_the_capture_event() {
        let payload =
            json!({ "modifiers": { "ctrl": true, "alt": false, "shift": false, "win": true } });
        let envelopes = capture_hotkey_progress(&OperationEvent::Progress {
            payload: payload.clone(),
        });
        assert_eq!(envelopes.len(), 1);
        assert_eq!(envelopes[0].command, "hotkeyCaptureProgress");
        assert_eq!(envelopes[0].data, payload);

        assert!(
            capture_hotkey_progress(&OperationEvent::Completed {
                result: Value::Null
            })
            .is_empty()
        );
    }
}
