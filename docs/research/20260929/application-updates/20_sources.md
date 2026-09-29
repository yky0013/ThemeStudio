# Source checkpoints

**Time**: 2026-09-29, Asia/Shanghai
**Source**: https://docs.github.com/en/rest/releases/releases
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: GitHub documents `Get the latest release` as returning the most recent non-prerelease, non-draft release, sorted by `created_at`. The endpoint is public-readable for public resources, returns `200` on success or `404` when no matching resource exists, and its example release payload includes an `assets` array.

# Relevant extracted content

> `View the latest published full release for the repository.`
>
> `The latest release is the most recent non-prerelease, non-draft release, sorted by the created_at attribute.`
>
> `This endpoint can be used without authentication ... if only public resources are requested.`
>
> `Status code | Description` — `200 | OK`; `404 | Resource not found`.
>
> The example `Get the latest release` response contains `draft`, `prerelease`, and `assets`; each example asset contains `browser_download_url`, `size`, and `digest`.

---

**Time**: 2026-09-29, Asia/Shanghai
**Source**: https://api.github.com/repos/yky0013/ThemeStudio/releases/latest
**Method**: extract (native PowerShell `System.Net.Http.HttpClient`, anonymous; GitHub Docs example API version `2026-03-10`, no credentials)
**Confidence**: high
**Insight**: Repeating the latest-release request with the current API-version header shown in GitHub Docs produces the same HTTP `404 Not Found` and the same documented error URL. The result is therefore not explained by using the older `2022-11-28` version header.

# Relevant extracted content

> HTTP status: `404 Not Found`
>
> Body: `{"message":"Not Found","documentation_url":"https://docs.github.com/rest/releases/releases#get-the-latest-release","status":"404"}`

---

**Time**: 2026-09-29, Asia/Shanghai
**Source**: https://api.github.com/repos/yky0013/ThemeStudio/releases?per_page=100
**Method**: extract (native PowerShell `System.Net.Http.HttpClient`, anonymous; same public GitHub headers, no credentials)
**Confidence**: high
**Insight**: The public release-list endpoint returns HTTP `404 Not Found` as well, so there is no anonymously readable release collection at the requested owner/repository path at this check time. This corroborates the latest-release 404 and makes the current update source unavailable to an anonymous client.

# Relevant extracted content

> HTTP status: `404 Not Found`
>
> Body: `{"message":"Not Found","documentation_url":"https://docs.github.com/rest/releases/releases#list-releases","status":"404"}`

---

**Time**: 2026-09-29, Asia/Shanghai
**Source**: https://api.github.com/repos/yky0013/ThemeStudio
**Method**: extract (native PowerShell `System.Net.Http.HttpClient`, anonymous; same public GitHub headers, no credentials)
**Confidence**: high
**Insight**: The repository metadata endpoint also returns HTTP `404 Not Found` anonymously. Together with the latest-release 404, the current API evidence cannot establish that a public repository or release is available at this owner/name; the update client must handle this as a no-current-release/unavailable-repository response rather than assuming a release JSON object.

# Relevant extracted content

> HTTP status: `404 Not Found`
>
> Body: `{"message":"Not Found","documentation_url":"https://docs.github.com/rest/repos/repos#get-a-repository","status":"404"}`

---

**Time**: 2026-09-29, Asia/Shanghai
**Source**: https://api.github.com/repos/yky0013/ThemeStudio/releases/latest
**Method**: extract (native PowerShell `System.Net.Http.HttpClient`, anonymous; `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`, explicit non-secret `User-Agent`)
**Confidence**: high
**Insight**: The endpoint is reachable anonymously but currently returns HTTP `404 Not Found`, with JSON `{"message":"Not Found", ... "status":"404"}` and no release payload. This proves the request reached GitHub and was not an authentication failure; the 404 alone does not distinguish an unavailable repository from a repository with no published release, so repository and release-list endpoints should be checked separately before treating it as a product defect.

# Relevant extracted content

> HTTP status: `404 Not Found`
>
> Body: `{"message":"Not Found","documentation_url":"https://docs.github.com/rest/releases/releases#get-the-latest-release","status":"404"}`
>
> Anonymous response headers included `X-RateLimit-Limit: 60` and `X-RateLimit-Remaining: 42`; no `Authorization` header or credential was supplied.

---

**Time**: 2026-09-29, Asia/Shanghai
**Source**: https://docs.github.com/en/rest/releases/assets
**Method**: browser-rendered (via `web__run` open)
**Confidence**: high
**Insight**: GitHub’s release-assets documentation shows that release asset payloads expose `browser_download_url`, byte `size`, and `digest` in the `sha256:<64-hex>` form. For browser downloads, the documented client path is the `browser_download_url`; public resources can be queried without authentication.

# Relevant extracted content

> `If within a browser, fetch the location specified in the browser_download_url key provided in the response.`
>
> The `Get a release asset`, `List release assets`, and upload response examples include `size: 1024` and `digest: "sha256:2151b604e3429bff440b9fbc03eb3617bc2603cda96c95b9bb05277f9ddba255"` alongside `browser_download_url`.
>
> `This endpoint can be used without authentication ... if only public resources are requested.`

---
