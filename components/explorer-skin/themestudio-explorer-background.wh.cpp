// ==WindhawkMod==
// @id themestudio-explorer-background
// @name ThemeStudio Explorer background
// @description Theme image in the native Explorer file list and navigation pane
// @version 1.0.0
// @author ThemeStudio contributors
// @license MIT
// @include explorer.exe
// @architecture x86-64
// @compilerOptions -luser32 -lgdi32 -luxtheme -ldwmapi
// ==/WindhawkMod==

// ==WindhawkModReadme==
/*
Native GDI rendering adapted from the paint/DC tracking approach in
Maplespe/explorerTool (MIT, Copyright (c) 2021 Maplespe).
The original source and license are retained in docs/research/20261004/explorer-background/source.
ThemeStudio validates and composites a static bitmap before enabling this mod.
No shell-extension registration and no Explorer restart are required.
Hold Escape while enabling to skip loading; disable this mod to restore painting.
*/
// ==/WindhawkModReadme==

// ==WindhawkModSettings==
/*
- imagePath: ""
  $name: Validated background bitmap
- textColor: "#e4edfa"
  $name: File name color
- captionColor: "#081b32"
  $name: Title bar color
*/
// ==/WindhawkModSettings==

#include <windows.h>
#include <uxtheme.h>
#include <dwmapi.h>
#ifndef THEMESTUDIO_PAINT_TEST
#include <windhawk_utils.h>
#endif
#include <algorithm>
#include <atomic>
#include <array>
#include <mutex>
#include <unordered_map>
#include <string>

// Immutable while hooks are active. A setting change requests a Windhawk reload.
HBITMAP g_bitmap = nullptr;
BITMAP g_info{};
COLORREF g_text = RGB(228, 237, 250);
COLORREF g_caption = RGB(8, 27, 50);
std::atomic<bool> g_stopping{false};
std::mutex g_mutex;
std::mutex g_renderMutex;
std::unordered_map<HDC, HWND> g_dcWindows;
std::unordered_map<HWND, std::array<int,4>> g_layouts;
struct CaptionState { DWORD dark, background, text; bool hasDark, hasBackground, hasText; };
std::unordered_map<HWND, CaptionState> g_captions;
thread_local bool g_drawing = false;

bool ClassIs(HWND window, PCWSTR expected) {
    WCHAR name[128]{};
    return GetClassNameW(window, name, ARRAYSIZE(name)) && !wcscmp(name, expected);
}
bool IsExplorer(HWND window) {
    return window && ClassIs(GetAncestor(window, GA_ROOT), L"CabinetWClass");
}
bool IsSurface(HWND window) {
    if (!IsExplorer(window)) return false;
    // Do not touch desktop icons, dialogs, menus or other processes.
    return (ClassIs(window, L"DirectUIHWND") && ClassIs(GetParent(window), L"SHELLDLL_DefView")) ||
           ClassIs(window, L"SysTreeView32");
}
void StyleCaption(HWND window) {
    if (g_stopping || !IsExplorer(window)) return;
    HWND root = GetAncestor(window, GA_ROOT);
    std::lock_guard<std::mutex> guard(g_mutex);
    if (g_captions.count(root)) return;
    CaptionState before{};
    before.hasDark=SUCCEEDED(DwmGetWindowAttribute(root,20,&before.dark,sizeof(DWORD)));
    before.hasBackground=SUCCEEDED(DwmGetWindowAttribute(root,35,&before.background,sizeof(DWORD)));
    before.hasText=SUCCEEDED(DwmGetWindowAttribute(root,36,&before.text,sizeof(DWORD)));
    g_captions[root]=before;
    DWORD dark=TRUE;
    if(before.hasDark) DwmSetWindowAttribute(root,20,&dark,sizeof(dark));
    if(before.hasBackground) DwmSetWindowAttribute(root,35,&g_caption,sizeof(g_caption));
    if(before.hasText) DwmSetWindowAttribute(root,36,&g_text,sizeof(g_text));
}
void RestoreCaptions() {
    std::lock_guard<std::mutex> guard(g_mutex);
    for(auto& [window,before]:g_captions) if(IsExplorer(window)) {
        if(before.hasDark) DwmSetWindowAttribute(window,20,&before.dark,sizeof(DWORD));
        if(before.hasBackground) DwmSetWindowAttribute(window,35,&before.background,sizeof(DWORD));
        if(before.hasText) DwmSetWindowAttribute(window,36,&before.text,sizeof(DWORD));
    }
    g_captions.clear();
}
HWND WindowForDC(HDC dc) {
    HWND window = WindowFromDC(dc);
    if (IsSurface(window)) return window;
    std::lock_guard<std::mutex> guard(g_mutex);
    auto found = g_dcWindows.find(dc);
    return found != g_dcWindows.end() && IsSurface(found->second) ? found->second : nullptr;
}
void Track(HDC dc, HWND window) {
    if (!dc || !IsSurface(window)) return;
    std::lock_guard<std::mutex> guard(g_mutex);
    g_dcWindows[dc] = window;
}

decltype(&BeginPaint) BeginPaint_Original;
HDC WINAPI BeginPaint_Hook(HWND window, LPPAINTSTRUCT paint) {
    if(IsSurface(window)) StyleCaption(window);
    HDC dc = BeginPaint_Original(window, paint);
    Track(dc, window);
    return dc;
}
decltype(&DestroyWindow) DestroyWindow_Original;
BOOL WINAPI DestroyWindow_Hook(HWND window) {
    { std::lock_guard<std::mutex> guard(g_mutex);
      g_captions.erase(window);
      for(auto it=g_dcWindows.begin();it!=g_dcWindows.end();) {
          if(it->second==window) it=g_dcWindows.erase(it); else ++it;
      }
    }
    { std::lock_guard<std::mutex> guard(g_renderMutex); g_layouts.erase(window); }
    return DestroyWindow_Original(window);
}
decltype(&EndPaint) EndPaint_Original;
BOOL WINAPI EndPaint_Hook(HWND window, const PAINTSTRUCT* paint) {
    { std::lock_guard<std::mutex> guard(g_mutex); if (paint) g_dcWindows.erase(paint->hdc); }
    return EndPaint_Original(window, paint);
}
decltype(&CreateCompatibleDC) CreateCompatibleDC_Original;
HDC WINAPI CreateCompatibleDC_Hook(HDC dc) {
    HDC created = CreateCompatibleDC_Original(dc);
    if (!g_drawing) Track(created, WindowForDC(dc));
    return created;
}
decltype(&DeleteDC) DeleteDC_Original;
BOOL WINAPI DeleteDC_Hook(HDC dc) {
    { std::lock_guard<std::mutex> guard(g_mutex); g_dcWindows.erase(dc); }
    return DeleteDC_Original(dc);
}

// Drawing only backgrounds keeps native hit testing, selection and file actions intact.
void PaintImage(HDC dc, HWND window, const RECT* clip) {
    if (g_drawing || g_stopping || !g_bitmap || !window || !clip) return;
    HWND root = GetAncestor(window, GA_ROOT);
    RECT client{}; GetClientRect(root, &client);
    if (client.right <= 0 || client.bottom <= 0) return;
    POINT offset{}; MapWindowPoints(window, root, &offset, 1);
    double scale = std::max(double(client.right) / g_info.bmWidth, double(client.bottom) / g_info.bmHeight);
    int width = int(g_info.bmWidth * scale + .5), height = int(g_info.bmHeight * scale + .5);
    g_drawing = true;
    std::lock_guard<std::mutex> guard(g_renderMutex);
    std::array<int,4> layout{client.right,client.bottom,offset.x,offset.y};
    if (!g_layouts.count(window) || g_layouts[window] != layout) {
        g_layouts[window]=layout;
        // Explorer can repaint only the newly exposed strip during a resize.
        // Schedule a full pass when the cover crop or pane origin changes.
        InvalidateRect(window,nullptr,TRUE);
    }
    HDC source = CreateCompatibleDC_Original(dc);
    if (source) {
        auto old = SelectObject(source, g_bitmap);
        int saved = SaveDC(dc);
        if (saved) {
            IntersectClipRect(dc, clip->left, clip->top, clip->right, clip->bottom);
            SetStretchBltMode(dc, HALFTONE); SetBrushOrgEx(dc, 0, 0, nullptr);
            StretchBlt(dc, (client.right-width)/2-offset.x, (client.bottom-height)/2-offset.y,
                       width, height, source, 0, 0, g_info.bmWidth, g_info.bmHeight, SRCCOPY);
            RestoreDC(dc, saved);
        }
        SelectObject(source, old); DeleteDC_Original(source);
    }
    g_drawing = false;
}
decltype(&FillRect) FillRect_Original;
int WINAPI FillRect_Hook(HDC dc, const RECT* rect, HBRUSH brush) {
    int result = FillRect_Original(dc, rect, brush);
    if (g_drawing || g_stopping) return result;
    HWND window = WindowForDC(dc);
    // Only neutral surface brushes are replaced. Selection/focus brushes retain
    // their native color, including a full-row selection in Details view.
    LOGBRUSH info{};
    bool background = brush == (HBRUSH)(COLOR_WINDOW + 1);
    if (GetObjectW(brush, sizeof(info), &info) && info.lbStyle == BS_SOLID) {
        auto color = info.lbColor;
        background = background || color == GetSysColor(COLOR_WINDOW) || color == RGB(255,255,255) ||
            color == RGB(25,25,25) || color == RGB(30,30,30) || color == RGB(32,32,32);
    }
    if (window && rect && background)
        PaintImage(dc, window, rect);
    return result;
}
decltype(&SetTextColor) SetTextColor_Original;
COLORREF WINAPI SetTextColor_Hook(HDC dc, COLORREF color) {
    return SetTextColor_Original(dc, !g_stopping && WindowForDC(dc) ? g_text : color);
}
decltype(&DrawThemeTextEx) DrawThemeTextEx_Original;
HRESULT WINAPI DrawThemeTextEx_Hook(HTHEME theme, HDC dc, int part, int state, LPCWSTR text,
                                  int length, DWORD flags, LPRECT rect, const DTTOPTS* opts) {
    if (!g_stopping && WindowForDC(dc)) {
        DTTOPTS copy{};
        if (opts && opts->dwSize == sizeof(copy)) copy = *opts;
        copy.dwSize = sizeof(copy); copy.dwFlags |= DTT_TEXTCOLOR; copy.crText = g_text;
        return DrawThemeTextEx_Original(theme, dc, part, state, text, length, flags, rect, &copy);
    }
    return DrawThemeTextEx_Original(theme, dc, part, state, text, length, flags, rect, opts);
}

BOOL CALLBACK RedrawChild(HWND window, LPARAM) { InvalidateRect(window, nullptr, TRUE); return TRUE; }
BOOL CALLBACK RedrawExplorer(HWND window, LPARAM) {
    DWORD pid{}; GetWindowThreadProcessId(window, &pid);
    if (pid == GetCurrentProcessId() && ClassIs(window, L"CabinetWClass")) {
        StyleCaption(window);
        RedrawWindow(window, nullptr, nullptr, RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN | RDW_FRAME);
        EnumChildWindows(window, RedrawChild, 0);
    }
    return TRUE;
}

#ifndef THEMESTUDIO_PAINT_TEST
BOOL Wh_ModInit() {
    if (GetAsyncKeyState(VK_ESCAPE) & 0x8000) return FALSE;
    PCWSTR path = Wh_GetStringSetting(L"imagePath");
    g_bitmap = (HBITMAP)LoadImageW(nullptr, path, IMAGE_BITMAP, 0, 0, LR_LOADFROMFILE | LR_CREATEDIBSECTION);
    Wh_FreeStringSetting(path);
    if (!g_bitmap || !GetObjectW(g_bitmap, sizeof(g_info), &g_info) || g_info.bmWidth <= 0 ||
        g_info.bmHeight <= 0 || g_info.bmWidth > 3840 || g_info.bmHeight > 2160) {
        if (g_bitmap) DeleteObject(g_bitmap); g_bitmap = nullptr;
        Wh_Log(L"Validated background bitmap unavailable"); return FALSE;
    }
    PCWSTR color = Wh_GetStringSetting(L"textColor");
    if (color && color[0] == L'#' && wcslen(color) == 7) {
        wchar_t* end{}; unsigned long rgb = wcstoul(color + 1, &end, 16);
        if (end && !*end) g_text = RGB((rgb>>16)&255, (rgb>>8)&255, rgb&255);
    }
    Wh_FreeStringSetting(color);
    color = Wh_GetStringSetting(L"captionColor");
    if (color && color[0] == L'#' && wcslen(color) == 7) {
        wchar_t* end{}; unsigned long rgb = wcstoul(color + 1, &end, 16);
        if (end && !*end) g_caption = RGB((rgb>>16)&255, (rgb>>8)&255, rgb&255);
    }
    Wh_FreeStringSetting(color);
    bool ok = WindhawkUtils::SetFunctionHook(BeginPaint, BeginPaint_Hook, &BeginPaint_Original) &&
        WindhawkUtils::SetFunctionHook(EndPaint, EndPaint_Hook, &EndPaint_Original) &&
        WindhawkUtils::SetFunctionHook(DestroyWindow, DestroyWindow_Hook, &DestroyWindow_Original) &&
        WindhawkUtils::SetFunctionHook(CreateCompatibleDC, CreateCompatibleDC_Hook, &CreateCompatibleDC_Original) &&
        WindhawkUtils::SetFunctionHook(DeleteDC, DeleteDC_Hook, &DeleteDC_Original) &&
        WindhawkUtils::SetFunctionHook(FillRect, FillRect_Hook, &FillRect_Original) &&
        WindhawkUtils::SetFunctionHook(SetTextColor, SetTextColor_Hook, &SetTextColor_Original) &&
        WindhawkUtils::SetFunctionHook(DrawThemeTextEx, DrawThemeTextEx_Hook, &DrawThemeTextEx_Original);
    if (!ok) { DeleteObject(g_bitmap); g_bitmap = nullptr; return FALSE; }
    return TRUE;
}
void Wh_ModAfterInit() { EnumWindows(RedrawExplorer, 0); }
void Wh_ModBeforeUninit() { g_stopping = true; RestoreCaptions(); EnumWindows(RedrawExplorer, 0); }
void Wh_ModUninit() { if (g_bitmap) DeleteObject(g_bitmap); g_bitmap = nullptr; EnumWindows(RedrawExplorer, 0); }
BOOL Wh_ModSettingsChanged(BOOL* reload) { *reload = TRUE; return TRUE; }
#endif
