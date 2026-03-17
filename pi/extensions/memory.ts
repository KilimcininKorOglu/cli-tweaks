/**
 * Persistent project-scoped memory for Pi Agent.
 *
 * Memory is stored at ~/.cli-tweaks/memory/<project>/ and shared with
 * Factory Droid, Claude Code, and OpenCode.
 *
 * Events:
 *   before_agent_start  - Load memory into context
 *   agent_end           - Remind agent to save learnings
 *   session_compact     - Re-inject memory after compaction
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { readFileSync, readdirSync, existsSync, mkdirSync } from "fs";
import { join, basename } from "path";
import { homedir } from "os";

const MAX_MEMORY_LINES = 200;

function getProjectName(cwd: string): string {
  return basename(cwd) || "unknown";
}

function getMemoryDir(cwd: string): string {
  return join(homedir(), ".cli-tweaks", "memory", getProjectName(cwd));
}

function readMemory(memoryDir: string): string {
  const memoryFile = join(memoryDir, "MEMORY.md");
  if (!existsSync(memoryFile)) return "";
  try {
    const content = readFileSync(memoryFile, "utf-8");
    return content.split("\n").slice(0, MAX_MEMORY_LINES).join("\n");
  } catch {
    return "";
  }
}

function listTopicFiles(memoryDir: string): string[] {
  if (!existsSync(memoryDir)) return [];
  try {
    return readdirSync(memoryDir)
      .filter((f) => f.endsWith(".md") && f !== "MEMORY.md")
      .sort();
  } catch {
    return [];
  }
}

function buildMemoryContext(
  memoryDir: string,
  memoryContent: string,
  topicFiles: string[],
  projectName: string,
): string {
  const parts: string[] = [];

  parts.push(`[AUTO MEMORY SYSTEM]
You have a persistent memory system that carries knowledge across sessions.
Memory location: ${memoryDir}

How it works:
- MEMORY.md is loaded at session start (first ${MAX_MEMORY_LINES} lines). Keep it concise.
- Create topic files (e.g., debugging.md, patterns.md) for detailed notes.
- MEMORY.md should be an index pointing to topic files.
- Read topic files on demand when you need the information.

IMPORTANT: All memory files (MEMORY.md and topic files) MUST be written in English only.
This ensures consistency and searchability across sessions.

When to save memory:
- Build commands, test commands, or project setup steps you discovered
- Architecture decisions or patterns you identified
- Debugging insights or tricky bugs you solved
- User preferences or coding style you observed
- Workflow habits (e.g., "user prefers Turkish responses")
- DO NOT save trivial or obvious information
- DO NOT save sensitive data (passwords, keys, tokens)

How to save:
- Write directly to ${memoryDir}/MEMORY.md or topic files using file tools
- Keep MEMORY.md under ${MAX_MEMORY_LINES} lines -- move details to topic files
- Use markdown headers and bullets for structure
- ALWAYS write in English regardless of conversation language`);

  if (memoryContent) {
    parts.push("\n[LOADED MEMORY]\n" + memoryContent);
  } else {
    parts.push(
      `\n[NO MEMORY YET] This is the first session for project '${projectName}'. ` +
        "Start building memory as you learn about this project.",
    );
  }

  if (topicFiles.length > 0) {
    const listing = topicFiles.map((f) => "- " + f).join("\n");
    parts.push(
      "\n[TOPIC FILES AVAILABLE]\n" +
        listing +
        "\nRead these with file tools when you need detailed information.",
    );
  }

  return parts.join("\n");
}

function loadMemoryContext(cwd: string): string {
  const projectName = getProjectName(cwd);
  const memoryDir = getMemoryDir(cwd);
  const memoryContent = readMemory(memoryDir);
  const topicFiles = listTopicFiles(memoryDir);
  return buildMemoryContext(memoryDir, memoryContent, topicFiles, projectName);
}

export default function (pi: ExtensionAPI) {
  pi.on("before_agent_start", async (_event, ctx) => {
    const memoryContext = loadMemoryContext(ctx.cwd);
    return {
      message: {
        customType: "cli-tweaks-memory",
        content: memoryContext,
        display: false,
      },
    };
  });

  pi.on("agent_end", async (_event, ctx) => {
    const memoryDir = getMemoryDir(ctx.cwd);
    mkdirSync(memoryDir, { recursive: true });

    const memoryFile = join(memoryDir, "MEMORY.md");
    const hasMemory = existsSync(memoryFile);

    const reminder = hasMemory
      ? `Before stopping: if you learned anything new or useful in this session ` +
        `(build commands, architecture insights, debugging solutions, user preferences, ` +
        `workflow patterns), update your memory at ${memoryDir}/MEMORY.md or create/update ` +
        `topic files there. If nothing new was learned, just stop without changes. ` +
        `Keep MEMORY.md under ${MAX_MEMORY_LINES} lines. IMPORTANT: Always write memory in English only.`
      : `Before stopping: this is a new project with no memory yet. ` +
        `Create ${memoryDir}/MEMORY.md with key learnings from this session: ` +
        `project overview, build/test commands, architecture notes, ` +
        `user preferences you observed. Keep it concise (under ${MAX_MEMORY_LINES} lines). ` +
        `IMPORTANT: Always write memory in English only. ` +
        `If this was a trivial session with nothing worth remembering, just stop.`;

    pi.sendMessage({
      customType: "cli-tweaks-memory-reminder",
      content: reminder,
      display: true,
    });
  });

  pi.on("session_compact", async (_event, ctx) => {
    const memoryContext = loadMemoryContext(ctx.cwd);
    return {
      message: {
        customType: "cli-tweaks-memory",
        content: memoryContext,
        display: false,
      },
    };
  });
}
