# AI Citability Scoring

Score how likely AI systems are to cite and quote content from a page. Analyzes at the passage level — AI models extract and cite individual passages, not entire pages.

## Command

```bash
/ai-seo citability <url>
```

## Core Insight

Research (Georgia Tech, Princeton, IIT Delhi 2024) shows AI systems preferentially cite passages that are:
- **134-167 words** in length (optimal extraction window)
- **Self-contained** (readable without surrounding context)
- **Fact-rich** (statistics, named entities, specific claims)
- **Answer-shaped** (directly answers an implicit question)

Applying these patterns yields 30-115% visibility lifts in AI search results.

## Scoring Categories

### 1. Answer Block Quality (30%)

Does the passage directly answer a question a user would ask?

| Score | Criteria |
|-------|----------|
| 90-100 | Opens with a clear definition or direct answer. Uses "X is...", "X refers to...", or leads with the key fact. No filler before the answer. |
| 70-89 | Answer present but buried after 1-2 setup sentences. Good substance once reached. |
| 50-69 | Answer partially present. Mixed with tangential information. Requires reader effort. |
| 30-49 | Vague or indirect. Talks around the topic without committing to a clear answer. |
| 0-29 | No discernible answer. Pure narrative or opinion without extractable facts. |

**Definition patterns to look for:**
- "X is [definition]" — strongest
- "X refers to [explanation]"
- "[Question]? [Direct answer]." — Q&A format
- "[Statistic]. This means [interpretation]." — data-first

### 2. Self-Containment (25%)

Can the passage be understood without reading anything before or after it?

| Score | Criteria |
|-------|----------|
| 90-100 | Fully self-contained. Uses explicit subject names (not pronouns). No "as mentioned above" or "this approach". Word count 100-200. |
| 70-89 | Mostly self-contained. One minor reference to context. Key terms defined inline. |
| 50-69 | Partially dependent. Uses "it", "they", "this" without clear antecedent. |
| 30-49 | Heavily context-dependent. Multiple pronoun references. Assumes reader knowledge. |
| 0-29 | Incomprehensible without surrounding text. |

**Red flags:** "As we discussed", "this approach", "the above method", bare pronouns at start of passages.

### 3. Structural Readability (20%)

Is the content structured for easy extraction?

- Question-based headings (`## What is X?`, `## How does Y work?`) → +15
- Short paragraphs (2-4 sentences per paragraph) → +10
- Numbered lists or tables with data → +10
- Heading hierarchy (H2 → H3, no skips) → +5
- Long unbroken paragraphs (>7 sentences) → -15
- Missing headings on long pages → -10

### 4. Statistical Density (15%)

Does the passage contain verifiable, citable data?

- Named percentages ("37% of enterprises") → +5 each (max 20)
- Dollar amounts or metrics ("$4.2M revenue") → +5 each (max 15)
- Named sources ("according to Gartner") → +10 each (max 20)
- Specific timeframes ("in Q3 2025") → +3 each (max 10)
- Comparative claims with numbers ("3x faster than") → +5 each (max 15)
- Vague claims ("many companies", "significant growth") → -5 each

### 5. Uniqueness & Original Data (10%)

Does the content offer something AI can only get here?

- First-party research or survey data → +30
- Proprietary benchmarks or datasets → +25
- Original case studies with named companies + numbers → +20
- Unique methodology or framework → +15
- Expert interviews with named individuals → +10
- Regurgitated industry knowledge available everywhere → 0

## Analysis Procedure

1. **Fetch the page** using WebFetch. Extract the main content body (ignore nav, footer, sidebar).

2. **Segment into passages** at heading boundaries. Each section under a heading is one passage.

3. **Score each passage** across all 5 categories. Calculate weighted score:
   ```
   Passage Score = (Answer * 0.30) + (SelfContain * 0.25) +
                   (Structure * 0.20) + (Stats * 0.15) + (Unique * 0.10)
   ```

4. **Calculate page score** = average of all passage scores.

5. **Identify top 3 most citable passages** and **top 3 weakest passages**.

6. **Generate rewrite suggestions** for the 3 weakest passages using before/after format.

## Output Format

```markdown
# Citability Report: [URL]

## Page Score: [XX]/100 (Grade [A-F])

## Passage Breakdown

| # | Heading | Words | Answer | Self-Contain | Structure | Stats | Unique | Total | Grade |
|---|---------|-------|--------|--------------|-----------|-------|--------|-------|-------|
| 1 | [heading] | [N] | XX | XX | XX | XX | XX | XX | X |
| 2 | ... | ... | ... | ... | ... | ... | ... | ... | ... |

## Top 3 Most Citable Passages
1. **[Heading]** (Score: XX) — [why it works]
2. ...

## Top 3 Weakest Passages
1. **[Heading]** (Score: XX) — [primary issue]
2. ...

## Rewrite Suggestions

### Passage: [Heading of weakest passage]

**Before:**
> [Current text — first 2-3 sentences]

**After:**
> [Rewritten for citability — same information, better structure]

**What changed:** [Specific improvements: added definition opener, replaced pronouns, added statistic]

[Repeat for top 3 weakest]

## Quick Wins
- [Actionable improvement 1]
- [Actionable improvement 2]
- [Actionable improvement 3]
```

## Important Notes

- Score based on actual content analysis, not regex patterns. The LLM's understanding of passage quality is more accurate than keyword matching.
- Optimal passage length (134-167 words) is a guideline, not a hard rule. A 200-word passage with perfect self-containment scores higher than a 150-word passage with pronoun dependencies.
- Rewrite suggestions must preserve the author's voice and facts — only restructure, don't rewrite content.
