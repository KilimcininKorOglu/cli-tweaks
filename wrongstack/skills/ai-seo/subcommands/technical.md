# Technical SEO for AI

Audit technical SEO foundations that directly impact AI crawler accessibility and content extraction. Focuses on what matters for AI — not a generic SEO checklist.

## Command

```bash
/ai-seo technical <url|path>
```

## Critical Insight: SSR and AI Crawlers

**Server-Side Rendering is CRITICAL for GEO.** AI crawlers (GPTBot, ClaudeBot, PerplexityBot) have limited or no JavaScript rendering capability. If your content is rendered client-side only (React SPA, Vue SPA without SSR), AI crawlers see an empty page.

| Crawler         | JS Rendering        | Implication                        |
|-----------------|---------------------|------------------------------------|
| GPTBot          | Limited             | May miss client-rendered content   |
| ClaudeBot       | None                | Sees only server-rendered HTML     |
| PerplexityBot   | Limited             | Relies primarily on HTML response  |
| Google-Extended | Yes (via Googlebot) | Can render JS, but slower indexing |

## Local Mode

When the argument is a local path (see SKILL.md Input Modes), this audit shifts from HTTP inspection to source inspection. Per-category mapping:

| Category              | Local source                                                                                               | Note                                                                    |
|-----------------------|------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| AI Crawler Access     | `robots.txt` in root / `public/` / `static/`                                                               | Full check (see crawlers.md)                                            |
| Server-Side Rendering | `package.json` deps + framework config (`next.config.*`, `nuxt.config.*`, `astro.config.*`) + build output | Infer SSR/SSG/SPA from the framework and config, not from response HTML |
| Page Speed Signals    | image/bundle config, asset sizes on disk                                                                   | Lower bound — real Core Web Vitals need the live site                   |
| Crawlability          | local `sitemap.xml`, `<link rel="canonical">` in templates                                                 | Mostly assessable                                                       |
| Security Headers      | host/CDN config if committed (`vercel.json`, `netlify.toml`, `_headers`, nginx conf)                       | Otherwise **live-only** — exclude and renormalize                       |
| Mobile & Responsive   | viewport meta in templates                                                                                 | Assessable                                                              |
| IndexNow              | key file in root / `public/`                                                                               | Assessable                                                              |

For any check that depends on the HTTP response and has no committed config (chiefly Security Headers), mark it "Not assessable locally — run against the live URL" and renormalize the technical score over the remaining categories rather than scoring them 0. Treat SSR and Page Speed results as a lower bound.

## Analysis Categories

### 1. AI Crawler Accessibility (25 points)

Check robots.txt for AI crawler rules (see `crawlers.md` for detail). Quick assessment:
- All Tier 1 crawlers allowed → 25
- Some Tier 1 blocked → 15
- All Tier 1 blocked → 0

### 2. Server-Side Rendering (20 points)

Fetch the page with WebFetch and check:
- Does the HTML response contain the full content? → 20
- Partial content (hydration model — some content server-rendered) → 12
- Empty root div (`<div id="root"></div>`, `<div id="app"></div>`, `<div id="__next"></div>` with no content) → 0

**Detection signals:**
- Meta tags present in initial HTML (title, description) → likely SSR
- `__NEXT_DATA__` script tag → Next.js SSR
- `window.__NUXT__` → Nuxt SSR
- Empty `<div id="root">` with large JS bundles → likely client-only SPA

### 3. Page Speed & Core Web Vitals (15 points)

Assess from HTML analysis (not Lighthouse — we're doing static analysis):
- Large unoptimized images (no width/height, no lazy loading) → -5
- Render-blocking resources in `<head>` (large CSS/JS without defer/async) → -5
- No resource hints (preconnect, preload for critical resources) → -3
- Estimated page weight from visible resources → flag if > 3MB

Scoring: Start at 15, subtract for each issue found.

### 4. Crawlability Signals (15 points)

- Sitemap exists and is valid → +5
- `<link rel="canonical">` present → +3
- Clean URL structure (no query parameters for content pages) → +3
- Internal linking (pages link to each other) → +2
- No orphan pages detected → +2

### 5. Security Headers (10 points)

Check response headers (from WebFetch or `Bash(curl -sI <url>)`):
- HTTPS → +4 (HTTP = 0 for entire category)
- HSTS header → +2
- Content-Security-Policy → +2
- X-Content-Type-Options → +1
- Referrer-Policy → +1

### 6. Mobile & Responsive (10 points)

- Viewport meta tag present → +4
- No fixed-width elements in HTML → +3
- Touch-friendly elements (no tiny click targets visible in HTML) → +3

### 7. IndexNow Support (5 points)

IndexNow pushes content updates to Bing (which powers ChatGPT's web search).
- IndexNow key file exists: `Bash(curl -s -o /dev/null -w "%{http_code}" <domain>/[key].txt)` → +5
- Or check for IndexNow integration signals in HTML/meta

## Output Format

```markdown
# Technical SEO Report: [URL]

## Score: [XX]/100 (Grade [A-F])

## Category Breakdown

| Category              | Score | Max | Key Finding |
|-----------------------|-------|-----|-------------|
| AI Crawler Access     | XX    | 25  | [one-line]  |
| Server-Side Rendering | XX    | 20  | [one-line]  |
| Page Speed Signals    | XX    | 15  | [one-line]  |
| Crawlability          | XX    | 15  | [one-line]  |
| Security Headers      | XX    | 10  | [one-line]  |
| Mobile & Responsive   | XX    | 10  | [one-line]  |
| IndexNow              | XX    | 5   | [one-line]  |

## Critical Issues
[Issues that directly block AI visibility — SSR failures, crawler blocks]

## Findings

### AI Crawler Access
[robots.txt summary for AI crawlers]

### Server-Side Rendering
[SSR detection result with evidence]

### Page Speed
[Resource optimization findings]

### Crawlability
[Sitemap, canonical, URL structure findings]

### Security
[Header analysis]

## Recommendations
| # | Priority | Action   | Impact   |
|---|----------|----------|----------|
| 1 | Critical | [action] | [impact] |
| 2 | High     | ...      | ...      |
```

## Important Notes

- SSR issues are the #1 technical blocker for AI visibility. Flag prominently.
- This is a static analysis from HTML response — not a Lighthouse audit. We assess what AI crawlers see, not browser performance.
- IndexNow matters because ChatGPT uses Bing's index for web search. Faster Bing indexing = faster AI visibility.
- Google-Extended blocking does NOT affect Google Search ranking. Only affects Gemini and AI Overviews.
