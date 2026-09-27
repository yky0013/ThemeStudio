//! In-memory `HotkeyCapture` port: a scripted capture - a sequence of held
//! modifier sets reported as progress, a wait, then an outcome - or an
//! injected failure to start. The wait blocks on the token, so a cancel that
//! lands during it ends the capture as the real hook would.

use std::sync::Mutex;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Duration;

use windhawk_core_ports::{
    CancelReason, CancelToken, CaptureOutcome, HotkeyCapture, HotkeyModifiers, OsError,
};

/// What a scripted capture ends with.
#[derive(Debug, Clone)]
pub enum FakeCaptureEnd {
    Outcome(CaptureOutcome),
    /// The capture could not start (the hook could not be installed).
    Unavailable(String),
}

struct Script {
    steps: Vec<HotkeyModifiers>,
    delay: Duration,
    end: FakeCaptureEnd,
}

pub struct FakeHotkeyCapture {
    script: Mutex<Script>,
    started: AtomicUsize,
}

impl FakeHotkeyCapture {
    /// Report each of `steps` as a change of the held modifiers, wait `delay`
    /// (ending as canceled if the token fires first), then end with `end`.
    pub fn scripted(steps: &[HotkeyModifiers], delay: Duration, end: FakeCaptureEnd) -> Self {
        Self {
            script: Mutex::new(Script {
                steps: steps.to_vec(),
                delay,
                end,
            }),
            started: AtomicUsize::new(0),
        }
    }

    /// A capture that completes at once with `modifiers` + `vk`.
    pub fn chord(modifiers: HotkeyModifiers, vk: u32) -> Self {
        Self::scripted(
            &[],
            Duration::ZERO,
            FakeCaptureEnd::Outcome(CaptureOutcome::Chord { modifiers, vk }),
        )
    }

    /// A capture that never completes on its own: it waits on the token for
    /// `delay`, ending as canceled when the token fires, and as `end` when the
    /// wait runs out (a test's guard against hanging).
    pub fn blocking(delay: Duration, end: FakeCaptureEnd) -> Self {
        Self::scripted(&[], delay, end)
    }

    /// Fail every capture to start with `message`.
    pub fn unavailable(message: &str) -> Self {
        Self::scripted(
            &[],
            Duration::ZERO,
            FakeCaptureEnd::Unavailable(message.to_owned()),
        )
    }

    /// How many captures reached the port.
    pub fn started(&self) -> usize {
        self.started.load(Ordering::SeqCst)
    }
}

impl Default for FakeHotkeyCapture {
    /// Ctrl+Alt+T at once, for sessions whose test is not about the capture.
    fn default() -> Self {
        Self::chord(
            HotkeyModifiers {
                ctrl: true,
                alt: true,
                shift: false,
                win: false,
            },
            84,
        )
    }
}

impl HotkeyCapture for FakeHotkeyCapture {
    fn capture(
        &self,
        cancel: &CancelToken,
        on_modifiers: &mut dyn FnMut(HotkeyModifiers),
    ) -> Result<CaptureOutcome, OsError> {
        self.started.fetch_add(1, Ordering::SeqCst);
        let (steps, delay, end) = {
            let script = self.script.lock().unwrap_or_else(|e| e.into_inner());
            (script.steps.clone(), script.delay, script.end.clone())
        };
        let outcome = match end {
            FakeCaptureEnd::Outcome(outcome) => outcome,
            FakeCaptureEnd::Unavailable(message) => {
                return Err(OsError::new("SetWindowsHookExW", 0, message));
            }
        };
        // A capture superseded before it ran ends without reporting anything,
        // as the real one does.
        if cancel.is_canceled() {
            return Ok(CaptureOutcome::Canceled(CancelReason::Canceled));
        }
        for step in steps {
            on_modifiers(step);
        }
        if cancel.wait(delay) {
            return Ok(CaptureOutcome::Canceled(CancelReason::Canceled));
        }
        Ok(outcome)
    }
}
