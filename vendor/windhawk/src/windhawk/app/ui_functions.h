#pragma once

namespace Functions {

PCWSTR LoadStrFromRsrc(UINT uStrId);
UINT GetDpiForWindowWithFallback(HWND hWnd);
int GetSystemMetricsForDpiWithFallback(int nIndex, UINT dpi);
int GetSystemMetricsForWindow(HWND hWnd, int nIndex);

bool IsRightToLeftLanguage(LANGID langId);
void ApplyDialogLayoutRtl(CWindow wnd, bool isLayoutRtl);

}  // namespace Functions
