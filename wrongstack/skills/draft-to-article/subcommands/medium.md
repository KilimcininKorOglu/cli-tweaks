# Medium / Substack Articles

Platform-specific formatting rules for Medium and Substack articles. Apply these ON TOP of the shared rules in `../SKILL.md`.

## Platform Constraints

- No character limit (long-form is the native format)
- H2, H3 headers supported
- Rich formatting: pull quotes, code blocks, footnotes, embedded media
- Desktop-first reading (but mobile-responsive)
- SEO matters -- subtitle and tags influence discovery

## Subheadings

- Insert H2 subheadings every 4-8 paragraphs
- H3 allowed for detailed sub-sections
- Can be more descriptive and nuanced than X or LinkedIn
  - OK: "What the research actually says about remote work productivity"
  - OK: "A brief history of the problem"
- Sentence case

## Paragraph Rules

- Max 7 sentences per paragraph (longer exposition acceptable)
- Default: 2-5 sentences
- Single-sentence paragraphs for emphasis (3-5 per article)
- Medium readers expect depth -- do not over-fragment

## Formatting

- **Bold**: key concepts, definitions, pivotal arguments
- **Italics**: book titles, foreign terms, introducing terminology
- **Lists**: acceptable for step-by-step processes, comparisons, feature lists
- **Code blocks**: fully supported -- use for technical content with language syntax highlighting
- **Block quotes**: two uses:
  1. Real quotations from sources
  2. Pull quotes -- extract the most shareable sentence and display as a block quote mid-article
- **Horizontal rules** (`---`): use to mark major section transitions (not between every section)
- **Links**: inline with descriptive anchor text, reference sources liberally

## Pull Quotes

Medium supports pull quotes as a formatting element. Identify the single most quotable/shareable sentence in the article and format it as a block quote:

```markdown
> The best frameworks don't eliminate complexity -- they make it navigable.
```

Place this at a natural pause point (usually between major sections). One pull quote per article is optimal; two maximum.

## SEO and Discovery

After the formatted article, include:

```markdown
## SEO Suggestions
- **Subtitle**: [A complementary sentence that expands on the title -- Medium shows this in previews]
- **Tags**: [tag1], [tag2], [tag3], [tag4], [tag5]
- **Clap-worthy moment**: "[The single most shareable sentence from the article]"
```

Tags should be:
- 5 tags maximum (Medium's limit)
- Mix of broad and specific: e.g., "Programming", "Software Architecture", "Microservices", "System Design", "Backend"
- Check what tags have active followers on Medium

## Opening Enhancement

Medium rewards hooks that are visible in the feed preview (~150 characters for title + subtitle). The opening paragraph should work as a standalone hook even without the title.

## Tone Guidance

Medium/Substack reward:
- Deep expertise with accessible language
- Personal narrative woven into technical or analytical content
- "Show your work" approach -- reasoning visible, not just conclusions
- References and citations (builds credibility)
- Longer, more developed arguments than X or LinkedIn

Medium/Substack penalize:
- Shallow listicles without depth
- Purely promotional content
- Paywalled content that doesn't deliver value in the free preview
- Clickbait titles that the content doesn't support

## Closing Rules

- End with the strongest version of the thesis or a thought-provoking implication
- Optional: "Further reading" section with 2-3 relevant links
- Optional: brief author note for Substack newsletters ("If you found this useful, consider subscribing for weekly deep dives on [topic].")
- No generic CTAs

## Reading Time

Include estimated reading time in the structural summary. Calculate at ~250 words per minute. Medium displays this automatically, but include it for Substack where it's manual.

## Footnotes / References

If the article references studies, books, or data:

```markdown
## References
1. [Author], "[Title]" ([Year]). [Link if available]
2. [Source description]. [Link]
```

Keep footnotes minimal -- inline links are preferred for web reading. Use a references section only for academic or data-heavy articles.
