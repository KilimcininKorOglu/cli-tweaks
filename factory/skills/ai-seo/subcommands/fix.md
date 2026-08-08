# GEO Fix

Apply the fixes that a sweep found. This is the ONLY ai-seo mode that writes to
project files. Every other subcommand is read-only.

## Command

```bash
/ai-seo fix           # sweep the current project, then fix
/ai-seo fix <path>    # sweep that project path, then fix
/ai-seo fix <url>     # refused, see Step 1
```

## Step 1: Preconditions

1. Resolve the input mode with the SKILL.md **Input Modes: Web vs Local** table.
   `fix` requires **Local mode**.
   - With no argument, target `.`.
   - If the target is a URL or a bare domain, STOP before any edit. You fetched
     that site, you do not own its files, so there is nothing here to write to.
     Tell the user, then offer exactly two paths: re-run against the local
     project path, or run the read-only sweep and take copy-paste ready snippets
     (robots.txt block, llms.txt body, JSON-LD) without editing anything.
2. Inspect the working tree:
   ```bash
   git status --porcelain
   ```
   If changes exist that this run did not create, show them and ask whether to
   stash them, continue on top of them, or abort. Never overwrite uncommitted
   work. If the path is not a git repository, say so and warn that there is no
   rollback before continuing.
3. Confirm the path really holds a site. Look for the control files and
   templates listed under SKILL.md **Local project layout**. If nothing matches,
   STOP and tell the user this path has no site to fix.

## Step 2: Sweep first, always

Run the full **Sequential Full Sweep** from SKILL.md against the target: all
seven analyses, in the fixed order, before proposing anything.

The sweep output is the only accepted input to Step 3. Never fix from an earlier
report, a remembered score, or the user's description of the problem. The one
exception: a sweep you ran in this same session against this same target, with no
file changed since. Say out loud that you are reusing it.

## Step 3: Split every finding into two buckets

Each finding lands in exactly one bucket. Print both lists.

| Bucket | Meaning | Typical findings |
|--------|---------|------------------|
| **Fixable here** | The fix is an edit to a file in this repo | robots.txt AI crawler blocks, missing llms.txt, missing or broken JSON-LD, missing title/meta description/canonical, broken heading hierarchy, missing alt text, weak internal linking |
| **Out of repo** | The fix is real but lives somewhere else | brand mentions on third-party platforms, CDN or edge headers, DNS, CMS-hosted content, hosting-level SSR and Core Web Vitals, review-platform presence |

An out-of-repo finding stays OPEN. It keeps its category non-green, and it
appears in the final report with an owner and a next action. Never close a
finding because you cannot fix it from here, and never drop it from the
composite.

## Step 4: Propose, then wait

Present the fix plan before touching a file:

- Rank it by severity, using the same Critical / High / Medium / Low definitions
  as audit.md Phase 3 step 4.
- Give one line per fix: the file, what changes, which finding it closes, and the
  expected category movement.
- Put content edits in their own group, because they change what the site says
  rather than how it is marked up.

Ask for explicit confirmation with `AskUser`. Apply only the groups the
user approves. Approval is per group: never treat a yes to markup fixes as a yes
to rewriting copy. A fix the user declines is deferred, and deferred means still
open.

## Step 5: Apply

Work the approved groups in this order: crawlers, llms.txt, schema, technical,
content. Access comes first because a blocked crawler makes every later fix
invisible, and copy changes come last because they need the most review.

### robots.txt

- Edit the existing file in place. Preserve every rule you did not agree to
  change, and keep all `Sitemap:` lines.
- A `Disallow` aimed at a named AI crawler is often deliberate, for paywalled or
  licensed content. Ask before removing any of them. Never unblock a crawler
  silently.

### llms.txt

- Generate it with the rules in [llmstxt.md](llmstxt.md).
- List only URLs that exist in this project. Never invent a page to fill out the
  file.
- Write it to the directory that already serves robots.txt.

### Schema and JSON-LD

- Markup must describe what the page actually shows. Never add a rating, review,
  price, author, date, or credential that is not visible on the page. Fabricated
  markup earns a manual action, and it lies to the exact crawlers this skill
  exists to serve.
- Repair broken schema before adding new types. Confirm the JSON parses.
- Add a `sameAs` entry only for a profile you verified exists.

### Technical

- Edit templates and source files. Never edit `dist/`, `build/`, or any other
  generated output, because the next build erases the change.
- Treat an SSR or rendering-architecture change as out of scope for this step.
  Describe it and get a separate go-ahead instead of implementing it here.

### Content and E-E-A-T

- Never fabricate experience, credentials, author identity, citations, dates, or
  statistics. E-E-A-T is a claim about reality, so inventing it destroys the
  authority this skill is meant to build.
- Restructuring is allowed: split long passages, add headings, tighten answers,
  surface the direct answer first.
- Adding a fact, a source, or an author bio needs material the user supplies or
  the repo already contains.

## Step 6: Prove the fix

Re-run only the analyses whose findings you changed. Never re-score a category
from your own reading of the edit.

- Report before and after per category, then the recomputed composite.
- A finding closes only when the re-run stops reporting it. Your confidence in
  the edit does not close it.
- If the re-run still reports it, say so and leave it open.

**Verdict rule:** a category is green only when it has zero OPEN findings.
Judging a finding unfixable, out of repo, or deferred does not close it. It stays
open and keeps the category non-green. Count open findings, never "real" ones.

## Output Format

```markdown
# GEO Fix Report: [project path]

## Composite: [before]/100 → [after]/100 (Grade [X] → [Y])

| Category          | Before | After | Fixed | Still open |
|-------------------|--------|-------|-------|------------|
| AI Citability     | XX     | XX    | N     | N          |
| Brand Authority   | XX     | XX    | N     | N          |
| Content & E-E-A-T | XX     | XX    | N     | N          |
| Technical SEO     | XX     | XX    | N     | N          |
| Structured Data   | XX     | XX    | N     | N          |
| Platform Access   | XX     | XX    | N     | N          |

## Applied

| # | Severity | File | Change | Finding closed |
|---|----------|------|--------|----------------|

## Deferred (user declined)

| Finding | Severity | Why it was declined |
|---------|----------|---------------------|

## Out of repo (cannot be fixed here)

| Finding | Owner | Next action |
|---------|-------|-------------|

## Verification

[Which analyses were re-run, and what each one reports now]
```

## Rules

- Never edit a file in any mode except `fix`.
- Never edit generated output such as `dist/` or `build/`.
- Never fabricate content, credentials, citations, reviews, ratings, or dates,
  and never mark up something the page does not show.
- Never remove a `Disallow` aimed at a named AI crawler without asking first.
- Never close a finding you did not re-verify with a fresh run.
- Confirm every group of changes with the user before applying it.
- Keep out-of-repo and deferred findings visible in the report as OPEN.
- Reports are written in English. Explanations to the user follow the user's
  language.
