# Brand Mentions on AI-Cited Platforms

Analyze brand presence and authority across platforms that AI systems use as training data and citation sources. Unlinked brand mentions now outperform traditional backlinks for AI search visibility.

## Command

```bash
/ai-seo brands <url|path>
```

## Core Insight

Ahrefs research (2025-26, ~75K brands) on AI search visibility found:
- **Brand mentions correlate more strongly than backlinks** — domain authority and link-building matter less than in traditional search
- **YouTube mentions** are among the strongest correlating signals (YouTube is heavily represented in training data)
- **Wikipedia entity presence** is a strong signal for AI entity recognition
- Conversational platforms like **Reddit** are frequently cited in AI answers (noted in separate Semrush research)

These are correlations, not proven causation. The consistent takeaway: being mentioned across trusted platforms matters more than accumulating links.

## Platform Weights

| Platform | Weight | Why |
|----------|--------|-----|
| YouTube | 25% | Among the strongest correlating signals for AI citation. Overrepresented in training data. |
| Reddit | 25% | Conversational mentions carry high trust signal for AI models. |
| Wikipedia | 20% | Strongest entity recognition signal. If you exist on Wikipedia, AI knows you exist. |
| LinkedIn | 15% | Professional authority signal. Company pages, thought leadership articles. |
| Other (GitHub, StackOverflow, industry forums) | 15% | Domain-specific authority platforms. |

## Analysis Procedure

1. **Extract brand identity** from the target:
   - Web mode: from the URL's title, meta, and structured data
   - Local mode (see SKILL.md Input Modes): from `package.json` (name, description, author, homepage), README, config, and content files; brand/product names from headings and copy
   - In both modes capture: company/brand name, key products or service names, founder/CEO name (if relevant for personal brand)

2. **Search each platform** using WebSearch with platform-specific queries:
   - YouTube: `site:youtube.com "[brand name]"`
   - Reddit: `site:reddit.com "[brand name]"`
   - Wikipedia: `site:wikipedia.org "[brand name]"`
   - LinkedIn: `site:linkedin.com/company "[brand name]"` or `site:linkedin.com/in "[person name]"`
   - GitHub: `site:github.com "[brand name]"` (for tech companies)

3. **Assess each platform**:
   - **Presence**: Does the brand appear? How many mentions?
   - **Context**: Are mentions positive, negative, neutral, or mixed?
   - **Authority**: Are mentions in authoritative contexts (Wikipedia article vs. talk page, top Reddit posts vs. buried comments)?
   - **Recency**: Are mentions current or outdated?

4. **Score per platform** (0-100):
   - YouTube: Has channel (20) + mentioned in other channels (30) + educational content (25) + comment engagement (15) + recency (10)
   - Reddit: Mentioned in relevant subreddits (30) + positive sentiment (25) + AMA/official presence (20) + recency (15) + depth of discussion (10)
   - Wikipedia: Has article (40) + article quality/length (25) + linked from other articles (20) + updated recently (15)
   - LinkedIn: Company page exists (20) + employee content (25) + industry mentions (25) + thought leadership (20) + followers (10)

5. **Calculate composite score**:
   ```
   Brand Score = (YouTube * 0.25) + (Reddit * 0.25) + (Wikipedia * 0.20) +
                 (LinkedIn * 0.15) + (Other * 0.15)
   ```

## Output Format

```markdown
# Brand Mentions Report: [Brand Name]

## Score: [XX]/100 (Grade [A-F])

## Platform Breakdown

| Platform | Score | Presence | Sentiment | Key Finding |
|----------|-------|----------|-----------|-------------|
| YouTube | XX/100 | [Y/N + details] | [+/-/~] | [one-line] |
| Reddit | XX/100 | [Y/N + details] | [+/-/~] | [one-line] |
| Wikipedia | XX/100 | [Y/N + details] | [N/A] | [one-line] |
| LinkedIn | XX/100 | [Y/N + details] | [+/-/~] | [one-line] |
| Other | XX/100 | [Y/N + details] | [+/-/~] | [one-line] |

## Strongest Signal
[Which platform and why]

## Biggest Gap
[Which platform is missing and what to do about it]

## Recommendations
1. [Highest-impact platform action]
2. [...]
3. [...]
```

## Important Notes

- WebSearch results may not capture all mentions. Findings represent a sample, not an exhaustive count.
- Wikipedia articles cannot be created for promotional purposes — only note the gap and suggest building genuine notability.
- Reddit mentions must be organic. Astroturfing is detectable and harmful.
- Focus on authority and context of mentions, not raw count. One Wikipedia article > 100 Reddit comments.
- **Local mode** changes only where brand identity is read (from `package.json`/config/content instead of the live page). The mention search still uses WebSearch — brand reputation lives on the open web, not in the repo — so this category stays fully scored in Local mode.
