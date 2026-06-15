# Structured Data & Entity Recognition

Audit structured data (JSON-LD, Microdata, RDFa) with a focus on AI entity recognition — not just Google rich snippets. Structured data tells AI systems "this is a known entity" and connects it to the knowledge graph.

## Command

```bash
/ai-seo schema <url|path>
```

## Why Schema Matters for AI (Beyond Rich Snippets)

Traditional schema.org focus: earn rich snippets in Google results.
GEO schema focus: **entity recognition** — make AI systems understand WHO you are and connect you to your broader presence.

The `sameAs` property is the single most impactful schema element for GEO. It creates explicit entity links that AI systems use to build knowledge graphs.

## Analysis Procedure

1. **Get the page markup** and extract all structured data:
   - Web mode: WebFetch the URL
   - Local mode (see SKILL.md Input Modes): `Grep "application/ld+json"` across source/template files and Read the matches; also grep for Microdata (`itemscope`, `itemprop`) and RDFa (`typeof`, `property`) attributes
   - JSON-LD blocks (`<script type="application/ld+json">`)
   - Microdata attributes (`itemscope`, `itemprop`)
   - RDFa attributes (`typeof`, `property`)

2. **Detect existing schemas** and categorize:

   | Schema Type | GEO Points | Purpose |
   |-------------|------------|---------|
   | Organization + sameAs | 20 | Entity recognition (CRITICAL) |
   | Person (author) + sameAs | 20 | E-E-A-T author authority |
   | Article + author link | 15 | Content attribution for citation |
   | Business-type specific | 15 | SaaS/Local/E-commerce/Publisher |
   | WebSite + SearchAction | 10 | Site-level signals |
   | speakable | 10 | Voice/AI assistant citation target |
   | BreadcrumbList | 5 | Navigation context |
   | knowsAbout | 5 | Expertise signals |

3. **Audit sameAs links** (most important for GEO):

   Priority order for sameAs URLs:
   | Priority | Platform | Why |
   |----------|----------|-----|
   | 1 | Wikipedia | Strongest entity signal for AI |
   | 2 | Wikidata | Structured knowledge graph |
   | 3 | LinkedIn (company/person) | Professional authority |
   | 4 | YouTube (channel) | High AI training weight |
   | 5 | Twitter/X | Social proof |
   | 6 | GitHub | Technical authority (for tech) |
   | 7 | Crunchbase | Business authority (for startups) |
   | 8 | Facebook | Social presence |
   | 9-14 | Instagram, TikTok, Apple Podcasts, industry directories | Secondary signals |

   Check: Do sameAs URLs actually resolve? Do they point to the correct entity?

4. **Validate schemas**:
   - Are required properties present?
   - Are values actual content (not placeholder/empty)?
   - Is JSON-LD well-formed?
   - Are there deprecated schemas? (HowTo, FAQPage lost rich results support in 2023-2024)

5. **Score calculation** (0-100): Sum GEO points from detected schemas (full coverage totals 100; cap at 100).

6. **Generate missing schemas** as copy-paste JSON-LD based on business type:

   - **All sites**: Organization + sameAs, WebSite + SearchAction
   - **SaaS**: SoftwareApplication
   - **Local business**: LocalBusiness with geo coordinates
   - **E-commerce**: Product with offers and reviews
   - **Publisher**: Article + Person (author) with speakable

## Output Format

```markdown
# Structured Data Report: [URL]

## Score: [XX]/100 (Grade [A-F])

## Detected Schemas

| Schema Type | Format | Valid | GEO Points | Issues |
|-------------|--------|-------|------------|--------|
| [type] | JSON-LD/Microdata/RDFa | YES/NO | [N] | [issue or "None"] |

## sameAs Audit

| Platform | URL | Resolves | Correct Entity |
|----------|-----|----------|----------------|
| [platform] | [url] | YES/NO | YES/NO/MISSING |

## Missing (Recommended)

| Schema | GEO Points | Priority |
|--------|------------|----------|
| [type] | [N] | Critical/High/Medium |

## Generated JSON-LD

### Organization (with sameAs)
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "[extracted name]",
  "url": "[site url]",
  "sameAs": [
    "[wikipedia url if found]",
    "[linkedin url]",
    "[youtube url]",
    "[twitter url]"
  ]
}
```

### [Business-type specific schema]
```json
[Generated based on detected business type]
```

## Recommendations
1. [Highest-impact schema action]
2. [...]
```

## Important Notes

- `sameAs` URLs must point to YOUR entity, not generic pages. Verify each link.
- `speakable` marks content sections AI assistants should quote — add it to your most citable passages (pairs with citability analysis).
- `knowsAbout` on Person schemas strengthens E-E-A-T signals for author entities.
- HowTo and FAQPage schemas lost Google rich results but still provide structured signals to AI systems — keep them if they exist, but don't add new ones.
- **Local mode is a lower bound:** a static file scan sees only JSON-LD written literally in source. Schema injected at runtime (Next.js `<Head>` / Metadata API, CMS plugins, `react-helmet`) is invisible locally — report the local score as a floor and recommend confirming against the live URL.
