---
name: ai-seo
description: >
  This skill MUST be invoked when the user says "ai seo", "seo analiz",
  "GEO audit", "site optimize", "AI arama optimizasyonu", "citability",
  "ai citation", "crawlers check", "llms.txt", "brand mentions",
  "structured data audit", "schema audit", "technical seo", "E-E-A-T",
  "ai visibility", "generative engine optimization", or any variation
  requesting website optimization for AI-powered search engines. Analyzes
  websites for AI search readiness across citability, crawler access,
  brand authority, structured data, technical foundations, and content quality.
argument-hint: "[audit | citability | crawlers | llmstxt | brands | schema | technical | content] <url>"
---

# AI SEO — Generative Engine Optimization

Optimize websites for AI-powered search engines (ChatGPT, Claude, Perplexity, Gemini, Google AI Overviews) while maintaining traditional SEO foundations.

AI search is eating traditional search. This skill optimizes for where traffic is going, not where it was.

## Usage

```bash
/ai-seo audit <url>            # Full GEO + SEO audit with parallel analysis
/ai-seo citability <url>       # AI citation readiness scoring
/ai-seo crawlers <url>         # AI crawler access check (robots.txt)
/ai-seo llmstxt <url>          # llms.txt analysis or generation
/ai-seo brands <url>           # Brand mentions across AI-cited platforms
/ai-seo schema <url>           # Structured data + entity recognition audit
/ai-seo technical <url>        # Technical SEO foundations for AI
/ai-seo content <url>          # Content quality + E-E-A-T assessment
```

## Why GEO Matters

| Signal | Impact |
|--------|--------|
| AI-referred traffic growth | +527% YoY |
| AI traffic conversion vs organic | 4.4x higher |
| Brand mentions vs backlinks for AI | 3x stronger correlation |
| Gartner: search traffic drop by 2028 | -50% |
| Sites with llms.txt | < 5% (early mover advantage) |

## Subcommands

| Subcommand   | Command                      | Description                                     |
|--------------|------------------------------|-------------------------------------------------|
| `audit`      | `/ai-seo audit <url>`        | Full GEO audit with composite scoring           |
| `citability` | `/ai-seo citability <url>`   | Passage-level AI citation readiness              |
| `crawlers`   | `/ai-seo crawlers <url>`     | AI crawler access analysis (robots.txt)          |
| `llmstxt`    | `/ai-seo llmstxt <url>`      | llms.txt standard analysis or generation         |
| `brands`     | `/ai-seo brands <url>`       | Brand authority on AI training platforms          |
| `schema`     | `/ai-seo schema <url>`       | Structured data + entity recognition             |
| `technical`  | `/ai-seo technical <url>`    | Technical SEO for AI crawlers                    |
| `content`    | `/ai-seo content <url>`      | Content quality + E-E-A-T scoring                |

- For `/ai-seo audit`: see [subcommands/audit.md](subcommands/audit.md)
- For `/ai-seo citability`: see [subcommands/citability.md](subcommands/citability.md)
- For `/ai-seo crawlers`: see [subcommands/crawlers.md](subcommands/crawlers.md)
- For `/ai-seo llmstxt`: see [subcommands/llmstxt.md](subcommands/llmstxt.md)
- For `/ai-seo brands`: see [subcommands/brand-mentions.md](subcommands/brand-mentions.md)
- For `/ai-seo schema`: see [subcommands/schema.md](subcommands/schema.md)
- For `/ai-seo technical`: see [subcommands/technical.md](subcommands/technical.md)
- For `/ai-seo content`: see [subcommands/content.md](subcommands/content.md)

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

## How to Fetch Pages

All subcommands that need page content should use available tools:

1. **WebFetch** for HTML content extraction and analysis
2. **Bash(curl -s)** for raw file fetching (robots.txt, llms.txt, sitemaps)
3. **WebSearch** for brand mention discovery across platforms

Do NOT use Python scripts or external dependencies. The LLM's analysis capabilities replace regex-based scoring with context-aware, more accurate assessment.

## Output Format

All subcommands return analysis in the response as structured markdown. No files are created unless explicitly requested. Each analysis includes:

- Score (0-100) with grade (A-F)
- Key findings with specific file/line/URL references
- Prioritized recommendations (Critical → High → Medium → Low)
- Quick wins highlighted separately
