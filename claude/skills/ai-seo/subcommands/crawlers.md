# AI Crawler Access Analysis

Analyze whether AI search engine crawlers can access a website's content. AI visibility starts with crawler access — if crawlers are blocked, nothing else matters.

## Command

```bash
/ai-seo crawlers <url>
```

## AI Crawler Tiers

### Tier 1 — Must Allow (AI Search Products)

These crawlers power live AI search. Blocking them removes your site from AI-generated answers.

| Crawler | User-Agent | Platform | Role |
|---------|-----------|----------|------|
| GPTBot | `GPTBot` | ChatGPT, OpenAI | OpenAI's main crawler (index + training) |
| OAI-SearchBot | `OAI-SearchBot` | OpenAI real-time search | Powers ChatGPT web results |
| ChatGPT-User | `ChatGPT-User` | ChatGPT browse mode | User-initiated browsing |
| ClaudeBot | `ClaudeBot` | Claude (crawl/index) | Anthropic's main crawler |
| Claude-User | `Claude-User` | Claude browse mode | User-initiated browsing |
| Claude-SearchBot | `Claude-SearchBot` | Claude search | Anthropic search features |
| PerplexityBot | `PerplexityBot` | Perplexity AI | Strong AI referral traffic |

### Tier 2 — Recommended (Broader Ecosystem)

These support AI features within larger platforms. Blocking reduces indirect AI visibility.

| Crawler | User-Agent | Platform | Note |
|---------|-----------|----------|------|
| Google-Extended | `Google-Extended` | Gemini, AI Overviews | robots.txt control token (AI opt-out), not a live crawling UA; does NOT affect Google Search ranking |
| Applebot-Extended | `Applebot-Extended` | Apple Intelligence | robots.txt control token (AI-training opt-out), not a live crawling UA |
| Meta-ExternalAgent | `Meta-ExternalAgent` | Meta AI | Meta's AI crawler (replaces the older FacebookBot for AI use) |
| Amazonbot | `Amazonbot` | Alexa, Amazon AI | Voice search + product discovery |
| Bytespider | `Bytespider` | TikTok / ByteDance AI | Emerging AI search |
| MistralAI-User | `MistralAI-User` | Mistral Le Chat | User-initiated browsing |
| DuckAssistBot | `DuckAssistBot` | DuckDuckGo AI assist | DuckAssist answers |

### Tier 3 — Optional (Training Only)

These crawl for model training, not live search. Blocking has no immediate search impact.

| Crawler | User-Agent | Purpose |
|---------|-----------|---------|
| CCBot | `CCBot` | Common Crawl (training data) |
| anthropic-ai | `anthropic-ai` | Legacy Anthropic training UA — superseded by ClaudeBot; may still appear in older robots.txt |
| GoogleOther | `GoogleOther` | Google AI training |
| Cohere-ai | `Cohere-ai` | Cohere training (undocumented; current status uncertain) |

## Analysis Procedure

1. **Fetch robots.txt** using `Bash(curl -s <domain>/robots.txt)`.

2. **Parse rules for each crawler**: For every AI crawler listed above, determine status:
   - **ALLOWED** — No blocking rules, or explicit `Allow: /`
   - **BLOCKED** — Explicit `Disallow: /` for this user-agent
   - **PARTIALLY BLOCKED** — Some paths disallowed (list which)
   - **BLOCKED BY WILDCARD** — `User-agent: *` with `Disallow: /` and no specific override
   - **NOT MENTIONED** — No rules for this crawler (inherits wildcard or defaults to allowed)

3. **Check for AI-specific files**:
   - `Bash(curl -s -o /dev/null -w "%{http_code}" <domain>/llms.txt)` — existence check

4. **Score calculation**:
   ```
   Score = (Tier1_allowed / Tier1_total * 50) +
           (Tier2_allowed / Tier2_total * 25) +
           (no_blanket_block * 15) +
           (ai_files_exist * 10)
   ```

5. **Generate recommended robots.txt** if issues found.

## Output Format

```markdown
# AI Crawler Access Report: [Domain]

## Score: [XX]/100 (Grade [A-F])

## Crawler Status

| Tier | Crawler | Status | Impact |
|------|---------|--------|--------|
| 1 | GPTBot | ALLOWED/BLOCKED/... | [impact if blocked] |
| 1 | OAI-SearchBot | ... | ... |
| 1 | ChatGPT-User | ... | ... |
| 1 | ClaudeBot | ... | ... |
| 1 | PerplexityBot | ... | ... |
| 2 | Google-Extended | ... | ... |
| 2 | Amazonbot | ... | ... |
| 2 | Applebot-Extended | ... | ... |
| 3 | CCBot | ... | ... |
| 3 | anthropic-ai | ... | ... |

## AI Files

| File | Status | Notes |
|------|--------|-------|
| robots.txt | EXISTS/MISSING | [summary of AI rules] |
| llms.txt | EXISTS/MISSING | [quality note if exists] |

## Issues Found
[List any blocking issues with severity]

## Recommended robots.txt
[If changes needed, provide the full recommended robots.txt content]
```

## Important Notes

- Blocking `Google-Extended` does NOT affect Google Search ranking — it only controls Gemini/AI training. This is a common misconception.
- `User-agent: *` with `Disallow: /` blocks ALL crawlers unless specific overrides exist.
- Some sites block AI crawlers defensively. Recommend allowing Tier 1 crawlers if the business benefits from AI search traffic.
- `PerplexityBot` generates the highest quality referral traffic among AI crawlers — prioritize allowing it.
