"""Compile migrated mods as disabled fixtures; never start an injection engine."""
from datetime import datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "components/icon-workbench"))
from runtime_adapter import RuntimeAdapter

target = ROOT / "qa/native-mods" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
adapter = RuntimeAdapter(target / "profile")
results = []
for name in ("net-toggle", "uwp-assets-redirect"):
    result = adapter._wh("mod", "install", "--file",
                         ROOT / "vendor/windhawk-mods/mods" / (name + ".wh.cpp"),
                         "--disabled", timeout=240)
    if not result.get("compiledLocally") or result.get("config", {}).get("disabled") is not True:
        raise RuntimeError("CLI did not acknowledge a disabled compiled module: " + name)
    library = Path(result["config"]["libraryFileName"])
    # The upstream CLI stores a filename shared by separate architecture folders.
    libraries = [library] if library.is_absolute() else [
        path for path in (adapter.windhawk_data / "Engine/Mods").rglob(library.name)
        if path.parent.name in {"32", "64"}
    ]
    if not libraries:
        raise RuntimeError("Compiled module not found: " + str(library))
    for compiled in libraries:
        helper = compiled.parent / "ThemeStudio.NativeActions.exe"
        if not helper.is_file():
            raise RuntimeError("Native helper is not beside the installed mod: " + str(compiled))
    results.append({"mod": name, "compiled": True, "disabled": True, "helperBesideModule": True,
                    "architectures": [path.parent.name for path in libraries]})
report = {"passed": True, "engineStarted": False, "results": results}
(target / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report))
