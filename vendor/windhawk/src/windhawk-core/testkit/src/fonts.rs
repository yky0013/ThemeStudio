//! In-memory `Fonts` port: a canned raw enumeration, or an injected failure.

use windhawk_core_ports::{Fonts, OsError};

pub struct FakeFonts {
    names: Vec<String>,
    failure: Option<String>,
}

impl FakeFonts {
    /// Enumerate exactly `names`, raw (the service does the normalizing, so a
    /// test hands over repeats and `@` variants to exercise it).
    pub fn new(names: &[&str]) -> Self {
        Self {
            names: names.iter().map(|s| (*s).to_owned()).collect(),
            failure: None,
        }
    }

    /// Fail every enumeration with `message` (a GDI failure).
    pub fn failing(message: &str) -> Self {
        Self {
            names: Vec::new(),
            failure: Some(message.to_owned()),
        }
    }
}

impl Default for FakeFonts {
    /// A small realistic enumeration, for sessions whose test is not about fonts.
    fn default() -> Self {
        Self::new(&["Arial", "Segoe UI", "Consolas"])
    }
}

impl Fonts for FakeFonts {
    fn list_font_families(&self) -> Result<Vec<String>, OsError> {
        match &self.failure {
            Some(message) => Err(OsError::new("GetDC", 0, message.clone())),
            None => Ok(self.names.clone()),
        }
    }
}
