# Elicitation Guide

Interactive discovery process for understanding a project before generating documentation.
Use `AskUserQuestion` tool for structured choices; reserve freeform for open-ended questions.

## Core Strategy

1. **Extract before asking.** Scan everything the user already said. Don't re-ask answered questions.
2. **Tap, don't type.** Use `AskUserQuestion` for any question with 2-4 clear options.
3. **Batch related questions.** Group 1-3 related questions per interaction, never 5+.
4. **Adapt depth to ambition.** Weekend hack = 5-8 questions. Full product = 15-25 questions.
5. **Stop when you have enough.** Not every question needs answering. Move on when you can
   generate a useful specification.

## Question Tiers

**Tier 1 — Blockers** (always ask if unanswered):
Cannot generate SPECIFICATION.md without these.

**Tier 2 — Important** (ask for medium+ projects):
Significantly improve document quality.

**Tier 3 — Depth** (ask for large projects or engaged users):
Add thoroughness and prevent design mistakes.

---

## Discovery Flow

### Step 1: Project Identity (Tier 1 — always ask)

**Freeform:**
"Describe what you want to build in a few sentences — the problem it solves and who it's for."

**Then use `AskUserQuestion`:**

```
Question: "What type of project is this?"
Options: ["Web Application", "CLI Tool / Library", "API / Backend Service", "Mobile / Desktop App"]
```

```
Question: "What's the scope?"
Options: ["MVP / Proof of Concept", "Full Product v1.0", "Enterprise-grade System"]
```

### Step 2: Technical Direction (Tier 1)

**Use `AskUserQuestion`:**

```
Question: "Do you have a programming language preference?"
Options: ["Yes, I know what I want", "Help me choose", "No preference"]
```

If "Help me choose" → read `references/tech-stacks.md` and run the stack advisor flow.

If "Yes, I know what I want" → ask freeform: "What language and framework?"

```
Question: "Where will this run?"
Options: ["Cloud / SaaS", "Self-hosted / On-premise", "Local only (CLI/desktop)", "Hybrid"]
```

### Step 3: Data & Storage (Tier 1-2)

```
Question: "Does this project need a database?"
Options: ["Yes, relational (SQL)", "Yes, document (NoSQL)", "Yes, help me choose", "No / File-based only"]
```

If "help me choose" → present options based on project type using `AskUserQuestion`:
```
Question: "What best describes your data?"
Options: [
  "Structured with relationships (users→orders→items)",
  "Flexible/nested documents (profiles, configs, content)",
  "Time-series / event logs",
  "Key-value / cache-heavy"
]
```

Then recommend: structured → PostgreSQL/MySQL/SQLite, flexible → MongoDB/CobaltDB,
time-series → TimescaleDB/ClickHouse, key-value → Redis/DragonflyDB. Present 2-3
concrete options with trade-offs.

### Step 4: Features & Scope (Tier 1-2)

**Freeform:**
"What are the 3-5 core features? The ones without which the project doesn't make sense."

```
Question: "Does this need user authentication?"
Options: ["Yes, full auth (register/login/roles)", "API keys only", "No auth needed", "Undecided"]
```

If auth is needed:
```
Question: "Authentication approach?"
Options: ["Session-based (traditional)", "JWT tokens", "OAuth / SSO", "Help me choose"]
```

```
Question: "Does this need a user interface?"
Options: ["Web UI (browser)", "CLI / Terminal", "Desktop app", "No UI (API only)"]
```

If Web UI:
```
Question: "Frontend approach?"
Options: [
  "Full SPA (React/Vue/Svelte)",
  "Server-rendered (Next/Nuxt/SvelteKit)",
  "Embedded/minimal (Alpine/HTMX/vanilla)",
  "Help me choose"
]
```

### Step 5: Architecture Preferences (Tier 2)

```
Question: "How do you think about external dependencies?"
Options: [
  "Use whatever works best (ecosystem standard)",
  "Prefer fewer, well-chosen dependencies",
  "Minimal dependencies (stdlib-first)",
  "No preference"
]
```

```
Question: "Does this need real-time capabilities?"
Options: ["Yes (WebSocket/SSE/live updates)", "No", "Maybe later"]
```

```
Question: "API style preference?"
Options: ["REST", "GraphQL", "gRPC", "Multiple protocols", "Help me choose", "No API"]
```

### Step 6: Operations & Deployment (Tier 2)

```
Question: "How will users get this software?"
Options: [
  "Docker container",
  "Single binary / executable",
  "Package manager (npm/pip/go install)",
  "Cloud-hosted (I deploy it)",
  "Not decided yet"
]
```

```
Question: "Do you need CI/CD from day one?"
Options: ["Yes, full pipeline", "Basic (lint + test)", "Not yet", "Help me set it up"]
```

### Step 7: Scale & Performance (Tier 2-3)

```
Question: "Expected scale at launch?"
Options: [
  "Personal / small team (<100 users)",
  "Medium (100-10K users)",
  "Large (10K-100K users)",
  "Massive (100K+ users)",
  "Unknown / will figure out later"
]
```

### Step 8: Project Meta (Tier 2-3)

```
Question: "Will this be open source?"
Options: ["Yes, fully open", "Open-core (free + paid)", "Proprietary / closed", "Undecided"]
```

```
Question: "Team size?"
Options: ["Solo developer", "Small team (2-5)", "Larger team (5+)"]
```

**Freeform (only if user is engaged):**
"Any deadlines, specific constraints, or things this should explicitly NOT do?"

---

## Adaptive Questioning Matrix

| User Signal                  | Questions to Ask                                     | Depth   |
|------------------------------|------------------------------------------------------|---------|
| "I want to build X" (1 line) | Steps 1-5 fully, 6-8 selectively                     | High    |
| Detailed 3+ paragraph brief  | Gaps in Steps 1-3 only                               | Low     |
| "Help me with everything"    | All steps, all tiers                                 | Maximum |
| "Just need a quick spec"     | Step 1-2 only, sensible defaults                     | Minimal |
| `prd.md` / PRD found in CWD  | Apply "PRD → SPEC Mapping" below, ask only eng gaps  | Low     |
| Uploads existing SPEC        | Validate against spec checklist, ask only gaps       | Varies  |
| "You decide" on a question   | Choose the most common/safe option, state it clearly | N/A     |

---

## PRD → SPEC Mapping

When an existing PRD (Product Requirements Document) or similar input file is
detected in CWD (see SKILL.md Phase 0 Step 0), extract answers from it instead of
running the full question flow. PRDs are typically business/product-focused and
need translation into a technical SPECIFICATION.md.

### Section Mapping

| Typical PRD Section                       | Maps to SPEC Section                             |
|-------------------------------------------|--------------------------------------------------|
| "Vision", "Overview", "Problem Statement" | §1.1 What Is, §1.2 Target Audience               |
| "User Personas", "Target Users"           | §1.2 Target Audience                             |
| "Goals", "Success Metrics", "KPIs"        | §1.3 Key Differentiators, §10 Performance        |
| "Features", "User Stories"                | §3 Functional Requirements                       |
| "Use Cases", "User Flows"                 | §3 Functional Requirements (acceptance criteria) |
| "Competitors", "Market Analysis"          | §1.4 Competitive Landscape                       |
| "Glossary", "Terminology"                 | §2 Core Concepts                                 |
| "Out of Scope", "Non-Goals"               | §11.2 Non-Goals                                  |
| "Assumptions", "Risks"                    | §11.3 Assumptions                                |
| "Open Questions", "TBD"                   | §11.4 Open Questions                             |
| "Roadmap", "Future"                       | §12 Future Considerations                        |

### Typical PRD Gaps (Almost Always Need Follow-Up)

PRDs are rarely written with engineering in mind. Expect to ask the user about:

1. **Data model details** — PRD says "users have profiles", SPEC needs field-level
   entities with types and constraints (§5)
2. **API contract shape** — PRD says "REST API for mobile", SPEC needs endpoint list,
   auth model, error format (§6)
3. **Tech stack constraints** — PRD rarely specifies language / framework / database
4. **Non-functional requirements** — latency targets, throughput, resource limits (§10)
5. **Deployment model** — where it runs, how it's distributed, environments (§9)
6. **Security specifics** — auth method, permission model, data protection (§8)

### Extraction Flow

1. **Read** the PRD file fully using the `Read` tool.
2. **Map** each PRD section to SPEC sections using the table above. Draft SPEC
   content directly from the PRD where possible.
3. **Identify gaps** using the list above. These become the only questions you
   ask the user via `AskUserQuestion` — narrow, targeted, 2-6 questions total.
4. **Present a summary** before generating any document:
   > "I read your `prd.md` and extracted: [decisions]. I still need: [gaps].
   > Quick questions: [`AskUserQuestion` items]."
5. **Generate SPECIFICATION.md** with a `Source:` line in the header citing the
   PRD file and the date.

### Handling Conflicts and Ambiguity

- If the PRD contradicts itself, **flag the contradiction explicitly** instead of
  silently picking one interpretation.
- Mark unresolved items with `[TBD: question]` in the generated SPEC — never
  invent details the PRD does not contain.
- If a requirement is vague ("fast", "scalable"), ask a targeted follow-up to
  quantify it before writing SPEC §10.

---

## After Discovery

Once you have sufficient answers, summarize the decisions before generating:

"Here's what I understand about your project:
- **Project**: [name/description]
- **Type**: [web app / CLI / etc.]
- **Stack**: [language + framework + database]
- **Key Features**: [bulleted list]
- **Deployment**: [how/where]
- **Scope**: [MVP / full]

Does this look right? I'll start with the SPECIFICATION.md."

Wait for confirmation before generating any document.
