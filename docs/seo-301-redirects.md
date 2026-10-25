# NimTech: required HTTP 301 redirects

GitHub Pages serves static files and does not implement HTTP 301 rules from a `_redirects` file. Configure these rules in the **actual HTTP reverse proxy/CDN** serving `nimtech.ru` (for example Cloudflare Redirect Rules if the domain is proxied through Cloudflare).

| Old path | Permanent destination |
|---|---|
| `/blog/montazh-dpk-na-betonnoe-osnovanie-instrukciya/` | `https://nimtech.ru/blog/montazh-dpk-na-beton/` |
| `/blog/pochemu-dpk-razrushilsya-cherez-dva-goda/` | `https://nimtech.ru/blog/chto-s-dpk-cherez-dva-goda/` |
| `/blog/pyat-oshibok-montazha-terrasnoy-doski/` | `https://nimtech.ru/blog/5-oshibok-montazha-dpk/` |
| `/blog/raschet-stoimosti-terrasy-dpk/` | `https://nimtech.ru/blog/stoimost-terrasy-iz-dpk/` |

For each rule use status **301**, preserve query strings, and match the exact source path. Test both slash and no-slash variants and avoid redirect chains.

Verification:

```bash
curl -sI https://nimtech.ru/blog/pyat-oshibok-montazha-terrasnoy-doski/
# Expected: HTTP 301 and Location: https://nimtech.ru/blog/5-oshibok-montazha-dpk/
```

The four existing Astro pages currently use HTML meta-refresh and `noindex` as a fallback; **they are not HTTP 301 redirects**. Do not delete the fallback pages until real HTTP redirect behavior is verified.
