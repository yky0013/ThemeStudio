#pragma once

#include "resource.h"

class CToolkitDlg : public CDialogImpl<CToolkitDlg> {
   public:
    enum { IDD = IDD_TOOLKIT };

    using DlgCallback = std::function<void(HWND)>;

    struct DialogOptions {
        bool createInactive = false;
        bool showTaskbarCrashExplanation = false;
        DlgCallback runButtonCallback;
        DlgCallback loadedModsButtonCallback;
        DlgCallback exitButtonCallback;
        DlgCallback safeModeButtonCallback;
        DlgCallback finalMessageCallback;
    };

    CToolkitDlg(DialogOptions dialogOptions);

    void LoadLanguageStrings();

    bool WasActive();
    void Close();

   private:
    BEGIN_MSG_MAP_EX(CToolkitDlg)
        MSG_WM_INITDIALOG(OnInitDialog)
        MSG_WM_DESTROY(OnDestroy)
        MSG_WM_ACTIVATE(OnActivate)
        MSG_WM_DPICHANGED(OnDpiChanged)
        MSG_WM_CTLCOLORDLG(OnCtlColorDlg)
        MSG_WM_CTLCOLORSTATIC(OnCtlColorStatic)
        MSG_WM_CTLCOLORBTN(OnCtlColorBtn)
        MSG_WM_SETTINGCHANGE(OnSettingChange)
        COMMAND_ID_HANDLER_EX(IDOK, OnOK)
        COMMAND_ID_HANDLER_EX(IDC_TOOLKIT_LOADED_MODS, OnLoadedMods)
        COMMAND_ID_HANDLER_EX(IDC_TOOLKIT_EXIT, OnExit)
        COMMAND_ID_HANDLER_EX(IDC_TOOLKIT_SAFE_MODE, OnSafeMode)
        COMMAND_ID_HANDLER_EX(IDC_TOOLKIT_CLOSE, OnClose)
    END_MSG_MAP()

    BOOL OnInitDialog(CWindow wndFocus, LPARAM lInitParam);
    void OnDestroy();
    void OnActivate(UINT nState, BOOL bMinimized, CWindow wndOther);
    void OnDpiChanged(UINT nDpiX, UINT nDpiY, PRECT pRect);
    HBRUSH OnCtlColorDlg(CDCHandle dc, CWindow wnd);
    HBRUSH OnCtlColorStatic(CDCHandle dc, CStatic wndStatic);
    HBRUSH OnCtlColorBtn(CDCHandle dc, CButton button);
    void OnSettingChange(UINT uFlags, LPCTSTR lpszSection);
    void OnOK(UINT uNotifyCode, int nID, CWindow wndCtl);
    void OnLoadedMods(UINT uNotifyCode, int nID, CWindow wndCtl);
    void OnExit(UINT uNotifyCode, int nID, CWindow wndCtl);
    void OnSafeMode(UINT uNotifyCode, int nID, CWindow wndCtl);
    void OnClose(UINT uNotifyCode, int nID, CWindow wndCtl);

    void OnFinalMessage(HWND hWnd) override;
    void ReloadMainIcon();
    void ApplyDarkMode();
    void AdjustLayoutForExplanation();
    void PlaceWindowAtTrayArea();

    const DialogOptions m_dialogOptions;
    bool m_wasActive = false;
    bool m_darkMode = false;
    CBrush m_darkBgBrush;
    int m_explanationExtraWidth = 0;
    int m_explanationOffsetY = 0;
};
