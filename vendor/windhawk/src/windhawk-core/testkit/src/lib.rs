//! In-memory port implementations, fault injection, and fixture helpers
//! for windhawk-core tests. Behavioral fakes, not expectation mocks: tests
//! assert on outcomes. Never linked into the shipping DLL (dev-dependency
//! only).

#![forbid(unsafe_code)]
#![cfg_attr(not(test), deny(clippy::unwrap_used, clippy::expect_used))]

mod clock;
mod files;
mod fixtures;
mod fonts;
mod hotkey_capture;
mod http;
mod named_lock;
mod processes;
mod settings;
mod storage;

pub use clock::FakeClock;
pub use files::FakeFiles;
pub use fixtures::{fixture_commands, fixture_files, fixtures_dir};
pub use fonts::FakeFonts;
pub use hotkey_capture::{FakeCaptureEnd, FakeHotkeyCapture};
pub use http::{FakeHttp, FakeResponse};
pub use named_lock::FakeNamedLock;
pub use processes::FakeProcesses;
pub use settings::{FakeSettings, tree_key};
pub use storage::FakeStorageProvider;
