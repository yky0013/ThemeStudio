# Discovery checkpoints

**Time**: 2026-09-29, Asia/Shanghai
**Source**: query-search: `site:docs.github.com/en/rest/releases/releases Get the latest release prerelease draft`; `site:docs.github.com/en/rest/releases/assets digest size browser_download_url release asset`
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: Official GitHub Docs search results identify the releases endpoint page and the release-assets endpoint page. The returned examples expose the release flags `draft` and `prerelease`, and the asset fields `browser_download_url`, `size`, and `digest` with a `sha256:` prefix; the endpoint pages must be opened to confirm the latest-release selection rule and field semantics.

# Relevant extracted content

> Releases docs: `https://docs.github.com/en/rest/releases/releases` — example release object includes `draft: false`, `prerelease: false`, and an `assets` array.
>
> Release-assets docs: `https://docs.github.com/en/rest/releases/assets` — example asset includes `browser_download_url`, `size`, and `digest: "sha256:..."`.

---

## Current bounded conclusion (2026-09-29)

GitHub’s official `Get the latest release` contract is suitable for an update check: it selects the newest non-prerelease, non-draft release by `created_at`; the release payload’s assets expose `browser_download_url`, `size`, and `digest` in the documented `sha256:<64-hex>` form. The anonymous request to `https://api.github.com/repos/yky0013/ThemeStudio/releases/latest` is currently GitHub-reachable but returns `404 Not Found`; the repository metadata and release-list endpoints return the same status, so no current anonymous release payload is available to consume at this owner/repository path.

Precise official links:

- [REST API endpoints for releases](https://docs.github.com/en/rest/releases/releases#get-the-latest-release)
- [REST API endpoints for release assets](https://docs.github.com/en/rest/releases/assets)
- [ThemeStudio latest release API request](https://api.github.com/repos/yky0013/ThemeStudio/releases/latest)

---

**Time**: 2026-09-29, Asia/Shanghai
**Source**: query-search: `site:docs.github.com/en/rest/releases/assets digest SHA256 release asset`
**Method**: query-search (via `web__run`)
**Confidence**: high
**Insight**: The official GitHub Docs search result repeats the complete example release-asset schema, including `browser_download_url`, numeric `size`, and a full `sha256:` digest value. This independently corroborates the field names and digest format recorded from the opened page.

# Relevant extracted content

> `https://docs.github.com/en/rest/releases/assets` — example asset fields include `browser_download_url`, `size: 1024`, and `digest: "sha256:2151b604e3429bff440b9fbc03eb3617bc2603cda96c95b9bb05277f9ddba255"`.

---
