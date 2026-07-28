# Generate DESIGN.md from URL

Analyze a live website and generate a DESIGN.md file following the 9-section standard format.

## Command

```bash
/design-ref generate <url>
```

## Procedure

### Step 1: Fetch and Analyze

Use WebFetch to fetch the target URL. Instruct the fetch to extract:
- All CSS custom properties / design tokens
- Font families (from `<link>` tags, `@font-face`, `font-family` declarations)
- Color values from key elements (backgrounds, text, buttons, links, borders)
- Spacing patterns (padding, margin, gap values)
- Shadow definitions
- Border radius values
- Breakpoint definitions (from media queries)
- Component patterns (buttons, cards, inputs, navigation)

If the homepage isn't sufficient, fetch 1-2 additional pages (e.g., a product page, a blog post) to observe more component patterns.

### Step 2: Extract Design Tokens

From the fetched content, identify:

**Colors:**
- Primary brand color (most prominent accent)
- Background colors (page, card, elevated surfaces)
- Text colors (primary, secondary, muted, disabled)
- State colors (success, warning, error, info)
- Interactive colors (links, buttons, hover states)
- Border colors

**Typography:**
- Font families (sans-serif, serif, monospace stacks)
- Type scale (heading sizes, body size, caption size)
- Font weights used
- Line heights
- Letter spacing

**Spacing:**
- Base unit (usually 4px or 8px)
- Common spacing values
- Container max-widths
- Section padding patterns

**Depth:**
- Shadow definitions (elevation levels)
- Border styles and radii

### Step 3: Generate DESIGN.md

Produce a complete DESIGN.md following the 9-section standard:

```markdown
# [Site Name] Design System

> [1-2 sentence description of the visual identity and design philosophy]

---

## 1. Visual Theme & Atmosphere

### Overall Aesthetic
[2-3 sentences describing the design philosophy]

### Mood & Feeling
- [3-5 bullet points describing the emotional quality]

### Design Density
[Low/Medium/High density with explanation]

### Visual Character
- [5-8 bullet points describing distinguishing visual traits]

---

## 2. Color Palette & Roles

### Core Colors
| Token  | Hex   | Role            |
|--------|-------|-----------------|
| [name] | [hex] | [semantic role] |

### Light Mode
| Element   | Hex   | Role   |
|-----------|-------|--------|
| [element] | [hex] | [role] |

### Dark Mode (if detected)
| Element   | Hex   | Role   |
|-----------|-------|--------|
| [element] | [hex] | [role] |

### State Colors
| State   | Color  | Hex   |
|---------|--------|-------|
| Success | [name] | [hex] |
| Warning | [name] | [hex] |
| Error   | [name] | [hex] |
| Info    | [name] | [hex] |

---

## 3. Typography Rules

### Font Stacks
[CSS font-family declarations]

### Type Scale
| Style   | Size   | Weight   | Line Height   |
|---------|--------|----------|---------------|
| [style] | [size] | [weight] | [line-height] |

### Typography Guidelines
- [Key typography rules observed]

---

## 4. Component Stylings

### Buttons
[Primary, secondary, ghost, destructive variants with colors, radii, padding, states]

### Cards
[Background, border, shadow, padding, radius]

### Inputs
[Border, background, focus state, error state, placeholder color]

### Navigation
[Layout, active state, hover, mobile behavior]

---

## 5. Layout Principles

### Spacing Scale
| Token  | Value   |
|--------|---------|
| [name] | [value] |

### Grid
[Column system, max-width, gutters]

### Breakpoints
| Name   | Value   |
|--------|---------|
| [name] | [value] |

---

## 6. Depth & Elevation

### Shadow System
| Level   | Shadow       | Usage        |
|---------|--------------|--------------|
| [level] | [CSS shadow] | [where used] |

### Surface Hierarchy
[How depth is used to create visual hierarchy]

---

## 7. Do's and Don'ts

### Do
- [Design guideline to follow]

### Don't
- [Anti-pattern to avoid]

---

## 8. Responsive Behavior

### Breakpoint Strategy
[Mobile-first / Desktop-first, key breakpoints]

### Touch Targets
[Minimum sizes for interactive elements]

### Collapsing Strategy
[How navigation, grids, content adapt on smaller screens]

---

## 9. Agent Prompt Guide

### Quick Color Reference
[5-6 most important colors with hex codes for copy-paste]

### Ready-to-Use Prompts
[2-3 example prompts that use this design system effectively]
```

### Step 4: Present Output

Return the generated DESIGN.md in the response. Add a note at the top:

```
> Generated from [URL] on [date]. Values are observed from live CSS and may
> need verification against the official design system documentation.
```

## Quality Notes

- WebFetch extracts what's visible in the HTML/CSS response. Client-side-only styles (loaded via JS) may be missed.
- Dark mode colors may not be detected if they require a class toggle or media query that isn't in the initial HTML.
- When uncertain about a value, note it as "observed" rather than asserting it as definitive.
- If the site has a public design system documentation (like GitHub's Primer or Shopify's Polaris), suggest the user cross-reference with the official docs.

## Saving the Generated File

After presenting the DESIGN.md, ask the user if they want to save it:
- To the project: Write to `DESIGN.md` in the project root
- To the catalog: Write to `catalog/[site-name]/DESIGN.md` in this skill's directory
