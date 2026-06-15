import type { Plugin } from "@opencode-ai/plugin"
import { join } from "node:path"
import { existsSync, readFileSync } from "node:fs"

/**
 * Compaction hook: re-injects the project instruction file(s) so the rules
 * survive context compaction.
 *
 * Port of claude/hooks/compact-reinject.py. Claude restores CLAUDE.md after a
 * compact; OpenCode reads AGENTS.md natively, so this preserves AGENTS.md (and
 * CLAUDE.md when present) through the compaction summary by pushing them onto
 * the preserved-context list.
 *
 * NOT runtime-tested: authored against the documented
 * `experimental.session.compacting` signature (output.context.push). OpenCode
 * flags this hook `experimental.`, so its shape may change.
 */

const INSTRUCTION_FILES = ["AGENTS.md", "CLAUDE.md"]

export const CompactReinjectPlugin: Plugin = async ({ directory }) => {
  return {
    "experimental.session.compacting": async (_input: any, output: any) => {
      for (const name of INSTRUCTION_FILES) {
        const path = join(directory, name)
        if (!existsSync(path)) continue
        let content = ""
        try {
          content = readFileSync(path, "utf8").trim()
        } catch {
          // Unreadable file; skip it and keep the compaction going.
          continue
        }
        if (!content) continue
        output.context.push(`[RE-INJECTED AFTER COMPACTION: ${name}]\n${content}`)
      }
    },
  }
}
