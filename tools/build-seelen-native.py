"""Rebuild the pinned Seelen fork with native Start layout export.

Toolchain lives inside this checkout. Read docs/research/20261020/seelen-build
for the verified portable toolchain preparation. All environment changes apply
only to child processes; no user/global PATH, compiler, or proxy settings change.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "vendor/runtime-sources/Seelen-UI-2.8.6"
TARGET = ROOT / "build/seelen-target"
ORIGINAL = ROOT / ".cache/runtimes/seelen-engine"
OUTPUT = ROOT / ".cache/runtimes/seelen-native"


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def build_environment():
    local = ROOT / ".tools/seelen-build/build-env.json"
    configuration = json.loads((local if local.exists() else ROOT / "config/seelen-toolchain.example.json")
                               .read_text(encoding="utf-8-sig"))
    def expand(value):
        if isinstance(value, str):
            return value.replace("${PROJECT_ROOT}", str(ROOT))
        if isinstance(value, list):
            return [expand(item) for item in value]
        if isinstance(value, dict):
            return {key: expand(item) for key, item in value.items()}
        return value
    configuration = expand(configuration)
    msvc = Path(configuration["msvc_root"])
    binary = msvc / "bin/Hostx64/x64"
    toolchain = Path(configuration["rustup_home"]) / "toolchains" / configuration["rustup_toolchain"]
    linker = toolchain / "lib/rustlib/x86_64-pc-windows-msvc/bin"
    for needed in (binary / "cl.exe", msvc / "lib/x64/msvcrt.lib",
                   Path(configuration["windows_sdk_bin_x64"]) / "rc.exe"):
        if not needed.is_file():
            raise RuntimeError("Portable build toolchain incomplete: " + str(needed))
    paths = [str(binary), str(linker), *configuration["path_prepend"]]
    environment = {**os.environ,
        "PATH": os.pathsep.join(dict.fromkeys([*paths, os.environ.get("PATH", "")])),
        "LIB": ";".join(dict.fromkeys([str(msvc / "lib/x64"), *configuration["lib"]])),
        "INCLUDE": ";".join(dict.fromkeys([str(msvc / "include"), *configuration["include"]])),
        "CARGO_HOME": configuration["cargo_home"],
        "RUSTUP_HOME": configuration["rustup_home"],
        "RUSTUP_TOOLCHAIN": configuration["rustup_toolchain"],
        "CARGO_TARGET_DIR": str(TARGET),
        "CARGO_INCREMENTAL": "0",
        "CARGO_PROFILE_DEV_DEBUG": "0", "CARGO_PROFILE_TEST_DEBUG": "0",
        "CARGO_PROFILE_RELEASE_DEBUG": "0",
        "CARGO_BUILD_JOBS": "4",
        "DENO_DIR": str(ROOT / "build/deno-cache"), "DENO_TLS_CA_STORE": "system",
        "CC": str(binary / "cl.exe"), "CXX": str(binary / "cl.exe"),
        "AR": str(binary / "lib.exe"),
        "VCToolsInstallDir": str(msvc) + "\\",
        "WindowsSdkDir": configuration["windows_sdk_root"] + "\\",
        "WindowsSDKVersion": configuration["windows_sdk_version"] + "\\",
        "THEMESTUDIO_VERIFIED_STATIC_DIR": str(ORIGINAL),
    }
    environment.update(configuration.get("tool_env", {}))
    # LINK is an MSVC command-line-options variable, not an executable selector.
    environment.pop("LINK", None)
    environment["CMAKE_GENERATOR"] = "NMake Makefiles"
    proxy = configuration.get("proxy_for_download_only")
    if proxy:
        environment.update(HTTP_PROXY=proxy, HTTPS_PROXY=proxy, CARGO_HTTP_PROXY=proxy)
    return configuration, environment


def run(command, environment, cwd=SOURCE):
    return subprocess.run([str(item) for item in command], cwd=cwd, env=environment,
                          stdout=sys.stdout, stderr=sys.stderr, check=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["proof", "bindings", "frontend", "check", "build", "collect", "all"])
    arguments = parser.parse_args()
    configuration, environment = build_environment()
    cargo = Path(configuration["cargo_home"]) / "bin/cargo.exe"
    deno = configuration["deno_exe"]
    lock = SOURCE / "Cargo.lock"
    lock_digest = digest(lock)
    if arguments.stage in {"bindings", "frontend", "all"} and not (SOURCE / "node_modules/.package-lock.json").is_file():
        node = Path(shutil.which("node.exe") or "")
        npm = node.parent / "node_modules/npm/bin/npm-cli.js"
        if not npm.is_file():
            raise RuntimeError("Node.js/npm is required to prepare Seelen's pinned frontend dependencies.")
        run([node, npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"], environment)
    if arguments.stage == "proof":
        proof = ROOT / "docs/research/20261020/native-start-layout/rust-proof"
        # Keep the small API test build separate from full application profiles.
        environment["CARGO_TARGET_DIR"] = str(ROOT / "build/start-layout-proof")
        environment["CARGO_TARGET_X86_64_PC_WINDOWS_MSVC_LINKER"] = "rust-lld.exe"
        run([cargo, "test", "--manifest-path", proof / "Cargo.toml", "--target", "x86_64-pc-windows-msvc"], environment, proof)
    if arguments.stage in {"bindings", "all"}:
        run([deno, "task", "build"], environment, SOURCE / "libs/core")
        if not (SOURCE / "libs/core/npm/package.json").is_file():
            raise RuntimeError("The local Seelen UI library was not generated.")
    if arguments.stage in {"frontend", "all"}:
        run([shutil.which("node.exe"), "--import", "tsx", "scripts/build.ts", "--production"], environment)
    if arguments.stage == "check":
        run([cargo, "check", "--locked", "--target", "x86_64-pc-windows-msvc",
             "-p", "seelen-ui", "--features", "custom-protocol"], environment)
    if arguments.stage in {"build", "all"}:
        # This is the final redistributable build, not the iteration/test loop.
        run([cargo, "build", "--locked", "--release", "--target", "x86_64-pc-windows-msvc",
             "-p", "seelen-ui", "-p", "sluhk", "--features", "seelen-ui/custom-protocol"], environment)
    if digest(lock) != lock_digest:
        raise RuntimeError("Pinned Cargo.lock changed during the build.")
    if arguments.stage in {"collect", "all"}:
        binary = TARGET / "x86_64-pc-windows-msvc/release"
        names = ["seelen-ui.exe", "slu.exe", "slu-service.exe", "sluhk.dll"]
        for name in names + ["SHA256SUMS", "SHA256SUMS.sig"]:
            if not (binary / name).is_file():
                raise RuntimeError("Compiled Seelen artifact missing: " + name)
        if any(digest(binary / name) != digest(ORIGINAL / name) for name in ["SHA256SUMS", "SHA256SUMS.sig"]):
            raise RuntimeError("Original signed static integrity files changed.")
        OUTPUT.mkdir(parents=True, exist_ok=True)
        shutil.copytree(ORIGINAL / "static", OUTPUT / "static", dirs_exist_ok=True)
        for name in names + ["SHA256SUMS", "SHA256SUMS.sig"]:
            shutil.copy2(binary / name, OUTPUT / name)
        manifest = {
            "upstreamCommit": "079c38584d48ef02e800d6f596bbef97bd00e327",
            "variant": "themestudio-native-start-layout.1",
            "files": {name: digest(OUTPUT / name) for name in names},
            "cargoLockSha256": lock_digest,
            "originalStaticIntegrityPreserved": True,
            "authenticode": "Local rebuild; not the original signed upstream executables",
            "nativeSourceSha256": {
                name: digest(SOURCE / name) for name in [
                    "src/background/utils/start_layout.rs", "src/background/utils/mod.rs",
                    "src/background/exposed.rs", "src/build.rs"
                ]
            },
        }
        (OUTPUT / "native-build.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        lock_path = ROOT / "config/runtime-distributions.json"
        distribution = json.loads(lock_path.read_text(encoding="utf-8-sig"))
        seelen = distribution["seelen"]
        seelen.setdefault("upstreamFiles", seelen["files"])
        seelen.update(variant=manifest["variant"], files=manifest["files"],
                      deployment="Locally rebuilt native Start layout export; original signed static assets retained.")
        lock_path.write_text(json.dumps(distribution, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(manifest))


if __name__ == "__main__":
    main()
