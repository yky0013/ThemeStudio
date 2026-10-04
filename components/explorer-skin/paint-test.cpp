// Tests the production GDI renderer in hidden, isolated Win32 windows.
#define THEMESTUDIO_PAINT_TEST
#include "themestudio-explorer-background.wh.cpp"
#include <cstdio>

int main() {
    FillRect_Original=FillRect; CreateCompatibleDC_Original=CreateCompatibleDC;
    DeleteDC_Original=DeleteDC; SetTextColor_Original=SetTextColor;
    WNDCLASSW cls{}; cls.lpfnWndProc=DefWindowProcW; cls.hInstance=GetModuleHandleW(nullptr);
    for (auto name:{L"CabinetWClass", L"SHELLDLL_DefView", L"DirectUIHWND", L"ThemeStudioTestOther"}) {
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
    if(SetTextColor_Hook(dst,RGB(0,0,0))==CLR_INVALID||GetTextColor(dst)!=g_text) return 6;
    DWORD before=GetGuiResources(GetCurrentProcess(),GR_GDIOBJECTS);
    for(int i=0;i<500;i++) FillRect_Hook(dst,&target,(HBRUSH)(COLOR_WINDOW+1));
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
    std::puts("PASS: root-aligned image, partial repaint, native selection, text contrast, scoped HWNDs, 500-paint GDI lifetime");
    return 0;
}
