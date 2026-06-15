import type { Plugin } from "@opencode-ai/plugin"
import { homedir } from "node:os"
import { join, basename } from "node:path"
import { existsSync, mkdirSync, writeFileSync, rmSync } from "node:fs"
import { execSync } from "node:child_process"

/**
 * Stop hook: reminds the agent to save learnings to memory before ending.
 *
 * Port of claude/hooks/memory-save.py. On the first stop attempt this blocks by
 * injecting a continuation prompt; on the follow-up stop (the result of our own
 * prompt) it lets the agent stop. A per-session toggle file replaces Claude's
 * `stop_hook_active` flag, which has no documented OpenCode equivalent.
 *
 * NOT runtime-tested: authored against the documented `stop` hook signature
 * (input.sessionID + client.session.prompt). OpenCode was not installed.
 */

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

const TEMPLATE =
  "Use this MEMORY.md structure (sections in this order):\n" +
  "  ## CRITICAL RULES        - non-negotiable active rules, imperative mood\n" +
  "  ## Architecture & Config Facts - stable technical context (not rules)\n" +
  "  ## Active Warnings       - pitfalls and recurring mistakes\n" +
  "  ## Topic Files           - pointers to detail files (e.g. history.md)\n" +
  "Write each bullet on a single line; do NOT hard-wrap text mid-bullet. " +
  "Hard-wrapping inflates the line count and weakens the 40-line fallback reminder.\n"

export const MemorySavePlugin: Plugin = async ({ directory, client }) => {
  return {
    stop: async (input: any) => {
      const sessionId = input?.sessionID || input?.session_id
      if (!sessionId) return

      // Per-session toggle replaces Claude's stop_hook_active flag.
      // Absent  -> first stop: block, and record that we fired.
      // Present -> our own prompt's stop: clear it and let the agent stop.
      const guardDir = join(homedir(), ".cli-tweaks", ".stop-fired")
      const guardFile = join(guardDir, sessionId)
      try {
        mkdirSync(guardDir, { recursive: true })
      } catch {
        // Fail safe: if the state dir is unwritable, do not block the stop.
        return
      }
      if (existsSync(guardFile)) {
        rmSync(guardFile, { force: true })
        return
      }

      const projectName = resolveProjectName(directory)
      const memoryDir = join(homedir(), ".cli-tweaks", "memory", projectName)
      mkdirSync(memoryDir, { recursive: true })
      const hasMemory = existsSync(join(memoryDir, "MEMORY.md"))

      const reason = hasMemory
        ? "Before stopping: if you learned an ACTIVE RULE that changes future behavior " +
          "(build/test commands, an architecture fact, a user preference, a workflow rule), " +
          `update ${memoryDir}/MEMORY.md or a topic file. Write rules in imperative mood. ` +
          "Put durable behavior rules under the '## CRITICAL RULES' section. " +
          "Do NOT save commit hashes, dated fix histories, or archival narrative — " +
          "put any historical detail in history.md, not MEMORY.md. " +
          "MIGRATION: if MEMORY.md has no '## CRITICAL RULES' section, restructure the " +
          "whole file into the template below this session (preserve all real content, " +
          "just reorganize and convert rules to imperative mood). " +
          "If nothing new was learned and the format is already correct, just stop. " +
          "Keep MEMORY.md under 200 lines. IMPORTANT: Always write memory in English only.\n" +
          TEMPLATE
        : "Before stopping: this is a new project with no memory yet. " +
          `Create ${memoryDir}/MEMORY.md following the template below. ` +
          "Write rules in imperative mood. Do NOT save commit hashes or dated history. " +
          "Keep it concise (under 200 lines). IMPORTANT: Always write memory in English only. " +
          "If this was a trivial session with nothing worth remembering, just stop.\n" +
          TEMPLATE

      // Write the toggle BEFORE prompting so the follow-up stop is recognized.
      writeFileSync(guardFile, "1")
      await client.session.prompt({
        path: { id: sessionId },
        body: { parts: [{ type: "text", text: reason }] },
      })
    },
  }
}
