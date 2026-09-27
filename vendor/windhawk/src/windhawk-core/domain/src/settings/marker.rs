//! The `#!` marker: a second spelling of the annotations that Windhawk 1.7.3
//! reads as a comment.
//!
//! Every annotation past `$name` / `$description` / `$options` is a `$` key
//! 1.7.3's parser rejects, so a block carrying one bare installs only behind
//! a `minWindhawkVersion`. A line inside the block whose content begins with
//! `#! ` is read here with those three characters removed, and by 1.7.3 - by
//! every YAML reader - as the comment it looks like, so the annotation stands
//! beside the item it annotates and the block still parses there. The rule is
//! about LINES, not keys: whatever follows the marker is YAML, judged by the
//! loader and the validator exactly as if it had been written bare, so one
//! rule covers a scalar annotation, a multi-line one, the entries of a marked
//! `$options` list and any key a later release adds.
//!
//! A marker anywhere makes the block answerable to 1.7.3. The orchestrator
//! reads the block twice - with the markers stripped (the FULL tree, what this
//! core means by the block) and as written, the marked lines left as comments
//! (the LEGACY tree, what 1.7.3 reads) - holds the legacy tree to 1.7.3's key
//! set, and requires the two readings to differ only by the annotations the
//! marker is for. The comparison is what lets the pass stay textual: it
//! strips a marked line inside a `|` / `>` block scalar like any other, and
//! the two readings of that scalar then differ and the block is rejected
//! there, so no reading of the text is silent.

use std::borrow::Cow;

use yaml_rust2::Yaml;
use yaml_rust2::yaml::Hash;

use super::validate::{annotation_flag, is_plain_param_key};
use super::{parse_annotation_key, scalar_key_to_string};

const MARKER: &str = "#!";

/// Strip the marker from every marked line: the text, borrowed when there was
/// nothing to remove, and whether anything was, which is what decides whether
/// the legacy reading runs at all. Removing exactly `#! ` leaves the content
/// at the column the `#` held, so a marked annotation is written where it
/// would stand bare with the marker in front of it. `#!` followed by anything
/// but a space or the end of the line is an error naming the line, so a typo
/// in the marker fails loudly rather than staying a comment; `#!` alone is a
/// marked empty line and stays one. Characters are removed, never lines, so
/// the loader's line numbers address the source in either reading.
pub(super) fn strip_markers(block: &str) -> Result<(Cow<'_, str>, bool), String> {
    if !block.contains(MARKER) {
        return Ok((Cow::Borrowed(block), false));
    }
    let mut out = String::with_capacity(block.len());
    let mut removed = false;
    // `split` keeps a `\r` on the line it ends, so a CRLF block keeps its
    // terminators; the marker sits after the indentation, before either.
    for (index, line) in block.split('\n').enumerate() {
        if index > 0 {
            out.push('\n');
        }
        let content = line.trim_start_matches([' ', '\t']);
        let Some(rest) = content.strip_prefix(MARKER) else {
            out.push_str(line);
            continue;
        };
        let kept = if rest.strip_suffix('\r').unwrap_or(rest).is_empty() {
            rest
        } else {
            rest.strip_prefix(' ').ok_or_else(|| {
                format!(
                    "the '#!' marker on line {} must be followed by a space",
                    index + 1
                )
            })?
        };
        out.push_str(&line[..line.len() - content.len()]);
        out.push_str(kept);
        removed = true;
    }
    if removed {
        Ok((Cow::Owned(out), true))
    } else {
        Ok((Cow::Borrowed(block), false))
    }
}

/// Reject a `$` key in the legacy tree that Windhawk 1.7.3's schema does not
/// admit. The tree is the block as written, the marked lines left as
/// comments, so such a key stands bare there and fails 1.7.3's parse however
/// the rest of the block is spelled: a marker anywhere is a statement that
/// the WHOLE block installs on 1.7.3, and this checks the statement rather
/// than letting a block mark `$format` and leave `$showIf` to fail there.
/// Runs ahead of the validator, so a shape it does not expect is passed over
/// for the validator to report.
pub(super) fn reject_non_legacy_keys(items: &[Yaml]) -> Result<(), String> {
    reject_non_legacy_keys_at(items, "instance")
}

fn reject_non_legacy_keys_at(items: &[Yaml], path: &str) -> Result<(), String> {
    for (i, item) in items.iter().enumerate() {
        let Yaml::Hash(map) = item else {
            continue;
        };
        let item_path = format!("{path}[{i}]");
        for (key, value) in map.iter() {
            let key = scalar_key_to_string(key);
            if is_plain_param_key(&key) {
                let key_path = format!("{item_path}.{key}");
                match value {
                    Yaml::Array(entries) if entries.iter().all(|e| matches!(e, Yaml::Hash(_))) => {
                        reject_non_legacy_keys_at(entries, &key_path)?;
                    }
                    Yaml::Array(entries) if entries.iter().all(|e| matches!(e, Yaml::Array(_))) => {
                        for (j, row) in entries.iter().enumerate() {
                            if let Yaml::Array(row) = row {
                                reject_non_legacy_keys_at(row, &format!("{key_path}[{j}]"))?;
                            }
                        }
                    }
                    _ => {}
                }
            } else if key.starts_with('$') && !is_legacy_annotation_key(&key) {
                return Err(format!(
                    "{item_path}.{key} is not an allowed property for Windhawk 1.7.3; \
                     mark it, or mark nothing in this block"
                ));
            }
        }
    }
    Ok(())
}

/// The `$` keys Windhawk 1.7.3's schema admits: `$name`, `$description` and
/// `$options`, with or without a language suffix.
fn is_legacy_annotation_key(key: &str) -> bool {
    matches!(
        parse_annotation_key(key),
        Some(("name" | "description" | "options", _))
    )
}

/// Walk the two readings together and reject every difference but an
/// annotation 1.7.3 rejects standing in the full tree alone. Items align by
/// their setting key at each level (unique there, by the validator), the rows
/// of an object array and the elements of a value array by position, and
/// groups recurse. Both trees have passed the validator, so every item is a
/// mapping and every array is homogeneous; an item without a setting key is
/// the transform's to reject and is not aligned.
pub(super) fn compare_readings(legacy: &[Yaml], full: &[Yaml], path: &str) -> Result<(), String> {
    for (i, item) in full.iter().enumerate() {
        let Yaml::Hash(full_map) = item else {
            continue;
        };
        let Some(key) = setting_key(full_map) else {
            continue;
        };
        let item_path = format!("{path}[{i}]");
        let Some(legacy_map) = item_by_key(legacy, &key) else {
            return Err(format!(
                "{item_path} ({key}) exists only with the markers; a settings item may not be marked"
            ));
        };
        compare_items(legacy_map, full_map, &item_path)?;
    }
    // A stripped marker only ever adds to what a line says, so an item the
    // legacy tree alone has is a re-interpretation of its neighbors.
    for (j, item) in legacy.iter().enumerate() {
        if let Some(key) = item.as_hash().and_then(setting_key)
            && item_by_key(full, &key).is_none()
        {
            return Err(reads_differently(&format!("{path}[{j}].{key}")));
        }
    }
    Ok(())
}

/// The setting key of an item: its first non-`$` key.
fn setting_key(map: &Hash) -> Option<String> {
    map.iter()
        .map(|(key, _)| scalar_key_to_string(key))
        .find(|key| is_plain_param_key(key))
}

fn item_by_key<'a>(items: &'a [Yaml], key: &str) -> Option<&'a Hash> {
    items.iter().find_map(|item| match item {
        Yaml::Hash(map) if setting_key(map).as_deref() == Some(key) => Some(map),
        _ => None,
    })
}

fn compare_items(legacy: &Hash, full: &Hash, path: &str) -> Result<(), String> {
    // `$options` may be marked beside `$dynamicSelect: true`, where 1.7.3 has
    // no runtime entries and a static list would pin the user to the few
    // declared values; hidden, the setting is a free text field there. The
    // language variants go together, or 1.7.3's language fallback would draw
    // the one variant left from the dropdown the marker meant to hide.
    let dynamic_select = annotation_flag(full, "dynamicSelect");
    let mut options_marked = false;
    let mut options_bare = false;
    for (key, value) in full.iter() {
        let name = scalar_key_to_string(key);
        let key_path = format!("{path}.{name}");
        match legacy.get(key) {
            Some(legacy_value) => {
                if is_plain_param_key(&name) {
                    compare_values(legacy_value, value, &key_path)?;
                } else if legacy_value != value {
                    return Err(reads_differently(&key_path));
                }
                if matches!(parse_annotation_key(&name), Some(("options", _))) {
                    options_bare = true;
                }
            }
            None if is_plain_param_key(&name) => {
                return Err(format!(
                    "{key_path} exists only with the markers; a settings item may not be marked"
                ));
            }
            None => match parse_annotation_key(&name) {
                Some(("name" | "description", _)) => {
                    return Err(format!(
                        "{key_path} needs no marker: Windhawk 1.7.3 accepts it"
                    ));
                }
                Some(("options", _)) if !dynamic_select => {
                    return Err(format!(
                        "{key_path} may be marked only beside $dynamicSelect: Windhawk 1.7.3 accepts $options"
                    ));
                }
                Some(("options", _)) => options_marked = true,
                // The annotations the marker is for, `$_`-prefixed keys
                // included; the validator admitted nothing else.
                _ => {}
            },
        }
    }
    if options_marked && options_bare {
        return Err(format!(
            "{path}: $options and its language variants must be marked together"
        ));
    }
    if let Some((key, _)) = legacy.iter().find(|(key, _)| !full.contains_key(key)) {
        return Err(reads_differently(&format!(
            "{path}.{}",
            scalar_key_to_string(key)
        )));
    }
    Ok(())
}

/// A setting value in both readings: a group's items and an object array's
/// rows are walked, anything else must be equal.
fn compare_values(legacy: &Yaml, full: &Yaml, path: &str) -> Result<(), String> {
    let (Yaml::Array(legacy_items), Yaml::Array(full_items)) = (legacy, full) else {
        return if legacy == full {
            Ok(())
        } else {
            Err(reads_differently(path))
        };
    };
    if full_items.iter().all(|v| matches!(v, Yaml::Hash(_))) {
        if !legacy_items.iter().all(|v| matches!(v, Yaml::Hash(_))) {
            return Err(reads_differently(path));
        }
        return compare_readings(legacy_items, full_items, path);
    }
    if full_items.iter().all(|v| matches!(v, Yaml::Array(_))) {
        if !legacy_items.iter().all(|v| matches!(v, Yaml::Array(_))) {
            return Err(reads_differently(path));
        }
        if legacy_items.len() != full_items.len() {
            return Err(format!(
                "{path} has {} rows with the markers and {} without",
                full_items.len(),
                legacy_items.len()
            ));
        }
        for (i, (legacy_row, full_row)) in legacy_items.iter().zip(full_items).enumerate() {
            if let (Yaml::Array(legacy_row), Yaml::Array(full_row)) = (legacy_row, full_row) {
                compare_readings(legacy_row, full_row, &format!("{path}[{i}]"))?;
            }
        }
        return Ok(());
    }
    if legacy_items == full_items {
        Ok(())
    } else {
        Err(reads_differently(path))
    }
}

fn reads_differently(path: &str) -> String {
    format!(
        "{path} reads differently with and without the markers; a marker may only add an annotation"
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    fn stripped(block: &str) -> (String, bool) {
        let (text, removed) = strip_markers(block).unwrap();
        (text.into_owned(), removed)
    }

    #[test]
    fn a_marked_key_loses_the_marker_and_keeps_its_column() {
        assert_eq!(
            stripped("- a: x\n  #! $format: colorRgb\n- b: 1"),
            ("- a: x\n  $format: colorRgb\n- b: 1".to_owned(), true)
        );
    }

    #[test]
    fn a_marked_map_reads_the_same_at_either_indent() {
        // The continuation's marker may sit at the item's indent or at its
        // own; the content lands at the same column either way.
        let at_item = stripped("- a: 1\n  #! $showIf:\n  #!   b: true");
        let at_own = stripped("- a: 1\n  #! $showIf:\n    #! b: true");
        assert_eq!(at_item.0, "- a: 1\n  $showIf:\n    b: true");
        assert_eq!(at_own.0, at_item.0);
    }

    #[test]
    fn a_marked_empty_line_stays_an_empty_line() {
        assert_eq!(
            stripped("- a: 1\n#!\n- b: 2"),
            ("- a: 1\n\n- b: 2".to_owned(), true)
        );
        assert_eq!(
            stripped("- a: 1\n  #!\n- b: 2"),
            ("- a: 1\n  \n- b: 2".to_owned(), true)
        );
        // With its terminator kept.
        assert_eq!(
            stripped("- a: 1\r\n#!\r\n- b: 2"),
            ("- a: 1\r\n\r\n- b: 2".to_owned(), true)
        );
    }

    #[test]
    fn crlf_lines_keep_their_terminator() {
        assert_eq!(
            stripped("- a: x\r\n  #! $format: colorRgb\r\n"),
            ("- a: x\r\n  $format: colorRgb\r\n".to_owned(), true)
        );
    }

    #[test]
    fn a_block_without_a_marker_is_borrowed_back() {
        for block in [
            "- a: x\n  $format: colorRgb",
            // A commented-out annotation, with a space after the `#`.
            "- a: x\n  # $format: colorRgb",
            // The two characters elsewhere than at the head of a line.
            "- a: 'x #! y'\n  $description: shebang #!",
        ] {
            let (text, removed) = strip_markers(block).unwrap();
            assert!(matches!(text, Cow::Borrowed(_)), "{block:?}");
            assert!(!removed, "{block:?}");
        }
    }

    #[test]
    fn a_marker_followed_by_anything_but_a_space_is_rejected_with_its_line() {
        for block in ["- a: x\n  #!$format: colorRgb", "- a: x\n  #!\t$format: x"] {
            assert_eq!(
                strip_markers(block).unwrap_err(),
                "the '#!' marker on line 2 must be followed by a space",
                "{block:?}"
            );
        }
        assert_eq!(
            strip_markers("#!x").unwrap_err(),
            "the '#!' marker on line 1 must be followed by a space"
        );
    }

    #[test]
    fn the_flag_is_set_only_when_something_was_removed() {
        assert!(!stripped("- a: 1").1);
        assert!(stripped("#! - a: 1").1);
    }
}
