#![cfg(windows)]

mod error {
    use std::{fmt, io};

    #[derive(Debug)]
    pub struct Error(String);

    impl fmt::Display for Error {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            f.write_str(&self.0)
        }
    }

    impl std::error::Error for Error {}

    impl From<&str> for Error {
        fn from(value: &str) -> Self {
            Self(value.to_owned())
        }
    }

    impl From<String> for Error {
        fn from(value: String) -> Self {
            Self(value)
        }
    }

    impl From<io::Error> for Error {
        fn from(value: io::Error) -> Self {
            Self(value.to_string())
        }
    }

    impl From<windows::core::Error> for Error {
        fn from(value: windows::core::Error) -> Self {
            Self(format!("{value:?}"))
        }
    }

    pub type Result<T = ()> = std::result::Result<T, Error>;
}

#[path = "../../../../../../vendor/runtime-sources/Seelen-UI-2.8.6/src/background/utils/start_layout.rs"]
mod start_layout;

fn main() {}

#[cfg(test)]
mod tests {
    use std::{
        fs,
        path::PathBuf,
        time::{SystemTime, UNIX_EPOCH},
    };

    use serde_json::Value;

    use super::start_layout;

    fn unique_test_dir(label: &str) -> PathBuf {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system clock must be after the Unix epoch")
            .as_nanos();
        let path = std::env::temp_dir().join(format!(
            "ThemeStudio native Start layout {label} 用户 空格 {}-{stamp}",
            std::process::id()
        ));
        fs::create_dir_all(&path).expect("test output directory must be creatable");
        path
    }

    fn pinned_list(bytes: &[u8]) -> Vec<Value> {
        let root: Value = serde_json::from_slice(bytes).expect("export must be valid JSON");
        root.get("pinnedList")
            .and_then(Value::as_array)
            .cloned()
            .expect("export must contain a pinnedList array")
    }

    fn reference_path() -> PathBuf {
        std::env::var_os("NATIVE_START_LAYOUT_REFERENCE")
            .map(PathBuf::from)
            .unwrap_or_else(|| {
                PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                    .join("..")
                    .join("proof-output")
                    .join("powershell-reference.json")
            })
    }

    fn remove_test_tree(path: &PathBuf) {
        let target = fs::canonicalize(path).expect("fixture exists");
        let root = fs::canonicalize(std::env::temp_dir()).expect("temporary directory exists");
        assert!(target.starts_with(&root) && target != root);
        assert!(target.file_name().unwrap().to_string_lossy().starts_with("ThemeStudio native Start layout "));
        fs::remove_dir_all(target).expect("remove only the checked fixture");
    }

    #[test]
    fn rust_com_export_matches_existing_reference_bytes_and_pinned_list() {
        let reference = reference_path();
        assert!(
            reference.is_file(),
            "reference export is missing: {}; set NATIVE_START_LAYOUT_REFERENCE or keep the local proof-output reference",
            reference.display()
        );
        let reference_bytes = fs::read(&reference).expect("reference export must be readable");
        let reference_pins = pinned_list(&reference_bytes);
        assert!(!reference_pins.is_empty(), "reference pinnedList must not be empty");

        let output_dir = unique_test_dir("byte-equivalence");
        let output = output_dir.join("start layout 用户 output.json");
        start_layout::export_start_layout(&output).expect("native COM export must succeed");

        let actual_bytes = fs::read(&output).expect("native COM output must be readable");
        assert_eq!(actual_bytes, reference_bytes, "Rust COM output must be byte-identical");
        assert_eq!(pinned_list(&actual_bytes), reference_pins);
        remove_test_tree(&output_dir);
    }

    #[test]
    fn rust_com_export_accepts_unicode_and_space_output_path() {
        let output_dir = unique_test_dir("unicode-path");
        let output = output_dir.join("Start layout 用户 空格.json");
        assert!(output.is_absolute());
        assert!(output.to_string_lossy().contains("用户"));
        assert!(output.to_string_lossy().contains(" "));

        start_layout::export_start_layout(&output).expect("native COM export must support Unicode paths");
        let bytes = fs::read(&output).expect("Unicode-path output must be readable");
        assert!(!pinned_list(&bytes).is_empty());
        remove_test_tree(&output_dir);
    }

    #[test]
    fn rust_com_export_reports_invalid_destination_without_writing_settings() {
        let output_dir = unique_test_dir("invalid-destination");
        fs::create_dir_all(&output_dir).expect("test directory must be creatable");
        let parent_file = output_dir.join("destination-is-a-file");
        fs::write(&parent_file, b"sentinel").expect("test parent file must be writable");
        let output = parent_file.join("start-layout.json");

        let result = start_layout::export_start_layout(&output);
        assert!(result.is_err(), "COM export must reject a destination below a file");
        assert!(!output.exists(), "failed export must not create the invalid output");
        assert_eq!(fs::read(&parent_file).expect("sentinel must remain"), b"sentinel");
        remove_test_tree(&output_dir);
    }
}
