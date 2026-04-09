# Load Design System Reference

Load a design system into context from the built-in catalog or a custom file path.

## Command

```bash
/design-ref use <site>              # Load from catalog by name
/design-ref use <path/to/DESIGN.md> # Load custom file
```

## Catalog Lookup

When the argument matches a known site name, resolve the path to the catalog file.

The catalog directory is located at `catalog/` relative to this skill's directory. Each site has its own subdirectory with a `DESIGN.md` file.

**Name resolution** (case-insensitive):

| Input | Resolves To |
|-------|-------------|
| `github` | `catalog/github/DESIGN.md` |
| `vercel` | `catalog/vercel/DESIGN.md` |
| `discord` | `catalog/discord/DESIGN.md` |
| `anthropic` | `catalog/anthropic/DESIGN.md` |
| `x` or `twitter` | `catalog/x/DESIGN.md` |
| `tiktok` | `catalog/tiktok/DESIGN.md` |
| `reddit` | `catalog/reddit/DESIGN.md` |
| `linkedin` | `catalog/linkedin/DESIGN.md` |
| `snapchat` | `catalog/snapchat/DESIGN.md` |
| `threads` | `catalog/threads/DESIGN.md` |
| `mastodon` | `catalog/mastodon/DESIGN.md` |
| `amazon` | `catalog/amazon/DESIGN.md` |
| `shopify` | `catalog/shopify/DESIGN.md` |
| `etsy` | `catalog/etsy/DESIGN.md` |
| `ebay` | `catalog/ebay/DESIGN.md` |
| `target` | `catalog/target/DESIGN.md` |
| `walmart` | `catalog/walmart/DESIGN.md` |
| `booking` | `catalog/booking/DESIGN.md` |
| `doordash` | `catalog/doordash/DESIGN.md` |
| `starbucks` | `catalog/starbucks/DESIGN.md` |
| `steam` | `catalog/steam/DESIGN.md` |
| `epicgames` or `epic` | `catalog/epicgames/DESIGN.md` |
| `playstation` or `ps` | `catalog/playstation/DESIGN.md` |
| `xbox` | `catalog/xbox/DESIGN.md` |
| `twitch` | `catalog/twitch/DESIGN.md` |
| `supabase` | `catalog/supabase/DESIGN.md` |
| `openai` | `catalog/openai/DESIGN.md` |

If the argument doesn't match any catalog name, treat it as a file path and read with the Read tool.

## Procedure

1. **Resolve path** — catalog name → file path, or use provided path directly.

2. **Read the file** using the Read tool. If the file doesn't exist:
   - For catalog names: "Design system '[name]' not found in catalog. Use `/design-ref list` to see available systems or `/design-ref generate <url>` to create one."
   - For paths: "File not found at [path]."

3. **Present a summary** of the loaded design system:

```markdown
## Design System Loaded: [Name]

**Atmosphere:** [1-sentence mood/philosophy from Section 1]

**Key Colors:**
| Role | Color | Hex |
|------|-------|-----|
| Primary | [name] | [hex] |
| Background | [name] | [hex] |
| Text | [name] | [hex] |
| Accent | [name] | [hex] |

**Typography:** [Primary font family] — [base size]

**Spacing:** [Base unit]px scale

**Components:** [List 3-4 key component types defined]

This design system is now in context. Reference it when building UI with `frontend-design` or other design skills.
```

4. **Keep the full DESIGN.md content in context** for subsequent tool calls in this conversation. The summary is for the user; the full content is for the AI to reference.

## Notes

- Loading a new design system replaces the previous one in context.
- The full content may be large (200-400+ lines). The summary keeps the response concise while the full content stays available for reference.
- If using with `frontend-design`, mention which design system is loaded so the agent knows which tokens to use.
