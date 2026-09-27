"""Image-to-ICO conversion, independent of the desktop interface."""

from __future__ import annotations

import io
from dataclasses import dataclass
from itertools import count
from pathlib import Path

from PIL import Image, ImageColor, ImageOps, UnidentifiedImageError


ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)
MAX_PIXELS = 40_000_000


@dataclass(frozen=True)
class Options:
    sizes: tuple[int, ...] = ICON_SIZES
    mode: str = "contain"
    padding: float = 0.0
    background: str | None = None

    def __post_init__(self) -> None:
        if not self.sizes or any(size not in ICON_SIZES for size in self.sizes):
            raise ValueError("请至少选择一个有效的图标尺寸。")
        object.__setattr__(self, "sizes", tuple(sorted(set(self.sizes))))
        if self.mode not in ("contain", "crop"):
            raise ValueError("图片处理方式必须为完整保留或居中裁切。")
        if not 0 <= self.padding <= 0.24:
            raise ValueError("边距应在 0% 到 24% 之间。")
        if self.background is not None:
            ImageColor.getcolor(self.background, "RGBA")


def load_image(source: str | Path) -> Image.Image:
    """Decode frame 0, apply EXIF rotation, and detach from the source file."""
    try:
        with Image.open(source) as original:
            if original.width * original.height > MAX_PIXELS:
                raise ValueError("图片超过 4000 万像素，请先缩小图片再导入。")
            original.seek(0)
            return ImageOps.exif_transpose(original).convert("RGBA")
    except (UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValueError("无法读取这张图片，请检查文件是否完整、格式是否受支持。") from exc


def render_icon(image: Image.Image, size: int, options: Options) -> Image.Image:
    """Render each size directly from the original, preserving its alpha."""
    inner = max(1, round(size * (1 - 2 * options.padding)))
    if options.mode == "crop":
        foreground = ImageOps.fit(
            image, (inner, inner), method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
    else:
        ratio = min(inner / image.width, inner / image.height)
        dimensions = (max(1, round(image.width * ratio)),
                      max(1, round(image.height * ratio)))
        foreground = image.resize(dimensions, Image.Resampling.LANCZOS)
    background = (
        ImageColor.getcolor(options.background, "RGBA")
        if options.background else (0, 0, 0, 0)
    )
    canvas = Image.new("RGBA", (size, size), background)
    canvas.alpha_composite(
        foreground,
        ((size - foreground.width) // 2, (size - foreground.height) // 2),
    )
    return canvas


def encode_ico(image: Image.Image, options: Options) -> bytes:
    frames = [render_icon(image, size, options) for size in options.sizes]
    buffer = io.BytesIO()
    # The largest frame must be first: Pillow ignores sizes larger than it.
    frames[-1].save(
        buffer, format="ICO", sizes=[(size, size) for size in options.sizes],
        append_images=frames[:-1],
    )
    return buffer.getvalue()


def convert_file(
    source: str | Path, output_dir: str | Path, options: Options = Options(),
) -> Path:
    """Create a new ICO. Exclusive creation preserves all existing files."""
    source = Path(source)
    encoded = encode_ico(load_image(source), options)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for number in count(1):
        suffix = "" if number == 1 else f"_{number}"
        destination = output_dir / f"{source.stem}{suffix}.ico"
        try:
            stream = destination.open("xb")
        except FileExistsError:
            continue
        try:
            with stream:
                stream.write(encoded)
        except BaseException:
            # Only remove the incomplete file just created by this operation.
            destination.unlink(missing_ok=True)
            raise
        return destination
    raise RuntimeError("无法创建输出文件。")
