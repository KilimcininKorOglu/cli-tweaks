import type { Plugin } from "@opencode-ai/plugin"
import { homedir } from "node:os"
import { join } from "node:path"
import { existsSync, readFileSync } from "node:fs"

/**
 * tool.execute.before hook: blocks `git add -f` / `git add --force` on files
 * listed in the global gitignore (~/.gitignore_global), so protected files like
 * AGENTS.md / CLAUDE.md cannot be force-added by mistake.
 *
 * Port of claude/hooks/git-protect.py. Throwing from tool.execute.before aborts
 * the bash tool call (per the opencode.ai/docs/plugins .env-protection example,
 * which throws to deny a tool by inspecting input.tool + output.args).
 *
 * NOT runtime-tested: authored against the documented `tool.execute.before`
 * signature (input.tool === "bash", output.args.command). OpenCode was not installed.
 */
export const GitProtectPlugin: Plugin = async () => {
  return {
    "tool.execute.before": async (input: any, output: any) => {
      if (input?.tool !== "bash") return

      const command: string = output?.args?.command ?? ""
      if (!/\bgit\s+add\b/.test(command)) return
      if (!/\s-f\b|\s--force\b/.test(command)) return

      const gitignorePath = join(homedir(), ".gitignore_global")
      if (!existsSync(gitignorePath)) return

      const entries = readFileSync(gitignorePath, "utf8")
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line && !line.startsWith("#") && !line.startsWith("!"))

      // Mirror git-protect.py: match the raw entry (minus trailing slash) or its
      // stripped form (leading globs/dots removed) as a substring of the command.
      const matched: string[] = []
      for (const entry of entries) {
        const raw = entry.replace(/\/+$/, "")
        const clean = raw.replace(/^\*+/, "").replace(/^\.+/, "")
        if (raw && command.includes(raw)) matched.push(entry)
        else if (clean && command.includes(clean)) matched.push(entry)
      }

      if (matched.length > 0) {
        throw new Error(
          `BLOCKED: git add -f on protected file(s): ${matched.join(", ")}. ` +
            `These files are in the global gitignore for a reason. ` +
            `Analyze the root cause of the error instead of force-adding.`,
        )
      }
    },
  }
}
