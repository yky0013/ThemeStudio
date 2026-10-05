# Source checkpoints — Explorer transparent surfaces (2026-10-05)

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-beginbufferedpaint
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: `BeginBufferedPaint` takes a target `HDC` and a `RECT` that specifies the target-DC area to paint, then returns a buffered-paint handle and a new device-context handle through `phdc`. The buffered handle is freed by `EndBufferedPaint`; initialize/uninitialize buffered painting on the calling thread for normal performance.

# Relevant extracted content

> “The handle of the target DC on which the buffer will be painted.” (`hdcTarget`)

> “A pointer to a RECT structure that specifies the area of the target DC in which to paint.” (`prcTarget`)

> “When this function returns, points to the handle of the new device context.” (`phdc`)

> “The returned handle is freed when EndBufferedPaint is called.”

> “An application should call BufferedPaintInit on the calling thread before calling BeginBufferedPaint, and BufferedPaintUnInit before the thread is terminated.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-drawthemeparentbackgroundex
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: For a partially transparent child, Microsoft’s helper draws the parent portion using the child HDC and defines the requested rectangle in child coordinates. It sends `WM_ERASEBKGND` followed by `WM_PRINTCLIENT`; `DTPB_USECTLCOLORSTATIC` can route through `WM_CTLCOLORSTATIC` and use a supplied brush, while `DTPB_USEERASEBKGND` can avoid that if the parent actually painted during erasure.

# Relevant extracted content

> “Used by partially-transparent or alpha-blended child controls to draw the part of their parent in front of which they appear. Sends a WM_ERASEBKGND message followed by a WM_PRINTCLIENT.”

> “Handle of the child control.” (`hwnd`)

> “HDC of the child control.” (`hdc`)

> “DTPB_USECTLCOLORSTATIC … this function sends a WM_CTLCOLORSTATIC message to the parent and uses the brush if one is provided.”

> “DTPB_USEERASEBKGND … returns S_OK without sending a WM_CTLCOLORSTATIC message if the parent actually painted on WM_ERASEBKGND.”

> “The area to be drawn, in child coordinates.” (`prc`)

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/controls/parts-and-states
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: The official theme table defines the `SCROLLBAR` class parts and their valid state families. Arrow buttons use directional `ABS_*` states (including normal, hot, hover, pressed, disabled); thumb, tracks, and grippers use `SCRBS_*` states (normal, hot, hover, pressed, disabled); size box uses `SZB_*ALIGN` states. Microsoft warns state ID 0 should be used only where no states are defined.

# Relevant extracted content

> “The values in the table are defined in Vsstyle.h and Vssym32.h.”

> “SCROLLBAR | SBP_ARROWBTN | ABS_DOWNDISABLED, ABS_DOWNHOT, ABS_DOWNNORMAL, ABS_DOWNPRESSED, ABS_DOWNHOVER, ABS_LEFTDISABLED, ABS_LEFTHOT, ABS_LEFTHOVER, ABS_LEFTNORMAL, ABS_LEFTPRESSED, ABS_RIGHTDISABLED, ABS_RIGHTHOT, ABS_RIGHTHOVER, ABS_RIGHTNORMAL, ABS_RIGHTPRESSED, ABS_UPDISABLED, ABS_UPHOT, ABS_UPHOVER, ABS_UPNORMAL, ABS_UPPRESSED”

> “SBP_GRIPPERHORZ … SCRBS_DISABLED, SCRBS_HOT, SCRBS_HOVER, SCRBS_NORMAL, SCRBS_PRESSED”

> “SBP_GRIPPERVERT … SCRBS_DISABLED, SCRBS_HOT, SCRBS_HOVER, SCRBS_NORMAL, SCRBS_PRESSED”

> “SBP_LOWERTRACKHORZ … SCRBS_DISABLED, SCRBS_HOT, SCRBS_HOVER, SCRBS_NORMAL, SCRBS_PRESSED”

> “SBP_LOWERTRACKVERT … SCRBS_DISABLED, SCRBS_HOT, SCRBS_HOVER, SCRBS_NORMAL, SCRBS_PRESSED”

> “SBP_THUMBBTNHORZ … SCRBS_DISABLED, SCRBS_HOT, SCRBS_HOVER, SCRBS_NORMAL, SCRBS_PRESSED”

> “SBP_THUMBBTNVERT … SCRBS_DISABLED, SCRBS_HOT, SCRBS_HOVER, SCRBS_NORMAL, SCRBS_PRESSED”

> “SBP_UPPERTRACKHORZ … SCRBS_DISABLED, SCRBS_HOT, SCRBS_HOVER, SCRBS_NORMAL, SCRBS_PRESSED”

> “SBP_UPPERTRACKVERT … SCRBS_DISABLED, SCRBS_HOT, SCRBS_HOVER, SCRBS_NORMAL, SCRBS_PRESSED”

> “SBP_SIZEBOX | SZB_HALFBOTTOMRIGHTALIGN, SZB_HALFBOTTOMLEFTALIGN, SZB_HALFTOPRIGHTALIGN, SZB_HALFTOPLEFTALIGN, SZB_LEFTALIGN, SZB_RIGHTALIGN, SZB_TOPRIGHTALIGN, SZB_TOPLEFTALIGN”

> “Use stateId=0 only when there are no states defined.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/ns-uxtheme-dttopts
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: `DTTOPTS` is where `DrawThemeTextEx` adds explicit text color, border, shadow, glow, and `DTT_CALCRECT` options. `DTT_COMPOSITED` is the key caveat for a transparent buffer: Microsoft requires the passed HDC to have a top-down DIB section selected; the parent’s `BPBF_TOPDOWNDIB` pixel test directly covers that prerequisite.

# Relevant extracted content

> “DTT_CALCRECT … The pRect parameter … will be used as both an in and an out parameter.”

> “DTT_COMPOSITED … Draws text with antialiased alpha. Use of this flag requires a top-down DIB section. This flag works only if the HDC passed to function DrawThemeTextEx has a top-down DIB section currently selected in it.”

> “DTT_TEXTCOLOR … The crText member value is valid.”

> “DTT_BORDERCOLOR … The crBorder member value is valid.”

> “DTT_SHADOWCOLOR … The crShadow member value is valid.”

> “DTT_GLOWSIZE … The iGlowSize member value is valid.”

> “iGlowSize … Specifies the size of a glow that will be drawn on the background prior to any text being drawn.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-drawthemetextex
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: `DrawThemeTextEx` uses the same themed part/state and HDC model as `DrawThemeText` but adds a caller-supplied `DTTOPTS` structure for extra formatting. Its rectangle is in logical coordinates and is in/out, matching the API’s layout-calculation extension.

# Relevant extracted content

> “Extends DrawThemeText by allowing additional text format options.”

> “HDC to use for drawing.”

> “Pointer to a RECT structure that contains the rectangle, in logical coordinates, in which the text is to be drawn.”

> “A DTTOPTS structure that defines additional formatting options that will be applied to the text being drawn.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-drawthemetext
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: `DrawThemeText` draws themed color/font into the HDC supplied by the caller, with a logical-coordinate `RECT`; `dwTextFlags2` is unused and must be zero. It cannot calculate a layout rectangle (`DT_CALCRECT`), and Microsoft’s own example sets `SetBkMode(hdc, TRANSPARENT)` before calling it.

# Relevant extracted content

> “HDC to use for drawing.”

> “DrawThemeText does not support DT_CALCRECT. However, DrawThemeTextEx does support DT_CALCRECT.”

> “Not used. Set to zero.” (`dwTextFlags2`)

> “Pointer to a RECT structure that contains the rectangle, in logical coordinates, in which the text is to be drawn.”

> “The function always uses the themed font for the specified part and state if one is defined. Otherwise it uses the font currently selected into the device context.”

> Microsoft’s example calls `SetBkMode(hdcPaint, TRANSPARENT)` before `DrawThemeText`.

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-getstockobject
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: Microsoft defines `HOLLOW_BRUSH` and `NULL_BRUSH` as equivalent stock brushes. They are valid handles for the `WM_CTLCOLORSTATIC` return path and do not require deletion; this supports returning the stock null brush while the HDC uses transparent text mode.

# Relevant extracted content

> “HOLLOW_BRUSH — Hollow brush (equivalent to NULL_BRUSH).”

> “NULL_BRUSH — Null brush (equivalent to HOLLOW_BRUSH).”

> “The HOLLOW_BRUSH and NULL_BRUSH stock objects are equivalent.”

> “It is not necessary (but it is not harmful) to delete stock objects…”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-setbkmode
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: `SetBkMode(hdc, TRANSPARENT)` makes the background unaffected while text is drawn; `OPAQUE` fills it with the current background color first. The mode is HDC state and should be changed on the static control’s HDC supplied by `WM_CTLCOLORSTATIC`.

# Relevant extracted content

> “The SetBkMode function sets the background mix mode of the specified device context.”

> “OPAQUE — Background is filled with the current background color before the text … is drawn.”

> “TRANSPARENT — Background is unaffected.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/controls/wm-ctlcolorstatic
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: A static control sends `WM_CTLCOLORSTATIC` to its parent immediately before drawing; `wParam` is the static control’s HDC and `lParam` is its HWND. The parent may set foreground/background colors and must return a brush handle for the static background. Returning a stock hollow/null brush is the documented shape for leaving the already-painted surface visible; `SetBkMode(TRANSPARENT)` controls text background drawing separately.

# Relevant extracted content

> “A static control … sends the WM_CTLCOLORSTATIC message to its parent window when the control is about to be drawn.”

> “wParam … Handle to the device context for the static control window.”

> “lParam … Handle to the static control.”

> “If an application processes this message, the return value is a handle to a brush that the system uses to paint the background of the static control.”

> “By default, the DefWindowProc function selects the default system colors for the static control.”

> “The WM_CTLCOLORSTATIC message is never sent between threads; it is sent only within the same thread.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-erasebkgnd
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: `WM_ERASEBKGND` arrives when the background must be erased, including resize, and `wParam` is the DC handle. Returning nonzero tells Windows erasure was performed; returning zero leaves the window marked for erasing and commonly makes `PAINTSTRUCT.fErase` true. For transparent painting, the handler must avoid accidental class-brush erasure and return a deliberate status.

# Relevant extracted content

> “Sent when the window background must be erased (for example, when a window is resized). The message is sent to prepare an invalidated portion of a window for painting.”

> “wParam … A handle to the device context.”

> “An application should return nonzero if it erases the background; otherwise, it should return zero.”

> “The DefWindowProc function erases the background by using the class background brush … If hbrBackground is NULL, the application should process the WM_ERASEBKGND message and erase the background.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-nccreate
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: `WM_NCCREATE` is sent through the window’s `WindowProc` before `WM_CREATE`, while the window is first being created. A later `SetWindowSubclass` call cannot retroactively receive this message; an owner window procedure must install any needed state before or while creation dispatch is active.

# Relevant extracted content

> “Sent prior to the WM_CREATE message when a window is first created.”

> “A window receives this message through its WindowProc function.”

> “If an application processes this message, it should return TRUE to continue creation of the window. If the application returns FALSE, the CreateWindow or CreateWindowEx function will return a NULL handle.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/commctrl/nf-commctrl-setwindowsubclass
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: `SetWindowSubclass` installs or updates a callback identified by callback address plus caller-defined subclass ID; reference data is passed to the callback. The helper cannot subclass across threads. The page does not promise delivery of messages that occurred before installation, so subclassing is effective only from the call onward.

# Relevant extracted content

> “Installs or updates a window subclass callback.”

> “If the callback address and ID pair have not yet been installed, then this function installs the subclass. If the pair has already been installed, then this function just updates the reference data.”

> “You cannot use the subclassing helper functions to subclass a window across threads.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-bufferedpaintinit
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: Buffered painting is initialized per calling thread before `BeginBufferedPaint` and balanced with `BufferedPaintUnInit`; Microsoft gives “before creating the main application window or during `WM_CREATE`” and “after destroying the window or during `WM_NCDESTROY`” as typical lifecycle points.

# Relevant extracted content

> “BufferedPaintInit is called before BeginBufferedPaint or BeginBufferedAnimation for each thread that uses these functions.”

> “Each call to BufferedPaintInit should be matched with a call to BufferedPaintUnInit…”

> “Typically, this function is called before creating the main application window, or during WM_CREATE. Call BufferedPaintUnInit after destroying the window, or during WM_NCDESTROY.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-getbufferedpaintdc
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: `GetBufferedPaintDC` returns exactly the paint DC returned by `BeginBufferedPaint` (or NULL on failure). This is the buffer HDC to pass to theme/GDI drawing while the buffer is active.

# Relevant extracted content

> “Gets the paint device context (DC). This is the same value retrieved by BeginBufferedPaint.”

> “This is the same DC that is returned by BeginBufferedPaint. Returns NULL upon failure.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-bufferedpaintclear
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: `BufferedPaintClear` clears a rectangle in the active buffer to transparent ARGB zero, with `prc=NULL` meaning the entire buffer. It operates directly on the buffer bits.

# Relevant extracted content

> “Clears a specified rectangle in the buffer to ARGB = {0,0,0,0}.”

> “Set this parameter to NULL to specify the entire buffer.”

> “This function accesses the buffer bits directly and is therefore faster than calling a GDI function to erase the buffer.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-bufferedpaintsetalpha
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: Alpha is set per pixel in the requested target rectangle; `prc=NULL` means the whole buffer and alpha 0–255 means fully transparent to fully opaque. The docs describe the alpha as the value used when blending the buffer into the target DC.

# Relevant extracted content

> “The alpha controls the amount of transparency applied when blending with the buffer onto the destination target device context (DC).”

> “Set this parameter to NULL to specify the entire buffer.”

> “The alpha value can range from zero (fully transparent) to 255 (fully opaque).”

> “This function sets the alpha value for each pixel in the target rectangle.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/ns-uxtheme-bp_paintparams
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: `BP_PAINTPARAMS` controls erase, target-DC clipping, non-client mode, exclusion rectangles, and blending. Default clipping applies the target DC’s window clip to the double buffer unless `BPPF_NOCLIP` is set; `prcExclude` is excluded from that clipping region.

# Relevant extracted content

> “BPPF_ERASE … Initialize the buffer to ARGB = {0, 0, 0, 0} during BeginBufferedPaint.”

> “BPPF_NOCLIP … Do not apply the clip region of the target DC to the double buffer. If this flag is not set and if the target DC is a window DC, then clipping due to overlapping windows is applied to the double buffer.”

> “BPPF_NONCLIENT … A non-client DC is being used.”

> “This rectangle is excluded from the clipping region.” (`prcExclude`)

> “If NULL, the source buffer is copied to the destination with no blending.” (`pBlendFunction`)

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/ns-uxtheme-bp_paintparams
**Method**: query-search (via `web__run` official Microsoft Learn search)
**Confidence**: high
**Insight**: `BP_PAINTPARAMS` documents the clip behavior that matters for a target window DC: without `BPPF_NOCLIP`, clipping caused by overlapping windows is applied to the double buffer; `prcExclude` supplies an exclusion rectangle.

# Relevant extracted content

> “BPPF_NOCLIP … Do not apply the clip region of the target DC to the double buffer. If this flag is not set and if the target DC is a window DC, then clipping due to overlapping windows is applied to the double buffer.”

> “prcExclude … A pointer to exclusion RECT structure. This rectangle is excluded from the clipping region.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-bufferedpaintsetalpha
**Method**: query-search (via `web__run` official Microsoft Learn search)
**Confidence**: high
**Insight**: `BufferedPaintSetAlpha` applies alpha to a rectangle in the buffer (or the entire buffer when `prc=NULL`) and controls the transparency used when composing into the target DC.

# Relevant extracted content

> “The alpha controls the amount of transparency applied when blending with the buffer onto the destination target device context (DC).”

> “Set this parameter to NULL to specify the entire buffer.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-bufferedpaintclear
**Method**: query-search (via `web__run` official Microsoft Learn search)
**Confidence**: high
**Insight**: `BufferedPaintClear` directly clears the selected buffer rectangle to transparent ARGB zero; `prc=NULL` means the entire buffer.

# Relevant extracted content

> “Clears a specified rectangle in the buffer to ARGB = {0,0,0,0}.”

> “Set this parameter to NULL to specify the entire buffer.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-getbufferedpaintdc
**Method**: query-search (via `web__run` official Microsoft Learn search)
**Confidence**: high
**Insight**: `GetBufferedPaintDC` returns the same paint DC that `BeginBufferedPaint` returned, confirming that the buffered HDC is the paint target for all drawing during the active buffer lifetime.

# Relevant extracted content

> “Gets the paint device context (DC). This is the same value retrieved by BeginBufferedPaint.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-bufferedpaintinit
**Method**: query-search (via `web__run` official Microsoft Learn search)
**Confidence**: high
**Insight**: `BufferedPaintInit` is thread-scoped and should be balanced with `BufferedPaintUnInit`; the docs give `WM_CREATE` and `WM_NCDESTROY` as typical lifecycle locations.

# Relevant extracted content

> “BufferedPaintInit is called before BeginBufferedPaint or BeginBufferedAnimation for each thread that uses these functions.”

> “Typically, this function is called before creating the main application window, or during WM_CREATE. Call BufferedPaintUnInit after destroying the window, or during WM_NCDESTROY.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-getbufferedpainttargetrect
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: The target rectangle can be queried back from the active `HPAINTBUFFER`; this is the rectangle that was specified to `BeginBufferedPaint`. Failure sets the output `RECT` to empty.

# Relevant extracted content

> “Retrieves the target rectangle specified by BeginBufferedPaint.”

> “When this function returns, contains the requested rectangle.”

> “If this function fails, the RECT structure at prc is set to empty.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-getbufferedpainttargetdc
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: The target DC can be recovered from the `HPAINTBUFFER`; the documented return is exactly the target `HDC` originally passed to `BeginBufferedPaint`.

# Relevant extracted content

> “If successful, this function returns the target DC that was passed by the application to BeginBufferedPaint.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-getbufferedpainttargetdc
**Method**: query-search (via `web__run` official Microsoft Learn search)
**Confidence**: high
**Insight**: The official companion API explicitly identifies the target DC associated with a buffered paint as the exact `HDC` passed to `BeginBufferedPaint`.

# Relevant extracted content

> “If successful, this function returns the target DC that was passed by the application to BeginBufferedPaint.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-getbufferedpainttargetrect
**Method**: query-search (via `web__run` official Microsoft Learn search)
**Confidence**: high
**Insight**: The official companion API retrieves the target rectangle originally specified by `BeginBufferedPaint`, allowing code to keep the target-DC coordinate rectangle as the source of truth.

# Relevant extracted content

> “Retrieves the target rectangle specified by BeginBufferedPaint.”

> “When this function returns, contains the requested rectangle.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/
**Method**: query-search (via `web__run` official Microsoft Learn search)
**Confidence**: high
**Insight**: The official `uxtheme.h` index ties `GetBufferedPaintDC` to the `HDC` returned by `BeginBufferedPaint`, and lists `BufferedPaintClear`, `BufferedPaintSetAlpha`, and `DrawThemeParentBackground` as relevant transparency helpers. This is an index corroboration, not a replacement for each function's own contract.

# Relevant extracted content

> “GetBufferedPaintDC — Gets the paint device context (DC). This is the same value retrieved by BeginBufferedPaint.”

> “GetBufferedPaintTargetDC — Retrieves the target device context (DC).”

> “BufferedPaintClear — Clears a specified rectangle in the buffer to ARGB = {0,0,0,0}.”

> “DrawThemeParentBackground — Draws the part of a parent control that is covered by a partially-transparent or alpha-blended child control.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-endbufferedpaint
**Method**: browser-rendered (via `web__run` open; Microsoft Learn official page)
**Confidence**: high
**Insight**: `EndBufferedPaint` completes the operation and frees the associated `HPAINTBUFFER`; `fUpdateTarget=TRUE` copies the buffer into the target DC. The commit flag is therefore the lifetime boundary for the buffer and the only documented copy-to-target operation.

# Relevant extracted content

> “Completes a buffered paint operation and frees the associated buffered paint handle.”

> “The handle of the buffered paint context, obtained through BeginBufferedPaint.”

> “TRUE to copy the buffer to the target DC.”

---
