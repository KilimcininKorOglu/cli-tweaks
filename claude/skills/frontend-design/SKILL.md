---
name: frontend-design
description: >
  This skill MUST be invoked when the user says "frontend yap", "UI tasarla",
  "component oluştur", "sayfa yap", "design ref", "design system", "DESIGN.md",
  "site gibi yap", "GitHub tarzı", "Vercel tarzı", "Anthropic tarzı",
  "generate design system", "design system oluştur", or any variation requesting
  frontend code generation, design system reference loading, or UI building.
  Builds distinctive production-grade interfaces and provides a 27-site design
  system catalog with URL-based generator.
argument-hint: "[use <site> | generate <url> | list]"
---

# Frontend Design

Create distinctive, production-grade frontend interfaces. Load real-world design systems for reference or generate new ones from any URL.

## What To Do Right Now

### Path A: Design reference (`use`, `generate`, `list`)

If the user's command includes `use`, `generate`, or `list`:

- `/frontend-design use github` → Read `subcommands/use.md` and follow it. STOP.
- `/frontend-design generate <url>` → Read `subcommands/generate.md` and follow it. STOP.
- `/frontend-design list` → Print the catalog table from the bottom of this file.

For subcommand routing:
1. Read the full content of the matching subcommand file using the Read tool.
2. Execute its instructions as your complete workflow.
3. STOP. Do not continue reading this file.

### Path B: Build frontend (default)

If no subcommand — build distinctive frontend code following the Design Guidelines below.

If a design system was loaded via Path A earlier in this conversation, use those
tokens (colors, fonts, spacing, components). Otherwise, make bold creative choices.

---

## Design Guidelines

### Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work — the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

### Frontend Aesthetics

- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt for distinctive choices that elevate the design. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions. Focus on high-impact moments: one well-orchestrated page load with staggered reveals creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, grain overlays.

### Anti-Patterns (NEVER)

- Generic AI aesthetics: overused fonts (Inter, Roboto, Arial), cliched purple gradients on white, predictable layouts
- Cookie-cutter design that lacks context-specific character
- Same choices across generations (vary themes, fonts, aesthetics every time)
- Holding back — show what can truly be created when committing fully to a distinctive vision
- Gradients of any kind — no linear, radial, or mesh gradients anywhere
- Unnecessary hover effects — only add hover states when they serve a clear functional purpose

### Implementation

Match complexity to the vision. Maximalist designs need elaborate code with extensive animations. Minimalist designs need restraint, precision, careful spacing and typography. Elegance comes from executing the vision well.

---

## Design System Catalog (28 Sites)

Use `/frontend-design use <name>` to load any of these into context:

### Social Media

| Site       | Directory        | Description                                      |
|------------|------------------|--------------------------------------------------|
| X (Twitter)| `catalog/x/`     | Dark mode dominant, blue accent, minimalist      |
| TikTok     | `catalog/tiktok/` | Vibrant cyan/pink gradient, neon on dark         |
| Reddit     | `catalog/reddit/` | Orange-red #FF4500, card-based layout            |
| Discord    | `catalog/discord/`| Blurple #5865F2, gaming aesthetic                |
| LinkedIn   | `catalog/linkedin/`| Corporate blue #0A66C2, structured              |
| Snapchat   | `catalog/snapchat/`| Yellow #FFFC00, playful UI                      |
| Threads    | `catalog/threads/`| Clean black/white, Instagram-adjacent            |
| Mastodon   | `catalog/mastodon/`| Purple #6364FF, open-source aesthetic            |

### E-commerce & Retail

| Site       | Directory         | Description                                     |
|------------|-------------------|-------------------------------------------------|
| Amazon     | `catalog/amazon/` | Orange #FF9900, dense product layouts            |
| Shopify    | `catalog/shopify/`| Green #008060, Polaris design system             |
| Etsy       | `catalog/etsy/`   | Orange-coral #F56400, artisan aesthetic           |
| eBay       | `catalog/ebay/`   | Blue #3665F3, multicolor logo                    |
| Target     | `catalog/target/` | Red #CC0000, clean shopping UI                   |
| Walmart    | `catalog/walmart/`| Blue #0071DC, utility-focused                    |

### Travel & Food

| Site        | Directory           | Description                                   |
|-------------|---------------------|-----------------------------------------------|
| Booking.com | `catalog/booking/`  | Deep blue #003580, yellow CTAs                |
| DoorDash    | `catalog/doordash/` | Red #FF3008, restaurant-focused               |
| Starbucks   | `catalog/starbucks/`| Green #00704A, warm inviting UI               |

### Gaming

| Site         | Directory             | Description                                 |
|--------------|-----------------------|---------------------------------------------|
| Steam        | `catalog/steam/`      | Dark blue #1b2838, cyan accent              |
| Epic Games   | `catalog/epicgames/`  | Dark theme, blue #0074e4, cinematic         |
| PlayStation  | `catalog/playstation/`| Blue #003791, premium gaming                |
| Xbox         | `catalog/xbox/`       | Green #107C10, Fluent Design                |
| Twitch       | `catalog/twitch/`     | Purple #9146FF, live content focus          |

### Developer Tools & AI

| Site       | Directory           | Description                                    |
|------------|---------------------|------------------------------------------------|
| GitHub     | `catalog/github/`   | Primer system, octicon icons                   |
| Vercel     | `catalog/vercel/`   | Black-white precision, Geist font              |
| Supabase   | `catalog/supabase/` | Emerald #3ECF8E, code-first                    |
| OpenAI     | `catalog/openai/`   | Clean white/dark, ChatGPT green                |
| Anthropic  | `catalog/anthropic/`| Warm terracotta #DA7756, editorial             |
| Hacker     | `catalog/hacker/`   | Matrix green #00ff41, terminal-native dark     |

---

## Subcommand Reference

- For `/frontend-design use`: see [subcommands/use.md](subcommands/use.md)
- For `/frontend-design generate`: see [subcommands/generate.md](subcommands/generate.md)
