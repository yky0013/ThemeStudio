use std::{fs::create_dir, path::PathBuf};

use slu_utils::{checksums::CheckSums, signature::sign_minisign};

fn main() {
    let _ = create_dir("gen");

    let mut checksums = CheckSums::new();
    read_folder_recursive(PathBuf::from("static"), &mut |path| {
        checksums.add(&path).unwrap();
    });

    let target_dir = target_dir();
    let sums_path = target_dir.join("SHA256SUMS");
    checksums.write(&sums_path).unwrap();

    // ThemeStudio changes native code only. Reuse the original, verified upstream
    // signature for byte-identical static assets; never disable runtime integrity.
    println!("cargo:rerun-if-env-changed=THEMESTUDIO_VERIFIED_STATIC_DIR");
    if let Some(directory) = std::env::var_os("THEMESTUDIO_VERIFIED_STATIC_DIR") {
        let directory = PathBuf::from(directory);
        let original_sums = std::fs::read(directory.join("SHA256SUMS"))
            .expect("Verified upstream SHA256SUMS missing");
        let signature = std::fs::read_to_string(directory.join("SHA256SUMS.sig"))
            .expect("Verified upstream static signature missing");
        let original = CheckSums::parse(&original_sums).expect("Invalid upstream checksums");
        assert!(
            original.compare(&checksums).is_empty(),
            "Static assets differ from the signed upstream files; refusing native-only build"
        );
        slu_utils::signature::verify_minisign(
            &original_sums, &signature,
            "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IDQ4QjU1RUI0NEM0NzBERUIKUldUckRVZE10RjYxU0lpaERvdklYL05DVlg0Sk9EVngvaEgzZjMvU1NNemJTZXZ1K0dNVXU3ZkQK",
        ).expect("Upstream static signature is not valid");
        std::fs::write(&sums_path, original_sums).unwrap();
        std::fs::write(sums_path.with_extension("sig"), signature).unwrap();
    } else if !cfg!(debug_assertions) {
        sign_sha256sums(&sums_path);
    } else {
        std::fs::write(
            sums_path.with_extension("sig"),
            "NOT SIGNED NEEDED FOR DEBUG",
        )
        .unwrap();
    }

    tauri_build::build();
}

fn target_dir() -> PathBuf {
    let out_dir = PathBuf::from(std::env::var("OUT_DIR").unwrap());
    // see <https://github.com/rust-lang/cargo/issues/5457>
    out_dir
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .to_path_buf()
}

fn read_folder_recursive<F>(path: PathBuf, cb: &mut F)
where
    F: FnMut(PathBuf),
{
    for entry in std::fs::read_dir(path).unwrap() {
        let entry = entry.unwrap();
        let path = entry.path();
        if path.is_dir() {
            read_folder_recursive(path, cb);
        } else {
            cb(path);
        }
    }
}

fn sign_sha256sums(path: &PathBuf) {
    let key_base64 =
        std::env::var("TAURI_SIGNING_PRIVATE_KEY").expect("TAURI_SIGNING_PRIVATE_KEY missing");
    let password = std::env::var("TAURI_SIGNING_PRIVATE_KEY_PASSWORD")
        .expect("TAURI_SIGNING_PRIVATE_KEY_PASSWORD missing");

    let data = std::fs::read(path).expect("Failed to read SHA256SUMS file");
    let signature = sign_minisign(&data, &key_base64, password).expect("Failed to sign data");

    let sig_path = path.with_extension("sig");
    std::fs::write(&sig_path, signature).expect("Failed to write signature");
}
