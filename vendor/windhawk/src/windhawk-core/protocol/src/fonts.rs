//! DTO of `listFontFamilies`, the installed font families for a `fontFamily`
//! mod setting's completion. Takes no params.

use serde::{Deserialize, Serialize};

/// Result of `listFontFamilies`: family names as a font picker shows them
/// (`Segoe UI`, `Consolas`): deduplicated, sorted case-insensitively, without
/// the `@`-prefixed vertical variants.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, Default)]
#[serde(rename_all = "camelCase")]
pub struct ListFontFamiliesResult {
    pub families: Vec<String>,
}
