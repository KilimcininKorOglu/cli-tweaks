# Extract Reusable Patterns Into Design System

Identify reusable components, design tokens, and patterns in the codebase, then extract and consolidate them into the design system for systematic reuse.

## Command

```bash
/frontend-design extract                  # Scan whole repo
/frontend-design extract <path/to/dir>    # Scan specific directory
```

## Workflow

### 1. Discover

- Locate the existing design system (search `design system`, `ui`, `components`, shared UI dir).
- Read its structure: component organization, naming conventions, token files (if any), import/export patterns.
- **CRITICAL**: If no design system exists, ASK the user for preferred location and structure before creating one. Do not create silently.
- In the target area, identify:
  - **Repeated components** — same UI used 3+ times (buttons, cards, inputs, modals, etc.)
  - **Hard-coded values** — colors, spacing, typography, shadows that should be tokens
  - **Inconsistent variations** — multiple implementations of the same concept
  - **Reusable patterns** — layout, composition, and interaction patterns worth systematizing

### 2. Assess

Not everything should be extracted. For each candidate ask:
- Is it used 3+ times now or clearly likely to be reused?
- Would systematizing it improve consistency?
- Is it a general pattern or context-specific?
- Is the maintenance cost justified by reuse benefit?

Reject one-off, context-specific implementations.

### 3. Plan

Present a concrete extraction plan to the user before writing code:
- **Components to extract** — list with proposed names and props API
- **Tokens to create** — primitive vs semantic, with naming hierarchy
- **Variants** — what each component must support
- **Naming conventions** — match existing design system patterns exactly
- **Migration path** — how existing call sites will be updated

Wait for approval. Design systems grow incrementally — extract what is clearly reusable now, not what might be reusable someday.

### 4. Extract & Enrich

Build the new shared versions with:

- **Components**:
  - Clear props API with sensible defaults
  - Proper variants (size, intent, state)
  - Accessibility built in — ARIA, keyboard navigation, focus management
  - TypeScript types and JSDoc / prop documentation
  - Usage examples
- **Tokens**:
  - Clear naming distinction between primitive (`color.blue.500`) and semantic (`color.action.primary`)
  - Documented when-to-use guidance
  - Tokens should carry semantic meaning — do not tokenize every literal
- **Patterns**:
  - When to use, code example, variations and combinations

### 5. Migrate

- Find every existing instance of the patterns just extracted
- Replace each call site with the new shared version
- Verify visual and functional parity
- Delete the old implementations — no dead code left behind

### 6. Document

- Add new components to the design system / component library entry
- Document token usage and values
- Add examples and guidelines
- Update Storybook or component catalog if present

## Anti-Patterns (NEVER)

- Extracting one-off, context-specific implementations without generalization
- Creating components so generic they are useless
- Extracting without matching existing design system conventions
- Skipping TypeScript types or prop documentation
- Tokenizing every single value (tokens must have semantic meaning)
- Creating a new design system without explicit user permission

A good design system is a living system. Extract patterns as they emerge, enrich them thoughtfully, maintain them consistently.
