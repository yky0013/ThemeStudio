"""Windows shortcut icon operations, with durable backups and conflict-safe undo."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import hashlib
import io
import json
import msvcrt
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import time
from typing import Callable
import unicodedata
import uuid

from PIL import Image
import pythoncom
from win32com.shell import shell, shellcon


SUPPORTED = {".lnk", ".url"}
MAX_ICO_BYTES = 32 * 1024 * 1024
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.tif', '.tiff', '.ico'}


def canonical(path: Path | str) -> str:
    return os.path.normcase(os.path.abspath(path))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    name = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with name.open("w", encoding="utf-8", newline="\n") as output:
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        name.unlink(missing_ok=True)


def new_sibling(path: Path, prefix: str) -> Path:
    """Fail promptly on Windows ACL denial; tempfile.mkstemp may retry TMP_MAX times."""
    for _ in range(3):
        candidate = path.with_name(prefix + uuid.uuid4().hex + path.suffix)
        try:
            descriptor = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_BINARY, 0o600)
        except FileExistsError:
            continue
        os.close(descriptor)
        return candidate
    raise FileExistsError("临时文件命名冲突，请重试。")


def default_storage() -> Path:
    return Path(os.environ["LOCALAPPDATA"]) / "ThemeStudio"


@contextmanager
def com_session():
    pythoncom.CoInitialize()
    try:
        yield
    finally:
        pythoncom.CoUninitialize()


def load_link(path: Path):
    link = pythoncom.CoCreateInstance(
        shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
    )
    link.QueryInterface(pythoncom.IID_IPersistFile).Load(str(path), 0)
    return link


def link_snapshot(link) -> dict:
    """Never Resolve(): inspecting a shortcut must not launch or repair its target."""
    return {
        "target": link.GetPath(shell.SLGP_RAWPATH)[0],
        "arguments": link.GetArguments(),
        "working_directory": link.GetWorkingDirectory(),
        "description": link.GetDescription(),
        "hotkey": link.GetHotkey(),
        "show_command": link.GetShowCmd(),
        "id_list": repr(link.GetIDList()),
    }


def read_url(path: Path) -> tuple[str, str, list[str], int, int, dict]:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        encoding = "utf-16"
    elif data.startswith(b"\xef\xbb\xbf"):
        encoding = "utf-8-sig"
    else:
        try:
            data.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            encoding = "mbcs"
    text = data.decode(encoding)
    lines = text.splitlines(keepends=True)
    sections = [i for i, line in enumerate(lines)
                if line.strip().casefold() == "[internetshortcut]"]
    if len(sections) != 1:
        raise ValueError("不是有效的 InternetShortcut 文件，或存在重复配置段。")
    start = sections[0] + 1
    end = next((i for i in range(start, len(lines)) if lines[i].lstrip().startswith("[")), len(lines))
    values = {}
    for line in lines[start:end]:
        if "=" in line and not line.lstrip().startswith((";", "#")):
            key, value = line.split("=", 1)
            key = key.strip().casefold()
            if key in values and key in {"url", "iconfile", "iconindex"}:
                raise ValueError("URL 快捷方式中存在重复字段，无法安全修改。")
            values[key] = value.strip()
    if not values.get("url"):
        raise ValueError("URL 快捷方式缺少目标地址。")
    return text, encoding, lines, start, end, values


def shortcut_info(path: Path | str, origin: str = "手动添加") -> dict:
    path = Path(path).absolute()
    if path.suffix.lower() not in SUPPORTED:
        raise ValueError("请选择 .lnk 或 .url 快捷方式。")
    if not path.is_file():
        raise FileNotFoundError(f"找不到快捷方式：{path}")
    if path.is_symlink() or path.stat().st_nlink > 1:
        raise ValueError("符号链接或硬链接快捷方式暂不支持，请选择独立的快捷方式文件。")
    if path.suffix.lower() == ".lnk":
        with com_session():
            link = load_link(path)
            details = link_snapshot(link)
            icon_path, icon_index = link.GetIconLocation()
    else:
        *_, values = read_url(path)
        details = {"target": values["url"], "arguments": "", "working_directory": "",
                   "description": "", "hotkey": 0, "show_command": 1,
                   "id_list": "", "url_values": {k: v for k, v in values.items()
                                                if k not in {"iconfile", "iconindex"}}}
        icon_path, icon_index = values.get("iconfile", ""), int(values.get("iconindex", "0"))
    return {"path": str(path), "name": path.stem, "origin": origin,
            "kind": path.suffix.lower(), "icon_path": icon_path, "icon_index": icon_index,
            "sha256": digest(path), "details": details}


def desktop_folders() -> list[tuple[Path, str]]:
    with com_session():
        candidates = [
            (Path(shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOPDIRECTORY, 0, 0)), "个人桌面"),
            (Path(shell.SHGetFolderPath(0, shellcon.CSIDL_COMMON_DESKTOPDIRECTORY, 0, 0)), "公共桌面"),
        ]
    seen = set()
    return [(p, label) for p, label in candidates if not (canonical(p) in seen or seen.add(canonical(p)))]


def scan_shortcuts(folders=None, extra_paths=()) -> tuple[list[dict], list[str]]:
    found, errors, seen, candidates = [], [], set(), []
    for folder, origin in (desktop_folders() if folders is None else folders):
        try:
            candidates.extend((p, origin) for p in Path(folder).iterdir()
                              if p.is_file() and p.suffix.lower() in SUPPORTED)
        except OSError as error:
            errors.append(f"{folder}：{friendly_error(error)}")
    candidates.extend((Path(p), "手动添加") for p in extra_paths)
    for path, origin in candidates:
        key = canonical(path)
        if key in seen:
            continue
        seen.add(key)
        try:
            found.append(shortcut_info(path, origin))
        except Exception as error:
            errors.append(f"{path.name}：{friendly_error(error)}")
    return sorted(found, key=lambda x: (x["name"].casefold(), x["origin"])), errors


def validate_icon(path: Path | str) -> dict:
    path = Path(path)
    if path.suffix.lower() != ".ico":
        raise ValueError("图标资源格式无效，请重新选择图片。")
    if not path.is_file():
        raise FileNotFoundError(f"找不到 ICO：{path}")
    if path.stat().st_size > MAX_ICO_BYTES:
        raise ValueError("ICO 超过 32 MB，请换用较小的图标。")
    data = path.read_bytes()
    if data[:4] != b"\x00\x00\x01\x00":
        raise ValueError("文件不是有效的 ICO，不能仅通过修改扩展名转换图片。")
    with Image.open(io.BytesIO(data)) as icon:
        if icon.format != "ICO":
            raise ValueError("无法识别 ICO 图标。")
        sizes = sorted(icon.ico.sizes())
        if not sizes or any(w > 1024 or h > 1024 for w, h in sizes):
            raise ValueError("ICO 尺寸异常。")
        for size in sizes:
            icon.ico.getimage(size).load()
    return {"name": path.name, "path": str(path.absolute()),
            "sizes": sizes, "sha256": hashlib.sha256(data).hexdigest()}


def match_key(name: str) -> str:
    return unicodedata.normalize("NFKC", name).strip().casefold()


def match_icons(shortcuts: list[dict], icons: list[dict]) -> dict[str, str]:
    """Only exact, case-insensitive names; ambiguous names are never guessed."""
    candidates = {}
    for icon in icons:
        candidates.setdefault(match_key(Path(icon["name"]).stem), set()).add(icon["path"])
    return {canonical(row["path"]): next(iter(candidates[match_key(row["name"])]))
            for row in shortcuts if len(candidates.get(match_key(row["name"]), set())) == 1}


def notify_shell(paths) -> None:
    with com_session():
        for path in paths:
            try:
                shell.SHChangeNotify(shellcon.SHCNE_UPDATEITEM,
                                     shellcon.SHCNF_PATHW | shellcon.SHCNF_FLUSHNOWAIT,
                                     str(path), None)
            except Exception:
                pass  # A refresh failure must never hide a successful file operation.


def friendly_error(error: Exception) -> str:
    code = getattr(error, "winerror", None) or getattr(error, "hresult", None)
    if isinstance(error, PermissionError) or code in (5, -2147024891):
        return "没有写入权限。公共桌面项目可能需要以管理员身份运行工作台；也可选择自己的快捷方式。"
    if code in (32, 33):
        return "文件正被其他程序占用，请关闭该文件的属性窗口后重试。"
    return str(error)


@dataclass(frozen=True)
class Assignment:
    shortcut: str
    icon: str
    expected_hash: str


class IconStore:
    def __init__(self, directory: Path | str | None = None):
        self.directory = (Path(directory) if directory else default_storage()).absolute()
        self.icons_dir = self.directory / "icons"
        self.history_dir = self.directory / "history"
        self.icons_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def lock(self):
        with (self.directory / ".write.lock").open("a+b") as stream:
            stream.seek(0, 2)
            if stream.tell() == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise RuntimeError("另一个工作台正在保存，请稍后再试。") from error
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)

    def import_image(self, path: Path | str) -> dict:
        """Accept ordinary artwork; materialize a durable icon with the existing converter."""
        path = Path(path).absolute()
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError('请选择 PNG、JPG、WebP、BMP、GIF、TIFF 或 ICO 图片。')
        if path.suffix.lower() == '.ico':
            return self.import_icon(path)
        if path.stat().st_size > MAX_ICO_BYTES:
            raise ValueError('图片超过 32 MB，请先缩小图片。')
        if not getattr(sys, 'frozen', False):
            converter_dir = str(Path(__file__).resolve().parents[1] / 'image-to-ico')
            if converter_dir not in sys.path:
                sys.path.insert(0, converter_dir)
        from converter import Options, encode_ico, load_image
        data = encode_ico(load_image(path), Options())
        target = self.icons_dir / (hashlib.sha256(data).hexdigest() + '.ico')
        with self.lock():
            if target.exists():
                if target.read_bytes() != data:
                    raise RuntimeError('资源库中的图标校验失败。')
            else:
                temporary = target.with_suffix('.' + uuid.uuid4().hex + '.tmp')
                try:
                    temporary.write_bytes(data)
                    os.replace(temporary, target)
                finally:
                    temporary.unlink(missing_ok=True)
        metadata = validate_icon(target)
        metadata.update(name=path.name, source=str(path))
        return metadata

    def import_icon(self, path: Path | str) -> dict:
        metadata = validate_icon(path)
        target = self.icons_dir / (metadata["sha256"] + ".ico")
        if not target.exists():
            temporary = target.with_suffix("." + uuid.uuid4().hex + ".tmp")
            try:
                shutil.copyfile(path, temporary)
                if digest(temporary) != metadata["sha256"]:
                    raise RuntimeError("导入期间 ICO 发生变化，请重试。")
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
        elif digest(target) != metadata["sha256"]:
            raise RuntimeError("资源库中的图标校验失败，请保留数据目录并检查该文件。")
        metadata["source"] = metadata["path"]
        metadata["path"] = str(target)
        return metadata

    def read_settings(self) -> dict:
        try:
            return json.loads((self.directory / "settings.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def save_settings(self, value: dict) -> None:
        with self.lock():
            atomic_json(self.directory / "settings.json", value)

    def _manifest_path(self, batch_id: str) -> Path:
        if not re.fullmatch(r"[0-9T_-]+[a-f0-9]{8}", batch_id):
            raise ValueError("备份编号无效。")
        return self.history_dir / batch_id / "manifest.json"

    def history(self) -> list[dict]:
        records = []
        for path in sorted(self.history_dir.glob("*/manifest.json"), reverse=True):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                if record.get("id") == path.parent.name and isinstance(record.get("entries"), list):
                    record.setdefault("created_ns", path.parent.stat().st_birthtime_ns)
                    records.append(record)
            except (OSError, ValueError):
                continue
        return sorted(records, key=lambda record: record["created_ns"], reverse=True)

    def _stage_icon(self, source: Path, destination: Path, icon: Path) -> None:
        if source.suffix.lower() == ".lnk":
            shutil.copyfile(source, destination)
            with com_session():
                link = load_link(destination)
                link.SetIconLocation(str(icon), 0)
                link.QueryInterface(pythoncom.IID_IPersistFile).Save(str(destination), 0)
        else:
            text, encoding, lines, start, end, _ = read_url(source)
            newline = "\r\n" if "\r\n" in text else "\n"
            kept = [line for line in lines[start:end]
                    if not re.match(r"^\s*(IconFile|IconIndex)\s*=", line, re.I)]
            if kept and not kept[-1].endswith(("\r", "\n")):
                kept[-1] += newline
            prefix = lines[:start]
            if prefix and not prefix[-1].endswith(("\r", "\n")):
                prefix[-1] += newline
            result = "".join(prefix + kept + [f"IconFile={icon}{newline}", f"IconIndex=0{newline}"] + lines[end:])
            try:
                data = result.encode(encoding)
            except UnicodeEncodeError:
                data = result.encode("utf-16")
            destination.write_bytes(data)

    def apply(self, assignments: list[Assignment], progress: Callable | None = None) -> dict:
        if not assignments:
            raise ValueError("请先为快捷方式关联 ICO。")
        if len({canonical(a.shortcut) for a in assignments}) != len(assignments):
            raise ValueError("同一批次中存在重复的快捷方式。")
        with self.lock():
            batch_id = datetime.now().strftime("%Y%m%dT%H%M%S_%f_") + uuid.uuid4().hex[:8]
            folder = self.history_dir / batch_id
            folder.mkdir()
            manifest = {"version": 1, "id": batch_id,
                        "created_ns": time.time_ns(),
                        "created": datetime.now().astimezone().isoformat(timespec="seconds"),
                        "entries": []}
            manifest_path = folder / "manifest.json"
            atomic_json(manifest_path, manifest)
            for i, assignment in enumerate(assignments):
                path = Path(assignment.shortcut).absolute()
                entry = {"name": path.stem, "path": str(path), "status": "pending", "error": ""}
                manifest["entries"].append(entry)
                temporary = None
                committed = False
                try:
                    before = shortcut_info(path)
                    if not assignment.expected_hash or before["sha256"] != assignment.expected_hash:
                        raise RuntimeError("快捷方式在选择后已被其他程序修改，请刷新列表后重新关联。")
                    if not path.stat().st_mode & stat.S_IWRITE:
                        raise PermissionError("快捷方式是只读文件。")
                    imported = self.import_icon(assignment.icon)
                    icon_path = Path(imported["path"])
                    backup = folder / f"{i:04d}{path.suffix.lower()}"
                    shutil.copy2(path, backup)
                    if digest(backup) != before["sha256"]:
                        raise RuntimeError("备份期间快捷方式发生变化，已跳过。")
                    entry.update(before_hash=before["sha256"], backup=backup.name,
                                 original_icon=before["icon_path"], original_index=before["icon_index"],
                                 applied_icon=str(icon_path), before=before["details"])
                    temporary = new_sibling(path, ".icon-workbench-")
                    self._stage_icon(path, temporary, icon_path)
                    staged = shortcut_info(temporary)
                    if staged["details"] != before["details"]:
                        raise RuntimeError("验证发现启动目标或参数发生变化，已取消该项替换。")
                    if canonical(staged["icon_path"]) != canonical(icon_path) or staged["icon_index"] != 0:
                        raise RuntimeError("新图标写入验证失败，原快捷方式未替换。")
                    entry.update(applied_hash=staged["sha256"], status="prepared")
                    # Journal must reach disk before the shortcut is changed.
                    atomic_json(manifest_path, manifest)
                    if digest(path) != before["sha256"]:
                        raise RuntimeError("应用前检测到快捷方式变化，请刷新后重试。")
                    os.replace(temporary, path)
                    committed = True
                    if digest(path) != staged["sha256"]:
                        raise RuntimeError("替换后文件又发生变化，请在备份记录中检查。")
                    entry["status"] = "applied"
                except Exception as error:
                    entry["status"] = "needs_attention" if committed else "failed"
                    entry["error"] = friendly_error(error)
                finally:
                    if temporary and temporary.exists():
                        temporary.unlink(missing_ok=True)
                    atomic_json(manifest_path, manifest)
                if progress:
                    progress(i + 1, len(assignments), dict(entry))
            notify_shell([e["path"] for e in manifest["entries"] if e["status"] == "applied"])
            return manifest

    def restore(self, batch_id: str, indexes: list[int] | None = None,
                progress: Callable | None = None) -> dict:
        with self.lock():
            manifest_path = self._manifest_path(batch_id)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            selected = indexes if indexes is not None else list(range(len(manifest["entries"])))
            results = []
            for count, index in enumerate(selected):
                entry = manifest["entries"][index]
                result = {"name": entry["name"], "path": entry["path"], "status": "skipped", "error": ""}
                temporary = None
                try:
                    if entry["status"] not in {"applied", "prepared", "needs_attention", "restoring"}:
                        result["error"] = "该项未应用或已经恢复。"
                        results.append(result)
                        continue
                    path = Path(entry["path"])
                    backup = manifest_path.parent / Path(entry["backup"]).name
                    if digest(backup) != entry["before_hash"]:
                        raise RuntimeError("备份文件校验失败，未覆盖当前快捷方式。")
                    current = digest(path)
                    if current == entry["before_hash"]:
                        entry["status"] = "restored"
                        result["status"] = "restored"
                    else:
                        if current != entry["applied_hash"]:
                            raise RuntimeError("当前快捷方式已有后续修改，已跳过。请先恢复较新的批次，或自行核对备份。")
                        shortcut_info(path)  # Recheck links and file type before writing.
                        if not path.stat().st_mode & stat.S_IWRITE:
                            raise PermissionError("快捷方式是只读文件。")
                        temporary = new_sibling(path, ".icon-restore-")
                        shutil.copy2(backup, temporary)
                        if digest(temporary) != entry["before_hash"]:
                            raise RuntimeError("恢复副本校验失败。")
                        entry["status"] = "restoring"
                        atomic_json(manifest_path, manifest)
                        if digest(path) != current:
                            raise RuntimeError("恢复前快捷方式发生变化，已跳过。")
                        os.replace(temporary, path)
                        if digest(path) != entry["before_hash"]:
                            raise RuntimeError("恢复后快捷方式又发生变化，请核对文件。")
                        entry["status"] = "restored"
                        entry["restored_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
                        result["status"] = "restored"
                    entry.pop("restore_error", None)
                except Exception as error:
                    result["status"] = "failed"
                    result["error"] = friendly_error(error)
                    entry["restore_error"] = result["error"]
                finally:
                    if temporary and temporary.exists():
                        temporary.unlink(missing_ok=True)
                    atomic_json(manifest_path, manifest)
                results.append(result)
                if progress:
                    progress(count + 1, len(selected), result)
            notify_shell([e["path"] for e in results if e["status"] == "restored"])
            return {"id": batch_id, "entries": results}
