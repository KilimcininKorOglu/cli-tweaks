---
name: design-ref
description: >
  This skill MUST be invoked when the user says "design ref", "design system",
  "tasarım referansı", "DESIGN.md", "site gibi yap", "X gibi tasarla",
  "GitHub tarzı", "Vercel tarzı", "Anthropic tarzı", "Discord tarzı",
  "generate design system", "design system oluştur", or any variation requesting
  a design system reference or generation. Provides a catalog of 27 real-world
  design systems (GitHub, Vercel, Discord, Amazon, etc.) and can generate new
  ones from any URL.
argument-hint: "[use <site|path> | generate <url>]"
---

# Design System Reference

Load real-world design systems from a curated catalog of 27 sites, or generate new ones from any URL. Each design system follows the DESIGN.md 9-section standard.

## Usage

```bash
/design-ref use github               # Load GitHub Primer design system
/design-ref use vercel               # Load Vercel Geist design system
/design-ref use anthropic            # Load Anthropic design system
/design-ref use discord              # Load Discord design system
/design-ref use <path/to/DESIGN.md>  # Load custom DESIGN.md file
/design-ref generate <url>           # Generate DESIGN.md from any URL
/design-ref list                     # Show all available design systems
```

## Subcommands

| Subcommand | Command | Description |
|------------|---------|-------------|
| `use`      | `/design-ref use <site>` | Load a design system into context |
| `generate` | `/design-ref generate <url>` | Generate DESIGN.md from a live URL |
| `list`     | `/design-ref list` | List all 27 available design systems |

- For `/design-ref use`: see [subcommands/use.md](subcommands/use.md)
- For `/design-ref generate`: see [subcommands/generate.md](subcommands/generate.md)
- For `/design-ref list`: print the catalog table below

## Catalog (27 Design Systems)

All files live under `catalog/` in this skill's directory.

### Social Media

| Site | Directory | Description |
|------|-----------|-------------|
| X (Twitter) | `catalog/x/` | Dark mode dominant, blue accent, minimalist |
| TikTok | `catalog/tiktok/` | Vibrant cyan/pink gradient, neon on dark |
| Reddit | `catalog/reddit/` | Orange-red #FF4500, card-based layout |
| Discord | `catalog/discord/` | Blurple #5865F2, gaming aesthetic |
| LinkedIn | `catalog/linkedin/` | Corporate blue #0A66C2, structured |
| Snapchat | `catalog/snapchat/` | Yellow #FFFC00, playful UI |
| Threads | `catalog/threads/` | Clean black/white, Instagram-adjacent |
| Mastodon | `catalog/mastodon/` | Purple #6364FF, open-source aesthetic |

### E-commerce & Retail

| Site | Directory | Description |
|------|-----------|-------------|
| Amazon | `catalog/amazon/` | Orange #FF9900, dense product layouts |
| Shopify | `catalog/shopify/` | Green #008060, Polaris design system |
| Etsy | `catalog/etsy/` | Orange-coral #F56400, artisan aesthetic |
| eBay | `catalog/ebay/` | Blue #3665F3, multicolor logo |
| Target | `catalog/target/` | Red #CC0000, clean shopping UI |
| Walmart | `catalog/walmart/` | Blue #0071DC, utility-focused |

### Travel & Food

| Site | Directory | Description |
|------|-----------|-------------|
| Booking.com | `catalog/booking/` | Deep blue #003580, yellow CTAs |
| DoorDash | `catalog/doordash/` | Red #FF3008, restaurant-focused |
| Starbucks | `catalog/starbucks/` | Green #00704A, warm inviting UI |

### Gaming

| Site | Directory | Description |
|------|-----------|-------------|
| Steam | `catalog/steam/` | Dark blue #1b2838, cyan accent |
| Epic Games | `catalog/epicgames/` | Dark theme, blue #0074e4, cinematic |
| PlayStation | `catalog/playstation/` | Blue #003791, premium gaming |
| Xbox | `catalog/xbox/` | Green #107C10, Fluent Design |
| Twitch | `catalog/twitch/` | Purple #9146FF, live content focus |

### Developer Tools & AI

| Site | Directory | Description |
|------|-----------|-------------|
| GitHub | `catalog/github/` | Primer system, octicon icons |
| Vercel | `catalog/vercel/` | Black-white precision, Geist font |
| Supabase | `catalog/supabase/` | Emerald #3ECF8E, code-first |
| OpenAI | `catalog/openai/` | Clean white/dark, ChatGPT green |
| Anthropic | `catalog/anthropic/` | Warm terracotta #DA7756, editorial |

## DESIGN.md Standard (9 Sections)

Every DESIGN.md follows this structure:

| # | Section | What It Captures |
|---|---------|-----------------|
| 1 | Visual Theme & Atmosphere | Mood, density, design philosophy |
| 2 | Color Palette & Roles | Semantic name + hex + functional role |
| 3 | Typography Rules | Font families, type scale, weights |
| 4 | Component Stylings | Buttons, cards, inputs, nav + states |
| 5 | Layout Principles | Spacing scale, grid, whitespace |
| 6 | Depth & Elevation | Shadow system, surface hierarchy |
| 7 | Do's and Don'ts | Design guardrails and anti-patterns |
| 8 | Responsive Behavior | Breakpoints, touch targets, collapse strategy |
| 9 | Agent Prompt Guide | Quick color ref, ready-to-use prompts |

## Integration with Other Skills

Once a design system is loaded with `/design-ref use`, it stays in context. Use it with:
- `frontend-design` — build UI matching the loaded design system
- `polish` / `normalize` — check consistency against the reference
- `critique` — evaluate against the loaded design system's standards
