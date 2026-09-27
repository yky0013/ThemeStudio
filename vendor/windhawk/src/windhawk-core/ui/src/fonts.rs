//! The installed font families, for a `fontFamily` setting's completion (the
//! `listFontFamilies` request). `EnumFontFamiliesExW` over the screen DC with
//! `DEFAULT_CHARSET` and an empty face name calls back once per family per
//! charset; the callback keeps each face name and [`normalize_families`] does
//! the rest. The enumeration is milliseconds, so nothing is cached. The core's
//! `listFontFamilies` (`windows/src/fonts.rs` + `core/src/services/fonts.rs`)
//! is the same enumeration and reduction for the extension; keep the two
//! aligned.

use windows::Win32::Foundation::LPARAM;
use windows::Win32::Graphics::Gdi::{
    DEFAULT_CHARSET, EnumFontFamiliesExW, GetDC, LOGFONTW, ReleaseDC, TEXTMETRICW,
};

/// The installed font families as a picker lists them: deduplicated, without
/// the `@`-prefixed vertical variants, sorted case-insensitively.
pub fn list_font_families() -> Result<Vec<String>, String> {
    let mut names: Vec<String> = Vec::new();
    // SAFETY: the screen DC is acquired and released around the enumeration;
    // `collect` reads the LOGFONTW GDI hands it and writes into `names`, which
    // outlives the call and is reached through the LPARAM only during it.
    unsafe {
        let hdc = GetDC(None);
        if hdc.is_invalid() {
            return Err("GetDC failed".to_owned());
        }
        let logfont = LOGFONTW {
            lfCharSet: DEFAULT_CHARSET,
            ..Default::default()
        };
        EnumFontFamiliesExW(
            hdc,
            &logfont,
            Some(collect),
            LPARAM(std::ptr::from_mut(&mut names) as isize),
            0,
        );
        ReleaseDC(None, hdc);
    }
    Ok(normalize_families(names))
}

/// The `FONTENUMPROCW` of [`list_font_families`]: appends the face name and
/// asks for the next family.
unsafe extern "system" fn collect(
    logfont: *const LOGFONTW,
    _metric: *const TEXTMETRICW,
    _font_type: u32,
    lparam: LPARAM,
) -> i32 {
    // SAFETY: GDI passes a valid LOGFONTW for the duration of the callback, and
    // `lparam` is the `Vec<String>` `list_font_families` handed it.
    let (face, names) = unsafe { (&(*logfont).lfFaceName, &mut *(lparam.0 as *mut Vec<String>)) };
    let len = face.iter().position(|&c| c == 0).unwrap_or(face.len());
    names.push(String::from_utf16_lossy(&face[..len]));
    1
}

/// Reduce the raw enumeration to a picker's list: drop empty names and the
/// `@`-prefixed vertical variants, sort case-insensitively (ties by exact
/// text, so the order is total), and drop the repeats the per-charset
/// callbacks produce.
pub fn normalize_families(names: Vec<String>) -> Vec<String> {
    let mut families: Vec<String> = names
        .into_iter()
        .filter(|name| !name.is_empty() && !name.starts_with('@'))
        .collect();
    families.sort_by(|a, b| {
        a.to_lowercase()
            .cmp(&b.to_lowercase())
            .then_with(|| a.cmp(b))
    });
    families.dedup();
    families
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn normalize_dedupes_filters_vertical_variants_and_sorts_case_insensitively() {
        let raw = [
            "Segoe UI",
            "consolas",
            "@Yu Gothic",
            "Arial",
            "Segoe UI",
            "",
            "Yu Gothic",
            "arial Narrow",
        ]
        .map(String::from)
        .to_vec();
        assert_eq!(
            normalize_families(raw),
            ["Arial", "arial Narrow", "consolas", "Segoe UI", "Yu Gothic"].map(String::from)
        );
    }

    #[test]
    fn the_real_enumeration_lists_the_installed_families() {
        let families = list_font_families().expect("enumerate the installed fonts");
        assert!(!families.is_empty());
        assert!(families.iter().all(|name| !name.starts_with('@')));
        let lower: Vec<String> = families.iter().map(|name| name.to_lowercase()).collect();
        assert!(
            lower.windows(2).all(|pair| pair[0] <= pair[1]),
            "{families:?}"
        );
        let mut deduped = families.clone();
        deduped.dedup();
        assert_eq!(deduped, families);
    }
}
