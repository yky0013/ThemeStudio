# Bounded synthesis — transparent themed Explorer surfaces (2026-10-05)

This note records only the Win32 contracts needed by the current implementation. It does not establish a broader rendering design.

## Buffered paint: target HDC, buffer HDC, coordinates, clip, and lifetime

[`BeginBufferedPaint`](https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-beginbufferedpaint) receives `hdcTarget` and `prcTarget`; the latter is the rectangle in the target DC in which to paint. It returns an `HPAINTBUFFER` and writes a new paint `HDC` through `phdc`. The returned paint HDC is the value later returned by [`GetBufferedPaintDC`](https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-getbufferedpaintdc). It is not documented as an HWND-associated DC. [`GetBufferedPaintTargetDC`](https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-getbufferedpainttargetdc) returns the original `hdcTarget` passed to `BeginBufferedPaint`, so an application-owned map from active buffer HDC to target HWND/target HDC is reasonable while the operation is active. Because [`EndBufferedPaint`](https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-endbufferedpaint) frees the associated buffered handle, remove that map before or as part of the end path and never retain the buffer HDC after the call.

The target rectangle can be recovered with [`GetBufferedPaintTargetRect`](https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-getbufferedpainttargetrect). Keep the drawing rectangle in target-DC logical coordinates; the parent’s nonzero-rectangle pixel test is useful evidence that this coordinate convention is preserved for the selected `BPBF_TOPDOWNDIB` buffer. The docs do not promise that a buffer HDC is a window DC or that its handle remains valid after `EndBufferedPaint`, so do not infer HWND identity from the HDC value itself.

[`BP_PAINTPARAMS`](https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/ns-uxtheme-bp_paintparams) controls the important clip behavior. With no `BPPF_NOCLIP`, if the target is a window DC, clipping caused by overlapping windows is applied to the double buffer. `BPPF_NOCLIP` disables that behavior; `prcExclude` excludes a rectangle from the clipping region. `BPPF_ERASE` initializes the buffer to transparent ARGB `{0,0,0,0}`. `BufferedPaintInit` is per calling thread and should be balanced with `BufferedPaintUnInit`; Microsoft gives `WM_CREATE` and `WM_NCDESTROY` as typical lifecycle locations.

## Alpha answer for `PaintImage` and `EndBufferedPaint(TRUE)`

The current null-parameter test passing does not prove alpha composition. In [`BP_PAINTPARAMS`](https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/ns-uxtheme-bp_paintparams), a null `pBlendFunction` means “the source buffer is copied to the destination with no blending.” [`EndBufferedPaint(TRUE)`](https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-endbufferedpaint) then copies the buffer to the target. Therefore `StretchBlt(..., SRCCOPY)` into a `BPBF_TOPDOWNDIB` followed by null paint parameters is a source-copy path; transparent pixels in the DIB do not, by that contract alone, reveal the pre-existing Explorer pixels in the target.

[`BufferedPaintSetAlpha`](https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-bufferedpaintsetalpha) is not required when the buffer has already been fully composed with the desired background, and it is not sufficient by itself to turn a null-`pBlendFunction` source copy into alpha composition. It sets each pixel’s alpha in a selected rectangle (or the whole buffer when `prc=NULL`) for use when blending the buffer into the target DC. To preserve a transparent Explorer backdrop, use one of these bounded mechanisms: paint/copy the parent surface into the buffer before drawing the image/text, or supply an appropriate `BLENDFUNCTION` in `BP_PAINTPARAMS` and ensure the buffer pixels carry the intended alpha. If the image was copied with `SRCCOPY`, verify its alpha channel rather than assuming the source image’s alpha survived that GDI operation.

## Subclass and message timing

[`WM_NCCREATE`](https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-nccreate) is sent through the window’s original `WindowProc` before `WM_CREATE`, during first creation. [`SetWindowSubclass`](https://learn.microsoft.com/en-us/windows/win32/api/commctrl/nf-commctrl-setwindowsubclass) installs or updates a callback for an existing HWND and does not promise delivery of messages that occurred before installation. A subclass installed from `WM_CREATE` therefore cannot handle that window’s earlier `WM_NCCREATE`; it can handle later messages. The helper also cannot subclass across threads.

`WM_ERASEBKGND` is sent when the background must be erased (including resize); `wParam` is the DC, and returning nonzero declares that erasure was performed. If the handler returns zero, the window remains marked for erasing and `PAINTSTRUCT.fErase` commonly remains true. Avoid allowing the class background brush or `DefWindowProc` to reintroduce an opaque fill when the intent is a transparent surface.

`WM_CTLCOLORSTATIC` is sent by a static control to its parent immediately before the static is drawn. `wParam` is the static control HDC and `lParam` is its HWND; the return value is a brush handle used for the static background. [`NULL_BRUSH`/`HOLLOW_BRUSH`](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-getstockobject) are equivalent stock brushes, so returning the stock null brush is valid and does not require deletion. [`SetBkMode(hdc, TRANSPARENT)`](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-setbkmode) separately makes the text background unaffected; it does not itself paint the parent surface. If the parent paints the surface manually in this handler, use the static HDC and child-client coordinates.

For the native themed-parent route, [`DrawThemeParentBackgroundEx`](https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-drawthemeparentbackgroundex) is explicit: it takes the child HWND and child HDC, sends `WM_ERASEBKGND` followed by `WM_PRINTCLIENT`, and interprets `prc` in child coordinates. `DTPB_USECTLCOLORSTATIC` sends `WM_CTLCOLORSTATIC` and uses a supplied brush; `DTPB_USEERASEBKGND` can skip that message when the parent actually painted during erasure. Avoid a recursive combination where the parent’s `WM_CTLCOLORSTATIC` handler calls a helper that requests `DTPB_USECTLCOLORSTATIC` again.

## Themed text choice and text-background clarity

[`DrawThemeText`](https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-drawthemetext) draws the theme-defined font/color into the caller’s HDC. Its `RECT` is in logical coordinates; `dwTextFlags2` is unused and must be zero. It does not support `DT_CALCRECT`. Microsoft’s own example sets `SetBkMode(hdc, TRANSPARENT)` before drawing.

[`DrawThemeTextEx`](https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-drawthemetextex) uses the same HDC, part, state, and logical-rectangle model but accepts [`DTTOPTS`](https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/ns-uxtheme-dttopts). That structure adds explicit text/border/shadow colors, glow, `DTT_CALCRECT`, and `DTT_COMPOSITED`. The latter draws antialiased alpha text only when the passed HDC currently has a top-down DIB section selected, which is satisfied by a correctly created `BPBF_TOPDOWNDIB` buffer but should remain an explicit precondition. A plain transparent label therefore needs both a transparent HDC background mode and a background surface already painted underneath; `DrawThemeTextEx` does not create that surface by itself.

## Scrollbar parts and states

Microsoft’s [`Parts and States`](https://learn.microsoft.com/en-us/windows/win32/controls/parts-and-states) table says the values are defined in `Vsstyle.h` and `Vssym32.h`, and warns to use `stateId=0` only when no states are defined. For the `SCROLLBAR` class:

| Part family | Parts | Valid state family |
|---|---|---|
| Arrow button | `SBP_ARROWBTN` | Directional `ABS_*`: up/down/left/right, each with normal, hot, pressed, disabled; the current table also lists hover variants. |
| Thumb | `SBP_THUMBBTNHORZ`, `SBP_THUMBBTNVERT` | `SCRBS_NORMAL`, `SCRBS_HOT`, `SCRBS_HOVER`, `SCRBS_PRESSED`, `SCRBS_DISABLED` |
| Track | `SBP_LOWERTRACKHORZ`, `SBP_LOWERTRACKVERT`, `SBP_UPPERTRACKHORZ`, `SBP_UPPERTRACKVERT` | `SCRBS_NORMAL`, `SCRBS_HOT`, `SCRBS_HOVER`, `SCRBS_PRESSED`, `SCRBS_DISABLED` |
| Gripper | `SBP_GRIPPERHORZ`, `SBP_GRIPPERVERT` | `SCRBS_NORMAL`, `SCRBS_HOT`, `SCRBS_HOVER`, `SCRBS_PRESSED`, `SCRBS_DISABLED` |
| Size box | `SBP_SIZEBOX` | `SZB_*ALIGN` states: half/top/bottom and left/right alignment variants |

The table establishes valid part/state names; it does not say that any one state is transparent. Transparency remains a property of the theme background and the destination/buffer composition path. Draw scrollbar backgrounds into the active buffer HDC with the state that matches the control’s actual interaction state, preserve the buffer’s clip, and handle parent-background composition separately.

## Bounded implementation verdict

The current HDC-to-target tracking and removal before `EndBufferedPaint` are consistent with the documented buffer/target distinction and lifetime. The `WM_CTLCOLORSTATIC` approach is also consistent if it uses the child HDC/child coordinates, sets `TRANSPARENT`, and returns the stock `NULL_BRUSH`/`HOLLOW_BRUSH`. The main unresolved visual issue is alpha composition: null `BP_PAINTPARAMS` plus `SRCCOPY` is a copy path, so a passing pixel-coordinate test does not establish a transparent Explorer backdrop. Validate the actual buffer alpha or paint the parent surface into the buffer before overlaying content; add `BufferedPaintSetAlpha` only in a blending path where its alpha values are consumed.


## Implementation follow-up

The final renderer paints the already-composited, root-aligned theme image into the buffer. It records the painted rectangles and calls BufferedPaintSetAlpha(...,255) immediately before a committing EndBufferedPaint, after GDI text may have changed alpha. The added real BPBF_TOPDOWNDIB/AC_SRC_ALPHA pixel test explicitly zeros alpha after drawing and verifies restoration on commit; a separate EndBufferedPaint(FALSE) test verifies the target remains unchanged. Both pass. This resolves the alpha gap above without changing the caller's blend mode. Live Explorer remains unverified.
