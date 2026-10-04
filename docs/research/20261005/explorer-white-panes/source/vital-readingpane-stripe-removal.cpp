// ==WindhawkMod==
// @id              readingpane-stripe-removal
// @name            Reading Pane Stripe Removal
// @description     Suppresses the stray Preview Pane background fill in the affected DUI element
// @version         1.0.0
// @author          VitalS
// @github          https://github.com/VitalSkib
// @include         explorer.exe
// ==/WindhawkMod==
#include <windows.h>
static void* g_expectedVtable = nullptr;
static thread_local bool g_insideTargetPaint = false;
using PaintBackground_t = void*(WINAPI*)(
    void* thisElement,
    void* a2,
    void* a3,
    void* a4,
    void* a5,
    void* a6);
using FillRect_t = int(WINAPI*)(HDC, const RECT*, HBRUSH);
PaintBackground_t PaintBackground_orig = nullptr;
FillRect_t FillRect_orig = nullptr;
void* WINAPI PaintBackground_hook(
    void* thisElement,
    void* a2,
    void* a3,
    void* a4,
    void* a5,
    void* a6)
{
    bool prevFlag = g_insideTargetPaint;
    if (thisElement) {
        void** fields = static_cast<void**>(thisElement);
        if (fields[0] == g_expectedVtable &&
            reinterpret_cast<ULONG_PTR>(fields[3]) == 4) {
            g_insideTargetPaint = true;
        }
    }
    void* result = PaintBackground_orig(
        thisElement, a2, a3, a4, a5, a6);
    g_insideTargetPaint = prevFlag;
    return result;
}
int WINAPI FillRect_hook(HDC hdc, const RECT* lprc, HBRUSH hbr)
{
    if (g_insideTargetPaint) {
        return TRUE;
    }
    return FillRect_orig(hdc, lprc, hbr);
}
BOOL Wh_ModInit()
{
    HMODULE hUser32 = LoadLibraryW(L"user32.dll");
    HMODULE hDui70 = LoadLibraryW(L"dui70.dll");
    if (!hUser32 || !hDui70) {
        Wh_Log(L"[StripeRemoval] Failed to load required modules");
        return FALSE;
    }
    void* pFillRect = reinterpret_cast<void*>(
        GetProcAddress(hUser32, "FillRect"));
    void* pPaintBackground =
        reinterpret_cast<BYTE*>(hDui70) + 0xD920;
    g_expectedVtable =
        reinterpret_cast<BYTE*>(hDui70) + 0x1037C0;
    if (!pFillRect) {
        Wh_Log(L"[StripeRemoval] Failed to resolve FillRect");
        return FALSE;
    }
    if (!Wh_SetFunctionHook(
            pFillRect,
            reinterpret_cast<void*>(FillRect_hook),
            reinterpret_cast<void**>(&FillRect_orig))) {
        Wh_Log(L"[StripeRemoval] Failed to hook FillRect");
        return FALSE;
    }
    if (!Wh_SetFunctionHook(
            pPaintBackground,
            reinterpret_cast<void*>(PaintBackground_hook),
            reinterpret_cast<void**>(&PaintBackground_orig))) {
        Wh_Log(L"[StripeRemoval] Failed to hook PaintBackground");
        return FALSE;
    }
    return TRUE;
}
void Wh_ModUninit()
{
}


