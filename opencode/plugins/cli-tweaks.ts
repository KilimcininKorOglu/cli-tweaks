/**
 * cli-tweaks plugin for OpenCode
 *
 * Provides persistent project-scoped memory and desktop notifications.
 * Memory is stored at ~/.cli-tweaks/memory/<project>/ and shared with
 * Factory Droid and Claude Code.
 *
 * Events:
 *   session.created                    - Load memory into context
 *   session.idle                       - Remind agent to save learnings
 *   experimental.session.compacting    - Re-inject memory before compaction
 */
import type { Plugin } from "@opencode-ai/plugin";

const MAX_MEMORY_LINES = 200;

function getProjectName(directory: string): string {
  return directory.split("/").pop() || "unknown";
}

function getMemoryDir(directory: string): string {
  const home = process.env.HOME || process.env.USERPROFILE || "~";
  return `${home}/.cli-tweaks/memory/${getProjectName(directory)}`;
}

async function readMemory(memoryDir: string, $: any): Promise<string> {
  try {
    const result = await $`cat ${memoryDir}/MEMORY.md 2>/dev/null`.text();
    const lines = result.split("\n").slice(0, MAX_MEMORY_LINES);
    return lines.join("\n");
  } catch {
    return "";
  }
}

async function listTopicFiles(memoryDir: string, $: any): Promise<string[]> {
  try {
    const result = await $`ls ${memoryDir}/*.md 2>/dev/null`.text();
    return result
      .trim()
      .split("\n")
      .map((f: string) => f.split("/").pop() || "")
      .filter((f: string) => f && f !== "MEMORY.md");
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

async function sendNotification(
  $: any,
  title: string,
  message: string,
): Promise<void> {
  try {
    const safeTitle = title.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
    const safeMessage = message.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
    await $`osascript -e 'display notification "${safeMessage}" with title "${safeTitle}"'`;
  } catch {
    // Notification failure is non-critical
  }
}

export default {
  name: "cli-tweaks",
  events: {
    "session.created": async (context, client, $) => {
      const directory = context.directory || process.cwd();
      const projectName = getProjectName(directory);
      const memoryDir = getMemoryDir(directory);

      const memoryContent = await readMemory(memoryDir, $);
      const topicFiles = await listTopicFiles(memoryDir, $);
      const memoryContext = buildMemoryContext(
        memoryDir,
        memoryContent,
        topicFiles,
        projectName,
      );

      client.app.log("cli-tweaks: memory loaded for " + projectName);

      return {
        output: {
          context: memoryContext,
        },
      };
    },

    "session.idle": async (context, client, $) => {
      const directory = context.directory || process.cwd();
      const memoryDir = getMemoryDir(directory);

      await sendNotification(
        $,
        "cli-tweaks",
        "Session idle -- remember to save learnings to memory",
      );

      client.app.log("cli-tweaks: idle reminder sent");

      return {
        output: {
          toast: {
            title: "Memory Reminder",
            description:
              "If you learned anything new, save it to " + memoryDir,
          },
        },
      };
    },

    "experimental.session.compacting": async (context, client, $) => {
      const directory = context.directory || process.cwd();
      const projectName = getProjectName(directory);
      const memoryDir = getMemoryDir(directory);

      const memoryContent = await readMemory(memoryDir, $);
      const topicFiles = await listTopicFiles(memoryDir, $);
      const memoryContext = buildMemoryContext(
        memoryDir,
        memoryContent,
        topicFiles,
        projectName,
      );

      client.app.log("cli-tweaks: memory re-injected after compaction");

      return {
        output: {
          context: memoryContext,
        },
      };
    },
  },
} satisfies Plugin;
