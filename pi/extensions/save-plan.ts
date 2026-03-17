/**
 * Plan saving extension for Pi Agent.
 *
 * Registers a /save-plan command that saves the last assistant message
 * (or a specified plan) to ~/.pi/agent/plans/<project>/.
 * Also provides a save_plan tool that the agent can call directly.
 *
 * Sends desktop notifications via cli-tweaks:notify-request event.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { writeFileSync, mkdirSync } from "fs";
import { join, basename } from "path";
import { homedir } from "os";
import { Type } from "@sinclair/typebox";

function sanitizeTitle(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s]+/g, "-")
    .replace(/^-+|-+$/g, "")
    || "untitled-plan";
}

function getPlansDir(cwd: string): string {
  const projectName = basename(cwd) || "unknown";
  return join(homedir(), ".pi", "agent", "plans", projectName);
}

function savePlan(cwd: string, title: string, plan: string): string {
  const plansDir = getPlansDir(cwd);
  mkdirSync(plansDir, { recursive: true });

  const now = new Date();
  const timestamp = now.toISOString().slice(0, 19).replace(/[-:T]/g, (m) =>
    m === "T" ? "-" : m === ":" ? "" : m,
  );
  const safeTitle = sanitizeTitle(title);
  const filename = `${timestamp}-${safeTitle}.md`;
  const filepath = join(plansDir, filename);

  const projectName = basename(cwd) || "unknown";
  const content =
    `# ${title}\n\n` +
    `*Created: ${now.toISOString().slice(0, 19).replace("T", " ")}*\n` +
    `*Project: ${projectName}*\n\n` +
    `---\n\n` +
    plan;

  writeFileSync(filepath, content, "utf-8");
  return filepath;
}

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "save_plan",
    label: "Save Plan",
    description:
      "Save a plan or specification to disk. Use this after creating an implementation plan.",
    parameters: Type.Object({
      title: Type.String({ description: "Plan title" }),
      plan: Type.String({ description: "Plan content in Markdown" }),
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      const filepath = savePlan(ctx.cwd, params.title, params.plan);

      pi.events.emit("cli-tweaks:notify-request", {
        title: "Plan Saved",
        message: `Plan saved: ${basename(filepath)}`,
      });

      return {
        content: [{ type: "text", text: `Plan saved to: ${filepath}` }],
        details: { filepath },
      };
    },
  });

  pi.registerCommand("save-plan", {
    description: "Save the last assistant plan to disk",
    handler: async (args, ctx) => {
      const entries = ctx.sessionManager.getBranch();
      let lastAssistantMessage = "";

      for (let i = entries.length - 1; i >= 0; i--) {
        const entry = entries[i];
        if (
          entry.type === "message" &&
          entry.message.role === "assistant" &&
          entry.message.content
        ) {
          const content = entry.message.content;
          if (typeof content === "string") {
            lastAssistantMessage = content;
          } else if (Array.isArray(content)) {
            lastAssistantMessage = content
              .filter((c: any) => c.type === "text")
              .map((c: any) => c.text)
              .join("\n");
          }
          break;
        }
      }

      if (!lastAssistantMessage) {
        ctx.ui.notify("No assistant message found to save.", "warning");
        return;
      }

      const title = args || "plan";
      const filepath = savePlan(ctx.cwd, title, lastAssistantMessage);

      pi.events.emit("cli-tweaks:notify-request", {
        title: "Plan Saved",
        message: `Plan saved: ${basename(filepath)}`,
      });

      ctx.ui.notify(`Plan saved to: ${filepath}`, "info");
    },
  });
}
