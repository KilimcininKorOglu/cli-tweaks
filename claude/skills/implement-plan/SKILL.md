---
name: implement-plan
description: >
  This skill MUST be invoked when the user says "plan this", "planla",
  "tasarla", "design this", "implementation plan", "nasıl implement ederiz"
  or any variation requesting implementation planning. SHOULD also invoke
  when user asks "how should I implement X", "en iyi yaklaşım ne", or
  wants a technical specification. Creates detailed implementation plans
  through interactive research and iteration, breaking down tasks into
  phases with mandatory user questions via AskUserQuestion.
---

# Implementation Planning

Create detailed implementation plans through an interactive, iterative process. Be skeptical, thorough, and collaborative.

## Quick Start

Given a task or ticket:

1. Read all referenced documents and files FULLY
2. Research by spawning `worker` subagents in parallel for codebase exploration
3. Present understanding with `file:line` references, ask only unanswerable questions
4. Verify any user corrections against code before accepting
5. Outline the phase structure, get approval
6. Detail each phase, then present with ExitPlanMode

## When to Plan (Use This Skill)

Prefer planning for implementation tasks unless they're simple. Use when ANY of these apply:

1. **New Feature Implementation**: Adding meaningful new functionality
   - "Add a logout button" -- where should it go? What happens on click?
   - "Add form validation" -- what rules? What error messages?
2. **Multiple Valid Approaches**: The task can be solved in several different ways
   - "Add caching to the API" -- Redis, in-memory, file-based?
   - "Improve performance" -- many optimization strategies possible
3. **Code Modifications**: Changes that affect existing behavior or structure
   - "Update the login flow" -- what exactly should change?
   - "Refactor this component" -- what's the target architecture?
4. **Architectural Decisions**: Choosing between patterns or technologies
   - "Add real-time updates" -- WebSockets vs SSE vs polling
   - "Implement state management" -- which approach?
5. **Multi-File Changes**: The task will likely touch more than 2-3 files
6. **Unclear Requirements**: You need to explore before understanding the full scope
7. **User Preferences Matter**: The implementation could reasonably go multiple ways

Also applies when:
- The hook injected "Spec mode is active" or "PLANNING MODE ACTIVE" into context
- User explicitly asks for a plan (Turkish: "planla", "tasarla", "plan yap")
- User asks "how should I implement X", "plan this feature", "write a spec"
- User references a ticket/task to plan

**Rule of thumb**: If unsure whether to plan, err on the side of planning. It's better to get alignment upfront than to redo work.

## When NOT to Plan (Skip This Skill)

Only skip planning for simple tasks:
- Single-line or few-line fixes (typos, obvious bugs, small tweaks)
- Adding a single function with clear, specific requirements
- Tasks where the user has given very detailed, step-by-step instructions
- Pure research/exploration tasks (use Explore subagent instead)

## Core Principles

1. **Interactive**: Never dump a complete plan. Gather context -> verify understanding -> align on approach -> detail phases.
2. **Grounded**: Every claim verified against actual code. Include `file:line` references.
3. **Bounded**: Every plan MUST include "What We're NOT Doing" section.
4. **TDD-First**: Plans describe what to build, not how to test. Automated testing is implicit. Never include explicit "testing phases" or "write tests" steps.
5. **Manual Verification**: Each phase ends with manual verification to ensure we're on track. This is separate from TDD.

## Process

### Step 1: Context Gathering (Explore)

1. Read all mentioned files FULLY (tickets, research, existing plans)
   - NEVER read files partially
2. Spawn research subagents in parallel using the Task tool:
   - `Explore` subagent -> Find all relevant files and understand current implementation
   - Use Grep/Glob tools directly for quick searches
   - Launch up to 3 Explore agents IN PARALLEL for faster exploration
3. Build an informed understanding of the codebase before asking anything.

### Step 2: Ask Clarifying Questions (MOST IMPORTANT STEP)

THIS IS THE MOST CRITICAL STEP. Never skip it.

Before designing any plan, you MUST use the AskUserQuestion tool to ask 1-4 focused questions. The goal is to understand what the user actually wants before committing to an approach.

What to ask about:
- Ambiguous requirements ("Should X include Y or just Z?")
- Design choices ("I found pattern A in the codebase. Should we follow it or try B?")
- Scope boundaries ("This could include X, Y, Z. Should we do all or start smaller?")
- Technology preferences ("Two options: A (fast but complex) vs B (simple but limited). Which?")
- Priority trade-offs ("Should we optimize for speed or maintainability?")

How to ask:
- Use the AskUserQuestion tool with structured multiple-choice questions
- Present what you found in Step 1 as context within the question
- Keep options short and mutually exclusive
- 2-4 options per question, 1-4 questions total

Example AskUserQuestion usage:
```
1. [question] I found the API uses REST handlers at server.go:45. For the new endpoint, should we follow the existing pattern or introduce a router?
[topic] Architecture
[option] Follow existing pattern (add handler to server.go)
[option] Introduce a lightweight router (e.g., gorilla/mux)

2. [question] The scope could include validation, error handling, and logging. What's the priority?
[topic] Scope
[option] Full scope (all three)
[option] Core only (validation + error handling)
[option] Minimal (just the happy path first)
```

Rules:
- ALWAYS ask at least one question, even if the request seems clear
- If the request is very specific, confirm your understanding with a verification question
- DO NOT proceed to Step 3 until you get answers
- DO NOT ask questions in plain text -- always use AskUserQuestion tool
- If user corrections conflict with what you found in code, present the discrepancy as a question

### Step 3: Design the Plan

After getting user answers:

1. If user corrects you, spawn new research tasks to verify. Don't just accept.
2. Track progress with TodoWrite.
3. Design a concrete plan based on user's chosen direction.

### Step 4: Present the Plan

Build the complete plan following the template below and present it using ExitPlanMode tool with:
- `title`: A descriptive plan title
- `plan`: The full plan in markdown format

## Plan Template

Use this structure for the final plan:

```markdown
## Overview
[1-2 sentence summary of what we're building and why]

## Current State
- [Key finding with file:line reference]
- [Existing pattern we'll follow]

## What We're NOT Doing
- [Explicitly excluded scope item]
- [Deferred feature]

## Phase 1: [Name]
Goal: [What this phase accomplishes]

Files to modify:
- `path/to/file.ext` - [what changes]

Steps:
1. [Concrete step with file reference]
2. [Next step]

Manual verification:
- [How to verify this phase works]

## Phase 2: [Name]
[Same structure as Phase 1]

## Risks and Trade-offs
- [Risk]: [Mitigation]
- [Trade-off]: [Justification]
```

## Guidelines

### Do
- Read files FULLY before planning
- Include file:line references for all claims
- Use Explore subagents for research (they work in read-only mode)
- Verify claims against code
- Get buy-in at each step
- Assume TDD for automated tests -- don't add explicit "write tests" steps
- Include manual verification checkpoints at phase boundaries
- Use ExitPlanMode with optionNames when presenting multiple approaches

### Don't
- Write complete plans before alignment
- Accept corrections without verification
- Leave open questions in final plan
- Assume -- verify with code
- Write any code or edit any files during planning
- Skip the "What We're NOT Doing" section

### No Open Questions Rule

If you encounter open questions during planning:
1. STOP
2. Research or ask for clarification immediately (use AskUserQuestion tool)
3. Do NOT present a plan with unresolved questions
4. Every decision must be made before finalizing

### Handling Edge Cases

- **No existing patterns found**: Document this explicitly; propose a new pattern with justification
- **Conflicting information**: Escalate to user with specific details about what conflicts (include file:line references)
- **User corrections conflict with code**: Present the discrepancy -- don't silently accept either version
- **Subagent failures or empty results**: Retry with different query terms; fall back to manual Grep/Glob; note the gap and ask user
- **Scope ambiguity**: Default to smaller scope; explicitly list what's deferred in "What We're NOT Doing"

## Common Patterns

### Database Changes
1. Schema/migration
2. Store methods
3. Business logic
4. API endpoints
5. Client updates

### New Features
1. Research existing patterns
2. Data model
3. Backend logic
4. API layer
5. UI last

### Refactoring
1. Document current behavior
2. Incremental changes
3. Backwards compatibility
4. Migration strategy

## Common Mistakes

| Mistake                              | Why It's Wrong                        | Do This Instead                                    |
|--------------------------------------|---------------------------------------|----------------------------------------------------|
| Dumping a complete plan immediately  | User can't course-correct early       | Present understanding first, get buy-in at each step |
| Skipping clarifying questions        | You'll plan the wrong thing           | ALWAYS use AskUserQuestion before designing the plan       |
| Asking questions in plain text       | User gets unstructured wall of text   | Use AskUserQuestion tool for structured multiple-choice    |
| Accepting user corrections blindly   | User may be wrong or outdated         | Verify corrections against code before proceeding  |
| Leaving "TBD" or "TODO" in plan      | Plan should be actionable             | Resolve all questions before finalizing            |
| Missing file:line references         | Claims become unverifiable            | Every code reference needs a location              |
| Skipping "What We're NOT Doing"      | Scope creep inevitable                | Always define boundaries explicitly                |
| Adding explicit "testing" phases     | TDD is implicit in all implementation | Describe what to build; tests come with it         |
| Writing code during planning         | Plan mode is read-only                | Only research and plan; code comes after approval  |
