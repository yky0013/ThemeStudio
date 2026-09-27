//! Domain models for mod source parsing. Shapes deliberately mirror the
//! contract DTOs, but the types are distinct: the protocol crate is
//! self-contained and conversions live in the application crate.
//!
//! Beside `$name`/`$description`/`$options`, a settings item carries seven
//! annotations that ride on the item rather than on the value: `$format` (an
//! opaque display hint the front-end interprets), `$float` and
//! `$dynamicSelect` (booleans), `$min` / `$max` (bounds on a number item,
//! forwarded as numbers), and `$showIf` / `$hideIf` (the settings the item's
//! visibility depends on, forwarded with each reference resolved to the named
//! setting's absolute declaration path). There is no `SettingValue::Float`: a `$float`
//! number is parsed into its canonical decimal text and held as a `String`
//! (or `StringArray`) with the item's `float` flag set, so every consumer that
//! matches over the value kinds - the engine flattener, the flat-key resolver,
//! the export canonicalizer, the CLI's leaf typing - sees a string setting and
//! needs no float arm. The engine store has no floating-point type either; a
//! mod reads the text back with `Wh_GetStringSetting`.

/// A metadata-parse failure (the `extract_metadata` producer), surfaced in
/// `ParsedModSource.errors.metadata`. The message is PRIVATE - read it via
/// `Display`/`to_string()`, not a public field (the producer split that removes
/// the old `ModSourceError(pub String)` `.0` access). No consumer branches on
/// the failure class, so this is a thin newtype, not a taxonomy.
#[derive(thiserror::Error, Debug, Clone, PartialEq, Eq)]
#[error("{0}")]
pub struct MetadataError(String);

impl MetadataError {
    pub(crate) fn new(message: impl Into<String>) -> Self {
        Self(message.into())
    }
}

/// An initial-settings parse failure (the `extract_initial_settings` /
/// `extract_initial_settings_for_engine` producers), surfaced in
/// `ParsedModSource.errors.initialSettings`. Like `MetadataError`, the message
/// is PRIVATE - read via `Display`/`to_string()`. Split from `MetadataError` by
/// producer so a metadata error cannot be misclassified as a settings error;
/// neither is a per-message taxonomy (nothing branches on the class).
///
/// `Display` owns the `Failed to parse settings: ` prefix and the stored message
/// is the bare cause, so the prefix appears exactly once however the error
/// reaches a caller: every producer is labeled without repeating itself, and a
/// consumer that adds the label too would double it.
#[derive(thiserror::Error, Debug, Clone, PartialEq, Eq)]
#[error("Failed to parse settings: {0}")]
pub struct SettingsParseError(String);

impl SettingsParseError {
    pub(crate) fn new(message: impl Into<String>) -> Self {
        Self(message.into())
    }
}

/// Parsed metadata block. Every field optional, matching `ModMetadata` of the
/// TypeScript implementation's `src/services/types.ts`.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct ModMetadata {
    pub id: Option<String>,
    pub version: Option<String>,
    pub github: Option<String>,
    pub twitter: Option<String>,
    pub homepage: Option<String>,
    pub compiler_options: Option<String>,
    pub license: Option<String>,
    pub donate_url: Option<String>,
    pub name: Option<String>,
    pub description: Option<String>,
    pub author: Option<String>,
    pub include: Option<Vec<String>>,
    pub exclude: Option<Vec<String>>,
    pub architecture: Option<Vec<String>>,
}

/// One item of the initial-settings tree, after language selection of the
/// `$name`/`$description`/`$options` annotations.
#[derive(Debug, Clone, PartialEq)]
pub struct SettingItem {
    pub key: String,
    pub value: SettingValue,
    pub name: Option<String>,
    pub description: Option<String>,
    /// Display options in declaration order; each entry is the single
    /// `{value: label}` pair of the YAML option object.
    pub options: Option<Vec<(String, String)>>,
    /// `$format`: an opaque display hint forwarded to the front-end, never
    /// interpreted here.
    pub format: Option<String>,
    /// `$float`: the value is a decimal held as a string.
    pub float: bool,
    /// `$dynamicSelect`: the mod supplies options at runtime.
    pub dynamic_select: bool,
    /// `$min` / `$max`: bounds on a number item (integer or `$float`), each
    /// holding its literal in its own kind. The editor and the CLI enforce
    /// them; a stored value outside them is not rejected on read.
    pub min: Option<serde_json::Number>,
    pub max: Option<serde_json::Number>,
    /// `$showIf` / `$hideIf`: the item is shown when every `show_if` entry
    /// holds and no `hide_if` entry does. An editor hint only: a hidden setting
    /// is stored, saved and read like any other.
    pub show_if: Option<Vec<Condition>>,
    pub hide_if: Option<Vec<Condition>>,
}

/// One entry of a `$showIf` / `$hideIf` map: a setting and the values under
/// which the entry holds (any of them). `path` is the named setting's absolute
/// declaration path - dotted, with no array subscripts (`group.enabled`,
/// `rows.action`) - once `settings::conditions` has resolved the relative
/// reference the mod wrote; `values` are scalar variants only, each of the
/// named setting's own kind.
#[derive(Debug, Clone, PartialEq)]
pub struct Condition {
    pub path: String,
    pub values: Vec<SettingValue>,
}

/// A setting value (dropped the unrepresentable `Null`: validation rejects the
/// null and out-of-range leaves it was meant for, and a float is either
/// rejected or, under `$float`, held as a `String`, so it was never
/// constructed).
#[derive(Debug, Clone, PartialEq)]
pub enum SettingValue {
    Bool(bool),
    Number(serde_json::Number),
    String(String),
    NumberArray(Vec<serde_json::Number>),
    StringArray(Vec<String>),
    Settings(Vec<SettingItem>),
    SettingsArray(Vec<Vec<SettingItem>>),
}

/// A flattened engine setting value (the leaf type the engine settings store
/// holds): a 32-bit integer or a string. The `extractInitialSettingsForEngine`
/// flattening turns the structured settings tree into a flat name->value map of
/// these (booleans become 0/1, the same way the TS does); the install flow
/// migrates and writes them as the mod's initial `[Settings]`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EngineSettingValue {
    Int(i32),
    Str(String),
}
