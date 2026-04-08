# Full GEO Audit

Run a comprehensive AI search optimization audit on a website. Produces a composite GEO Score (0-100) across 6 categories using parallel analysis.

## Command

```bash
/ai-seo audit <url>
```

## Process

### Phase 1: Discovery (Sequential)

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

Launch up to 5 subagents **in parallel**, each analyzing a different dimension. Each subagent receives the Phase 1 discovery data as context.

| Agent | Analysis | Subcommand Reference |
|-------|----------|---------------------|
| Agent 1 | AI Citability — passage-level scoring on top 5-10 pages | `citability.md` |
| Agent 2 | Brand Mentions — platform presence scan | `brand-mentions.md` |
| Agent 3 | Technical SEO — SSR, CWV, crawler access, security | `technical.md` + `crawlers.md` |
| Agent 4 | Content Quality — E-E-A-T, freshness, topical authority | `content.md` |
| Agent 5 | Structured Data — schema detection, entity recognition, sameAs | `schema.md` |

Each agent returns a category score (0-100) and top findings.

### Phase 3: Synthesis (Sequential)

1. Collect all agent results
2. Calculate composite GEO Score:
   ```
   GEO = (Citability * 0.25) + (Brand * 0.20) + (Content * 0.20) +
         (Technical * 0.15) + (Schema * 0.10) + (Platform * 0.10)
   ```
   Platform score = average of crawler access and llms.txt scores from Agent 3.

3. Apply business-type adjustments:
   - SaaS: +5 weight on citability, -5 on brand
   - Local: +5 weight on schema, -5 on citability
   - E-commerce: +5 weight on schema, -5 on content
   - Publisher: +5 weight on citability, +5 on content, -10 on schema

4. Classify all findings by severity:
   - **Critical**: Blocks AI visibility entirely (all Tier 1 crawlers blocked, no SSR, no structured data)
   - **High**: Significantly reduces AI citation potential (poor citability, missing sameAs, broken schema)
   - **Medium**: Missed optimization opportunity (no llms.txt, weak E-E-A-T signals, no speakable markup)
   - **Low**: Polish items (suboptimal passage length, missing alt tags, thin content pages)

## Output Format

```markdown
# GEO Audit Report: [Domain]

## Composite Score: [XX]/100 (Grade [A-F])

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
- WebFetch timeout: 30 seconds per page
- If a category analysis fails, report "Unable to assess" with reason — do not guess
