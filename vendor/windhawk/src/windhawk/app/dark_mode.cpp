#include "stdafx.h"

#include "dark_mode.h"

#include <dwmapi.h>
#include <uiautomation.h>
#include <vssym32.h>

#include "shared_functions.h"
#include "ui_functions.h"
#include "var_init_once.h"

namespace DarkMode {

namespace {

// The dark variant of the visual style classes of the common controls. The
// task dialog page uses the older DarkMode_Explorer variant instead: the
// DarkMode_DarkTheme variant of its class lacks the button strip panel, which
// stays light with it.
constexpr PCWSTR kDarkThemeName = L"DarkMode_DarkTheme";
constexpr PCWSTR kTaskDialogDarkThemeName = L"DarkMode_Explorer";

bool IsDisabledByEnvVar() {
    static bool disabled = [] {
        WCHAR value[16];
        DWORD size = GetEnvironmentVariable(L"WINDHAWK_DISABLE_DARK_MODE",
                                            value, ARRAYSIZE(value));
        return size > 0 && size < ARRAYSIZE(value) && wcscmp(value, L"1") == 0;
    }();
    return disabled;
}

// The DarkMode_DarkTheme visual style classes ship with Windows 11 24H2
// (26100.6899) and 25H2 (26200.6899) and later.
// https://github.com/ozone10/darkmodelib/issues/8
bool IsSupportedBuild() {
    ULONG major = 0;
    ULONG minor = 0;
    ULONG build = 0;
    Functions::GetNtVersionNumbers(&major, &minor, &build);

    if (major != 10 || minor != 0) {
        return major > 10;
    }

    if (build != 26100 && build != 26200) {
        return build > 26200;
    }

    DWORD ubr = 0;
    DWORD ubrSize = sizeof(ubr);
    RegGetValue(HKEY_LOCAL_MACHINE,
                L"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", L"UBR",
                RRF_RT_REG_DWORD, nullptr, &ubr, &ubrSize);
    return ubr >= 6899;
}

// Undocumented uxtheme.dll exports, resolved by ordinal. The ordinals only hold
// these functions starting with Windows 10 1809, the first version with dark
// mode support. On older versions they may resolve to unrelated exports.
// https://github.com/ysc3839/win32-darkmode
FARPROC GetUxThemeProcByOrdinal(WORD ordinal) {
    if (!Functions::IsWindowsVersionOrGreaterWithBuildNumber(10, 0, 17763)) {
        return nullptr;
    }

    return GetProcAddress(GetModuleHandle(L"uxtheme.dll"),
                          MAKEINTRESOURCEA(ordinal));
}

////////////////////////////////////////////////////////////////////////////////
// Task dialog
//
// A task dialog hosts a DirectUI window ("DirectUIHWND") which lays out and
// paints the page from a stylesheet in comctl32, and hosts the buttons as
// regular controls. The stylesheet paints the panels with the "TaskDialog"
// visual style class, opened through the dialog window, so the dialog's dark
// theme makes them dark. It takes the text colors from the "TaskDialogStyle"
// class, which has no dark variant, so the text is painted again here in dark
// colors over the panels, at the positions the page reports through UI
// Automation. Only the elements Windhawk's dialogs use are covered.

constexpr UINT_PTR kTaskDialogSubclassId = 1;

// Text elements of the page by their automation id: the "TaskDialogStyle"
// part the stylesheet takes the font from (also the "TaskDialog" part with the
// dark text color) and the "TaskDialog" part painted behind them.
struct TextElement {
    PCWSTR automationId;
    int part;
    int panelPart;
    // A themed glyph followed by the text box, which is focusable.
    bool checkBox = false;
};

constexpr TextElement kTextElements[] = {
    {L"ContentText", TDLG_CONTENTPANE, TDLG_PRIMARYPANEL},
    {L"VerificationCheckBox", TDLG_VERIFICATIONTEXT, TDLG_SECONDARYPANEL, true},
};

struct TaskDialogState {
    HWND hDlg = nullptr;
    HWND hDirectUI = nullptr;
    wil::com_ptr_nothrow<IUIAutomation> automation;
    wil::com_ptr_nothrow<IUIAutomationCacheRequest> cacheRequest;
    wil::com_ptr_nothrow<IUIAutomationCondition> trueCondition;
};

struct ElementLayout {
    // The area the page painted the text in, to paint over.
    RECT eraseRect;
    // The box of the text, where the focus rectangle goes.
    RECT boxRect;
    RECT textRect;
};

int ScaleForDpi(int value, UINT dpi) {
    return MulDiv(value, dpi, USER_DEFAULT_SCREEN_DPI);
}

ElementLayout GetElementLayout(const TextElement& element,
                               const RECT& rect,
                               HTHEME hTaskDialog,
                               HDC hdc,
                               UINT dpi) {
    if (!element.checkBox) {
        return {rect, rect, rect};
    }

    // The glyph is in a wrapper with a themed width and margins (stylesheet
    // fallbacks: 20 and (0,0,5,0)), followed by the text box, padded by 5 at
    // the top. The page insets the text by 2 in its box.
    int wrapperWidth = 0;
    if (FAILED(GetThemeMetric(hTaskDialog, hdc, TDLG_IMAGEALIGNMENT, 0,
                              TMT_WIDTH, &wrapperWidth))) {
        wrapperWidth = ScaleForDpi(20, dpi);
    }

    MARGINS wrapperMargins{};
    if (FAILED(GetThemeMargins(hTaskDialog, hdc, TDLG_IMAGEALIGNMENT, 0,
                               TMT_CONTENTMARGINS, nullptr, &wrapperMargins))) {
        wrapperMargins = {0, ScaleForDpi(5, dpi), 0, 0};
    }

    ElementLayout layout;
    layout.eraseRect = rect;
    layout.eraseRect.left +=
        wrapperMargins.cxLeftWidth + wrapperWidth + wrapperMargins.cxRightWidth;
    layout.boxRect = layout.eraseRect;
    layout.boxRect.top += ScaleForDpi(5, dpi);
    layout.textRect = layout.boxRect;
    InflateRect(&layout.textRect, -ScaleForDpi(2, dpi), 0);
    return layout;
}

void PaintDarkText(TaskDialogState& state, HDC hdc) {
    wil::com_ptr_nothrow<IUIAutomationElement> root;
    if (FAILED(state.automation->ElementFromHandleBuildCache(
            state.hDirectUI, state.cacheRequest.get(), &root)) ||
        !root) {
        return;
    }

    wil::com_ptr_nothrow<IUIAutomationElementArray> children;
    if (FAILED(root->FindAllBuildCache(TreeScope_Children,
                                       state.trueCondition.get(),
                                       state.cacheRequest.get(), &children)) ||
        !children) {
        return;
    }

    int count = 0;
    children->get_Length(&count);
    if (count == 0) {
        return;
    }

    using OpenThemeDataForDpi_t = decltype(&OpenThemeDataForDpi);
    GET_PROC_ADDRESS_ONCE(OpenThemeDataForDpi_t, pOpenThemeDataForDpi,
                          L"uxtheme.dll", "OpenThemeDataForDpi");
    if (!pOpenThemeDataForDpi) {
        return;
    }

    UINT dpi = Functions::GetDpiForWindowWithFallback(state.hDlg);

    wil::unique_htheme hTaskDialog(
        pOpenThemeDataForDpi(state.hDlg, L"TaskDialog", dpi));
    wil::unique_htheme hTaskDialogStyle(
        pOpenThemeDataForDpi(state.hDlg, L"TaskDialogStyle", dpi));
    if (!hTaskDialog || !hTaskDialogStyle) {
        return;
    }

    for (int i = 0; i < count; i++) {
        wil::com_ptr_nothrow<IUIAutomationElement> child;
        if (FAILED(children->GetElement(i, &child)) || !child) {
            continue;
        }

        wil::unique_bstr automationId;
        if (FAILED(child->get_CachedAutomationId(&automationId)) ||
            !automationId) {
            continue;
        }

        const TextElement* element = nullptr;
        for (const auto& textElement : kTextElements) {
            if (wcscmp(automationId.get(), textElement.automationId) == 0) {
                element = &textElement;
                break;
            }
        }

        if (!element) {
            continue;
        }

        RECT rect;
        if (FAILED(child->get_CachedBoundingRectangle(&rect)) ||
            IsRectEmpty(&rect)) {
            continue;
        }

        MapWindowPoints(nullptr, state.hDirectUI, (POINT*)&rect, 2);

        wil::unique_bstr name;
        if (FAILED(child->get_CachedName(&name)) || !name) {
            continue;
        }

        ElementLayout layout =
            GetElementLayout(*element, rect, hTaskDialog.get(), hdc, dpi);

        COLORREF panelColor = kBgColor;
        GetThemeColor(hTaskDialog.get(), element->panelPart, 0, TMT_FILLCOLOR,
                      &panelColor);
        SetDCBrushColor(hdc, panelColor);
        FillRect(hdc, &layout.eraseRect, (HBRUSH)GetStockObject(DC_BRUSH));

        DTTOPTS options = {
            .dwSize = sizeof(options),
            .dwFlags = DTT_TEXTCOLOR,
            .crText = kTextColor,
        };
        GetThemeColor(hTaskDialog.get(), element->part, 0, TMT_TEXTCOLOR,
                      &options.crText);

        DrawThemeTextEx(hTaskDialogStyle.get(), hdc, element->part, 0,
                        name.get(), -1,
                        DT_LEFT | DT_TOP | DT_WORDBREAK | DT_NOPREFIX,
                        &layout.textRect, &options);

        BOOL hasFocus = FALSE;
        if (element->checkBox &&
            SUCCEEDED(child->get_CachedHasKeyboardFocus(&hasFocus)) &&
            hasFocus) {
            DrawFocusRect(hdc, &layout.boxRect);
        }
    }
}

void PaintDirectUI(TaskDialogState& state, HWND hWnd, HDC hdc) {
    RECT clientRect;
    GetClientRect(hWnd, &clientRect);

    HDC hdcBuffer = nullptr;
    HPAINTBUFFER paintBuffer = BeginBufferedPaint(
        hdc, &clientRect, BPBF_TOPDOWNDIB, nullptr, &hdcBuffer);
    if (!paintBuffer) {
        hdcBuffer = hdc;
    }

    DefSubclassProc(hWnd, WM_PRINTCLIENT, (WPARAM)hdcBuffer, PRF_CLIENT);
    PaintDarkText(state, hdcBuffer);

    if (paintBuffer) {
        EndBufferedPaint(paintBuffer, TRUE);
    }
}

LRESULT CALLBACK DirectUISubclassProc(HWND hWnd,
                                      UINT uMsg,
                                      WPARAM wParam,
                                      LPARAM lParam,
                                      UINT_PTR uIdSubclass,
                                      DWORD_PTR dwRefData) {
    auto& state = *reinterpret_cast<TaskDialogState*>(dwRefData);

    switch (uMsg) {
        case WM_ERASEBKGND:
            return 1;

        case WM_PAINT: {
            PAINTSTRUCT ps;
            HDC hdc = BeginPaint(hWnd, &ps);
            if (hdc) {
                PaintDirectUI(state, hWnd, hdc);
                EndPaint(hWnd, &ps);
            }
            return 0;
        }

        case WM_NCDESTROY:
            RemoveWindowSubclass(hWnd, DirectUISubclassProc, uIdSubclass);
            break;
    }

    return DefSubclassProc(hWnd, uMsg, wParam, lParam);
}

LRESULT CALLBACK TaskDialogSubclassProc(HWND hWnd,
                                        UINT uMsg,
                                        WPARAM wParam,
                                        LPARAM lParam,
                                        UINT_PTR uIdSubclass,
                                        DWORD_PTR dwRefData) {
    auto* state = reinterpret_cast<TaskDialogState*>(dwRefData);

    switch (uMsg) {
        case WM_CTLCOLORDLG:
            SetDCBrushColor(reinterpret_cast<HDC>(wParam), kBgColor);
            return reinterpret_cast<LRESULT>(GetStockObject(DC_BRUSH));

        case WM_NCDESTROY:
            RemoveWindowSubclass(hWnd, TaskDialogSubclassProc, uIdSubclass);
            delete state;
            break;
    }

    return DefSubclassProc(hWnd, uMsg, wParam, lParam);
}

}  // namespace

bool IsSupported() {
    static bool supported = !IsDisabledByEnvVar() && IsSupportedBuild();
    return supported;
}

bool IsActive() {
    if (!IsSupported()) {
        return false;
    }

    using ShouldAppsUseDarkMode_t = bool(WINAPI*)();
    static auto pShouldAppsUseDarkMode =
        reinterpret_cast<ShouldAppsUseDarkMode_t>(GetUxThemeProcByOrdinal(132));
    return pShouldAppsUseDarkMode && pShouldAppsUseDarkMode();
}

void EnableForMenus() {
    if (IsDisabledByEnvVar()) {
        return;
    }

    // Note: Before 1903, `BOOL __stdcall AllowDarkModeForApp(BOOL)` (same
    // ordinal) only accepts TRUE or FALSE. TRUE means dark mode is allowed and
    // vice versa. After 1903, `PreferredMode __stdcall
    // SetPreferredAppMode(PreferredMode)` accepts 4 valid values. Calling it
    // with TRUE (1) is valid in both cases.
    enum PreferredAppMode {
        PreferredAppModeDefault,
        PreferredAppModeAllowDark,
        PreferredAppModeForceDark,
        PreferredAppModeForceLight,
        PreferredAppModeMax,
    };

    using SetPreferredAppMode_t =
        PreferredAppMode(WINAPI*)(PreferredAppMode appMode);
    static auto pSetPreferredAppMode =
        reinterpret_cast<SetPreferredAppMode_t>(GetUxThemeProcByOrdinal(135));
    if (pSetPreferredAppMode) {
        pSetPreferredAppMode(PreferredAppModeAllowDark);
    }
}

void SetDarkTitleBar(HWND hWnd, bool dark) {
    BOOL useDark = dark;
    DwmSetWindowAttribute(hWnd, DWMWA_USE_IMMERSIVE_DARK_MODE, &useDark,
                          sizeof(useDark));
}

void SetControlTheme(HWND hWnd, bool dark) {
    SetWindowTheme(hWnd, dark ? kDarkThemeName : L"Explorer", nullptr);
}

void ApplyToTaskDialog(HWND hDlg) {
    if (!IsActive()) {
        return;
    }

    HWND hDirectUI = FindWindowEx(hDlg, nullptr, L"DirectUIHWND", nullptr);
    if (!hDirectUI) {
        return;
    }

    auto state = std::make_unique<TaskDialogState>();
    state->hDlg = hDlg;
    state->hDirectUI = hDirectUI;

    if (FAILED(CoCreateInstance(__uuidof(CUIAutomation), nullptr,
                                CLSCTX_INPROC_SERVER,
                                IID_PPV_ARGS(&state->automation))) ||
        FAILED(state->automation->CreateCacheRequest(&state->cacheRequest)) ||
        FAILED(state->automation->CreateTrueCondition(&state->trueCondition))) {
        return;
    }

    for (PROPERTYID propertyId :
         {UIA_AutomationIdPropertyId, UIA_NamePropertyId,
          UIA_BoundingRectanglePropertyId, UIA_HasKeyboardFocusPropertyId}) {
        state->cacheRequest->AddProperty(propertyId);
    }

    if (!SetWindowSubclass(hDirectUI, DirectUISubclassProc,
                           kTaskDialogSubclassId,
                           reinterpret_cast<DWORD_PTR>(state.get()))) {
        return;
    }

    if (!SetWindowSubclass(hDlg, TaskDialogSubclassProc, kTaskDialogSubclassId,
                           reinterpret_cast<DWORD_PTR>(state.get()))) {
        RemoveWindowSubclass(hDirectUI, DirectUISubclassProc,
                             kTaskDialogSubclassId);
        return;
    }

    // Owned by the dialog subclass from here on.
    state.release();

    SetDarkTitleBar(hDlg, true);

    // The page reopens its theme handles, including the ones it opens through
    // the hosted controls, on its own theme change notification. The controls'
    // own theme change notifications don't reach them, so they're themed first.
    EnumChildWindows(
        hDirectUI,
        [](HWND hWnd, LPARAM) -> BOOL {
            SetWindowTheme(hWnd, kDarkThemeName, nullptr);
            return TRUE;
        },
        0);

    SetWindowTheme(hDlg, kTaskDialogDarkThemeName, nullptr);
    SendMessage(hDirectUI, WM_THEMECHANGED, 0, 0);
}

}  // namespace DarkMode
