//! The GDI `Fonts` adapter: `EnumFontFamiliesExW` over the screen DC with
//! `DEFAULT_CHARSET` and an empty face name calls back once per family per
//! charset; the callback keeps each face name. The native UI runs the same
//! enumeration in-process (`ui/src/fonts.rs`, outside the core layering), so
//! the two front-ends list the same families; keep the two aligned.

use windhawk_core_ports::{Fonts, OsError};
use windows_sys::Win32::Foundation::LPARAM;
use windows_sys::Win32::Graphics::Gdi::{
    DEFAULT_CHARSET, EnumFontFamiliesExW, GetDC, LOGFONTW, ReleaseDC, TEXTMETRICW,
};

use crate::wide::from_wide_nul;

pub struct WindowsFonts;

impl Fonts for WindowsFonts {
    fn list_font_families(&self) -> Result<Vec<String>, OsError> {
        let mut names: Vec<String> = Vec::new();
        // SAFETY: the screen DC is acquired and released around the enumeration;
        // `collect` reads the LOGFONTW GDI hands it and writes into `names`,
        // which outlives the call and is reached through the LPARAM only during
        // it.
        unsafe {
            let hdc = GetDC(std::ptr::null_mut());
            if hdc.is_null() {
                // GetDC sets no last error, so there is no code to report.
                return Err(OsError::new("GetDC", 0, "no screen device context"));
            }
            let logfont = LOGFONTW {
                lfCharSet: DEFAULT_CHARSET,
                ..Default::default()
            };
            EnumFontFamiliesExW(
                hdc,
                &logfont,
                Some(collect),
                std::ptr::from_mut(&mut names) as LPARAM,
                0,
            );
            ReleaseDC(std::ptr::null_mut(), hdc);
        }
        Ok(names)
    }
}

/// The `FONTENUMPROCW` of the enumeration: appends the face name and asks for
/// the next family.
unsafe extern "system" fn collect(
    logfont: *const LOGFONTW,
    _metric: *const TEXTMETRICW,
    _font_type: u32,
    lparam: LPARAM,
) -> i32 {
    // SAFETY: GDI passes a valid LOGFONTW for the duration of the callback, and
    // `lparam` is the `Vec<String>` `list_font_families` handed it.
    let (face, names) = unsafe { (&(*logfont).lfFaceName, &mut *(lparam as *mut Vec<String>)) };
    names.push(from_wide_nul(face));
    1
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_real_enumeration_lists_the_installed_families() {
        let names = WindowsFonts
            .list_font_families()
            .expect("enumerate the installed fonts");
        assert!(!names.is_empty());
        assert!(names.iter().all(|name| !name.is_empty()), "{names:?}");
    }
}
