#!/usr/bin/env python3
"""
Claude Code UserPromptSubmit hook: detects planning keywords AND complex
implementation requests, then injects planning instructions.

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
    # Turkish - explicit planning verbs (base forms)
    r"\bplanla\b",
    r"\bplanlayalım\b",
    r"\bplanlama yap\b",
    r"\bplan yap\b",
    r"\bplan oluştur\b",
    r"\bplan olustur\b",
    r"\bplan çıkar\b",
    r"\bplan cikar\b",
    r"\bplan hazırla\b",
    r"\bplan hazirla\b",
    r"\bplanla bunu\b",
    r"\bbunu planla\b",
    r"\btasarla\b",
    r"\btasarım yap\b",
    r"\btasarim yap\b",
    r"\bspec yaz\b",
    # Turkish - verb conjugations (imperative, question forms)
    r"\bplanlasana\b",
    r"\bplanlar mısın\b",
    r"\bplanlar misin\b",
    r"\bplanlarmısın\b",
    r"\bplanlarmisin\b",
    r"\bplanlar mıyız\b",
    r"\bplanlar miyiz\b",
    r"\bplanlarmıyız\b",
    r"\bplanlarmiyiz\b",
    r"\bplanlayabilir misin\b",
    r"\bplanlayabilirmisin\b",
    r"\bplanlayabilir misiniz\b",
    r"\bplanlayabilirmisiniz\b",
    r"\bplanlasak\b",
    r"\bplanlasak mı\b",
    r"\bplanlasakmı\b",
    r"\bplanlayalım mı\b",
    r"\bplanlayalımmı\b",
    r"\bplanlayalim mi\b",
    r"\bplanlayalimmi\b",
    r"\bplanla şunu\b",
    r"\bplanla sunu\b",
    r"\bşunu planla\b",
    r"\bsunu planla\b",
    # Turkish - tasarla conjugations
    r"\btasarlasana\b",
    r"\btasarlar mısın\b",
    r"\btasarlar misin\b",
    r"\btasarlayabilir misin\b",
    r"\btasarlayabilirmisin\b",
    r"\btasarlasak\b",
    r"\btasarlayalım mı\b",
    # Turkish - "how should we" variants
    r"\bnasıl implement\b",
    r"\bnasıl yapmalı\b",
    r"\bnasıl yaparız\b",
    r"\bnasıl yaparım\b",
    r"\bnasıl yaklaşalım\b",
    r"\bnasıl yaklaşmalı\b",
    r"\bnasıl ilerlemeliyiz\b",
    # English - explicit planning verbs (base forms)
    r"\bplan this\b",
    r"\bplan out\b",
    r"\blet'?s plan\b",
    r"\bcreate a plan\b",
    r"\bmake a plan\b",
    r"\bdraft a plan\b",
    r"\bmap out\b",
    r"\bdesign this\b",
    r"\bwrite a spec\b",
    r"\bcreate a spec\b",
    # English - question/request forms
    r"\bcan you plan\b",
    r"\bcould you plan\b",
    r"\bwould you plan\b",
    r"\bplan it out\b",
    r"\bplan it for me\b",
    r"\bhelp me plan\b",
    r"\bhelp plan\b",
    r"\bplan for\b",
    r"\bplan ahead\b",
    # English - design variants
    r"\bdesign it\b",
    r"\bdesign for me\b",
    r"\bcan you design\b",
    r"\bcould you design\b",
    r"\bhelp me design\b",
    # English - spec variants
    r"\bspec this out\b",
    r"\bspec it out\b",
    r"\bspec this\b",
    r"\bcan you spec\b",
    r"\bcould you spec\b",
    # English - "how to" variants
    r"\bhow should i implement\b",
    r"\bhow should we implement\b",
    r"\bhow to implement\b",
    r"\bhow would you implement\b",
    r"\bhow to approach\b",
    r"\bhow should we approach\b",
    # English - decomposition
    r"\bbreak (this|it) down\b",
    r"\bplan the implementation\b",
    r"\bimplementation plan\b",
]

explicit_match = any(re.search(p, prompt, re.IGNORECASE) for p in PLAN_PATTERNS)

# --- Mode 2: Implicit complexity detection ---
COMPLEXITY_SIGNALS = [
    (r"\b(add|implement|create|build)\b.*\b(feature|system|module|service|endpoint|api|authentication|auth)\b", 2),
    (r"(ekle|oluştur|yap|kur).*(özellik|sistem|modül|servis|authentication|auth)", 2),
    (r"\brefactor\b", 3),
    (r"yeniden yapılandır", 3),
    (r"\brewrite\b", 3),
    (r"\b(migrate|migration)\b", 2),
    (r"\b(architect|architecture)\b", 2),
    (r"\b(integrate|integration)\b", 1),
    (r"entegr(e|asyon)", 1),
    (r"\b(across|throughout|all files|every file)\b", 1),
    (r"tüm (dosya|sistem|modül|servis)", 1),
    (r"\b(best way|best approach|en iyi yol|en iyi yaklaşım)\b", 1),
    (r"\b(should i|should we|which approach|hangi yaklaşım)\b", 1),
    (r"\b(optimize|performance|performans)\b", 1),
    (r"\b(scale|scaling|ölçeklendir)\b", 1),
    (r"\b(database|db|frontend|backend|api|ui)\b.*\b(and|ve|with|ile)\b.*\b(database|db|frontend|backend|api|ui)\b", 2),
    (r"\b(authentication|auth|oauth|jwt|session)\b", 1),
    (r"\b(caching|cache|redis|memcache)\b", 1),
    (r"\b(real-?time|websocket|sse|polling)\b", 1),
    (r"\b(dark mode|theme|tema)\b", 1),
    (r"\b(middleware|interceptor)\b", 1),
    (r"\b(state management|durum yönetimi)\b", 1),
    (r"\b(notification|queue|worker|scheduler)\b", 1),
    (r"\b(add|implement|create|build)\b.*\b(real-?time|websocket|caching|auth|dark mode|middleware)\b", 1),
    (r"(ekle|oluştur).*(sistemi|modülü|servisi)", 1),
    (r"\b(database|db|query|queries|sql)\b", 1),
    (r"\b(add|implement)\b.*\b(update|to the|for the|with)\b", 1),
]

complexity_score = 0
for pattern, weight in COMPLEXITY_SIGNALS:
    if re.search(pattern, prompt, re.IGNORECASE):
        complexity_score += weight

if len(prompt) > 80 and re.search(r"\b(implement|add|create|build|refactor|optimize)\b|ekle|oluştur|yap", prompt, re.IGNORECASE):
    complexity_score += 1

implicit_match = complexity_score >= 3

# --- Skip conditions ---
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

    context = """[PLANNING MODE ACTIVE]
The user's request was detected as requiring planning (mode: {mode}).

You MUST call EnterPlanMode first, then follow this 5-phase workflow.

== PHASE 1: EXPLORE & UNDERSTAND ==
- DO NOT write any code or edit any files.
- Spawn up to 3 Explore sub-agents IN PARALLEL via Task tool.
- Use Grep, Glob, Read tools to understand patterns and architecture.

== PHASE 2: ASK CLARIFYING QUESTIONS ==
- BEFORE designing anything, use AskUserQuestion to ask 1-4 focused questions.
- Ask about ambiguous requirements, user preferences, and design choices.
- Present what you found in Phase 1 and ask what the user wants.
- Examples of good questions:
  * "I found X pattern in the codebase. Should we follow it or try Y?"
  * "There are two approaches: A (pros/cons) vs B (pros/cons). Which?"
  * "The scope could include X, Y, Z. Should we include all or start smaller?"
- DO NOT proceed to Phase 3 until you get answers.
- ALWAYS ask at least one question to confirm your understanding.

== PHASE 3: DESIGN THE PLAN ==
- Based on user answers, design a concrete implementation plan.
- Optionally spawn Plan sub-agents via Task tool for complex designs.
- Include file:line references for all claims about existing code.
- Include a "What We're NOT Doing" section to bound scope.
- Write the plan to the plan file.

== PHASE 4: PRESENT THE PLAN ==
- Use ExitPlanMode to present the completed plan.
- The plan must be actionable with no TBD/TODO items.

== PHASE 5: WAIT FOR APPROVAL ==
- Only after the user explicitly approves, begin implementation.
- If the user requests changes, re-enter plan mode and revise.

CRITICAL RULES:
- NEVER skip Phase 2 (asking questions). This is the most important phase.
- NEVER dump a complete plan without first asking questions.
- NEVER write code during planning. This is read-only.
- Use AskUserQuestion (not plain text) for structured questions.""".format(mode=mode)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))
    sys.exit(0)

sys.exit(0)
