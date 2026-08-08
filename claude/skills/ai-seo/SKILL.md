---
name: ai-seo
description: >
  This skill MUST be invoked when the user says "ai seo", "seo analiz",
  "GEO audit", "site optimize", "AI arama optimizasyonu", "citability",
  "ai citation", "crawlers check", "llms.txt", "brand mentions",
  "structured data audit", "schema audit", "technical seo", "E-E-A-T",
  "ai visibility", "generative engine optimization", "seo fix", "geo fix",
  "seo düzelt", or any variation
  requesting website optimization for AI-powered search engines. Analyzes
  websites for AI search readiness across citability, crawler access,
  brand authority, structured data, technical foundations, and content quality.
  With no subcommand it runs every analysis in sequence and scores the site;
  `fix` is the only mode that edits project files, and it asks first.
  Accepts a live URL or a local project path (scan source files before deploy).
argument-hint: "[audit | citability | crawlers | llmstxt | brands | schema | technical | content | fix] <url | path>"
---

# AI SEO — Generative Engine Optimization

Optimize websites for AI-powered search engines (ChatGPT, Claude, Perplexity, Gemini, Google AI Overviews) while maintaining traditional SEO foundations.

AI search is eating traditional search. This skill optimizes for where traffic is going, not where it was.

## Usage

```bash
/ai-seo <url|path>             # No subcommand: run every analysis in sequence, then score
/ai-seo audit <url|path>       # Same coverage, dispatched as parallel subagents
/ai-seo citability <url|path>  # AI citation readiness scoring
/ai-seo crawlers <url|path>    # AI crawler access check (robots.txt)
/ai-seo llmstxt <url|path>     # llms.txt analysis or generation
/ai-seo brands <url|path>      # Brand mentions across AI-cited platforms
/ai-seo schema <url|path>      # Structured data + entity recognition audit
/ai-seo technical <url|path>   # Technical SEO foundations for AI
/ai-seo content <url|path>     # Content quality + E-E-A-T assessment
/ai-seo fix <path>             # Sweep first, then apply fixes after confirmation
```

The argument is either a live URL (`https://example.com`) or a local project path (`.`, `./src`, `/path/to/project`). See **Input Modes: Web vs Local** below for how each subcommand reads from disk instead of fetching.

## Routing

The first token after `/ai-seo` selects the mode:

- If it matches a known subcommand keyword — `audit`, `citability`, `crawlers`, `llmstxt`, `brands`, `schema`, `technical`, `content`, `fix` — run that subcommand.
- Otherwise treat the whole argument as the target (URL or path) and run the **Sequential Full Sweep** described below.
- If there is no argument at all, run the Sequential Full Sweep against `.` in Local mode.

Keyword match always wins: `/ai-seo content` runs the content subcommand, not a sweep of a directory named `content`. To sweep a path that collides with a keyword, name it explicitly: `/ai-seo audit ./content`.

## Sequential Full Sweep (default mode)

With no subcommand, run ALL SEVEN analysis subcommands yourself, one after another, in this fixed order. Do not launch subagents, and do not drop a step because an earlier one scored well:

| # | Subcommand   | Reference           | Why it sits here |
|---|--------------|---------------------|------------------|
| 1 | `crawlers`   | `crawlers.md`       | Access gates everything else, so a total block reframes every later score |
| 2 | `llmstxt`    | `llmstxt.md`        | Second control file, read from the same place as robots.txt |
| 3 | `technical`  | `technical.md`      | Rendering decides what later steps can even see |
| 4 | `schema`     | `schema.md`         | Markup inventory, needed before judging passage quality |
| 5 | `citability` | `citability.md`     | Passage-level scoring on the pages the earlier steps identified |
| 6 | `content`    | `content.md`        | E-E-A-T judgement, reuses the same page set |
| 7 | `brands`     | `brand-mentions.md` | Off-site and slowest, so it never delays the on-site findings |

Sweep rules:

- Read each subcommand file before running its step. Never work from memory of what a subcommand does.
- Print each step's score and top findings as that step finishes. Do not batch every result to the end, because a later failure would then lose the earlier work.
- If a step fails, record `Unable to assess — <reason>` for that category and continue with the next step. Never abort the sweep.
- After step 7, produce the composite with the Phase 3 rules in [subcommands/audit.md](subcommands/audit.md): the same 6 categories, the same weights, the same business-type shift, and the same Local-mode exclude-and-renormalize ordering.
- The sweep is read-only. Never edit a file in this mode. Use `/ai-seo fix` to change anything.

The sweep and `audit` cover the same seven analyses and produce the same composite. `audit` dispatches them as parallel subagents after a discovery pass, so it is faster. The sweep runs them in one context, so each step can use what the earlier steps found. Choose `audit` for speed and the sweep for depth.

## Why GEO Matters

Figures below are directional and dated — verify current numbers before quoting them to a client.

| Signal | Trend (named source) |
|--------|----------------------|
| AI-referred traffic | Rising fast — one 2025 report tracked a 527% jump over five months (Previsible), though AI is still a small share of total traffic |
| AI traffic intent vs organic | Reported as higher-converting (Semrush 2025 modeled ~4.4x; other studies report very different multipliers) |
| Brand mentions vs backlinks for AI | Mentions correlate more strongly than backlinks (Ahrefs 2025-26) |
| Gartner: search engine volume | -25% by 2026 |
| llms.txt adoption | Still low among top sites — early-mover advantage |

## Subcommands

| Subcommand   | Command                          | Description                                     |
|--------------|----------------------------------|-------------------------------------------------|
| _(none)_     | `/ai-seo <url\|path>`            | Sequential full sweep with composite scoring     |
| `audit`      | `/ai-seo audit <url\|path>`      | Same coverage as the sweep, run in parallel      |
| `citability` | `/ai-seo citability <url\|path>` | Passage-level AI citation readiness              |
| `crawlers`   | `/ai-seo crawlers <url\|path>`   | AI crawler access analysis (robots.txt)          |
| `llmstxt`    | `/ai-seo llmstxt <url\|path>`    | llms.txt standard analysis or generation         |
| `brands`     | `/ai-seo brands <url\|path>`     | Brand authority on AI training platforms          |
| `schema`     | `/ai-seo schema <url\|path>`     | Structured data + entity recognition             |
| `technical`  | `/ai-seo technical <url\|path>`  | Technical SEO for AI crawlers                    |
| `content`    | `/ai-seo content <url\|path>`    | Content quality + E-E-A-T scoring                |
| `fix`        | `/ai-seo fix <path>`             | Sweep, then apply fixes after confirmation       |

Every subcommand above is read-only except `fix`, which is the only mode allowed
to write to project files.

- For `/ai-seo audit`: see [subcommands/audit.md](subcommands/audit.md)
- For `/ai-seo citability`: see [subcommands/citability.md](subcommands/citability.md)
- For `/ai-seo crawlers`: see [subcommands/crawlers.md](subcommands/crawlers.md)
- For `/ai-seo llmstxt`: see [subcommands/llmstxt.md](subcommands/llmstxt.md)
- For `/ai-seo brands`: see [subcommands/brand-mentions.md](subcommands/brand-mentions.md)
- For `/ai-seo schema`: see [subcommands/schema.md](subcommands/schema.md)
- For `/ai-seo technical`: see [subcommands/technical.md](subcommands/technical.md)
- For `/ai-seo content`: see [subcommands/content.md](subcommands/content.md)
- For `/ai-seo fix`: see [subcommands/fix.md](subcommands/fix.md)

## GEO Composite Score (Full Audit)

The full audit produces a weighted composite score (0-100):

| Category                    | Weight | Subcommand   |
|-----------------------------|--------|--------------|
| AI Citability & Visibility  | 25%    | citability   |
| Brand Authority Signals     | 20%    | brands       |
| Content Quality & E-E-A-T   | 20%    | content      |
| Technical Foundations        | 15%    | technical    |
| Schema & Structured Data    | 10%    | schema       |
| Platform Optimization       | 10%    | crawlers + llmstxt |

In **Local mode**, any category whose source is not in the repo (e.g. CMS-driven content, web-only brand reputation) is excluded from the composite and the remaining weights are renormalized to total 100 — never scored 0. See **Input Modes: Web vs Local** below.

**Score interpretation:**

| Range | Grade | Meaning |
|-------|-------|---------|
| 80-100 | A | AI-optimized — strong visibility in AI search |
| 60-79 | B | Good foundation — targeted improvements needed |
| 40-59 | C | Significant gaps — AI crawlers may struggle |
| 20-39 | D | Major issues — minimal AI search presence |
| 0-19  | F | Not optimized — invisible to AI search |

## Business Type Detection

When running a full audit, detect the site type to adjust analysis focus:

| Type | Signals | Adjusted Focus |
|------|---------|----------------|
| SaaS | /pricing, /docs, /api, app subdomain | Documentation citability, API schema |
| Local | Address, map embed, NAP data, reviews | LocalBusiness schema, Google Business |
| E-commerce | /products, cart, price elements | Product schema, review markup |
| Publisher | /blog, /articles, bylines, dates | Article schema, E-E-A-T, citability |
| Agency | /services, /portfolio, /case-studies | Organization schema, brand authority |

## Input Modes: Web vs Local

Every subcommand accepts either a live URL or a local project path. Detect the mode from the argument before doing anything else:

| Argument looks like | Mode | How the site is read |
|---------------------|------|----------------------|
| `http://…` or `https://…` | **Web** | Fetch the live site |
| A bare domain (`example.com`) with no matching local path | **Web** | Treat as `https://…` and fetch |
| `.`, `./src`, `../site`, `/abs/path`, `~/proj`, or any existing file/dir | **Local** | Read project files from disk |

If the argument is ambiguous, check whether it exists as a local path (Glob/Read). If it does, use Local mode; otherwise treat it as a URL.

### Tool mapping

| Need | Web mode | Local mode |
|------|----------|------------|
| Page / HTML content | WebFetch | Read + Glob + Grep on source files |
| Raw files (robots.txt, llms.txt, sitemap.xml) | `Bash(curl -s <domain>/<file>)` | Read from project root, then `public/`, `static/`, `dist/`, `build/` |
| Brand mention discovery | WebSearch | WebSearch — Local mode changes WHERE the site is read, not WHETHER the web is allowed |

Do NOT use Python scripts or external dependencies. The LLM's context-aware analysis replaces regex-based scoring.

### Local project layout

Where to look in Local mode (framework-dependent — Glob to find the real location):

- **Control files**: `robots.txt`, `llms.txt`, `llms-full.txt`, `sitemap.xml` → repo root or `public/`, `static/`, `dist/`, `build/`
- **Content & templates**: `*.html`, `*.md`, `*.mdx`, `*.vue`, `*.svelte`, `*.astro`, `*.jsx`, `*.tsx` → `content/`, `src/`, `pages/`, `app/`, `templates/`
- **Structured data**: `Grep "application/ld+json"` across source files
- **Framework signals**: `package.json` dependencies, `next.config.*`, `nuxt.config.*`, `astro.config.*`, `gatsby-config.*`, `svelte.config.*`, `vite.config.*`

### Local mode honesty rules

Local source is what you wrote, not what an AI crawler renders. Two rules keep local scores honest:

1. **Not in the repo → exclude, never zero.** If a category's source is not present locally (content is CMS- or API-driven, only empty templates exist, brand reputation needs the web), mark it "Not assessable locally — run against the live URL" and DROP it from the composite, then renormalize the remaining weights to total 100. Never score it 0 — that fabricates a low grade.
2. **Static analysis is a lower bound.** Runtime-injected markup (Next.js `<Head>` JSON-LD, CMS-injected schema, client-rendered content) is invisible to a static file scan. Local Schema / Citability / Content / SSR scores are a FLOOR, not authoritative. Say so in the report and recommend verifying against the live URL.

## Output Format

All subcommands return analysis in the response as structured markdown. Only `fix` writes to project files, and only after the user confirms each group of changes; `llmstxt generate` still needs an explicit request before it writes. Every other mode leaves the project untouched. Each analysis includes:

- Score (0-100) with grade (A-F)
- Key findings with specific file/line/URL references
- Prioritized recommendations (Critical → High → Medium → Low)
- Quick wins highlighted separately
