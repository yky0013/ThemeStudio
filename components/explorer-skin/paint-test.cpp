// Tests the production GDI renderer in hidden, isolated Win32 windows.
#define THEMESTUDIO_PAINT_TEST
#include "themestudio-explorer-background.wh.cpp"
#include <cstdio>
PCWSTR testTheme=L"Explorer::TreeView";
HRESULT WINAPI TestThemeClass(HTHEME,LPWSTR name,int count){lstrcpynW(name,testTheme,count);return S_OK;}
HRESULT WINAPI TestNestedWhiteTheme(HTHEME,HDC dc,int,int,const RECT* rect,const RECT*) {
    return FillRect_Hook(dc,rect,(HBRUSH)(COLOR_WINDOW+1)) ? S_OK : E_FAIL;
}
HRESULT WINAPI TestTextEx(HTHEME,HDC,int,int,LPCWSTR,int,DWORD,LPRECT,const DTTOPTS* options) {
    return options && (options->dwFlags&DTT_TEXTCOLOR) && options->crText==g_text ? S_OK : E_FAIL;
}
HRESULT WINAPI TestOriginalTheme(HTHEME,HDC dc,int,int,const RECT* rect,const RECT*){
    HBRUSH brush=CreateSolidBrush(RGB(50,90,160));FillRect_Original(dc,rect,brush);DeleteObject(brush);return S_OK;
}
HRESULT WINAPI TestOriginalThemeEx(HTHEME theme,HDC dc,int part,int state,const RECT* rect,const DTBGOPTS*) {
    return TestOriginalTheme(theme,dc,part,state,rect,nullptr);
}
BOOL WINAPI TestOpaqueText(HDC dc,int,int,UINT flags,const RECT* rect,LPCWSTR,UINT,const INT*){
    if((flags&ETO_OPAQUE)&&rect){HBRUSH brush=CreateSolidBrush(GetBkColor(dc));FillRect_Original(dc,rect,brush);DeleteObject(brush);}return TRUE;
}
LRESULT CALLBACK TestPreviewSubclass(HWND window,UINT msg,WPARAM wp,LPARAM lp,UINT_PTR,DWORD_PTR ref){return SurfaceSubclass(window,msg,wp,lp,ref);}

int main() {
    FillRect_Original=FillRect; CreateCompatibleDC_Original=CreateCompatibleDC;
    DeleteDC_Original=DeleteDC; SetTextColor_Original=SetTextColor;
    WNDCLASSW cls{}; cls.lpfnWndProc=DefWindowProcW; cls.hInstance=GetModuleHandleW(nullptr);
    for (auto name:{L"CabinetWClass", L"SHELLDLL_DefView", L"DirectUIHWND", L"DUIViewWndClassName", L"ThemeStudioTestOther"}) {
        cls.lpszClassName=name; if (!RegisterClassW(&cls)) return 1;
    }
    HWND root=CreateWindowW(L"CabinetWClass",L"",WS_POPUP,0,0,480,320,nullptr,nullptr,cls.hInstance,nullptr);
    HWND view=CreateWindowW(L"SHELLDLL_DefView",L"",WS_CHILD,100,80,380,240,root,nullptr,cls.hInstance,nullptr);
    HWND content=CreateWindowW(L"DirectUIHWND",L"",WS_CHILD,0,0,380,240,view,nullptr,cls.hInstance,nullptr);
    HWND other=CreateWindowW(L"ThemeStudioTestOther",L"",WS_POPUP,0,0,480,320,nullptr,nullptr,cls.hInstance,nullptr);
    if (!root||!view||!content||!other||!IsSurface(content)||IsSurface(other)) return 2;
    HDC screen=GetDC(nullptr), src=CreateCompatibleDC(screen), dst=CreateCompatibleDC(screen);
    g_bitmap=CreateCompatibleBitmap(screen,480,320); GetObjectW(g_bitmap,sizeof(g_info),&g_info);
    HBITMAP output=CreateCompatibleBitmap(screen,380,240);
    auto oldSrc=SelectObject(src,g_bitmap),oldDst=SelectObject(dst,output);
    RECT all{0,0,480,320}; HBRUSH red=CreateSolidBrush(RGB(210,40,60)); FillRect(src,&all,red);
    // A green band at root y=100..140 must land at child y=20..60.
    HBRUSH green=CreateSolidBrush(RGB(30,180,70)); RECT band{0,100,480,140}; FillRect(src,&band,green);
    SelectObject(src,oldSrc); Track(dst,content);
    RECT target{0,0,380,240}; FillRect_Hook(dst,&target,(HBRUSH)(COLOR_WINDOW+1));
    if(GetPixel(dst,20,30)!=RGB(30,180,70)||GetPixel(dst,20,80)!=RGB(210,40,60)) return 3;
    RECT selection{0,80,380,110}; HBRUSH blue=CreateSolidBrush(RGB(50,90,160)); FillRect_Hook(dst,&selection,blue);
    if(GetPixel(dst,20,90)!=RGB(50,90,160)) return 4;
    // A partial dirty rectangle repaints the correct image instead of solid gray.
    RECT dirty{10,20,60,60}; FillRect_Hook(dst,&dirty,(HBRUSH)(COLOR_WINDOW+1));
    if(GetPixel(dst,20,30)!=RGB(30,180,70)) return 5;
    INITCOMMONCONTROLSEX controls{sizeof(controls),ICC_TREEVIEW_CLASSES};InitCommonControlsEx(&controls);
    HWND tree=CreateWindowW(L"SysTreeView32",L"",WS_CHILD,100,80,380,240,root,nullptr,cls.hInstance,nullptr);
    if(!tree)return 10;
    Track(dst,tree);GetThemeClass_Original=TestThemeClass;DrawThemeBackground_Original=TestOriginalTheme;
    DrawThemeBackground_Hook((HTHEME)1,dst,TVP_TREEITEM,TREIS_NORMAL,&target,nullptr);
    if(GetPixel(dst,20,30)!=RGB(30,180,70))return 11;
    for(int state:{TREIS_HOT,TREIS_SELECTED,TREIS_SELECTEDNOTFOCUS,TREIS_HOTSELECTED}){
        DrawThemeBackground_Hook((HTHEME)1,dst,TVP_TREEITEM,state,&target,nullptr);
        if(GetPixel(dst,20,30)!=RGB(50,90,160))return 12;
    }
    ExtTextOutW_Original=TestOpaqueText;SetBkColor(dst,RGB(255,255,255));
    ExtTextOutW_Hook(dst,0,0,ETO_OPAQUE,&target,L"",0,nullptr);
    if(GetPixel(dst,20,30)!=RGB(30,180,70))return 17;
    SetBkColor(dst,RGB(50,90,160));ExtTextOutW_Hook(dst,0,0,ETO_OPAQUE,&target,L"",0,nullptr);
    if(GetPixel(dst,20,30)!=RGB(50,90,160))return 18;
    cls.lpszClassName=L"Shell Preview Extension Host";cls.hbrBackground=(HBRUSH)(COLOR_WINDOW+1);
    if(!RegisterClassW(&cls))return 13;
    HWND preview=CreateWindowW(cls.lpszClassName,L"",WS_CHILD,100,80,380,240,root,nullptr,cls.hInstance,nullptr);
    if(!preview||!IsSurface(preview))return 14;
    SetWindowSubclass(preview,TestPreviewSubclass,1,0);
    SendMessageW(preview,WM_ERASEBKGND,(WPARAM)dst,0);
    if(GetPixel(dst,20,30)!=RGB(30,180,70))return 15;
    RemoveWindowSubclass(preview,TestPreviewSubclass,1);
    SendMessageW(preview,WM_ERASEBKGND,(WPARAM)dst,0);
    if(GetPixel(dst,20,30)!=GetSysColor(COLOR_WINDOW))return 16;
    // Regression: the no-selection preview and columns belong to OUTER DUI,
    // not to the Shell Preview Extension Host used for a selected document.
    HWND duiHost=CreateWindowW(L"DUIViewWndClassName",L"",WS_CHILD,100,80,380,240,root,nullptr,cls.hInstance,nullptr);
    HWND outer=CreateWindowW(L"DirectUIHWND",L"",WS_CHILD,0,0,380,240,duiHost,nullptr,cls.hInstance,nullptr);
    HWND document=CreateWindowW(L"ThemeStudioTestOther",L"",WS_CHILD,0,0,380,240,preview,nullptr,cls.hInstance,nullptr);
    HWND documentDui=CreateWindowW(L"DirectUIHWND",L"",WS_CHILD,0,0,380,240,document,nullptr,cls.hInstance,nullptr);
    if(!outer||!IsSurface(outer)||IsSurface(document))return 20;
    // Document handler descendants must never be classified as shell chrome.
    if(IsSurface(documentDui))return 21;
    Track(dst,outer);testTheme=L"Explorer::ReadingPane";
    DrawThemeBackground_Hook((HTHEME)1,dst,1,0,&target,nullptr);
    if(GetPixel(dst,20,30)!=RGB(30,180,70))return 22;
    testTheme=L"Explorer::Header";
    for(int part:{HP_HEADERITEM,HP_HEADERITEMLEFT,HP_HEADERITEMRIGHT}) {
        DrawThemeBackground_Hook((HTHEME)1,dst,part,HIS_NORMAL,&target,nullptr);
        if(GetPixel(dst,20,30)!=RGB(30,180,70))return 23;
    }
    // The active sort column uses SORTEDNORMAL, not NORMAL. Reproduce the
    // reported white Name header with a native renderer that fills it white.
    DrawThemeBackground_Original=TestNestedWhiteTheme;
    for(int state:{HIS_SORTEDNORMAL,HIS_ICONNORMAL,HIS_ICONSORTEDNORMAL}) {
        DrawThemeBackground_Hook((HTHEME)1,dst,HP_HEADERITEM,state,&target,nullptr);
        if(GetPixel(dst,20,30)!=RGB(30,180,70)) {
            std::printf("FAIL: idle header state %d retained an opaque native background\n",state);
            return 43;
        }
    }
    // Check actual destination pixels and clip handling for both uxtheme entry
    // points, then verify readable feedback and preserved native glyph paths.
    DrawThemeBackground_Original=TestOriginalTheme;
    DrawThemeBackgroundEx_Original=TestOriginalThemeEx;
    FillRect_Original(dst,&target,blue);
    DTBGOPTS clipped{sizeof(clipped),DTBG_CLIPRECT,{10,20,50,45}};
    DrawThemeBackgroundEx_Hook((HTHEME)1,dst,HP_HEADERITEM,HIS_SORTEDNORMAL,&target,&clipped);
    if(GetPixel(dst,20,30)!=RGB(30,180,70) || GetPixel(dst,60,30)!=RGB(50,90,160))return 44;
    for(int state:{HIS_HOT,HIS_PRESSED,HIS_SORTEDHOT,HIS_SORTEDPRESSED,
                   HIS_ICONHOT,HIS_ICONPRESSED,HIS_ICONSORTEDHOT,HIS_ICONSORTEDPRESSED}) {
        DrawThemeBackground_Hook((HTHEME)1,dst,HP_HEADERITEM,state,&target,nullptr);
        COLORREF feedback=GetPixel(dst,20,30);
        if(GetRValue(feedback)<=30 || GetRValue(feedback)>=90 || GetGValue(feedback)<=180 ||
           GetGValue(feedback)>=205 || GetBValue(feedback)<=70 || GetBValue(feedback)>=125)return 45;
    }
    for(int part:{HP_HEADERSORTARROW,HP_HEADERDROPDOWN,HP_HEADERDROPDOWNFILTER,HP_HEADEROVERFLOW}) {
        DrawThemeBackground_Hook((HTHEME)1,dst,part,1,&target,nullptr);
        if(GetPixel(dst,20,30)!=RGB(50,90,160))return 46;
    }
    DrawThemeBackground_Hook((HTHEME)1,dst,0,HIS_NORMAL,&target,nullptr);
    if(GetPixel(dst,20,30)!=RGB(30,180,70))return 47;
    testTheme=L"Explorer::PreviewPane";
    for(int part:{3,4}) {
        DrawThemeBackground_Original=TestNestedWhiteTheme;
        RECT separator{10,0,15,200};
        FillRect_Original(dst,&target,blue);
        DrawThemeBackground_Hook((HTHEME)1,dst,part,0,&separator,nullptr);
        if(GetPixel(dst,12,30)!=RGB(30,180,70) || GetPixel(dst,12,80)!=RGB(210,40,60) ||
           GetPixel(dst,16,30)!=RGB(50,90,160))return 48;
        DrawThemeBackgroundEx_Hook((HTHEME)1,dst,part,0,&target,&clipped);
        if(GetPixel(dst,20,30)!=RGB(30,180,70) || GetPixel(dst,60,30)!=RGB(50,90,160))return 49;
        DrawThemeBackground_Original=TestOriginalTheme;
        // A loaded preview host has its own content: never erase its parts.
        Track(dst,preview);
        DrawThemeBackground_Hook((HTHEME)1,dst,part,0,&target,nullptr);
        if(GetPixel(dst,20,30)!=RGB(50,90,160))return 50;
        Track(dst,outer);
        DrawThemeBackground_Hook((HTHEME)1,dst,part,1,&target,nullptr);
        if(GetPixel(dst,20,30)!=RGB(50,90,160))return 51;
    }
    DrawThemeBackground_Hook((HTHEME)1,dst,1,0,&target,nullptr);
    if(GetPixel(dst,20,30)!=RGB(50,90,160))return 52;
    testTheme=L"Explorer::Header";
    DrawThemeBackground_Original=TestNestedWhiteTheme;
    DrawThemeBackground_Hook((HTHEME)1,dst,HP_HEADERITEM,HIS_PRESSED,&target,nullptr);
    if(GetPixel(dst,20,30)==GetSysColor(COLOR_WINDOW))return 24;
    // Navigation selection still delegates even if native painting fills white.
    Track(dst,tree);testTheme=L"Explorer::TreeView";
    DrawThemeBackground_Hook((HTHEME)1,dst,TVP_TREEITEM,TREIS_SELECTED,&target,nullptr);
    if(GetPixel(dst,20,30)!=GetSysColor(COLOR_WINDOW))return 53;
    Track(dst,outer);
    DrawThemeBackground_Original=TestOriginalTheme;
    testTheme=L"Explorer::Status";
    DrawThemeBackground_Hook((HTHEME)1,dst,SP_PANE,0,&target,nullptr);
    if(GetPixel(dst,20,30)!=RGB(30,180,70))return 42;
    testTheme=L"Explorer::ScrollBar";
    DrawThemeBackground_Hook((HTHEME)1,dst,SBP_UPPERTRACKVERT,SCRBS_NORMAL,&target,nullptr);
    if(GetPixel(dst,20,30)!=RGB(30,180,70))return 25;
    DrawThemeBackground_Hook((HTHEME)1,dst,SBP_UPPERTRACKVERT,SCRBS_HOT,&target,nullptr);
    if(GetPixel(dst,20,30)!=RGB(50,90,160))return 26;
    SetBkColor(dst,RGB(255,255,255));ExtTextOutW_Hook(dst,0,0,ETO_OPAQUE,&target,L"",0,nullptr);
    if(GetPixel(dst,20,30)!=RGB(30,180,70))return 27;
    DrawThemeTextEx_Original=TestTextEx;
    if(FAILED(DrawThemeText_Hook((HTHEME)1,dst,1,0,L"preview",7,0,0,&target)))return 28;
    // The static's CTLCOLOR response must not repaint it with a solid brush.
    HWND label=CreateWindowW(L"Static",L"Choose a file",WS_CHILD,0,0,380,240,preview,nullptr,cls.hInstance,nullptr);
    SetWindowSubclass(preview,TestPreviewSubclass,1,0);
    auto brush=(HBRUSH)SendMessageW(preview,WM_CTLCOLORSTATIC,(WPARAM)dst,(LPARAM)label);
    LOGBRUSH labelBrush{};GetObjectW(brush,sizeof(labelBrush),&labelBrush);
    if(labelBrush.lbStyle!=BS_HOLLOW || GetBkMode(dst)!=TRANSPARENT || GetTextColor(dst)!=g_text)return 29;
    if(GetPixel(dst,20,30)!=RGB(30,180,70))return 30;
    RemoveWindowSubclass(preview,TestPreviewSubclass,1);
    // Real uxtheme buffer, including non-zero clipping origin and DC disposal.
    BeginBufferedPaint_Original=BeginBufferedPaint;EndBufferedPaint_Original=EndBufferedPaint;
    BufferedPaintInit();Track(dst,outer);
    RECT bufferedArea{10,20,100,90};HDC bufferedDC{};
    HPAINTBUFFER buffer=BeginBufferedPaint_Hook(dst,&bufferedArea,BPBF_TOPDOWNDIB,nullptr,&bufferedDC);
    if(!buffer||WindowForDC(bufferedDC)!=outer)return 31;
    FillRect_Hook(bufferedDC,&bufferedArea,(HBRUSH)(COLOR_WINDOW+1));
    if(GetPixel(bufferedDC,20,30)!=RGB(30,180,70))return 32;
    if(FAILED(EndBufferedPaint_Hook(buffer,TRUE))||WindowForDC(bufferedDC)||!g_paintBuffers.empty())return 33;
    if(GetPixel(dst,20,30)!=RGB(30,180,70))return 34;
    // Alpha-composited buffers must retain the image even after GDI clears alpha.
    BLENDFUNCTION blend{AC_SRC_OVER,0,255,AC_SRC_ALPHA};
    BP_PAINTPARAMS alphaParams{sizeof(alphaParams),0,nullptr,&blend};
    FillRect_Original(dst,&target,blue);
    buffer=BeginBufferedPaint_Hook(dst,&bufferedArea,BPBF_TOPDOWNDIB,&alphaParams,&bufferedDC);
    if(!buffer)return 37;
    FillRect_Hook(bufferedDC,&bufferedArea,(HBRUSH)(COLOR_WINDOW+1));
    BufferedPaintSetAlpha(buffer,&bufferedArea,0);
    if(FAILED(EndBufferedPaint_Hook(buffer,TRUE))||GetPixel(dst,20,30)!=RGB(30,180,70))return 38;
    buffer=BeginBufferedPaint_Hook(dst,&bufferedArea,BPBF_TOPDOWNDIB,&alphaParams,&bufferedDC);
    if(!buffer)return 39;
    FillRect_Hook(bufferedDC,&bufferedArea,(HBRUSH)(COLOR_WINDOW+1));
    FillRect_Original(dst,&target,blue);EndBufferedPaint_Hook(buffer,FALSE);
    if(GetPixel(dst,20,30)!=RGB(50,90,160))return 40;
    BufferedPaintUnInit();
    GetDC_Original=GetDC;GetDCEx_Original=GetDCEx;ReleaseDC_Original=ReleaseDC;
    HDC direct=GetDC_Hook(outer);if(WindowForDC(direct)!=outer)return 35;
    ReleaseDC_Hook(outer,direct);
    {std::lock_guard<std::mutex> guard(g_mutex);if(g_dcWindows.count(direct))return 36;}
    // Automatic child destruction also clears our HWND bookkeeping.
    SetWindowSubclass(outer,TestPreviewSubclass,1,0);g_subclassed.insert(outer);
    DestroyWindow(duiHost);
    if(g_subclassed.count(outer)||WindowForDC(dst))return 41;
    DestroyWindow(preview);DestroyWindow(tree);Track(dst,content);
    if(SetTextColor_Hook(dst,RGB(0,0,0))==CLR_INVALID||GetTextColor(dst)!=g_text) return 6;
    DWORD before=GetGuiResources(GetCurrentProcess(),GR_GDIOBJECTS);
    testTheme=L"Explorer::Header";
    for(int i=0;i<500;i++) {
        FillRect_Hook(dst,&target,(HBRUSH)(COLOR_WINDOW+1));
        DrawThemeBackground_Hook((HTHEME)1,dst,HP_HEADERITEM,HIS_SORTEDHOT,&target,nullptr);
    }
    DWORD after=GetGuiResources(GetCurrentProcess(),GR_GDIOBJECTS);
    if(after>before+1) return 7;
    // A DC for an unrelated window is never tracked or styled.
    HDC outsider=CreateCompatibleDC(screen); Track(outsider,other);
    if(WindowForDC(outsider)) return 8;
    DeleteDC_Hook(outsider); SelectObject(dst,oldDst); DeleteDC_Hook(dst);
    if(!g_dcWindows.empty()) return 9;
    DeleteDC(src); DeleteObject(output); DeleteObject(g_bitmap); g_bitmap=nullptr;
    DeleteObject(red); DeleteObject(green); DeleteObject(blue); ReleaseDC(nullptr,screen);
    DestroyWindow(other); DestroyWindow(root);
    std::puts("PASS: root-aligned image; outer DUI empty preview; sorted/icon header idle states and empty strip; both PreviewPane splitters; clipped DrawThemeBackground/Ex; translucent hot/pressed headers and native sort/dropdown glyphs; header/status/scrollbar paths; preserved navigation selection including nested white fills; static text transparency; real uxtheme buffered paint, alpha commit/cancel and DC cleanup; document exclusion; text contrast; 500-paint GDI lifetime including header feedback");
    return 0;
}
