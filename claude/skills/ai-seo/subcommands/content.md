# Content Quality & E-E-A-T Assessment

Evaluate content quality through the lens of AI citation potential. Focuses on E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) as the primary quality signal AI models use when deciding what to cite.

## Command

```bash
/ai-seo content <url>
```

## E-E-A-T Framework

Since December 2025, Google applies E-E-A-T to ALL competitive queries — not just YMYL (Your Money, Your Life). AI systems follow similar quality signals when selecting sources to cite.

### Experience (25%)

First-hand knowledge the author demonstrates. AI models prefer citing someone who has DONE the thing over someone who merely reports on it.

**Strong signals:**
- "I tested...", "In our implementation...", "When we migrated..."
- Case studies with named companies, specific numbers, and outcomes
- Screenshots, original data, or unique observations from direct involvement
- Process descriptions with specific tooling and configurations used

**Weak signals:**
- "Many experts say...", "It is generally believed..."
- Rewritten summaries of other articles
- No first-person perspective or original observation
- Generic advice without implementation specifics

**Scoring:**
- 90-100: Multiple paragraphs of first-hand experience with verifiable specifics
- 70-89: Some first-hand content mixed with general information
- 50-69: Mostly reported/compiled information with occasional personal touches
- 0-49: No evidence of first-hand experience

### Expertise (25%)

Depth and accuracy of subject matter knowledge demonstrated in the content.

**Strong signals:**
- Technical accuracy (correct use of domain terminology)
- Nuanced explanations (addresses edge cases, trade-offs, limitations)
- Appropriate depth for the audience
- References to primary sources, not just popular articles

**Weak signals:**
- Surface-level explanations that any non-expert could write
- Incorrect or outdated technical claims
- Missing important caveats or limitations
- Reliance on a single source

**Scoring:**
- 90-100: Expert-level depth with nuance, trade-offs, and edge cases addressed
- 70-89: Good depth with minor gaps in nuance
- 50-69: Adequate coverage but shallow on specifics
- 0-49: Surface-level or inaccurate

### Authoritativeness (25%)

Recognition by others in the field. Measurable through external signals.

**Strong signals:**
- Author byline with credentials, linked to author page with bio
- Organization schema with sameAs linking to Wikipedia, LinkedIn
- Content cited or referenced by other authoritative sources
- Published on a domain with topical authority (consistently covers this subject)

**Weak signals:**
- No author attribution
- No organization context
- Content on a domain that covers unrelated topics
- No external references or citations

**Scoring:**
- 90-100: Named author with credentials, organizational backing, topical domain
- 70-89: Author identified with some credentials, reasonable domain authority
- 50-69: Author present but thin credentials, domain covers mixed topics
- 0-49: No author, no organizational context, off-topic domain

### Trustworthiness (25%)

Accuracy, transparency, and reliability signals.

**Strong signals:**
- Named and dated sources for claims
- Transparent methodology ("Here's how we measured this")
- Clear publication and update dates
- Contact information, privacy policy, editorial policy
- Corrections or updates noted when content changes

**Weak signals:**
- Unattributed statistics ("studies show...")
- No publication date
- No methodology for original claims
- Missing basic trust pages (about, contact, privacy)

**Scoring:**
- 90-100: All claims sourced, methodology transparent, dates clear, trust pages present
- 70-89: Most claims sourced, dates present, basic trust signals
- 50-69: Some sourcing, missing dates or methodology
- 0-49: Unattributed claims, no dates, no trust signals

## Content Quality Metrics

Beyond E-E-A-T, assess:

### Paragraph-Level Extraction Quality

AI models extract at the paragraph level. Each paragraph should be:
- **Self-contained**: 2-4 sentences, one idea per paragraph
- **Quotable in isolation**: No pronoun dependencies on previous paragraphs
- **Fact-rich**: At least one specific claim, number, or named entity per paragraph

### AI Content Assessment

AI-generated content is acceptable IF it has genuine E-E-A-T signals and human oversight. Flag as low-quality only if:
- Generic phrasing with no original insight ("In today's fast-paced world...")
- No first-hand experience or specific data
- Hedging overload ("it might be worth considering", "perhaps arguably")
- No named sources or verifiable claims
- Identical structure to typical AI output (intro → N points → conclusion)

### Topical Authority Modifier

Does the site consistently cover this topic?

| Signal | Modifier |
|--------|----------|
| 10+ published pieces on the same topic | +10 |
| Regular publication schedule on this topic | +5 |
| 3-9 related pieces | 0 |
| Only 1-2 pieces, or off-topic site | -5 |

## Analysis Procedure

1. **Fetch the page** with WebFetch. Extract main content, author info, dates, and structured data.

2. **Score each E-E-A-T dimension** (0-100) based on the criteria above.

3. **Assess paragraph quality** — count self-contained vs. context-dependent paragraphs.

4. **Check topical authority** — look for related content links, topic clusters, publication consistency.

5. **Calculate composite score**:
   ```
   Content Score = (Experience * 0.25) + (Expertise * 0.25) +
                   (Authority * 0.25) + (Trust * 0.25) + Topical Modifier
   ```

## Output Format

```markdown
# Content Quality Report: [URL]

## Score: [XX]/100 (Grade [A-F])

## E-E-A-T Breakdown

| Dimension | Score | Grade | Key Evidence |
|-----------|-------|-------|-------------|
| Experience | XX/100 | X | [what was found] |
| Expertise | XX/100 | X | [what was found] |
| Authoritativeness | XX/100 | X | [what was found] |
| Trustworthiness | XX/100 | X | [what was found] |

## Topical Authority: [+10/+5/0/-5] ([reason])

## Content Quality Signals
- Self-contained paragraphs: [N]/[total] ([%])
- Paragraphs with named data/sources: [N]/[total] ([%])
- Average paragraph length: [N] sentences
- AI content indicators: [None detected / Possible / Likely]

## Strongest Content Signal
[What this page does best for AI citation]

## Biggest Content Gap
[What most needs improvement]

## Recommendations
1. [Highest-impact content improvement]
2. [...]
3. [...]
```

## Important Notes

- E-E-A-T is assessed from content signals, not external authority metrics. This is what AI models can observe.
- First-person experience is the strongest differentiator. A page with genuine "I did X and found Y" beats a perfectly written summary.
- Topical authority requires looking beyond the single page — check if the site has related content.
- Do not penalize AI-assisted content that demonstrates real E-E-A-T. Penalize content that lacks substance regardless of how it was produced.
