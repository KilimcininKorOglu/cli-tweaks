# llms.txt Analysis & Generation

Analyze existing llms.txt files or generate one from scratch. llms.txt is an emerging standard (launched September 2024) that guides AI systems on how to understand and cite a website. Early adoption advantage: fewer than 5% of sites have one.

## Command

```bash
/ai-seo llmstxt <url>          # Analyze existing llms.txt
/ai-seo llmstxt <url> generate  # Generate llms.txt from site content
```

## What is llms.txt

llms.txt tells AI systems what your site IS and what content matters. It complements robots.txt:
- **robots.txt** = "Don't access these paths" (restrictions)
- **llms.txt** = "Here's what's important and why" (guidance)

### Format Specification

```markdown
# [Site Name]

> [One-paragraph site description — who you are, what you do, who you serve]

## [Section Name]
- [Page Title](URL): [Description of what this page contains and why it matters]
- [Page Title](URL): [Description]

## [Another Section]
- [Page Title](URL): [Description]
```

**Rules:**
- H1 title (required, one only)
- Blockquote description after H1 (required)
- H2 section headers to organize content
- Markdown links with descriptive annotations
- No deeper than H2 (no H3, H4)

### llms-full.txt Variant

Optional extended version with more pages and deeper descriptions. Same format but more comprehensive. Linked from llms.txt via `[Full documentation](llms-full.txt)`.

## Analysis Mode

When analyzing an existing llms.txt:

1. **Fetch the file** using `Bash(curl -s <domain>/llms.txt)`.

2. **Validate format**:
   - Has H1 title?
   - Has blockquote description?
   - Uses H2 sections?
   - Links are valid markdown format?
   - Descriptions are meaningful (not just page titles)?

3. **Score quality** (0-100):
   - **Completeness (40%)**: Does it cover the site's key content areas? Compare against sitemap or homepage navigation.
   - **Accuracy (35%)**: Are descriptions accurate? Do URLs resolve? Do descriptions match actual page content?
   - **Usefulness (25%)**: Would an AI system understand the site better after reading this? Are descriptions specific enough to guide citation?

4. **Check for llms-full.txt** at `<domain>/llms-full.txt`.

## Generation Mode

When generating a new llms.txt:

1. **Discover site structure**:
   - Fetch homepage with WebFetch — extract navigation, key sections
   - Try sitemap: `Bash(curl -s <domain>/sitemap.xml)`
   - Identify top content categories and key pages

2. **Classify pages by importance**:
   - **Must include**: Homepage, about/company, pricing, documentation index, key product pages
   - **Should include**: Top blog posts, case studies, guides, FAQ
   - **Skip**: Legal pages, login, utility pages, paginated archives

3. **Write descriptions that guide AI**:

   Weak (just a title):
   ```
   - [Pricing](https://example.com/pricing): Our pricing page
   ```

   Strong (explains what AI can extract):
   ```
   - [Pricing](https://example.com/pricing): Three pricing tiers (Starter $29/mo, Pro $99/mo, Enterprise custom) with feature comparison matrix and annual discount details
   ```

4. **Organize into logical sections**: Group by content type (Products, Resources, Company, etc.)

5. **Generate the file** and present it in the response.

## Output Format

### Analysis Output

```markdown
# llms.txt Analysis: [Domain]

## Score: [XX]/100 (Grade [A-F])

## Format Validation
- H1 title: PASS/FAIL
- Description blockquote: PASS/FAIL
- H2 sections: PASS/FAIL
- Valid links: [N]/[total] valid
- Meaningful descriptions: [N]/[total]

## Coverage Assessment
- Pages in llms.txt: [N]
- Key pages missing: [list]
- Unnecessary pages included: [list]

## Improvement Suggestions
1. [Specific suggestion]
2. [...]

## llms-full.txt: EXISTS/MISSING
```

### Generation Output

```markdown
# Generated llms.txt for [Domain]

[The complete llms.txt content ready to save]

---

## Generation Notes
- Pages analyzed: [N]
- Pages included: [N]
- Sections: [N]
- Save this file as `llms.txt` in your site root
- Consider creating `llms-full.txt` with additional pages
```

## Important Notes

- llms.txt descriptions should explain what an AI can EXTRACT from the page, not what the page IS. "Explains three pricing tiers with costs" is more useful than "Our pricing page."
- Keep llms.txt focused (15-30 entries). Use llms-full.txt for comprehensive coverage.
- llms.txt is not a replacement for good on-page content — it's a guide that helps AI find and prioritize your best content.
