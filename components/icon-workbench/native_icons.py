"""Small Windows shell icon previews. Every acquired GDI handle is released."""
from __future__ import annotations
import ctypes
from ctypes import wintypes as wt
from pathlib import Path
from PIL import Image, ImageDraw


class SHFILEINFOW(ctypes.Structure):
    _fields_ = [("hIcon", wt.HANDLE), ("iIcon", ctypes.c_int), ("dwAttributes", wt.DWORD),
                ("szDisplayName", wt.WCHAR * 260), ("szTypeName", wt.WCHAR * 80)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                ("biPlanes", wt.WORD), ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG),
                ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD)]


user32, gdi32, shell32 = (ctypes.WinDLL(n, use_last_error=True) for n in ("user32", "gdi32", "shell32"))
shell32.SHGetFileInfoW.argtypes = [wt.LPCWSTR, wt.DWORD, ctypes.POINTER(SHFILEINFOW), wt.UINT, wt.UINT]
shell32.SHGetFileInfoW.restype = ctypes.c_size_t
user32.DestroyIcon.argtypes = [wt.HANDLE]
user32.DrawIconEx.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int, wt.HANDLE, ctypes.c_int,
                              ctypes.c_int, wt.UINT, wt.HBRUSH, wt.UINT]
gdi32.CreateCompatibleDC.argtypes = [wt.HDC]
gdi32.CreateCompatibleDC.restype = wt.HDC
gdi32.CreateDIBSection.argtypes = [wt.HDC, ctypes.POINTER(BITMAPINFOHEADER), wt.UINT,
                                  ctypes.POINTER(ctypes.c_void_p), wt.HANDLE, wt.DWORD]
gdi32.CreateDIBSection.restype = wt.HBITMAP
gdi32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
gdi32.SelectObject.restype = wt.HGDIOBJ
gdi32.DeleteObject.argtypes = [wt.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wt.HDC]


def placeholder(size=64) -> Image.Image:
    image = Image.new("RGBA", (size, size), "white")
    draw = ImageDraw.Draw(image)
    pad = max(3, size // 8)
    draw.rounded_rectangle((pad, pad, size-pad, size-pad), radius=size//6, fill="#EAE7FC")
    draw.rectangle((size*.31, size*.31, size*.69, size*.69), outline="#8077CC", width=max(2, size//20))
    return image


def shortcut_image(path: Path | str, size=64) -> Image.Image:
    info = SHFILEINFOW()
    bitmap = dc = previous = None
    try:
        if not shell32.SHGetFileInfoW(str(path), 0, ctypes.byref(info), ctypes.sizeof(info), 0x100):
            return placeholder(size)
        if not info.hIcon:
            return placeholder(size)
        dc = gdi32.CreateCompatibleDC(None)
        header = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), size, -size, 1, 32)
        bits = ctypes.c_void_p()
        bitmap = gdi32.CreateDIBSection(dc, ctypes.byref(header), 0, ctypes.byref(bits), None, 0)
        if not bitmap or not bits.value:
            return placeholder(size)
        previous = gdi32.SelectObject(dc, bitmap)
        ctypes.memset(bits.value, 255, size * size * 4)
        if not user32.DrawIconEx(dc, 0, 0, info.hIcon, size, size, 0, None, 3):
            return placeholder(size)
        return Image.frombytes("RGBA", (size, size), ctypes.string_at(bits, size * size * 4), "raw", "BGRA").convert("RGB")
    except Exception:
        return placeholder(size)
    finally:
        if previous and dc:
            gdi32.SelectObject(dc, previous)
        if bitmap:
            gdi32.DeleteObject(bitmap)
        if dc:
            gdi32.DeleteDC(dc)
        if info.hIcon:
            user32.DestroyIcon(info.hIcon)


def ico_image(path: Path | str, size=96) -> Image.Image:
    with Image.open(path) as icon:
        sizes = icon.ico.sizes()
        best = min((s for s in sizes if s[0] >= size and s[1] >= size), default=max(sizes), key=lambda s:s[0]*s[1])
        image = icon.ico.getimage(best).convert("RGBA")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    canvas.alpha_composite(image, ((size-image.width)//2, (size-image.height)//2))
    return canvas


def cursor_image(path: Path | str, size=96) -> Image.Image:
    """Render a CUR, or frame 0 of ANI, without applying it to the desktop."""
    import os
    user32.LoadImageW.argtypes = [wt.HINSTANCE, wt.LPCWSTR, wt.UINT, ctypes.c_int, ctypes.c_int, wt.UINT]
    user32.LoadImageW.restype = wt.HANDLE
    user32.DestroyCursor.argtypes = [wt.HANDLE]
    # Select the matching embedded frame rather than stretching the 32px default.
    cursor = user32.LoadImageW(None, os.path.expandvars(str(path)), 2, size, size, 0x10)
    if not cursor:
        return placeholder(size)
    bitmap = dc = previous = None
    try:
        dc = gdi32.CreateCompatibleDC(None)
        header = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), size, -size, 1, 32)
        bits = ctypes.c_void_p()
        bitmap = gdi32.CreateDIBSection(dc, ctypes.byref(header), 0, ctypes.byref(bits), None, 0)
        if not bitmap or not bits.value:
            return placeholder(size)
        previous = gdi32.SelectObject(dc, bitmap)
        ctypes.memset(bits.value, 255, size * size * 4)
        user32.DrawIconEx(dc, 0, 0, cursor, size, size, 0, None, 3)
        return Image.frombytes('RGBA', (size, size), ctypes.string_at(bits, size * size * 4), 'raw', 'BGRA').convert('RGB')
    finally:
        if previous and dc:
            gdi32.SelectObject(dc, previous)
        if bitmap:
            gdi32.DeleteObject(bitmap)
        if dc:
            gdi32.DeleteDC(dc)
        user32.DestroyCursor(cursor)
