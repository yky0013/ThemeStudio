//! Resolution of the `$showIf` / `$hideIf` conditions, on the typed tree: each
//! reference the mod wrote relative to its item is rewritten to the named
//! setting's absolute declaration path, checked against that setting, and the
//! dependencies are checked for cycles. Runs after transform because a
//! reference can name any setting of the block, declared before or after the
//! item, and what it names is known only once the whole tree is typed.
//!
//! A reference resolves lexically: its first segment is looked up in the
//! annotated item's own list - the group it sits in, or the template row of
//! the object array it sits in, which is the schema of every row - then in
//! each enclosing list out to the root, and the first list declaring it wins;
//! further segments descend through groups. The declaration path it resolves
//! to carries no array subscripts (`rows.action` beside `rows[2].args`): every
//! array on the path encloses the annotated item, so the editor puts the
//! item's own subscripts back.

use std::collections::HashMap;

use crate::model::{Condition, SettingItem, SettingValue};

pub(super) fn resolve_conditions(items: &mut [SettingItem]) -> Result<(), String> {
    let mut index = Index::default();
    index.add_list(items, "", "", "", None);
    resolve_list(items, "", &mut index)?;
    index.reject_cycles()
}

fn resolve_list(
    items: &mut [SettingItem],
    flat_prefix: &str,
    index: &mut Index,
) -> Result<(), String> {
    for item in items {
        let flat = join(flat_prefix, &item.key);
        let id = index.by_flat[&flat];
        for (key, conditions) in [
            ("$showIf", &mut item.show_if),
            ("$hideIf", &mut item.hide_if),
        ] {
            let Some(conditions) = conditions else {
                continue;
            };
            let mut named = Vec::new();
            for condition in conditions.iter_mut() {
                let target = index.resolve_condition(id, key, condition)?;
                // Two references to one setting cannot both hold unless they
                // agree, and the wire carries one entry per setting.
                if named.contains(&target) {
                    return Err(format!(
                        "{flat}.{key} names '{}' more than once",
                        index.entries[target].decl
                    ));
                }
                named.push(target);
                index.entries[id].edges.push((target, Some(key)));
                condition.path = index.entries[target].decl.clone();
            }
        }
        match &mut item.value {
            SettingValue::Settings(inner) => resolve_list(inner, &flat, index)?,
            SettingValue::SettingsArray(rows) => {
                for (i, row) in rows.iter_mut().enumerate() {
                    resolve_list(row, &format!("{flat}[{i}]"), index)?;
                }
            }
            _ => {}
        }
    }
    Ok(())
}

/// One setting of the block. Keyed by its flat path with subscripts, the one
/// key unique per item: a declaration path is shared by every row of an
/// object array.
struct Entry {
    flat: String,
    /// The declaration path: `flat` with every subscript removed.
    decl: String,
    /// The flat prefix of the list the item's references resolve in: the list
    /// it sits in, with every subscript on the way set to the template row.
    scope: String,
    shape: Shape,
    /// The settings the item depends on, each with the annotation key naming
    /// it: first the group or the array the item sits in, with no key - an
    /// item is visible only while its parent is - then those its conditions
    /// name.
    edges: Vec<(usize, Option<&'static str>)>,
}

enum Shape {
    Bool,
    Number,
    /// `options` holds the declared values a condition value must be one of:
    /// static `$options` without `$dynamicSelect`, whose values are only known
    /// at runtime.
    String {
        options: Option<Vec<String>>,
    },
    /// A `$float` number or a value array: a leaf with no one value to compare.
    Other,
    Group,
    Array,
}

impl Shape {
    fn of(item: &SettingItem) -> Shape {
        match &item.value {
            _ if item.float => Shape::Other,
            SettingValue::Bool(_) => Shape::Bool,
            SettingValue::Number(_) => Shape::Number,
            SettingValue::String(_) => Shape::String {
                options: if item.dynamic_select {
                    None
                } else {
                    item.options
                        .as_ref()
                        .map(|options| options.iter().map(|(value, _)| value.clone()).collect())
                },
            },
            SettingValue::NumberArray(_) | SettingValue::StringArray(_) => Shape::Other,
            SettingValue::Settings(_) => Shape::Group,
            SettingValue::SettingsArray(_) => Shape::Array,
        }
    }
}

/// Why a reference names no setting an item may depend on.
enum Unresolved {
    NotInScope,
    /// The path descends into an object array: there is no row an item outside
    /// it could mean, and an item inside reaches its row's siblings directly.
    InsideArray,
}

#[derive(Default)]
struct Index {
    entries: Vec<Entry>,
    by_flat: HashMap<String, usize>,
}

impl Index {
    fn add_list(
        &mut self,
        items: &[SettingItem],
        decl_prefix: &str,
        flat_prefix: &str,
        scope_prefix: &str,
        parent: Option<usize>,
    ) {
        for item in items {
            let decl = join(decl_prefix, &item.key);
            let flat = join(flat_prefix, &item.key);
            let template = join(scope_prefix, &item.key);
            let id = self.entries.len();
            self.by_flat.insert(flat.clone(), id);
            self.entries.push(Entry {
                flat: flat.clone(),
                decl: decl.clone(),
                scope: scope_prefix.to_owned(),
                shape: Shape::of(item),
                edges: parent.into_iter().map(|parent| (parent, None)).collect(),
            });
            match &item.value {
                SettingValue::Settings(inner) => {
                    self.add_list(inner, &decl, &flat, &template, Some(id));
                }
                SettingValue::SettingsArray(rows) => {
                    let template = format!("{template}[0]");
                    for (i, row) in rows.iter().enumerate() {
                        self.add_list(row, &decl, &format!("{flat}[{i}]"), &template, Some(id));
                    }
                }
                _ => {}
            }
        }
    }

    /// The setting `reference` names from the item `from`. The scope chain of
    /// an item is the chain of its enclosing lists, each named by the flat
    /// prefix its items share; the setting found is a template-row one
    /// wherever an object array encloses it.
    fn resolve(&self, from: usize, reference: &str) -> Result<usize, Unresolved> {
        let mut segments = reference.split('.');
        let first = segments.next().unwrap_or_default();
        let mut scope = self.entries[from].scope.clone();
        let mut id = loop {
            if let Some(&id) = self.by_flat.get(&join(&scope, first)) {
                break id;
            }
            scope = enclosing_list_prefix(&scope).ok_or(Unresolved::NotInScope)?;
        };
        for segment in segments {
            id = match self.entries[id].shape {
                Shape::Group => *self
                    .by_flat
                    .get(&join(&self.entries[id].flat, segment))
                    .ok_or(Unresolved::NotInScope)?,
                Shape::Array => return Err(Unresolved::InsideArray),
                _ => return Err(Unresolved::NotInScope),
            };
        }
        Ok(id)
    }

    /// Resolve one condition of the item `from` under the annotation `key` and
    /// check it: the reference names a setting in scope that is neither the
    /// item's declaration nor under it and holds one comparable value, and
    /// every condition value is of that setting's kind and, under static
    /// `$options`, one of them. Every message is at the annotated item.
    fn resolve_condition(
        &self,
        from: usize,
        key: &str,
        condition: &Condition,
    ) -> Result<usize, String> {
        let at = format!("{}.{key}", self.entries[from].flat);
        let reference = &condition.path;
        let target = match self.resolve(from, reference) {
            Ok(target) => target,
            Err(Unresolved::NotInScope) => {
                return Err(format!(
                    "{at} refers to '{reference}', which is not a setting in scope"
                ));
            }
            Err(Unresolved::InsideArray) => {
                return Err(format!(
                    "{at} refers to '{reference}', which is inside an array"
                ));
            }
        };
        let entry = &self.entries[target];
        if entry.decl == self.entries[from].decl {
            return Err(format!("{at} refers to itself"));
        }
        // A group hiding its own member would hide the switch that shows the
        // group again.
        if entry
            .decl
            .starts_with(&format!("{}.", self.entries[from].decl))
        {
            return Err(format!("{at} refers to a setting under it"));
        }
        let kind = match entry.shape {
            Shape::Bool => "a boolean",
            Shape::Number => "an integer",
            Shape::String { .. } => "a string",
            Shape::Other | Shape::Group | Shape::Array => {
                return Err(format!(
                    "{at} refers to '{reference}', which must be a boolean, number or string setting"
                ));
            }
        };
        for value in &condition.values {
            match (&entry.shape, value) {
                (Shape::Bool, SettingValue::Bool(_))
                | (Shape::Number, SettingValue::Number(_))
                | (Shape::String { options: None }, SettingValue::String(_)) => {}
                (
                    Shape::String {
                        options: Some(options),
                    },
                    SettingValue::String(s),
                ) => {
                    if !options.contains(s) {
                        return Err(format!(
                            "{at} value '{s}' for '{reference}' is not one of its $options"
                        ));
                    }
                }
                _ => return Err(format!("{at} value for '{reference}' must be {kind}")),
            }
        }
        Ok(target)
    }

    /// Reject a cycle among the dependencies. The editor evaluates an item's
    /// visibility through the settings it names and through its parent, and a
    /// cycle would leave that no base case. Reported at a condition on the
    /// cycle: the parent edges alone form a tree, so every cycle has one.
    /// The walk keeps its own stack: a chain of dependencies is as long as
    /// the block has items, not as deep as it nests.
    fn reject_cycles(&self) -> Result<(), String> {
        let mut marks = vec![Mark::New; self.entries.len()];
        let mut path: Vec<Frame> = Vec::new();
        for start in 0..self.entries.len() {
            if marks[start] != Mark::New {
                continue;
            }
            marks[start] = Mark::Open;
            path.push(Frame::new(start, None));
            while let Some(frame) = path.last_mut() {
                let Some(&(next, via)) = self.entries[frame.id].edges.get(frame.taken) else {
                    marks[frame.id] = Mark::Done;
                    path.pop();
                    continue;
                };
                frame.taken += 1;
                match marks[next] {
                    Mark::Done => {}
                    Mark::New => {
                        marks[next] = Mark::Open;
                        path.push(Frame::new(next, via));
                    }
                    Mark::Open => return Err(self.cycle_message(&path, next, via)),
                }
            }
        }
        Ok(())
    }

    /// The cycle closed by an edge from the last frame of `path` back to
    /// `back_to`, reported at its first condition edge.
    fn cycle_message(&self, path: &[Frame], back_to: usize, via: Option<&'static str>) -> String {
        let start = path
            .iter()
            .position(|frame| frame.id == back_to)
            .unwrap_or(0);
        let cycle = &path[start..];
        let steps = cycle
            .windows(2)
            .map(|pair| (pair[0].id, pair[1].id, pair[1].via))
            .chain(std::iter::once((cycle[cycle.len() - 1].id, back_to, via)));
        for (from, to, via) in steps {
            if let Some(key) = via {
                return format!(
                    "{}.{key} forms a cycle through '{}'",
                    self.entries[from].flat, self.entries[to].flat
                );
            }
        }
        // Unreachable: the parent edges alone form a tree.
        format!("{} forms a cycle", self.entries[back_to].flat)
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Mark {
    New,
    Open,
    Done,
}

/// One entry on the walk's path from the start entry down, with the
/// annotation key of the edge it was entered through (none for a parent edge
/// or the start) and how many of its edges the walk has taken.
struct Frame {
    id: usize,
    via: Option<&'static str>,
    taken: usize,
}

impl Frame {
    fn new(id: usize, via: Option<&'static str>) -> Frame {
        Frame { id, via, taken: 0 }
    }
}

fn join(prefix: &str, key: &str) -> String {
    if prefix.is_empty() {
        key.to_owned()
    } else {
        format!("{prefix}.{key}")
    }
}

/// The flat prefix of the list an item sits in: its own flat path minus its
/// key. Keys hold no `.`, so the last segment is the key.
fn list_prefix(flat: &str) -> &str {
    flat.rsplit_once('.').map_or("", |(prefix, _)| prefix)
}

/// The flat prefix of the list enclosing the list `scope` names: past a
/// group, the list holding the group; past an object-array row (`rows[0]`),
/// the list holding the array. None past the root.
fn enclosing_list_prefix(scope: &str) -> Option<String> {
    if scope.is_empty() {
        return None;
    }
    let item = scope
        .strip_suffix(']')
        .and_then(|row| row.rfind('[').map(|at| &row[..at]))
        .unwrap_or(scope);
    Some(list_prefix(item).to_owned())
}
