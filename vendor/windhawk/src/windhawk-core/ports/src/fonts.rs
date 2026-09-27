//! The installed fonts port: the raw family enumeration behind
//! `listFontFamilies`. The adapter hands over what the OS enumerates and the
//! service reduces it to a picker's list, so the reduction is testable over a
//! canned enumeration.

use crate::os_error::OsError;

pub trait Fonts: Send + Sync {
    /// The face names of the installed font families as the OS enumerates
    /// them, raw: repeats (GDI calls back once per family per charset) and the
    /// `@`-prefixed vertical variants included, in enumeration order.
    fn list_font_families(&self) -> Result<Vec<String>, OsError>;
}
