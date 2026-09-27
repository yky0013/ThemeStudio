//! The `windhawk://` URL scheme: what a link the registered handler launched
//! this executable with asks for, parsed out of an argv and handed to the page.
//!
//! One route, `windhawk://mods/<id>`, opens `<id>` in the online mods browser.
//! The scheme is matched case-insensitively (Windows and browsers normalize it
//! inconsistently); the path as-is, since ids are lower-case by grammar. A
//! trailing `/`, a `?query`, and a `#fragment` after the id are accepted and
//! ignored, so a newer link still lands an older app on the mod. Everything
//! else - the bare `windhawk://`, another path, a malformed id - is `None`, and a
//! launch carrying it behaves as a bare launch: the window is shown, nothing is
//! navigated, nothing is reported. A malformed link is not something the user
//! can act on, and a dialog would be a way for a web page to make the app say
//! things.
//!
//! A link changes which page the window opens on and nothing else: no install,
//! enable, update, remove, settings write, or request happens because of one.
//! The id is grammar-checked and length-capped before it is used at all, and it
//! reaches the page JSON-encoded on both delivery paths - the cold start's
//! [`init_script`] global, read before the front-end creates its router, and the
//! [`EVENT`] the single-instance callback emits for a link forwarded to the
//! running instance (`run` in `lib.rs`).

use std::ffi::OsStr;

use serde::Serialize;

/// The Tauri event a link forwarded to the running instance is emitted on; the
/// payload is the serialized [`DeepLink`].
pub const EVENT: &str = "wh-deep-link";

/// The global the cold-start [`init_script`] sets, holding the serialized
/// [`DeepLink`] for the front-end to take before it creates its router.
const GLOBAL: &str = "__WINDHAWK_DEEP_LINK__";

/// The scheme prefix, compared case-insensitively.
const SCHEME: &str = "windhawk://";

/// The one route's leading segment, compared as-is.
const MODS_SEGMENT: &str = "mods/";

/// The longest id a link may carry, in bytes. The grammar has no cap of its own;
/// this one bounds what an arbitrary web page can push into the process.
const MAX_ID_LEN: usize = 128;

/// What a `windhawk://` link asks for. Serialized as `{"kind":"mod","modId":..}`,
/// the one shape both delivery paths carry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "camelCase")]
pub enum DeepLink {
    /// Open `mod_id` in the online mods browser.
    #[serde(rename = "mod")]
    Mod {
        #[serde(rename = "modId")]
        mod_id: String,
    },
}

/// The link in an argv, if any: the first argument that parses.
pub fn from_args<'a>(args: impl IntoIterator<Item = &'a str>) -> Option<DeepLink> {
    args.into_iter().find_map(parse)
}

/// [`from_args`] over the arguments as the OS hands them, converted lossily.
/// `std::env::args` panics on an argument that is not valid Unicode, and the
/// command line is the one input here a web page shapes (through the registered
/// handler). The grammar is ASCII, so the conversion changes nothing for a
/// well-formed link.
pub fn from_os_args<S: AsRef<OsStr>>(args: impl IntoIterator<Item = S>) -> Option<DeepLink> {
    args.into_iter()
        .find_map(|arg| parse(&arg.as_ref().to_string_lossy()))
}

/// Parse one `windhawk://` URL; `None` for the bare form and for anything that
/// is not a well-formed mod link (the module docs give the grammar).
pub fn parse(url: &str) -> Option<DeepLink> {
    let (scheme, path) = url.split_at_checked(SCHEME.len())?;
    if !scheme.eq_ignore_ascii_case(SCHEME) {
        return None;
    }
    let rest = path.strip_prefix(MODS_SEGMENT)?;
    // The id runs to the first `/`, `?`, or `#`. Past it, one `/` may precede a
    // query or a fragment, and both are ignored; any other continuation is
    // another path.
    let end = rest.find(['/', '?', '#']).unwrap_or(rest.len());
    let (id, tail) = rest.split_at(end);
    let tail = tail.strip_prefix('/').unwrap_or(tail);
    if !(tail.is_empty() || tail.starts_with(['?', '#'])) {
        return None;
    }
    is_valid_mod_id(id).then(|| DeepLink::Mod {
        mod_id: id.to_owned(),
    })
}

/// `ModId::str_is_valid_bare` from the `domain` crate, restated: non-empty and
/// drawn only from `0-9`, `a-z`, and `-`. This crate does not depend on
/// `domain`, so the predicate is mirrored rather than imported. The length cap
/// is this module's own ([`MAX_ID_LEN`]).
fn is_valid_mod_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= MAX_ID_LEN
        && id.chars().all(|c| matches!(c, '0'..='9' | 'a'..='z' | '-'))
}

/// The initialization script that publishes `link` as `window.__WINDHAWK_DEEP_LINK__`
/// before the front-end bundle runs. The value is serialized, never formatted
/// in, so the script is a literal whatever the link holds.
pub fn init_script(link: &DeepLink) -> String {
    match serde_json::to_string(link) {
        Ok(json) => format!("window.{GLOBAL}={json};"),
        // Unreachable for an enum of strings; an empty script leaves the page on
        // its usual first route rather than on a broken statement.
        Err(_) => String::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn mod_link(id: &str) -> Option<DeepLink> {
        Some(DeepLink::Mod {
            mod_id: id.to_owned(),
        })
    }

    #[test]
    fn a_mod_link_parses_to_its_id() {
        assert_eq!(
            parse("windhawk://mods/taskbar-clock-customization"),
            mod_link("taskbar-clock-customization")
        );
        // The domain grammar allows a hyphen anywhere, ends included.
        assert_eq!(parse("windhawk://mods/-x-"), mod_link("-x-"));
        assert_eq!(parse("windhawk://mods/0"), mod_link("0"));
    }

    // Windows and browsers normalize the scheme's case inconsistently, so it is
    // matched either way; the path is the id's own grammar, which is lower-case.
    #[test]
    fn the_scheme_is_case_insensitive_and_the_path_is_not() {
        assert_eq!(parse("WINDHAWK://mods/x"), mod_link("x"));
        assert_eq!(parse("WindHawk://mods/x"), mod_link("x"));

        assert_eq!(parse("windhawk://MODS/x"), None);
        assert_eq!(parse("windhawk://Mods/x"), None);
        assert_eq!(parse("windhawk://mods/X"), None);
    }

    // The forward-compatibility rule: a newer link may carry a trailing slash, a
    // query, or a fragment an older app does not know, and still lands on the mod.
    #[test]
    fn a_trailing_slash_a_query_and_a_fragment_are_ignored() {
        assert_eq!(parse("windhawk://mods/x/"), mod_link("x"));
        assert_eq!(parse("windhawk://mods/x?version=1.0"), mod_link("x"));
        assert_eq!(parse("windhawk://mods/x?"), mod_link("x"));
        assert_eq!(parse("windhawk://mods/x#top"), mod_link("x"));
        assert_eq!(parse("windhawk://mods/x?a=1&b=2#top"), mod_link("x"));
        assert_eq!(parse("windhawk://mods/x/?a=1"), mod_link("x"));
        assert_eq!(parse("windhawk://mods/x/#top"), mod_link("x"));
        assert_eq!(parse("windhawk://mods/x/?a=1#top"), mod_link("x"));
        // Whatever follows the cut is not looked at.
        assert_eq!(parse("windhawk://mods/x?id=../Y"), mod_link("x"));
    }

    #[test]
    fn an_empty_id_is_not_a_link() {
        assert_eq!(parse("windhawk://mods/"), None);
        assert_eq!(parse("windhawk://mods//"), None);
        assert_eq!(parse("windhawk://mods/?a=1"), None);
        assert_eq!(parse("windhawk://mods/#top"), None);
    }

    // The id is the domain charset and nothing else: no separators, no escapes,
    // no dots, nothing that could be read as a path once it is used as one.
    #[test]
    fn an_id_outside_the_grammar_is_not_a_link() {
        for url in [
            "windhawk://mods/x_y",
            "windhawk://mods/x y",
            "windhawk://mods/x%20y",
            "windhawk://mods/x.y",
            "windhawk://mods/../",
            "windhawk://mods/../x",
            "windhawk://mods/..",
            "windhawk://mods/x\"y",
            "windhawk://mods/x\\y",
            "windhawk://mods/\u{e9}",
            "windhawk://mods/x\u{0}",
        ] {
            assert_eq!(parse(url), None, "{url:?}");
        }
    }

    #[test]
    fn the_id_is_capped_at_128_bytes() {
        let longest = "a".repeat(128);
        assert_eq!(
            parse(&format!("windhawk://mods/{longest}")),
            mod_link(&longest)
        );

        let over = "a".repeat(129);
        assert_eq!(parse(&format!("windhawk://mods/{over}")), None);
        let far_over = "a".repeat(200);
        assert_eq!(parse(&format!("windhawk://mods/{far_over}")), None);
    }

    // Everything that is not the one route is the bare form: the empty link, the
    // segment without an id, a route this app does not have, and a continuation
    // past the id that is not a query or a fragment.
    #[test]
    fn the_bare_form_and_other_paths_are_not_links() {
        for url in [
            "windhawk://",
            "windhawk:///",
            "windhawk://mods",
            "windhawk://settings",
            "windhawk://settings/",
            "windhawk://mod/x",
            "windhawk://modsx",
            "windhawk://mods/x/y",
            "windhawk://mods/x//",
            "windhawk://mods/x/y?a=1",
            "windhawk://x/mods/x",
        ] {
            assert_eq!(parse(url), None, "{url:?}");
        }
    }

    #[test]
    fn a_non_url_argument_is_not_a_link() {
        for arg in [
            "",
            "-",
            "--runtime-broker",
            "mods/x",
            "windhawk",
            "windhawk:",
            "windhawk:/",
            "windhawk:mods/x",
            "windhawk:/mods/x",
            "windhawk//mods/x",
            "https://windhawk.net/mods/x",
            "http://windhawk.net/mods/x",
            r"C:\Program Files\Windhawk\windhawk-ui.exe",
            // A multi-byte character straddling where the scheme would end.
            "windhawk:/\u{e9}mods/x",
        ] {
            assert_eq!(parse(arg), None, "{arg:?}");
        }
    }

    // The launcher may put other arguments first, and a link among several is
    // the first that parses; arguments that parse as nothing are skipped over.
    #[test]
    fn from_args_takes_the_first_argument_that_parses() {
        let args = [
            "--flag",
            "windhawk://settings",
            "windhawk://mods/first",
            "windhawk://mods/second",
        ];
        assert_eq!(from_args(args), mod_link("first"));

        assert_eq!(from_args(["windhawk://mods/x"]), mod_link("x"));
        assert_eq!(from_args(["--flag", "windhawk://"]), None);
        assert_eq!(from_args([]), None);
    }

    // An argument that is not Unicode - an unpaired UTF-16 surrogate on Windows -
    // must not end the process; it is not a link either way.
    #[test]
    fn from_os_args_survives_an_argument_that_is_not_unicode() {
        use std::ffi::OsString;
        use std::os::windows::ffi::OsStringExt;

        let broken = OsString::from_wide(&[0x77, 0x69, 0xD800, 0x6E]);
        let link = OsString::from("windhawk://mods/x");
        assert_eq!(from_os_args([broken.clone(), link.clone()]), mod_link("x"));
        assert_eq!(from_os_args([link, broken.clone()]), mod_link("x"));
        assert_eq!(from_os_args([broken]), None);
        assert_eq!(from_os_args(Vec::<OsString>::new()), None);
    }

    // The one shape both delivery paths carry, and what the front-end's
    // takeInitialDeepLink / listenDeepLink read.
    #[test]
    fn a_link_serializes_as_kind_and_mod_id() {
        let link = DeepLink::Mod {
            mod_id: "taskbar-clock-customization".to_owned(),
        };
        assert_eq!(
            serde_json::to_value(&link).unwrap(),
            json!({ "kind": "mod", "modId": "taskbar-clock-customization" })
        );
    }

    #[test]
    fn the_init_script_sets_the_global_to_the_serialized_link() {
        let link = DeepLink::Mod {
            mod_id: "taskbar-clock-customization".to_owned(),
        };
        assert_eq!(
            init_script(&link),
            r#"window.__WINDHAWK_DEEP_LINK__={"kind":"mod","modId":"taskbar-clock-customization"};"#
        );
    }
}
