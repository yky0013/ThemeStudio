#pragma once

// Dark mode for the app's dialogs, following the system apps theme. Requires
// the DarkMode_DarkTheme visual style classes, which ship with Windows 11 24H2
// build 26100.6899 and later. Setting the WINDHAWK_DISABLE_DARK_MODE=1
// environment variable disables all of it, including the dark popup menus.
namespace DarkMode {

// Colors for what the visual style doesn't paint in a dark dialog: the dialog
// background and the text of static controls.
constexpr COLORREF kBgColor = RGB(32, 32, 32);
constexpr COLORREF kTextColor = RGB(240, 240, 240);

// Whether dark dialogs are possible on this OS and not disabled. When false,
// the functions below leave the UI alone.
bool IsSupported();

// Whether dark dialogs are supported and the system apps theme is dark.
bool IsActive();

// Opts the process into following the system dark/light setting for popup
// (context) menus. Relies on undocumented uxtheme exports.
void EnableForMenus();

void SetDarkTitleBar(HWND hWnd, bool dark);
void SetControlTheme(HWND hWnd, bool dark);

// Makes a task dialog dark if dark mode is active. Call from the TDN_CREATED
// task dialog callback notification. The dialog keeps its theme if the system
// theme changes while it's open.
void ApplyToTaskDialog(HWND hDlg);

}  // namespace DarkMode
