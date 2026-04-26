# Hacker Design System

> Terminal-native dark interface. Pure black background, bright matrix green (#00ff41) text, monospace typography, zero border-radius, zero shadows, zero gradients. Every element looks like it belongs in a terminal emulator.

**Design Philosophy:** Utilitarian hacker aesthetic. No decoration, no softness. Hard edges, bright phosphor green on void black. Information density over whitespace. The interface should feel like SSH'ing into a server.

## 1. Color Palette

### Core Colors

| Role         | Name         | Hex       | CSS Variable    | Usage                                    |
|--------------|--------------|-----------|-----------------|------------------------------------------|
| Background   | Void Black   | `#000000` | `--bg`          | Page background, base                    |
| Surface      | Near Black   | `#0a0a0a` | `--surface`     | Cards, table headers, elevated surfaces  |
| Border       | Dark Gray    | `#1a1a1a` | `--border`      | All borders, dividers, separators        |
| Primary Text | Matrix Green | `#00ff41` | `--green`       | All text, values, links, active elements |
| Muted Green  | Deep Green   | `#006b1d` | `--green-muted` | Borders on active badges, accent borders |
| Faint Green  | Shadow Green | `#002a0a` | `--green-faint` | Active badge background, highlight bg    |
| Danger       | Terminal Red | `#ff2d2d` | `--red`         | Error rates, destructive actions, danger |
| Danger Dim   | Dark Red     | `#661212` | `--red-dim`     | Danger button background                 |
| Inactive     | Dim Green    | `#005f17` | (hardcoded)     | Badge-inactive text only                 |

### Text Colors

| Role    | Hex       | CSS Variable   | Usage                           |
|---------|-----------|----------------|---------------------------------|
| Default | `#00ff41` | `--text`       | Body text, all content          |
| Dim     | `#00ff41` | `--text-dim`   | Same as default (unified green) |
| Muted   | `#00ff41` | `--text-muted` | Same as default (unified green) |

**Rule:** All text is bright `#00ff41`. No dim or muted text variants. The only exception is `.badge-inactive` which uses hardcoded `#005f17`.

### Per-Page Variations

| Variable       | index.html | admin.html | logs.html |
|----------------|------------|------------|-----------|
| `--green-dim`  | `#00ff41`  | `#00ff41`  | `#00cc33` |
| `--red`        | (none)     | `#ff2d2d`  | `#ff2d2d` |
| `--red-dim`    | (none)     | `#661212`  | `#661212` |
| `--yellow`     | (none)     | (none)     | `#ffcc00` |
| `--yellow-dim` | (none)     | (none)     | `#665200` |

### Logs Status Colors

| Class         | Color           | Usage                |
|---------------|-----------------|----------------------|
| `.status-2xx` | `var(--green)`  | Success status codes |
| `.status-4xx` | `var(--yellow)` | Client error codes   |
| `.status-5xx` | `var(--red)`    | Server error codes   |

## 2. Typography

### Font Stack

```css
font-family: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', 'Fira Code', monospace;
```

Single monospace stack for everything. No serif, no sans-serif. Loaded via Google Fonts:
```css
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap');
```

### Type Scale

| Element            | Size    | Weight | Letter Spacing | Usage                           |
|--------------------|---------|--------|----------------|---------------------------------|
| Page title (h1)    | 14-18px | 700    | 2-3px          | Header title                    |
| Stat value (large) | 20-28px | 700    | -1px           | Dashboard stat numbers          |
| Body text          | 13px    | 400    | 0              | Default body text               |
| Table cell         | 12px    | 400    | 0              | Table data                      |
| Section header     | 11px    | 700    | 2px            | Section titles (uppercase feel) |
| Table header       | 10px    | 700    | 1.5px          | Column headers                  |
| Badge              | 10px    | 700    | 0.5px          | Status badges                   |
| Chart label        | 9px     | 400    | 0              | Axis labels, footnotes          |
| Footer             | 10px    | 400    | 0              | Page footer                     |
| Config note        | 11px    | 400    | 0              | Help text, descriptions         |

### Line Height

Global: `1.6` — generous for monospace readability.

## 3. Spacing & Layout

### Spacing Scale

| Token | Value | Usage                             |
|-------|-------|-----------------------------------|
| xs    | 4px   | Chart label margin, tight gaps    |
| sm    | 8px   | Padding within cells, small gaps  |
| md    | 12px  | Grid gaps, form element padding   |
| lg    | 16px  | Section padding, standard spacing |
| xl    | 24px  | Page padding, section margins     |
| 2xl   | 32px  | Section bottom margin (admin)     |
| 3xl   | 40px  | Section bottom margin (public)    |
| 4xl   | 48px  | Header bottom margin              |

### Layout

| Page   | Max Width | Padding |
|--------|-----------|---------|
| Public | 960px     | 24px    |
| Admin  | 1280px    | 24px    |
| Logs   | 1400px    | 24px    |

### Breakpoints

| Name   | Width | Adjustments                                   |
|--------|-------|-----------------------------------------------|
| Mobile | 600px | Reduced cell padding (6px 8px)                |
| Tablet | 700px | Stats grid 2-col, form wraps, reduced padding |

### Grid Patterns

```css
/* Admin stats: 5-column grid with 1px gap borders */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
}

/* Public stats: 3-column grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
```

## 4. Borders & Shadows

### Borders

| Property      | Value                     | Usage                       |
|---------------|---------------------------|-----------------------------|
| Default       | `1px solid var(--border)` | All borders, dividers       |
| Section line  | `1px solid var(--border)` | Below section headers       |
| Editable hint | `1px dashed var(--green)` | Clickable editable cells    |
| Border Radius | `0`                       | **Never.** Zero everywhere. |

### Shadows

**None.** No box-shadow anywhere. Depth is conveyed through background color differences (`--bg` vs `--surface`) and borders only.

## 5. Component Patterns

### Stat Card

```css
.stat-card {
  background: var(--surface);
  padding: 16-20px;
  text-align: center; /* public */ or left /* admin */
}
.stat-card .label {
  font-size: 10px;
  letter-spacing: 1-1.5px;
}
.stat-card .value {
  font-size: 20-28px;
  font-weight: 700;
  color: var(--green);
}
```

### Badges

```css
.badge {
  display: inline-block;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  border: 1px solid;
}
.badge-active {
  color: var(--green);           /* #00ff41 */
  border-color: var(--green-muted); /* #006b1d */
  background: var(--green-faint);   /* #002a0a */
}
.badge-inactive {
  color: #005f17;                /* hardcoded dim */
  border-color: var(--border);
  background: transparent;
}
```

Text content: `Aktif` / `Pasif` (Turkish).

### Tables

```css
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { font-size: 10px; font-weight: 700; letter-spacing: 1.5px; background: var(--surface); }
td { color: var(--text); }
th, td { padding: 10px 12px; border-bottom: 1px solid var(--border); }
tr:last-child td { border-bottom: none; }
```

Wrap tables in `.table-wrap` with `border: 1px solid var(--border); overflow-x: auto;`.

### Buttons

```css
/* Primary — green on dark green */
.btn-primary {
  background: var(--green-faint);
  color: var(--green);
  border: 1px solid var(--green-muted);
  padding: 8-10px 12-16px;
  font-family: inherit;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

/* Danger — red on dark red */
.btn-danger {
  background: var(--red-dim);
  color: var(--red);
  border: 1px solid var(--red);
}

/* Small — for table action columns */
.btn-sm { padding: 4px 8px; font-size: 11px; }
```

**No hover effects** on buttons. Logs table has `tr:hover td { background: var(--surface) }` as the sole hover exception.

### Forms

```css
.add-form {
  display: flex;
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
}
.add-form input {
  padding: 10px 12px;
  border: none;
  background: var(--surface);
  color: var(--green);
  font-family: inherit;
  font-size: 12px;
}
.add-form input::placeholder { color: var(--green-muted); }
```

Inputs have no visible border — the form container's 1px gap creates visual separation. Focus state: `background: #0f0f0f` (slightly lighter).

### Filter Form (Logs)

```css
.filters {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}
.filters select, .filters input {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 6px 10px;
  font-family: inherit;
  font-size: 12px;
}
.filters select:focus, .filters input:focus {
  border-color: var(--green-muted);
}
```

### Registration Form

```css
.reg-form {
  display: flex;
  gap: 8px;
}
.reg-form input {
  flex: 1;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 8px 12px;
}
.reg-form input:focus { border-color: var(--green-muted); }
```

Three-step flow: email input → code input → token display. Steps toggle via `display:none/block`.

### Charts (Bar)

```css
.chart-bar {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 60-180px;
}
.chart-bar .bar, .chart-bar {
  background: var(--green);  /* solid green bars, no gradient */
  min-height: 1px;
}
```

### Sections

```css
.section { margin-bottom: 32-40px; }
.section-header {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 16px;
}
```

### Header

```css
.header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 32-48px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}
```

### Pulse Indicator (Admin)

```css
.pulse {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: var(--green);
  border-radius: 50%;  /* only exception: pulse dot */
  animation: blink 2s infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: .3; }
}
```

## 6. Motion & Animation

### Durations

| Type         | Duration | Usage                  |
|--------------|----------|------------------------|
| Pulse blink  | 2s       | Admin status indicator |
| Auto-refresh | 30s      | Dashboard data refresh |

### Rules

- **No hover transitions.** No fade, no scale, no color shift on hover.
- **No page transitions.** Instant navigation.
- **No loading spinners.** Text-based loading: `"Yükleniyor..."`.
- Only animation: pulse blink on admin status dot.

## 7. Accessibility

### Security Headers (all HTML pages)

```
X-Frame-Options: DENY
Content-Security-Policy: frame-ancestors 'none'
Cache-Control: no-store
```

### Color Contrast

- Green `#00ff41` on black `#000000`: ratio ~10.5:1 (AAA)
- Red `#ff2d2d` on black `#000000`: ratio ~5.2:1 (AA)
- Inactive `#005f17` on black `#000000`: ratio ~2.4:1 (intentionally dim)

### Keyboard

- Forms use standard `<form>` submission and `<button>` elements
- `tabindex` not customized — native browser order
- No custom focus styles (browser default)

## 8. Page Architecture

### Public Landing Page (`index.html`, max-width: 960px)

```
Header (h1 + subtitle)
├── Registration Form (3-step: email → code → token)
├── Statistics (3-col grid: total, today, active users)
│   └── Hourly Chart (24h bar chart)
│   └── Top Models Table
├── Benchmarks Table (TTFB + total, short + long)
├── Claude Code Configuration (code blocks)
├── Model List (grouped by provider, table)
└── Footer (version + GitHub link)
```

### Admin Dashboard (`admin.html`, max-width: 1280px)

```
Header (title + nav links)
├── Stats Grid (5-col: total, 24h, keys, tokens, error rate)
├── Hourly Chart (24h bar chart, taller)
├── Model Usage Table
├── API Keys (add form + CRUD table)
├── Auth Tokens (add form + generate + CRUD table)
├── Benchmark Models (add form + CRUD table)
└── Footer (auto-refresh timestamp)
```

### Logs Page (`logs.html`, max-width: 1400px)

```
Header (title + nav links)
├── Filters (status dropdown + model text input)
├── Logs Table (timestamp, model, status, key, token, error)
├── Pagination (prev/next buttons + page info)
└── Auto-refresh toggle
```

## 9. Anti-Patterns (NEVER)

- **No border-radius** — zero on everything (only exception: 50% on 6px pulse dot)
- **No box-shadow** — depth through color only
- **No gradients** — solid colors only
- **No hover effects** — except `tr:hover td { background: var(--surface) }` on logs table rows
- **No uppercase text** — all lowercase including section headers
- **No serif or sans-serif fonts** — monospace only
- **No images or icons** — text and unicode only
- **No loading spinners** — text-based indicators
- **No soft/rounded aesthetic** — hard edges, terminal feel
- **No emoji** — never, anywhere

## Quick Reference

### Essential CSS Variables

```css
:root {
  --bg: #000000;
  --surface: #0a0a0a;
  --border: #1a1a1a;
  --green: #00ff41;
  --green-dim: #00ff41;
  --green-muted: #006b1d;
  --green-faint: #002a0a;
  --red: #ff2d2d;
  --red-dim: #661212;
  --text: #00ff41;
  --text-dim: #00ff41;
  --text-muted: #00ff41;
}
```

### Font Import

```css
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap');
```

### Core Pattern

```css
body {
  font-family: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', 'Fira Code', monospace;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  font-size: 13px;
}
```
