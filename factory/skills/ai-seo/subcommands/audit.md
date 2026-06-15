# Full GEO Audit

Run a comprehensive AI search optimization audit on a website. Produces a composite GEO Score (0-100) across 6 categories using parallel analysis.

## Command

```bash
/ai-seo audit <url|path>
```

## Process

### Phase 1: Discovery (Sequential)

**Local mode** (argument is a local path — see SKILL.md Input Modes): replace every fetch below with its local equivalent — homepage → the main index/template file via Read + Glob; robots.txt / llms.txt / sitemap.xml → Read from repo root or `public/`/`static/`; page discovery → Glob content/template files instead of crawling the sitemap. Brand mention search still uses WebSearch.

1. **Fetch homepage** using WebFetch. Extract:
   - Title, meta description, H1-H6 structure
   - Business type signals (see SKILL.md Business Type Detection)
   - Existing structured data (JSON-LD, Microdata, RDFa)
   - Technology stack signals (framework, CMS, SSR indicators)

2. **Check robots.txt** using `Bash(curl -s <domain>/robots.txt)`. Note AI crawler rules.

3. **Check llms.txt** using `Bash(curl -s <domain>/llms.txt)`. Note existence and quality.

4. **Discover pages** via sitemap or internal links (max 50 pages):
   - Try `Bash(curl -s <domain>/sitemap.xml)` first
   - If no sitemap, extract internal links from homepage
   - Select representative pages: homepage + top content + key landing pages

### Phase 2: Parallel Analysis

Launch all 7 analysis subagents **in parallel**, each analyzing one dimension. Each subagent receives the Phase 1 discovery data as context.

| Agent | Analysis | Subcommand Reference |
|-------|----------|---------------------|
| Agent 1 | AI Citability — passage-level scoring on top 5-10 pages | `citability.md` |
| Agent 2 | Brand Mentions — platform presence scan | `brand-mentions.md` |
| Agent 3 | Technical SEO — SSR, CWV, security headers | `technical.md` |
| Agent 4 | Crawler Access — robots.txt AI crawler rules | `crawlers.md` |
| Agent 5 | llms.txt — presence and quality | `llmstxt.md` |
| Agent 6 | Content Quality — E-E-A-T, freshness, topical authority | `content.md` |
| Agent 7 | Structured Data — schema detection, entity recognition, sameAs | `schema.md` |

Each agent returns a category score (0-100) and top findings. The 7 agents map onto **6 composite categories**: crawlers (Agent 4) and llms.txt (Agent 5) both feed the single Platform category in Phase 3 — the agent count never changes the composite formula. In Local mode, each agent reads local files per its subcommand's Local Mode section instead of fetching, and returns "Not assessable locally" for any category whose source is not in the repo.

### Phase 3: Synthesis (Sequential)

1. Collect all agent results
2. Calculate composite GEO Score:
   ```
   GEO = (Citability * 0.25) + (Brand * 0.20) + (Content * 0.20) +
         (Technical * 0.15) + (Schema * 0.10) + (Platform * 0.10)
   ```
   Platform score = average of the crawler-access score (crawlers.md, Agent 4) and the llms.txt score (llmstxt.md, Agent 5). The composite always has exactly these 6 categories, regardless of how many agents ran.

3. Apply business-type weight adjustments BEFORE the weighted sum — shift the category weights from step 2 by these percentage points (each row nets to zero, so the weights still total 100), then recompute the GEO score with the adjusted weights:
   - SaaS: citability +5, brand -5
   - Local: schema +5, citability -5
   - E-commerce: schema +5, content -5
   - Publisher: citability +5, content +5, schema -10

   **Local mode ordering:** apply the business-type shift to the full six-category weight set FIRST (the invariant above holds — total stays 100). THEN drop any category flagged "Not assessable locally", renormalize the remaining adjusted weights to total 100 (divide each by their sum), and take the weighted sum over kept categories only — never substitute 0. List each excluded category with its reason and label the composite "partial". This ordering matters: excluding a category before the shift would leave an adjustment (e.g. E-commerce's `content -5`) with nothing to subtract, pushing the total off 100.

4. Classify all findings by severity:
   - **Critical**: Blocks AI visibility entirely (all Tier 1 crawlers blocked, no SSR, no structured data)
   - **High**: Significantly reduces AI citation potential (poor citability, missing sameAs, broken schema)
   - **Medium**: Missed optimization opportunity (no llms.txt, weak E-E-A-T signals, no speakable markup)
   - **Low**: Polish items (suboptimal passage length, missing alt tags, thin content pages)

## Output Format

```markdown
# GEO Audit Report: [Domain or local project path]

## Composite Score: [XX]/100 (Grade [A-F])
*(Local mode: append "— partial; [excluded categories] not assessable locally" when any category was dropped, and flag static-derived scores as a lower bound.)*

| Category | Score | Grade | Key Issue |
|----------|-------|-------|-----------|
| AI Citability | XX/100 | X | [one-line summary] |
| Brand Authority | XX/100 | X | [one-line summary] |
| Content & E-E-A-T | XX/100 | X | [one-line summary] |
| Technical SEO | XX/100 | X | [one-line summary] |
| Structured Data | XX/100 | X | [one-line summary] |
| Platform Access | XX/100 | X | [one-line summary] |

## Business Type: [Detected Type]

## Quick Wins (Do This Week)
1. [Highest-impact, lowest-effort action]
2. [...]
3. [...]

## Critical Issues
[Findings that block AI visibility]

## Detailed Findings

### AI Citability
[Top findings from citability analysis]

### Brand Authority
[Top findings from brand analysis]

### Content & E-E-A-T
[Top findings from content analysis]

### Technical SEO
[Top findings from technical analysis]

### Structured Data
[Top findings from schema analysis]

## Recommendations (Prioritized)

| # | Priority | Action | Category | Impact |
|---|----------|--------|----------|--------|
| 1 | Critical | [action] | [category] | [expected improvement] |
| 2 | High | ... | ... | ... |
```

## Quality Gates

- Respect robots.txt — do not fetch disallowed paths
- Max 50 pages analyzed per audit
- Skip any page that does not return promptly rather than blocking the whole audit
- If a category analysis fails, report "Unable to assess" with reason — do not guess
- In Local mode: read files from disk (no fetching), exclude categories whose source is not in the repo and renormalize instead of scoring 0, and treat static scores as a lower bound (see SKILL.md Input Modes)
