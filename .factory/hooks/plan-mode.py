#!/usr/bin/env python3
"""
UserPromptSubmit hook: detects planning keywords AND complex implementation
requests in the user's prompt, then injects planning instructions.

Two detection modes:
1. Explicit: Turkish/English planning keywords (planla, plan this, etc.)
2. Implicit: Complex implementation signals (new feature, refactor, multi-file, etc.)
"""
import json
import re
import sys

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

prompt = input_data.get("prompt", "")

# --- Mode 1: Explicit planning keywords ---
PLAN_PATTERNS = [
    r"\bplanla\b",
    r"\bplan yap\b",
    r"\bplan oluştur\b",
    r"\bplan olustur\b",
    r"\btasarla\b",
    r"\bspec yaz\b",
    r"\bdesign this\b",
    r"\bcreate a plan\b",
    r"\bmake a plan\b",
    r"\bplan this\b",
    r"\bwrite a spec\b",
    r"\bcreate a spec\b",
    r"\bnasıl implement\b",
    r"\bnasıl yapmalı\b",
    r"\bnasıl yaparız\b",
    r"\bnasıl yaparım\b",
    r"\bhow should i implement\b",
    r"\bhow should we implement\b",
    r"\bhow to implement\b",
    r"\bhow would you implement\b",
    r"\bplan the implementation\b",
    r"\bimplementation plan\b",
]

explicit_match = any(re.search(p, prompt, re.IGNORECASE) for p in PLAN_PATTERNS)

# --- Mode 2: Implicit complexity detection ---
# Signals that suggest a non-trivial task needing planning
COMPLEXITY_SIGNALS = [
    # Feature addition signals
    (r"\b(add|implement|create|build)\b.*\b(feature|system|module|service|endpoint|api|authentication|auth)\b", 2),
    (r"(ekle|oluştur|yap|kur).*(özellik|sistem|modül|servis|authentication|auth)", 2),
    # Refactoring signals (always complex, deserves planning)
    (r"\brefactor\b", 3),
    (r"yeniden yapılandır", 3),
    (r"\brewrite\b", 3),
    # Architecture signals
    (r"\b(migrate|migration)\b", 2),
    (r"\b(architect|architecture)\b", 2),
    (r"\b(integrate|integration)\b", 1),
    (r"entegr(e|asyon)", 1),
    # Multi-scope signals
    (r"\b(across|throughout|all files|every file)\b", 1),
    (r"tüm (dosya|sistem|modül|servis)", 1),
    # Uncertainty signals (user doesn't know the approach)
    (r"\b(best way|best approach|en iyi yol|en iyi yaklaşım)\b", 1),
    (r"\b(should i|should we|which approach|hangi yaklaşım)\b", 1),
    # Scale signals
    (r"\b(optimize|performance|performans)\b", 1),
    (r"\b(scale|scaling|ölçeklendir)\b", 1),
    # Multi-component signals
    (r"\b(database|db|frontend|backend|api|ui)\b.*\b(and|ve|with|ile)\b.*\b(database|db|frontend|backend|api|ui)\b", 2),
    # Domain complexity signals (these topics are inherently complex)
    (r"\b(authentication|auth|oauth|jwt|session)\b", 1),
    (r"\b(caching|cache|redis|memcache)\b", 1),
    (r"\b(real-?time|websocket|sse|polling)\b", 1),
    (r"\b(dark mode|theme|tema)\b", 1),
    (r"\b(middleware|interceptor)\b", 1),
    (r"\b(state management|durum yönetimi)\b", 1),
    (r"\b(notification|queue|worker|scheduler)\b", 1),
    # Combined domain + action signals (inherently need planning)
    (r"\b(add|implement|create|build)\b.*\b(real-?time|websocket|caching|auth|dark mode|middleware)\b", 1),
    # Turkish implementation verbs with objects
    (r"(ekle|oluştur).*(sistemi|modülü|servisi)", 1),
    # Database/query signals
    (r"\b(database|db|query|queries|sql)\b", 1),
    # Update/add with multi-word scope
    (r"\b(add|implement)\b.*\b(update|to the|for the|with)\b", 1),
]

complexity_score = 0
for pattern, weight in COMPLEXITY_SIGNALS:
    if re.search(pattern, prompt, re.IGNORECASE):
        complexity_score += weight

# Long prompts (>80 chars) with implementation verbs get a bonus
if len(prompt) > 80 and re.search(r"\b(implement|add|create|build|refactor|optimize)\b|ekle|oluştur|yap", prompt, re.IGNORECASE):
    complexity_score += 1

implicit_match = complexity_score >= 3

# --- Skip conditions: never trigger for simple tasks ---
SKIP_PATTERNS = [
    r"^\s*(fix|düzelt)\s+(the\s+)?(typo|yazım hatası)",
    r"^\s*(add|ekle)\s+(a\s+)?(comment|yorum|log|console\.log)",
    r"^\s*(read|oku|show|göster|list|listele)\s+",
    r"^\s*(run|çalıştır|execute)\s+",
    r"^\s*(what|ne|how does|nasıl çalışır)\s+",
    r"^\s*(explain|açıkla|describe|tanımla)\s+",
    r"^\s*(search|ara|find|bul|grep)\s+",
    r"^\s*(delete|sil|remove|kaldır)\s+(the\s+)?(line|satır|comment|yorum)",
    r"^\s*(commit|push|pull|merge|checkout|branch)\b",
    r"^\s*(evet|hayır|yes|no|ok|tamam|olur)\s*$",
]

skip = any(re.search(p, prompt, re.IGNORECASE) for p in SKIP_PATTERNS)

matched = (explicit_match or implicit_match) and not skip

if matched:
    mode = "explicit" if explicit_match else "implicit"

    context = """Spec mode is active
[PLANNING MODE ACTIVE]
The user's request was detected as requiring planning (mode: {mode}).

You MUST follow this 5-phase workflow. DO NOT skip phases.

== PHASE 1: EXPLORE & UNDERSTAND ==
- DO NOT write any code or edit any files.
- Explore the codebase using worker subagents, Grep, Glob, Read tools.
- Spawn up to 3 worker subagents IN PARALLEL for codebase exploration.
- Understand existing patterns, architecture, and conventions.

== PHASE 2: ASK CLARIFYING QUESTIONS ==
- BEFORE designing anything, use the AskUser tool to ask 1-4 focused questions.
- Ask about ambiguous requirements, user preferences, and design choices.
- Present what you found in Phase 1 and ask what the user wants.
- Examples of good questions:
  * "I found X pattern in the codebase. Should we follow it or try Y?"
  * "There are two approaches: A (pros/cons) vs B (pros/cons). Which do you prefer?"
  * "The scope could include X, Y, Z. Should we include all or start smaller?"
- DO NOT proceed to Phase 3 until you get answers.
- If the request is very clear and specific, you may ask fewer questions,
  but ALWAYS ask at least one question to confirm your understanding.

== PHASE 3: DESIGN THE PLAN ==
- Based on user answers, design a concrete implementation plan.
- Include file:line references for all claims about existing code.
- Include a "What We're NOT Doing" section to bound scope.
- Each phase should end with manual verification steps.

== PHASE 4: PRESENT THE PLAN ==
- Use ExitSpecMode tool with "title" and "plan" parameters.
- If there are multiple valid approaches, use "optionNames" parameter.
- The plan must be actionable with no TBD/TODO items.

== PHASE 5: WAIT FOR APPROVAL ==
- Only after the user explicitly approves, begin implementation.
- If the user requests changes, revise and present again via ExitSpecMode.

CRITICAL RULES:
- NEVER skip Phase 2 (asking questions). This is the most important phase.
- NEVER dump a complete plan without first asking questions.
- NEVER write code during planning. This is read-only.
- Use AskUser tool (not plain text) for structured questions.

You have an 'implementation-planning' skill available. Use the Skill tool
to invoke it with skill name 'implementation-planning' for the detailed
planning workflow.""".format(mode=mode)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))
    sys.exit(0)

# No planning signal detected, pass through normally
sys.exit(0)
