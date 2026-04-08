---
name: draft-to-article
description: >
  This skill MUST be invoked when the user says "format article", "makale formatla",
  "draft to article", "taslağı makaleye çevir", "taslağı formatla", "X article",
  "LinkedIn article", "Medium article", "Substack article", "makale yaz",
  "article format", or any variation requesting long-form draft formatting for a
  publishing platform. Restructures continuous text into platform-optimized articles
  with section architecture, paragraph rhythm, visual placement, and title options.
argument-hint: "[x | linkedin | medium]"
---

# Draft to Article

Transform continuous draft text into structured articles optimized for a specific publishing platform.

## Usage

```bash
/draft-to-article x            # X (Twitter) Articles format
/draft-to-article linkedin     # LinkedIn Articles format
/draft-to-article medium       # Medium / Substack format
/draft-to-article              # Ask which platform to target
```

## Platform Routing

| Subcommand | Command                      | Description                                |
|------------|------------------------------|--------------------------------------------|
| `x`        | `/draft-to-article x`        | X Articles with strict brevity constraints  |
| `linkedin` | `/draft-to-article linkedin` | LinkedIn Articles with professional tone    |
| `medium`   | `/draft-to-article medium`   | Medium/Substack with rich formatting        |

- For `/draft-to-article x`: see [subcommands/x-article.md](subcommands/x-article.md)
- For `/draft-to-article linkedin`: see [subcommands/linkedin.md](subcommands/linkedin.md)
- For `/draft-to-article medium`: see [subcommands/medium.md](subcommands/medium.md)

If no subcommand is provided, use AskUserQuestion to ask which platform the article targets.

## Process (All Platforms)

1. **Analyze the draft**: Identify core thesis, key arguments/steps, natural section breaks, tone
2. **Select platform rules**: Load the platform-specific subcommand
3. **Impose structure**: Apply Section Architecture rules
4. **Apply rhythm**: Enforce Paragraph Rhythm rules
5. **Insert visual markers**: Place `[IMAGE: description]` where visuals strengthen the piece
6. **Craft titles**: Generate 3 title options
7. **Output**: Formatted article with structural summary

## Shared Rules (Apply to All Platforms)

### Opening (First 2-3 Sentences)

The opening MUST do one of:
- Make a strong declarative stance
- Establish a counterintuitive premise or frame-shift
- State a personal position with conviction

Strong openings:
- "I am not a stock picker. I worship at the altar of..."
- "The last generation of [X] created a trillion-dollar ecosystem by..."
- "Everyone tells you to [conventional wisdom]. They're wrong."

Weak openings (NEVER use):
- "Have you ever wondered..."
- "In today's fast-paced world..."
- Questions as first lines
- Dictionary definitions
- "Let me tell you about..."

### The Zoom-Out Move

Every article needs a moment where the specific topic connects to broader implications. This usually occurs 40-60% through the piece. The transition must be explicit:

- "This isn't just about [specific topic]. It's about..."
- "Zoom out, and the pattern is clear..."
- "What [specific example] reveals about [broader trend]..."

### Closing

End with one of:
- A concrete story or anecdote that crystallizes the thesis
- A framework or checklist the reader can immediately apply
- A thesis restatement with forward-looking implications

NEVER end with:
- "What do you think? Let me know in the comments"
- Generic CTAs ("Like and subscribe")
- Trailing summaries that repeat everything said above

### Paragraph Rhythm

- Default: 1-3 sentences per paragraph
- Emphasis: single-sentence paragraphs (2-4 per article, use sparingly)
- Deep exposition: 4-5 sentences max (1-2 per section)
- Hard limit varies by platform (see subcommand)

### Title Generation

Generate 3 title options:

1. **Counterintuitive / Contrarian**: "Why [Accepted Belief] Is Actually [Opposite]"
2. **Specific + Stakes**: "The [Specific Thing] That [Concrete Consequence]"
3. **Declarative Stance**: "[Bold Claim About How the World Works]"

NEVER use:
- "X Tips for Y"
- "How to [Generic Outcome]"
- "The Ultimate Guide to..."
- Clickbait numbers without substance ("7 Ways to...")

### Visual Placement

Insert `[IMAGE: description]` on its own line where visuals strengthen the piece:
- After introducing a complex concept that benefits from illustration
- At natural pause points between major sections
- Where data, charts, or diagrams would support a claim
- After the opening section (header image reminder)

Each marker includes a brief note:
```
[IMAGE: diagram showing the feedback loop between X and Y]
```

### Bold Text

- Use to highlight key phrases within paragraphs
- Max 1-2 bold phrases per section
- Never bold entire sentences
- Bold should draw the skimmer's eye to the argument skeleton

### Lists and Bullets

- Use sparingly and strategically -- not as default structure
- When used: 3-5 items max, each item punchy
- Prefer prose with inline enumeration:
  - "Three things matter: speed, clarity, and repetition."
  - NOT a bullet list for the same content

## Output Format

```markdown
## Title Options
1. [Contrarian option]
2. [Specific + Stakes option]
3. [Declarative Stance option]

## Platform: [X Article / LinkedIn / Medium]

## Header Image Suggestion
[1-2 sentence concept for the header image based on the article's core theme]

---

[FORMATTED ARTICLE WITH STRUCTURE APPLIED]

---

## Structural Summary
- Platform: [X / LinkedIn / Medium]
- Sections: [count]
- Word count: [approximate]
- Reading time: ~[N] min
- Zoom-out moment: [where it occurs]
- Visual placements: [count]
```

## What This Skill Does NOT Do

- Rewrite content or change the author's voice
- Generate new content from scratch
- Change tone (assumes tone is already set by the author)
- Translate between languages
- Perform SEO keyword research
