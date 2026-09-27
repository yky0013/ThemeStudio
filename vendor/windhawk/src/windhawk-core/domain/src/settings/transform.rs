//! The YAML -> typed-tree transformer: `parseSettings` /
//! `parseSettingsValueAnnotated` / `parseSettingsValue` of the TS
//! implementation. Runs on schema-validated input (the `validate` pass ran
//! first), so the YAML shapes are known and this pass relies on that.

use yaml_rust2::Yaml;

use super::{float_literal, number_in_text, parse_annotation_key, scalar_key_to_string};
use crate::language::best_language_match;
use crate::model::{Condition, SettingItem, SettingValue, SettingsParseError};

pub(super) fn parse_settings(
    items: &[Yaml],
    language: &str,
) -> Result<Vec<SettingItem>, SettingsParseError> {
    items
        .iter()
        .map(|item| parse_item_annotated(item, language))
        .collect()
}

fn parse_item_annotated(item: &Yaml, language: &str) -> Result<SettingItem, SettingsParseError> {
    let Yaml::Hash(map) = item else {
        // Schema validation guarantees a mapping.
        return Err(SettingsParseError::new("Missing settings key"));
    };

    let entries: Vec<(String, &Yaml)> = map
        .iter()
        .map(|(k, v)| (scalar_key_to_string(k), v))
        .collect();

    let actual: Vec<&(String, &Yaml)> = entries
        .iter()
        .filter(|(k, _)| !k.starts_with('$'))
        .collect();
    if actual.is_empty() {
        return Err(SettingsParseError::new("Missing settings key"));
    }
    if actual.len() > 1 {
        return Err(SettingsParseError::new("More than one settings key"));
    }
    let (actual_key, actual_value) = actual[0];

    // Group `$param[:lang]` annotations by base name, in first-seen order. The
    // `$base[:lang]` split is the shared `super::parse_annotation_key`.
    type Candidates<'a> = Vec<(Option<String>, &'a Yaml)>;
    let mut groups: Vec<(&str, Candidates)> = Vec::new();
    for (key, value) in &entries {
        let Some((base, lang)) = parse_annotation_key(key) else {
            continue;
        };
        let lang = lang.map(str::to_owned);
        match groups.iter_mut().find(|(b, _)| *b == base) {
            Some((_, candidates)) => candidates.push((lang, *value)),
            None => groups.push((base, vec![(lang, *value)])),
        }
    }

    let mut name = None;
    let mut description = None;
    let mut options = None;
    let mut format = None;
    let mut float = false;
    let mut dynamic_select = false;
    let mut min = None;
    let mut max = None;
    let mut show_if = None;
    let mut hide_if = None;
    for (base, candidates) in groups {
        // `$format`/`$float`/`$dynamicSelect`/`$min`/`$max`/`$showIf`/`$hideIf`
        // take no language suffix, so their group holds the one neutral
        // candidate and the match returns it.
        let chosen = *best_language_match(language, &candidates);
        match base {
            "name" => name = yaml_string(chosen),
            "description" => description = yaml_string(chosen),
            "options" => options = Some(options_pairs(chosen)),
            "format" => format = yaml_string(chosen),
            "float" => float = matches!(chosen, Yaml::Boolean(true)),
            "dynamicSelect" => dynamic_select = matches!(chosen, Yaml::Boolean(true)),
            "min" => min = bound_number(chosen),
            "max" => max = bound_number(chosen),
            "showIf" => show_if = Some(conditions(chosen)),
            "hideIf" => hide_if = Some(conditions(chosen)),
            // Schema validation restricts annotations to the ten above and
            // the ignored `$_`-prefixed keys.
            _ => {}
        }
    }

    Ok(SettingItem {
        key: actual_key.clone(),
        value: parse_value(actual_value, language, float)?,
        name,
        description,
        options,
        format,
        float,
        dynamic_select,
        min,
        max,
        show_if,
        hide_if,
    })
}

fn yaml_string(value: &Yaml) -> Option<String> {
    match value {
        Yaml::String(s) => Some(s.clone()),
        _ => None,
    }
}

/// The text a `$float` number is stored as: the shortest decimal that
/// round-trips the value, in positional notation whatever its magnitude
/// (`0.85`, `1.0` -> `1`, `1e3` -> `1000`, `1e21` -> `1000000000000000000000`).
/// JavaScript's `String(number)` spells the same digits, switching to exponent
/// form only past its positional range, and the front-end compares `$float`
/// values as numbers, so a value it writes back untouched still reads as the
/// same one. An integer literal keeps its own decimal text rather than a lossy
/// trip through `f64`. A string default is the node its text resolves to, so
/// `"1.0"` and `1.0` produce one item. Validation accepted the literal through
/// the same `float_literal` and `number_in_text`, so `None` is unreachable in
/// practice.
fn canonical_float_text(value: &Yaml) -> Result<String, SettingsParseError> {
    match value {
        Yaml::Integer(i) => Ok(i.to_string()),
        Yaml::String(text) => match number_in_text(text) {
            Some(node) => canonical_float_text(&node),
            None => Err(SettingsParseError::new("unsupported value type")),
        },
        _ => float_literal(value)
            .map(|v| v.to_string())
            .ok_or_else(|| SettingsParseError::new("unsupported value type")),
    }
}

/// The number a `$min` / `$max` literal denotes, in its own kind: an integer
/// as itself, a real through `float_literal` (finite, by validation).
fn bound_number(value: &Yaml) -> Option<serde_json::Number> {
    match value {
        Yaml::Integer(i) => Some((*i).into()),
        _ => float_literal(value).and_then(serde_json::Number::from_f64),
    }
}

/// The entries of a `$showIf` / `$hideIf` map as the mod wrote them: each
/// reference still relative to the item (`conditions::resolve_conditions`
/// makes it absolute once the whole tree is typed), each value or list of
/// values as a list, so a consumer sees one shape. Validation accepted the
/// shape, so a non-scalar value cannot occur and is skipped rather than
/// reported.
fn conditions(value: &Yaml) -> Vec<Condition> {
    let Yaml::Hash(map) = value else {
        return Vec::new();
    };
    map.iter()
        .map(|(key, value)| {
            let values = match value {
                Yaml::Array(items) => items.iter().filter_map(condition_value).collect(),
                _ => condition_value(value).into_iter().collect(),
            };
            Condition {
                path: scalar_key_to_string(key),
                values,
            }
        })
        .collect()
}

fn condition_value(value: &Yaml) -> Option<SettingValue> {
    match value {
        Yaml::Boolean(b) => Some(SettingValue::Bool(*b)),
        Yaml::Integer(i) => Some(SettingValue::Number((*i).into())),
        Yaml::String(s) => Some(SettingValue::String(s.clone())),
        _ => None,
    }
}

fn options_pairs(value: &Yaml) -> Vec<(String, String)> {
    let Yaml::Array(items) = value else {
        return Vec::new();
    };
    items
        .iter()
        .filter_map(|item| {
            let Yaml::Hash(map) = item else {
                return None;
            };
            map.iter()
                .next()
                .map(|(k, v)| (scalar_key_to_string(k), yaml_string(v).unwrap_or_default()))
        })
        .collect()
}

/// `float` is the item's `$float` flag: its number leaves become their
/// canonical decimal text, held as strings.
fn parse_value(
    value: &Yaml,
    language: &str,
    float: bool,
) -> Result<SettingValue, SettingsParseError> {
    match value {
        Yaml::Boolean(b) => Ok(SettingValue::Bool(*b)),
        Yaml::Integer(_) | Yaml::Real(_) | Yaml::String(_) if float => {
            Ok(SettingValue::String(canonical_float_text(value)?))
        }
        Yaml::Integer(i) => Ok(SettingValue::Number((*i).into())),
        Yaml::String(s) => Ok(SettingValue::String(s.clone())),
        Yaml::Array(items) => parse_array_value(items, language, float),
        // Validation already rejected unmarked floats, out-of-range integers,
        // and null parameter values upstream, so no other YAML shape reaches
        // here. The arm cannot be deleted (the foreign yaml-rust2 `Yaml` enum
        // forces an exhaustive match), so it is an explicit Err rather than a
        // silent dead `Null` value (drops the unrepresentable
        // `SettingValue::Null`).
        _ => Err(SettingsParseError::new("unsupported value type")),
    }
}

/// The kind of a settings-array's elements. The `validate` pass classifies by
/// WHOLE-array homogeneity and ENFORCES it; this transform-side classifier
/// reads only the FIRST element, which is sound ONLY because validation runs
/// first and guarantees the array is homogeneous. The two share this kind
/// CONCEPT, not the mechanism (validate's number test spans floats to reject
/// them without `$float`; a `Real` reaches this one only under it, and a
/// string array is a number array under it).
enum ArrayKind {
    Numbers,
    Strings,
    SettingsArrays,
    Settings,
}

impl ArrayKind {
    fn of(items: &[Yaml], float: bool) -> ArrayKind {
        match items.first() {
            Some(Yaml::Integer(_) | Yaml::Real(_)) => ArrayKind::Numbers,
            Some(Yaml::String(_)) if float => ArrayKind::Numbers,
            Some(Yaml::String(_)) => ArrayKind::Strings,
            Some(Yaml::Array(_)) => ArrayKind::SettingsArrays,
            _ => ArrayKind::Settings,
        }
    }
}

fn parse_array_value(
    items: &[Yaml],
    language: &str,
    float: bool,
) -> Result<SettingValue, SettingsParseError> {
    // Classify by the first element via the shared `ArrayKind` (the schema has
    // already enforced homogeneity, and validated every number is int32 or,
    // under `$float`, a finite number or a string holding one); the
    // per-element conversions differ by kind, so each arm keeps its own map.
    match ArrayKind::of(items, float) {
        ArrayKind::Numbers if float => Ok(SettingValue::StringArray(
            items
                .iter()
                .map(canonical_float_text)
                .collect::<Result<_, _>>()?,
        )),
        ArrayKind::Numbers => Ok(SettingValue::NumberArray(
            items
                .iter()
                .map(|v| match v {
                    Yaml::Integer(i) => Ok((*i).into()),
                    _ => Err(SettingsParseError::new("Missing settings key")),
                })
                .collect::<Result<_, _>>()?,
        )),
        ArrayKind::Strings => Ok(SettingValue::StringArray(
            items.iter().filter_map(yaml_string).collect(),
        )),
        ArrayKind::SettingsArrays => Ok(SettingValue::SettingsArray(
            items
                .iter()
                .map(|v| match v {
                    Yaml::Array(inner) => parse_settings(inner, language),
                    _ => Err(SettingsParseError::new("Missing settings key")),
                })
                .collect::<Result<_, _>>()?,
        )),
        ArrayKind::Settings => Ok(SettingValue::Settings(parse_settings(items, language)?)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_float_text_is_the_shortest_round_trip_decimal() {
        // `Yaml::from_str` is the loader's own scalar resolution, so each input
        // is the node the transformer sees for that literal.
        for (literal, text) in [
            ("0.85", "0.85"),
            ("1.0", "1"),
            ("1.50", "1.5"),
            ("1e3", "1000"),
            (".5", "0.5"),
            // Positional at both ends of the range where JavaScript would
            // switch to exponent form.
            ("1e21", "1000000000000000000000"),
            ("1e-7", "0.0000001"),
            // `-0.0` keeps its sign; `wcstod` reads it as zero either way.
            ("-0.0", "-0"),
            // An integer literal past i64 resolves as a Real (the i64 parse
            // fails, the f64 one succeeds) and renders positionally.
            ("99999999999999999999", "100000000000000000000"),
            // An integer literal keeps its own text, with no f64 round trip.
            ("9007199254740993", "9007199254740993"),
            ("-7", "-7"),
        ] {
            let node = Yaml::from_str(literal);
            assert_eq!(
                canonical_float_text(&node).unwrap(),
                text,
                "{literal} resolved as {node:?}"
            );
        }
    }
}
