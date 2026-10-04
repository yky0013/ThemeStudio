// ==WindhawkMod==
// @id themestudio-explorer-background
// @name ThemeStudio Explorer background
// @description Theme image in the native Explorer file list and navigation pane
// @version 1.1.0
// @author ThemeStudio contributors
// @license MIT
// @include explorer.exe
// @architecture x86-64
// @compilerOptions -luser32 -lgdi32 -luxtheme -ldwmapi -lcomctl32
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
#include <commctrl.h>
#include <vssym32.h>
#ifndef THEMESTUDIO_PAINT_TEST
#include <windhawk_utils.h>
#endif
#include <algorithm>
#include <atomic>
#include <array>
#include <mutex>
#include <unordered_map>
#include <unordered_set>
#include <string>

// Immutable while hooks are active. A setting change requests a Windhawk reload.
HBITMAP g_bitmap = nullptr;
BITMAP g_info{};
COLORREF g_text = RGB(228, 237, 250);
COLORREF g_caption = RGB(8, 27, 50);
HBRUSH g_panelBrush = nullptr;
std::atomic<bool> g_stopping{false};
std::mutex g_mutex;
std::mutex g_renderMutex;
std::unordered_map<HDC, HWND> g_dcWindows;
std::unordered_map<HWND, std::array<int,4>> g_layouts;
struct CaptionState { DWORD dark, background, text; bool hasDark, hasBackground, hasText; };
std::unordered_map<HWND, CaptionState> g_captions;
std::unordered_set<HWND> g_subclassed;
thread_local bool g_drawing = false;

bool ClassIs(HWND window, PCWSTR expected) {
    WCHAR name[128]{};
    return GetClassNameW(window, name, ARRAYSIZE(name)) && !wcscmp(name, expected);
}
bool IsExplorer(HWND window) {
    return window && ClassIs(GetAncestor(window, GA_ROOT), L"CabinetWClass");
}
bool IsPreviewHost(HWND window) {
    return ClassIs(window,L"Shell Preview Extension Host") || ClassIs(window,L"Shell Preview Extension Host Previewer");
}
bool IsPreviewSurface(HWND window) {
    if (IsPreviewHost(window)) return true;
    // Paint the empty host/placeholder, never a document viewer or RichEdit content.
    if (!ClassIs(window,L"DirectUIHWND") && !ClassIs(window,L"Static")) return false;
    for (HWND parent=GetParent(window);parent;parent=GetParent(parent)) {
        if (IsPreviewHost(parent)) return true;
        if (ClassIs(parent,L"CabinetWClass")) break;
    }
    return false;
}
bool IsSurface(HWND window) {
    if (!IsExplorer(window)) return false;
    // Do not touch desktop icons, dialogs, menus or other processes.
    return (ClassIs(window, L"DirectUIHWND") && ClassIs(GetParent(window), L"SHELLDLL_DefView")) ||
           ClassIs(window,L"SysTreeView32") || ClassIs(window,L"SysHeader32") ||
           ClassIs(window,L"msctls_statusbar32") || IsPreviewSurface(window);
}
void InstallSurfaceSubclass(HWND window);
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
    InstallSurfaceSubclass(window);
    HDC dc = BeginPaint_Original(window, paint);
    Track(dc, window);
    return dc;
}
decltype(&DestroyWindow) DestroyWindow_Original;
BOOL WINAPI DestroyWindow_Hook(HWND window) {
    { std::lock_guard<std::mutex> guard(g_mutex);
      g_captions.erase(window);
      g_subclassed.erase(window);
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

LRESULT CALLBACK SurfaceSubclass(HWND window, UINT message, WPARAM wParam, LPARAM lParam, DWORD_PTR) {
    if (!g_stopping) {
        if (message==WM_ERASEBKGND && IsSurface(window)) {
            RECT rect{}; GetClientRect(window,&rect);
            PaintImage((HDC)wParam,window,&rect);
            return 1;
        }
        if (message==WM_CTLCOLORSTATIC && IsPreviewSurface((HWND)lParam)) {
            ::SetTextColor((HDC)wParam,g_text); SetBkMode((HDC)wParam,TRANSPARENT);
            return (LRESULT)g_panelBrush;
        }
    }
    return DefSubclassProc(window,message,wParam,lParam);
}
void InstallSurfaceSubclass(HWND window) {
    if (g_stopping || !IsExplorer(window) ||
        (!IsPreviewSurface(window) && !ClassIs(window,L"msctls_statusbar32"))) return;
    { std::lock_guard<std::mutex> guard(g_mutex); if(g_subclassed.count(window)) return; }
#ifndef THEMESTUDIO_PAINT_TEST
    if (WindhawkUtils::SetWindowSubclassFromAnyThread(window,SurfaceSubclass,0)) {
        std::lock_guard<std::mutex> guard(g_mutex); g_subclassed.insert(window);
    }
#endif
}
using GetThemeClass_t=HRESULT(WINAPI*)(HTHEME,LPWSTR,int);
GetThemeClass_t GetThemeClass_Original=nullptr;
bool ThemeClassIs(HTHEME theme, PCWSTR wanted) {
    WCHAR name[128]{};
    if (!GetThemeClass_Original || FAILED(GetThemeClass_Original(theme,name,ARRAYSIZE(name)))) return false;
    size_t length=wcslen(name), match=wcslen(wanted);
    return length>=match && !_wcsicmp(name+length-match,wanted) &&
        (length==match || (length>=match+2 && name[length-match-1]==L':' && name[length-match-2]==L':'));
}
bool ReplaceNormalBackground(HTHEME theme,HDC dc,int part,int state,const RECT* rect,const RECT* clip) {
    if(g_stopping || g_drawing || !rect) return false;
    HWND window=WindowForDC(dc);
    if(!window) return false;
    const bool normalTree=ClassIs(window,L"SysTreeView32") && ThemeClassIs(theme,L"TreeView") &&
        part==TVP_TREEITEM && state==TREIS_NORMAL;
    const bool normalHeader=ClassIs(window,L"SysHeader32") && ThemeClassIs(theme,L"Header") &&
        part==HP_HEADERITEM && state==HIS_NORMAL;
    const bool pane=IsPreviewSurface(window) && ThemeClassIs(theme,L"ReadingPane") && part==1;
    const bool status=ClassIs(window,L"msctls_statusbar32") && ThemeClassIs(theme,L"Status");
    if(!normalTree && !normalHeader && !pane && !status) return false;
    RECT area=*rect;
    if(clip && !IntersectRect(&area,rect,clip)) return true;
    PaintImage(dc,window,&area);
    return true;
}
decltype(&DrawThemeBackground) DrawThemeBackground_Original;
HRESULT WINAPI DrawThemeBackground_Hook(HTHEME theme,HDC dc,int part,int state,const RECT* rect,const RECT* clip) {
    if(ReplaceNormalBackground(theme,dc,part,state,rect,clip)) return S_OK;
    // HOT / SELECTED / SELECTEDNOTFOCUS / HOTSELECTED keep their existing rendering.
    return DrawThemeBackground_Original(theme,dc,part,state,rect,clip);
}
decltype(&DrawThemeBackgroundEx) DrawThemeBackgroundEx_Original;
HRESULT WINAPI DrawThemeBackgroundEx_Hook(HTHEME theme,HDC dc,int part,int state,const RECT* rect,const DTBGOPTS* options) {
    const RECT* clip=options && options->dwSize==sizeof(DTBGOPTS) && (options->dwFlags&DTBG_CLIPRECT) ? &options->rcClip : nullptr;
    if(ReplaceNormalBackground(theme,dc,part,state,rect,clip)) return S_OK;
    return DrawThemeBackgroundEx_Original(theme,dc,part,state,rect,options);
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
            color == RGB(25,25,25) || color == RGB(30,30,30) || color == RGB(32,32,32) || color==g_caption;
    }
    if (window && rect && background)
        PaintImage(dc, window, rect);
    return result;
}
decltype(&SetTextColor) SetTextColor_Original;
COLORREF WINAPI SetTextColor_Hook(HDC dc, COLORREF color) {
    return SetTextColor_Original(dc, !g_stopping && WindowForDC(dc) ? g_text : color);
}
bool IsSelectedTreeRow(HWND window,const RECT* rect) {
    if(!rect || !ClassIs(window,L"SysTreeView32"))return false;
    int rowHeight=TreeView_GetItemHeight(window);
    if(rowHeight<=0 || rect->bottom-rect->top>rowHeight*2)return false;
    TVHITTESTINFO hit{};hit.pt={rect->left+4,(rect->top+rect->bottom)/2};
    HTREEITEM item=TreeView_HitTest(window,&hit);
    return item && (TreeView_GetItemState(window,item,TVIS_SELECTED|TVIS_DROPHILITED)&(TVIS_SELECTED|TVIS_DROPHILITED));
}
decltype(&ExtTextOutW) ExtTextOutW_Original;
BOOL WINAPI ExtTextOutW_Hook(HDC dc,int x,int y,UINT flags,const RECT* rect,LPCWSTR text,UINT length,const INT* spacing) {
    HWND window=!g_stopping&&!g_drawing?WindowForDC(dc):nullptr;
    COLORREF background=GetBkColor(dc);
    bool neutral=background==GetSysColor(COLOR_WINDOW)||background==RGB(255,255,255)||
        background==RGB(25,25,25)||background==RGB(30,30,30)||background==RGB(32,32,32)||background==g_caption;
    // Common-controls can clear an unselected row through ETO_OPAQUE without
    // calling FillRect or DrawThemeBackground. Keep selected row painting intact.
    if(window&&(ClassIs(window,L"SysTreeView32")||IsPreviewSurface(window))&&neutral&&!IsSelectedTreeRow(window,rect)) {
        if((flags&ETO_OPAQUE)&&rect)PaintImage(dc,window,rect);
        int mode=SetBkMode(dc,TRANSPARENT);
        BOOL result=ExtTextOutW_Original(dc,x,y,flags&~ETO_OPAQUE,rect,text,length,spacing);
        SetBkMode(dc,mode);return result;
    }
    return ExtTextOutW_Original(dc,x,y,flags,rect,text,length,spacing);
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

BOOL CALLBACK RedrawChild(HWND window, LPARAM) { InstallSurfaceSubclass(window); InvalidateRect(window,nullptr,TRUE); return TRUE; }
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
    g_panelBrush=CreateSolidBrush(g_caption);
    GetThemeClass_Original=(GetThemeClass_t)GetProcAddress(GetModuleHandleW(L"uxtheme.dll"),MAKEINTRESOURCEA(74));
    bool ok = WindhawkUtils::SetFunctionHook(BeginPaint, BeginPaint_Hook, &BeginPaint_Original) &&
        WindhawkUtils::SetFunctionHook(EndPaint, EndPaint_Hook, &EndPaint_Original) &&
        WindhawkUtils::SetFunctionHook(DestroyWindow, DestroyWindow_Hook, &DestroyWindow_Original) &&
        WindhawkUtils::SetFunctionHook(CreateCompatibleDC, CreateCompatibleDC_Hook, &CreateCompatibleDC_Original) &&
        WindhawkUtils::SetFunctionHook(DeleteDC, DeleteDC_Hook, &DeleteDC_Original) &&
        WindhawkUtils::SetFunctionHook(FillRect, FillRect_Hook, &FillRect_Original) &&
        WindhawkUtils::SetFunctionHook(SetTextColor, SetTextColor_Hook, &SetTextColor_Original) &&
        WindhawkUtils::SetFunctionHook(ExtTextOutW,ExtTextOutW_Hook,&ExtTextOutW_Original) &&
        WindhawkUtils::SetFunctionHook(DrawThemeBackground,DrawThemeBackground_Hook,&DrawThemeBackground_Original) &&
        WindhawkUtils::SetFunctionHook(DrawThemeBackgroundEx,DrawThemeBackgroundEx_Hook,&DrawThemeBackgroundEx_Original) &&
        WindhawkUtils::SetFunctionHook(DrawThemeTextEx, DrawThemeTextEx_Hook, &DrawThemeTextEx_Original);
    if (!ok) { DeleteObject(g_bitmap); g_bitmap=nullptr; if(g_panelBrush)DeleteObject(g_panelBrush); return FALSE; }
    return TRUE;
}
void Wh_ModAfterInit() { EnumWindows(RedrawExplorer, 0); }
void Wh_ModBeforeUninit() { g_stopping=true; WindhawkUtils::RemoveAllWindowSubclasses(); RestoreCaptions(); EnumWindows(RedrawExplorer,0); }
void Wh_ModUninit() { if(g_bitmap)DeleteObject(g_bitmap);g_bitmap=nullptr;if(g_panelBrush)DeleteObject(g_panelBrush);g_panelBrush=nullptr;EnumWindows(RedrawExplorer,0); }
BOOL Wh_ModSettingsChanged(BOOL* reload) { *reload = TRUE; return TRUE; }
#endif
