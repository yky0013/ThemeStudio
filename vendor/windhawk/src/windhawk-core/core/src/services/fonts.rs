//! `listFontFamilies`: the installed font families as a font picker lists
//! them, for a `fontFamily` mod setting's completion. The `Fonts` port hands
//! over the raw enumeration and [`normalize_families`] reduces it. The
//! enumeration is milliseconds, so nothing is cached.

use serde_json::Value;
use windhawk_core_protocol::ListFontFamiliesResult;

use crate::error::CoreError;
use crate::services::wire::to_value_result;
use crate::session::SessionInner;

pub fn list_font_families(session: &SessionInner, _params: Value) -> Result<Value, CoreError> {
    let names =
        session.deps().fonts.list_font_families().map_err(|e| {
            CoreError::internal(format!("font enumeration: {}", e.render_operation()))
        })?;
    let dto = ListFontFamiliesResult {
        families: normalize_families(names),
    };
    to_value_result("listFontFamilies", &dto)
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
}
