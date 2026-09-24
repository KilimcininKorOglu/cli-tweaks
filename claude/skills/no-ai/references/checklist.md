# no-ai: marker checklist

Each marker has an ID, what it looks like, why a reader takes it as generated,
the usual fix, and what to leave alone. IDs are stable: the scan table and the
change log cite them.

A marker is a probability signal, not a rule violation. Report it when it
repeats, when it stacks with other markers in one passage, or when it is the
only thing a sentence does.

## W: Word level

### W1. Inflated verbs and nouns
- **Looks like:** leverage, harness, unlock, empower, elevate, streamline,
  foster, delve, navigate (for anything that is not travel), landscape, realm,
  tapestry, journey (for a process), ecosystem (for a product list).
- **Why:** these words promise more than the sentence delivers. They appear
  where a plain verb such as use, start, help, or read would carry the meaning.
- **Fix:** use the plain verb. If the plain verb makes the sentence empty, the
  sentence had nothing to say; cut it.
- **Leave alone:** a term with a fixed technical meaning, such as "ecosystem"
  in biology or "landscape" in a map layer.

### W2. Stock intensifiers
- **Looks like:** crucial, vital, pivotal, essential, seamless, robust,
  comprehensive, cutting-edge, game-changing, truly, incredibly.
- **Why:** they rate the content instead of showing it. Stacked, they make every
  point sound equally important, so none stands out.
- **Fix:** delete the intensifier, or replace it with the fact that justifies
  it ("robust" becomes "retries three times, then alerts").
- **Leave alone:** a rating the writer clearly means and supports in the next
  sentence.

### W3. Hedge stacks
- **Looks like:** "could potentially," "may possibly help to," "it might be
  argued that," "in some ways, arguably."
- **Why:** one hedge expresses uncertainty; two or three in one clause express
  nothing.
- **Fix:** keep exactly one hedge at the strength the writer intends.
- **Leave alone:** a single deliberate hedge in scientific, legal, or medical
  text.

### W4. Signpost adverbs
- **Looks like:** Additionally, Furthermore, Moreover, Notably, Importantly,
  Ultimately, Overall, In essence, at the start of consecutive sentences.
- **Why:** the connective does the work the logic should do, and it repeats in
  a fixed rhythm.
- **Fix:** delete most of them. Let order and content show the relation. Keep
  a connective only where the relation is not obvious.
- **Leave alone:** a single "however" that marks a real contrast.

## S: Sentence level

### S1. Triplets by default
- **Looks like:** "fast, reliable, and secure," "clarity, focus, and impact,"
  three parallel clauses in sentence after sentence.
- **Why:** lists of three feel complete, so generated text reaches for them
  whether there are two ideas or five.
- **Fix:** count the real items. Use two when there are two. Break a run of
  triplets by rewriting some as plain statements.
- **Leave alone:** a list of three that is literally three things.

### S2. Contrast frames
- **Looks like:** "It's not just X, it's Y." "This isn't about X; it's about Y."
  "Not X, but Y."
- **Why:** the first half sets up a claim nobody made, so the sentence spends
  its energy denying a straw position.
- **Fix:** state Y directly. Keep the contrast only when someone actually holds
  position X and the text is answering them.
- **Leave alone:** a correction of a real, stated misunderstanding.

### S3. Trailing participle clauses
- **Looks like:** "..., highlighting the importance of X." "..., ensuring a
  smooth experience." "..., reflecting a broader trend."
- **Why:** the tail adds an interpretation with no evidence and makes every
  sentence end the same way.
- **Fix:** cut the tail. If the interpretation matters, make it its own
  sentence with the reason attached.
- **Leave alone:** a participle that states a concrete, checkable result.

### S4. Colon reveals and setup questions
- **Looks like:** "The result? A faster build." "Here's the thing:" "The key
  takeaway: ..."
- **Why:** it stages a small drumroll before an ordinary statement.
- **Fix:** write the statement.
- **Leave alone:** a real question the text goes on to answer at length.

### S5. Uniform sentence length
- **Looks like:** a paragraph where every sentence has 15 to 25 words and the
  same subject-verb-object order.
- **Why:** human prose varies. Even rhythm reads as produced rather than
  written.
- **Fix:** merge two short related sentences, split a long one, and let one
  short sentence stand alone where it lands a point.
- **Leave alone:** reference text such as API docs, where uniformity helps.

### S6. Dash overuse
- **Looks like:** long dashes used several times per paragraph for asides,
  lists, and emphasis.
- **Why:** one dash is a choice; a dash in every other sentence is a tic.
- **Fix:** use commas, parentheses, a colon, or a full stop. Keep a dash only
  where the writer's sample shows the habit.
- **Leave alone:** ranges, compound modifiers, and the writer's own habit.

## P: Paragraph level

### P1. Announce, say, summarize
- **Looks like:** a paragraph that opens with "Let's explore X," makes the
  point, then closes with "In summary, X matters."
- **Why:** the reader gets the same point three times.
- **Fix:** keep the middle. Delete the announcement and the recap.
- **Leave alone:** a summary at the end of a long document, where a reader may
  have skipped ahead.

### P2. Moral of the story closers
- **Looks like:** a last sentence that zooms out: "As technology evolves, one
  thing is clear..." "This serves as a reminder that..."
- **Why:** it adds a lesson the content did not earn.
- **Fix:** end on the last concrete point.
- **Leave alone:** an explicit conclusion the writer asked for.

### P3. Balanced both-sides padding
- **Looks like:** "While X has benefits, it also has challenges. Ultimately,
  the right choice depends on your needs."
- **Why:** it avoids a position without adding any information about the
  trade-off.
- **Fix:** name the specific benefit and the specific cost, or cut the passage.
- **Leave alone:** a comparison that lists real, concrete trade-offs.

### P4. Mirror paragraphs
- **Looks like:** consecutive paragraphs with the same length and the same
  internal order: claim, elaboration, example, wrap-up.
- **Why:** repeated templates are the clearest signal at this scale.
- **Fix:** vary the order. Lead some paragraphs with the example, merge thin
  ones, and cut the wrap-up line.
- **Leave alone:** a deliberate parallel structure, such as a per-option
  section in a decision document.

## D: Document level

### D1. Headings on short text
- **Looks like:** a 300-word email or post split into titled sections.
- **Why:** headings organize long text; on short text they signal a template.
- **Fix:** remove the headings and join the sections with plain transitions.
- **Leave alone:** documentation, READMEs, and any format that requires
  headings.

### D2. Bullets instead of reasoning
- **Looks like:** an argument broken into fragments, each a noun phrase, with
  the connections between them missing.
- **Why:** the reasoning lived in the connections, and bullets remove them.
- **Fix:** rewrite the argument as sentences. Keep bullets for real lists of
  parallel items.
- **Leave alone:** steps, checklists, options, and inventories.

### D3. Bold labels and decoration
- **Looks like:** every bullet starting with a bolded two-word label and a
  colon, decorative emoji before headings or items.
- **Why:** it formats content that has no structure to show.
- **Fix:** remove the labels when the item is one sentence. Remove decorative
  emoji. Keep formatting that carries meaning.
- **Leave alone:** a glossary or definition list, where the label is the term.

## T: Stance and tone

### T1. Significance inflation
- **Looks like:** "a testament to," "a pivotal moment," "stands as a symbol
  of," "plays a vital role in shaping."
- **Why:** it assigns importance instead of showing the effect.
- **Fix:** say what happened and what it changed. Drop the importance claim if
  there is no effect to name.
- **Leave alone:** a quoted judgement attributed to a named source.

### T2. Promotional tone in neutral text
- **Looks like:** brochure wording in documentation, reports, or neutral
  descriptions: "boasts," "nestled," "world-class," "rich heritage."
- **Why:** the register does not match the purpose.
- **Fix:** describe the thing in neutral, checkable terms.
- **Leave alone:** marketing copy that the writer intends as marketing.

### T3. Unnamed authorities
- **Looks like:** "experts agree," "studies show," "many believe," "it is
  widely recognized."
- **Why:** the claim borrows authority it does not identify.
- **Fix:** name the source if the input names it. Otherwise make the claim in
  the writer's own voice, or cut it.
- **Leave alone:** a claim followed by a citation.

### T4. Assistant residue
- **Looks like:** "Great question," "I hope this helps," "Certainly! Here is,"
  "Feel free to reach out," "As an AI," knowledge-cutoff disclaimers.
- **Why:** these are artifacts of a chat reply pasted into a document.
- **Fix:** delete them.
- **Leave alone:** nothing. They never belong in the writer's text.

### T5. Empty empathy and flattery
- **Looks like:** "I understand how frustrating this must be," "You're
  absolutely right," "What a great idea."
- **Why:** it performs a feeling instead of addressing the reader's situation.
- **Fix:** delete it, or replace it with the concrete acknowledgement the
  situation needs.
- **Leave alone:** genuine condolence or apology the writer means.
