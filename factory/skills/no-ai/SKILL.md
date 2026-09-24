---
name: no-ai
description: >
  Finds the habits that make prose read as machine-generated and rewrites them
  in the writer's own voice, without changing facts, claims, or scope. `scan`
  lists the findings; `fix` returns the rewritten text with a short change log.
  An optional writing sample sets the target voice.
license: MIT
version: "2.0.0"
metadata:
  author: KilimcininKorOglu
  category: writing
argument-hint: "[scan | fix] [text or file path] [voice sample path]"
disable-model-invocation: true
---

# No AI

Generated prose is rarely wrong. It is predictable: the same safe words, the
same sentence shapes, the same way of opening and closing every paragraph. A
reader notices the pattern long before they can name it, and then trusts the
content less. This skill removes the pattern and keeps the content.

The job is editing, not authoring. The output says what the input said, to the
same reader, at roughly the same length. It never adds a fact, a number, a
quote, an anecdote, or an opinion that the input or the writer did not supply.

## Usage

```
/no-ai [scan | fix] <text or file path> [voice sample path]
```

| Argument | Meaning |
|----------|---------|
| `scan` | Report the findings only. Change nothing. |
| `fix` | Rewrite the text. This is the default when no mode is given. |
| text or file path | The prose to edit. A path that exists is read as a file; anything else is treated as the text itself. |
| voice sample path | Optional. Earlier writing by the same person. It sets the target voice. |

When the input is a file and the mode is `fix`, write the result back to that
file only after the user confirms. Otherwise return the result in the reply.

## Step 1: Read the input and its purpose

1. Load the text. Note its format: plain prose, Markdown, an email, release
   notes, documentation, a social post, a commit message.
2. Name the reader and the purpose in one line each. The same sentence can be
   right in a README and wrong in a personal email, so every later decision is
   made against this line.
3. Mark the regions that must not change: code blocks, inline code, command
   output, quotations, product and API names, legal or contractual wording,
   numbers, dates, and links. Edit around them, never inside them.

## Step 2: Set the target voice

If the user supplied a sample, measure it before editing anything:

- average sentence length and how much it varies;
- how paragraphs start: with the point, with context, or with an example;
- register: contractions, first person, humor, profanity, jargon level;
- punctuation habits: dashes, semicolons, parentheses, exclamation marks;
- words the writer uses often and words they never use.

Match those measurements. When there is no sample, take the voice from the
parts of the input that already sound human, and default to plain, direct,
specific prose. Never import a personality the writer did not show.

## Step 3: Scan

Read [references/checklist.md](references/checklist.md) and check the text
against every marker in it. The checklist is grouped by the scale a marker
works at: word, sentence, paragraph, document, and stance.

Record each finding with the exact excerpt, its marker ID, and the reason it
reads as generated in this context. One occurrence of a marker is often fine;
a marker that repeats, or several markers stacked in one passage, is the real
signal. Judge density, not single hits.

Do not flag what the checklist lists under "Leave alone" for that marker.

## Step 4: Rewrite (`fix` mode only)

Edit passage by passage, lowest scale first: fix words, then sentences, then
paragraph shape, then document shape.

- Replace a vague word with the specific thing it stands for, using only
  information already present. If the specific thing is unknown, cut the vague
  word instead of inventing a detail.
- Break a repeated sentence shape. Vary length, open some sentences with the
  subject and some with the condition, and let a short sentence stand alone.
- Cut sentences that only announce, restate, or summarize. Keep one clear
  statement of each point.
- Keep the author's structure unless the structure itself is a marker. Do not
  turn prose into bullets or bullets into prose unless the checklist says so.
- Keep the length within about 20 percent of the input. A shorter result is
  acceptable when the cut material was filler; a longer one needs a reason.
- Keep every protected region from Step 1 byte for byte.

## Step 5: Check the rewrite

Scan the rewrite again with the same checklist. A rewrite often trades one
marker for another, for example removing dashes and adding semicolons in the
same rhythm. Repeat Step 4 on any passage that still triggers.

Then compare the rewrite with the input, claim by claim:

- every fact, number, name, and commitment in the input is still present;
- nothing new is asserted;
- the hedging level is unchanged: a "may" stays a "may", a "will" stays a
  "will";
- the reader and purpose from Step 1 are still served.

Fix any difference before returning the result.

## Step 6: Report

**`scan` mode** returns a table and a one-line verdict:

```
| # | Marker | Excerpt | Why it reads as generated |
|---|--------|---------|---------------------------|
| 1 | S2 | "It's not just a tool, it's a partner." | Contrast frame with an empty first half |

Verdict: <clean | light | heavy>, N findings, densest in <section>.
```

`clean` means no marker repeats. `light` means isolated markers that a reader
may not notice. `heavy` means repeated or stacked markers in most paragraphs.

**`fix` mode** returns the rewritten text first, then a change log of at most
eight lines that names the marker IDs addressed and anything deliberately left
unchanged, with the reason.

## Rules

- Preserve meaning over style. When a stylistic fix would change what a
  sentence claims, keep the claim and leave the style.
- Never invent specifics to make prose sound concrete. An honest general
  statement is better than a fabricated example.
- Never add personality, jokes, opinions, or first-person experience the
  writer did not provide.
- Keep the writer's language. Edit Turkish as Turkish and English as English;
  do not translate.
- Treat the checklist as evidence, not as a quota. Text that has none of the
  markers needs no edit, and a clean result may be identical to the input.
- In `scan` mode, never modify the input.
