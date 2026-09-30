# 鸣潮官方桌宠补充核实

**Time**: 2026-10-01 (session date)
**Source**: https://www.google.com/search?q=鸣潮+官方+桌宠
**Method**: browser-rendered via CUA
**Confidence**: discovery only
**Insight**: 搜索片段引用鸣潮账号宣布《鸣潮》主题桌宠 Wuwa Tappo 即将上线，由 Bongo Cat 开发商 Irox 开发。不能从搜索摘要确认已发售；下一步核对库街区一手来源。

> 新浪搜索片段：鸣潮：#鸣潮# 《鸣潮》主题桌宠 Wuwa Tappo 即将上线！漂泊者，准备好让共鸣者住进桌面了吗？由桌宠游戏《Bongo Cat》开发商 Irox ...
> 搜索也显示库街区官方社区入口。

Checkpoint clock: 2026-09-30 17:02:31 UTC (session date supplied by client: 2026-10-01).
---

**Time**: 2026-09-30 17:04 UTC (clock; client session date 2026-10-01)
**Source**: https://www.kurobbs.com/mc/post/1550859675671269376
**Method**: browser-rendered (CUA, followed visible Google official-community result)
**Confidence**: low for post body
**Insight**: Official Kuro community page is reachable, but initial snapshot exposes only page shell and not announcement body. Need loaded-body verification.

> Title: 帖子 - 库街区; footer Copyright©2026广州库洛科技有限公司; article body not yet visible.
---

**Time**: 2026-09-30 17:12 UTC
**Source**: https://www.kurobbs.com/mc/post/1550859675671269376
**Method**: extract (public HTML fallback)
**Confidence**: low for post content
**Insight**: HTML is a client-rendered shell; it loads index-DMg_S_nC.js from web-static.kurobbs.com. No article text is embedded.
---

**Time**: 2026-09-30 17:13 UTC
**Source**: https://web-static.kurobbs.com/resource/prod/assets/index-DMg_S_nC.js
**Method**: extract (public client asset)
**Confidence**: high for routing only
**Insight**: Asset defines PostDetail client route; it contains no announcement text. This does not confirm availability.
---

**Time**: 2026-09-30 17:14 UTC
**Source**: https://web-static.kurobbs.com/resource/prod/assets/post-detail-BZ-eAvn1.js
**Method**: extract (public route asset)
**Confidence**: high for routing only
**Insight**: Retrieved the official public route asset to identify its public post-detail request. No account credentials used.
---

**Time**: 2026-09-30 17:16 UTC
**Source**: https://web-static.kurobbs.com/resource/prod/assets/useConfig-C_w4jjCu.js
**Method**: extract (public client module)
**Confidence**: high for request schema only
**Insight**: Inspected public client module for post detail API. This is read-only research, not authentication.
---

**Time**: 2026-09-30 17:17 UTC
**Source**: https://api.kurobbs.com/forum/getPostDetail (postId=1550859675671269376)
**Method**: extract (documented-by-public-client anonymous post detail read)
**Confidence**: high for returned response
**Insight**: Queried the public detail API identified from official client; no authentication used.

```json
{"code":102,"msg":"服务器外部错误","success":false,"traceId":"2673fe48-3888-44ee-a06e-1ad62790f04f"}
```
---

**Time**: 2026-09-30 17:18 UTC
**Source**: https://store.steampowered.com/search/?term=Wuwa%20Tappo
**Method**: extract (Steam public search)
**Confidence**: discovery only
**Insight**: Follow-up search for the exact product name observed in search results.


---

Steam returned: "0 results match your search." No exact product detail link was present. This is not evidence of global absence.
