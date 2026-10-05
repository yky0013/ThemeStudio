# Discovery log — Explorer transparent surfaces (2026-10-05)

Scope is limited to official Microsoft Win32 documentation for buffered painting, window subclass message timing, themed text, and scrollbar theme parts/states. Direct page retrieval and synthesis are recorded in `20_sources.md` and `90_synthesis.md`.

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-beginbufferedpaint
**Method**: query-search (via `web__run` domain-scoped Microsoft Learn search)
**Confidence**: high
**Insight**: Candidate official page for `BeginBufferedPaint`; its result identifies `hdcTarget`, `prcTarget`, and returned buffered `HDC`/`HPAINTBUFFER` semantics.

# Relevant extracted content

> “Begins a buffered paint operation.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-endbufferedpaint
**Method**: query-search (via `web__run` domain-scoped Microsoft Learn search; direct URL candidate)
**Confidence**: high
**Insight**: Candidate official page for `EndBufferedPaint`; direct retrieval is required for commit/update and handle-lifetime details.

# Relevant extracted content

> Search target: `EndBufferedPaint function (uxtheme.h)`.

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/commctrl/nf-commctrl-setwindowsubclass
**Method**: query-search (via `web__run` domain-scoped Microsoft Learn search)
**Confidence**: high
**Insight**: Candidate official page for `SetWindowSubclass`; the result confirms it installs or updates a window-subclass callback and must be tied to message timing analysis.

# Relevant extracted content

> “Installs or updates a window subclass callback.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-drawthemetext
**Method**: query-search (via `web__run` domain-scoped Microsoft Learn search)
**Confidence**: high
**Insight**: Candidate official page for `DrawThemeText`; result explicitly notes no `DT_CALCRECT` support and points to `DrawThemeTextEx` for that option.

# Relevant extracted content

> “DrawThemeText does not support DT_CALCRECT. However, DrawThemeTextEx does support DT_CALCRECT.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/api/uxtheme/nf-uxtheme-drawthemetextex
**Method**: query-search (via `web__run` domain-scoped Microsoft Learn search)
**Confidence**: high
**Insight**: Candidate official page for `DrawThemeTextEx`; result describes it as `DrawThemeText` extended with additional text-format options.

# Relevant extracted content

> “Extends DrawThemeText by allowing additional text format options.”

---

**Time**: 2026-10-05, Asia/Shanghai
**Source**: https://learn.microsoft.com/en-us/windows/win32/controls/parts-and-states
**Method**: query-search (via `web__run` domain-scoped Microsoft Learn search)
**Confidence**: high
**Insight**: Candidate official Microsoft Learn table for standard-control theme parts and states, including scrollbar rows and the `Vsstyle.h`/`Vssym32.h` constants.

# Relevant extracted content

> “The values in the table are defined in Vsstyle.h and Vssym32.h.”

---
