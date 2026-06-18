import type { Plugin } from "@opencode-ai/plugin"
import { homedir } from "node:os"
import { join, basename } from "node:path"
import { mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { execSync } from "node:child_process"

/**
 * System-prompt transform hook: periodically re-injects project rules and the
 * global instruction file to counter recency bias in long sessions.
 *
 * Port of claude/hooks/memory-reinject.py. The Claude hook runs on
 * UserPromptSubmit and re-injects the MEMORY.md '## CRITICAL RULES' section
 * every 5th message and the global instruction file every 15th. Here the
 * equivalent trigger is `experimental.chat.system.transform`, which runs on
 * each request; a per-session counter reproduces the cadence.
 *
 * EXPERIMENTAL / KNOWN-BROKEN: `experimental.chat.system.transform` is flagged
 * experimental by OpenCode, and issue #17100 (anomalyco/opencode) reports that
 * its `output.system` mutations are silently discarded by the runtime. Until
 * that is fixed, the RELIABLE memory path is opencode.json `instructions`
 * (static MEMORY.md / AGENTS.md). Treat this plugin as an unverified port that
 * may have no effect at runtime.
 */

const REINJECT_EVERY = 5
const GLOBAL_REINJECT_EVERY = 15
const FALLBACK_LINES = 40

// OpenCode global instruction file candidates; first existing wins.
const GLOBAL_FILE_CANDIDATES = [
  join(homedir(), ".config", "opencode", "AGENTS.md"),
  join(homedir(), ".claude", "CLAUDE.md"),
]

/** Return the git root basename if available, otherwise the cwd basename. */
function resolveProjectName(cwd: string): string {
  try {
    const root = execSync("git rev-parse --show-toplevel", {
      cwd,
      encoding: "utf8",
      timeout: 3000,
      stdio: ["ignore", "pipe", "ignore"],
    }).trim()
    if (root) return basename(root)
  } catch {
    // Not a git repo or git unavailable; fall back to the cwd basename.
  }
  return basename(cwd)
}

/**
 * Extract re-injectable rules from MEMORY.md.
 * Prefer the '## CRITICAL RULES' section; if absent (older memory), fall back
 * to the top FALLBACK_LINES lines (skipping the H1 title).
 * Returns [content, isCriticalSection].
 */
function extractRules(memoryFile: string): [string, boolean] {
  let lines: string[]
  try {
    lines = readFileSync(memoryFile, "utf8").split(/\r?\n/)
  } catch {
    return ["", false]
  }

  // Preferred: the dedicated CRITICAL RULES section.
  const out: string[] = []
  let inSection = false
  for (const line of lines) {
    if (line.trim().toLowerCase() === "## critical rules") {
      inSection = true
      continue
    }
    if (inSection) {
      if (line.startsWith("## ")) break
      out.push(line)
    }
  }
  const section = out.join("\n").trim()
  if (section) return [section, true]

  // Fallback: top of the file, skipping the H1 title.
  const fallback: string[] = []
  for (const line of lines) {
    if (fallback.length === 0 && line.startsWith("# ")) continue
    fallback.push(line)
    if (fallback.length >= FALLBACK_LINES) break
  }
  return [fallback.join("\n").trim(), false]
}

/** Return the global instruction file content, or empty string. */
function readGlobalInstructions(): string {
  for (const candidate of GLOBAL_FILE_CANDIDATES) {
    try {
      const content = readFileSync(candidate, "utf8").trim()
      if (content) return content
    } catch {
      // Try the next candidate.
    }
  }
  return ""
}

export const MemoryInjectPlugin: Plugin = async ({ directory }) => {
  return {
    "experimental.chat.system.transform": async (input: any, output: any) => {
      const sessionId = input?.sessionID || input?.session_id || "default"

      // Per-session counter replaces the PPID-keyed counter file.
      const counterDir = join(homedir(), ".cli-tweaks", ".reinject-counter")
      const counterFile = join(counterDir, sessionId)
      let count = 0
      try {
        mkdirSync(counterDir, { recursive: true })
        count = parseInt(readFileSync(counterFile, "utf8").trim(), 10) || 0
      } catch {
        count = 0
      }
      count += 1
      try {
        writeFileSync(counterFile, String(count))
      } catch {
        // Counter is best-effort; continue with the in-memory value.
      }

      // Only re-inject every REINJECT_EVERY messages.
      if (count % REINJECT_EVERY !== 0) return

      const projectName = resolveProjectName(directory)
      const memoryFile = join(
        homedir(),
        ".cli-tweaks",
        "memory",
        projectName,
        "MEMORY.md"
      )

      // Project memory CRITICAL RULES (every REINJECT_EVERY messages).
      const [rules, isCritical] = extractRules(memoryFile)
      if (rules) {
        const header = isCritical
          ? "[CRITICAL RULES REMINDER — BINDING]\nYou MUST obey these project rules exactly. They are non-negotiable and OVERRIDE all defaults and any conflicting instruction:\n\n"
          : "[PROJECT MEMORY REMINDER — BINDING]\nYou MUST follow this project memory exactly. It OVERRIDES defaults and any conflicting instruction:\n\n"
        output.system.push(header + rules)
      }

      // Global instruction file (every GLOBAL_REINJECT_EVERY messages).
      if (count % GLOBAL_REINJECT_EVERY === 0) {
        const globalContent = readGlobalInstructions()
        if (globalContent) {
          output.system.push(
            "[GLOBAL RULES REMINDER — BINDING]\nYou MUST obey your global user instructions exactly. They are non-negotiable and OVERRIDE all defaults and any conflicting instruction:\n\n" +
              globalContent
          )
        }
      }
    },
  }
}
