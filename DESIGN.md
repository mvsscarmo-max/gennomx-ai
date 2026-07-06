---
name: GennomX AI
description: Infraestrutura de dados biomédicos e inteligência competitiva para life sciences — dashboard operacional, não gerador de relatórios.
colors:
  brand-rose: "#F2829B"
  brand-rose-light: "#F9B8C9"
  brand-rose-dark: "#D4607A"
  surface-default: "#FFFFFF"
  surface-subtle: "#F8FAFC"
  surface-muted: "#F1F5F9"
  slate-50: "#F8FAFC"
  slate-100: "#F1F5F9"
  slate-200: "#E2E8F0"
  slate-300: "#CBD5E1"
  slate-400: "#94A3B8"
  slate-500: "#64748B"
  slate-600: "#475569"
  slate-700: "#334155"
  slate-800: "#1E293B"
  slate-900: "#0F172A"
  slate-950: "#020617"
  success: "#10B981"
  success-light: "#D1FAE5"
  warning: "#F59E0B"
  warning-light: "#FEF3C7"
  danger: "#EF4444"
  danger-light: "#FEE2E2"
  info: "#3B82F6"
  info-light: "#DBEAFE"
typography:
  display:
    fontFamily: "Montserrat, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "normal"
  title:
    fontFamily: "Montserrat, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "normal"
  body:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.08em"
rounded:
  badge: "6px"
  card: "12px"
  control: "8px"
spacing:
  sidebar-width: "240px"
  header-height: "56px"
components:
  button-primary:
    backgroundColor: "{colors.brand-rose}"
    textColor: "#FFFFFF"
    rounded: "{rounded.control}"
    padding: "8px 16px"
  button-primary-hover:
    backgroundColor: "{colors.brand-rose-dark}"
    rounded: "{rounded.control}"
    padding: "8px 16px"
  button-secondary:
    backgroundColor: "{colors.surface-default}"
    textColor: "{colors.slate-700}"
    rounded: "{rounded.control}"
    padding: "8px 16px"
  card-default:
    backgroundColor: "{colors.surface-default}"
    textColor: "{colors.slate-800}"
    rounded: "{rounded.card}"
    padding: "20px"
  nav-item-active:
    backgroundColor: "{colors.brand-rose}"
    textColor: "{colors.brand-rose-dark}"
    rounded: "{rounded.control}"
    padding: "8px 12px"
---

# Design System: GennomX AI

## 1. Overview

**Creative North Star: "The Clinical Ledger"**

GennomX AI's dashboard reads as a rigorous ledger, not a marketing surface: dense relational data (assets, trials, indications, targets, companies) laid out with the precision of a scientific record book, where a single deliberate accent marks what deserves attention. The base is a cool, institutional slate-and-white foundation — the visual equivalent of a clean lab notebook — because this data underwrites real investment and R&D decisions, and the interface must earn trust through rigor before it earns attention through style.

Against that quiet foundation, **brand-rose** (`#F2829B`) is used as a rare, deliberate mark: primary actions, the active nav item, and semantic emphasis in badges. It is not a brand-wide wash of color; it is a pointer. This system explicitly rejects generic AI-SaaS dashboard chrome — identical card grids, gradient text, uppercase eyebrow labels, hero-metric templates, decorative glassmorphism — and rejects the visual language of Gosset AI or flashy fintech/crypto dashboards (neon, bright gold glow, speculative-market energy). Confidence here comes from restraint and precision, not decoration.

**Key Characteristics:**
- Slate-institutional base (`surface-subtle` body, white cards) with one rose accent used sparingly
- Near-flat surfaces at rest; elevation responds only to interaction
- Montserrat carries structural weight (headings, stat values); Inter carries density (body, tables, labels)
- Two audiences (external analytical screens, internal ops/admin screens) share one system, differentiated by content, not by re-skinning

## 2. Colors

The palette is restrained: a cool institutional neutral scale carries the majority of every screen, with one warm accent reserved for emphasis.

### Primary
- **Rose Clínico** (`#F2829B`): the single accent. Used on primary buttons, the active sidebar item, focus rings, and rose-tinted badges. Deliberately rare — it marks the action or state that matters on a given screen, never a decorative wash.
- **Rose Clínico Dark** (`#D4607A`): hover/active state for the primary accent, and the text color paired with rose-tinted badge backgrounds.
- **Rose Clínico Light** (`#F9B8C9`): lightest step of the accent ramp, reserved for the softest tint use (e.g. subtle background fills at low opacity).

### Neutral
- **Institutional White** (`#FFFFFF`): card and control surface (`surface-default` / `surface-elevated`).
- **Institutional Mist** (`#F8FAFC`): page background (`surface-subtle`, = `slate-50`).
- **Institutional Fog** (`#F1F5F9`): muted fills, hover backgrounds on ghost elements (`surface-muted` / `slate-100`).
- **Ledger Ink** (`#0F172A` / `slate-900`): heading and highest-emphasis text.
- **Ledger Graphite** (`#1E293B` / `slate-800`): default body text color.
- **Ledger Slate** (`#334155`–`#64748B` / `slate-700`–`slate-500`): secondary text, table cells, labels.
- **Ledger Mist Border** (`#E2E8F0` / `slate-200`): default borders and dividers.

### Semantic
- **Success** (`#10B981` on `#D1FAE5`): positive status (e.g. active sources, passed checks).
- **Warning** (`#F59E0B` on `#FEF3C7`): attention-needed status (e.g. stale ingestion).
- **Danger** (`#EF4444` on `#FEE2E2`): failure/error status (e.g. failed jobs, security flags).
- **Info** (`#3B82F6` on `#DBEAFE`): neutral informational status.

### Named Rules
**The One Accent Rule.** Brand-rose appears on ≤10% of any given screen — one primary action, one active nav state, a handful of badges. If a screen has more than one saturated rose element competing for attention, it's wrong.

**The Semantic-Only Saturation Rule.** Outside of brand-rose, saturated color (success/warning/danger/info) is reserved strictly for status communication — never for decoration or emphasis unrelated to state.

## 3. Typography

**Display Font:** Montserrat (with system-ui, sans-serif fallback)
**Body Font:** Inter (with system-ui, sans-serif fallback)

**Character:** A structural geometric sans (Montserrat) for headings and stat values paired with a neutral, highly-legible humanist sans (Inter) for body and table density — the contrast reads as "structured record" (Montserrat) annotated with "working notes" (Inter), reinforcing the ledger metaphor without introducing a second decorative voice.

### Hierarchy
- **Display / Page Title** (Montserrat, 700, `1.25rem`/20px, line-height 1.2): page-level titles (`.page-title`).
- **Title / Section Title** (Montserrat, 600, `1rem`/16px, line-height 1.3): section and card headers (`.section-title`), and stat values at `1.5rem`/24px tabular-nums for numeric alignment.
- **Body** (Inter, 400, `0.875rem`/14px, line-height 1.5): default text, table cells, form inputs. Cap prose blocks (detail-page descriptions) at 65–75ch.
- **Label** (Inter, 600, `0.75rem`/12px, letter-spacing 0.08em, uppercase): table headers, nav group labels, stat labels.

### Named Rules
**The No-Third-Voice Rule.** Only Montserrat and Inter exist in this system. Never introduce a third family (mono, script, serif) for a one-off component; if a technical/tabular need arises, use Inter's tabular-nums feature instead.

## 4. Elevation

Surfaces are near-flat at rest. The default card carries only a whisper of shadow (`0 1px 3px 0 rgb(0 0 0 / 0.08)`) plus a near-invisible border (`slate-200` at 60% opacity) — elevation is not the primary way this system communicates hierarchy; spacing, borders, and the rose accent do that work instead. Shadow exists to respond to interaction, not to sit decoratively under every surface.

### Shadow Vocabulary
- **card** (`box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.08), 0 1px 2px -1px rgb(0 0 0 / 0.06)`): resting state for every card, stat tile, and panel.
- **card-hover** (`box-shadow: 0 4px 12px 0 rgb(0 0 0 / 0.10), 0 2px 4px -2px rgb(0 0 0 / 0.08)`): hover state for interactive cards (`.card-hover`), transitioning over 150ms.
- **nav** (`box-shadow: 1px 0 0 0 #E2E8F0`): the sidebar's right-edge separation — a hairline, not a drop shadow.

### Named Rules
**The Flat-at-Rest Rule.** No card, panel, or stat tile carries a resting shadow heavier than `card`. Heavier shadows appear only as a direct response to hover/focus, never as a permanent decoration.

## 5. Components

Every component favors quiet precision: nothing calls attention to itself beyond what the accent is reserved for.

### Buttons
- **Shape:** rounded corners (`8px`, Tailwind `rounded-lg`), consistent across primary/secondary/ghost.
- **Primary:** `brand-rose` background, white text, `8px 16px` padding, hover/active to `brand-rose-dark`, focus ring in `brand-rose` with 2px offset.
- **Secondary:** white background, `slate-200` border, `slate-700` text; hover moves to `slate-50` background with `slate-300` border.
- **Ghost:** transparent background, `slate-600` text; hover fills `slate-100`, active `slate-200`.

### Badges
- **Shape:** `6px` radius, `2.5px/0.5px` (px-2.5 py-0.5) padding, `12px`/text-xs, medium weight.
- **Rose variant:** `brand-rose` at 10% opacity background, `brand-rose-dark` text — used for premium/notable status, sparingly.
- **Semantic variants:** success/warning/danger/info each pair a light tint background with its saturated text color, reserved strictly for status meaning (see Named Rules, Colors).

### Cards / Containers
- **Corner Style:** `12px` radius (`rounded-card`).
- **Background:** white (`surface-default`) on a `surface-subtle` (`#F8FAFC`) page background — the card-vs-page contrast is the only "elevation" most screens need.
- **Shadow Strategy:** see Elevation — `card` at rest, `card-hover` only on interactive cards.
- **Border:** `slate-200` at 60% opacity, effectively a hairline.
- **Internal Padding:** `20px` (stat cards use `p-5`).

### Inputs / Fields
- **Style:** white background, `slate-200` border, `8px` radius (`rounded-lg`), `14px` text.
- **Focus:** border shifts to `brand-rose`, focus ring `brand-rose` at 30% opacity — a controlled, low-intensity glow rather than a hard outline.
- **Placeholder:** `slate-400` — must be checked against the 4.5:1 contrast floor on white, not left at default gray.

### Navigation (Sidebar)
- **Style:** fixed `240px` white sidebar, `nav` hairline shadow on the right edge, grouped into labeled sections ("Ciência" / "Operações") with `10px` uppercase tracked-wide group labels.
- **Item default:** `slate-600` text, hover fills `slate-100` and darkens text to `slate-900`.
- **Item active:** `brand-rose` at 10% opacity background, `brand-rose-dark` text — the single most visible use of the accent on any screen, which is why it must never be duplicated elsewhere on the same view.
- **Mobile treatment:** not yet implemented — the sidebar assumes a persistent desktop-width viewport; this is a real gap for an analytical tool that may be checked on tablets.

### Stat Tiles (Signature Component)
Card variant (`p-5`, flex column) presenting one numeric value in Montserrat 700 tabular-nums at `1.5rem`, a `slate-500` label beneath, and an optional delta indicator. This is the primary "at a glance" component on the Overview screen and should remain the only place raw metrics appear large — resist turning every screen into a stat-tile grid (the hero-metric SaaS cliché this system explicitly rejects).

## 6. Do's and Don'ts

### Do:
- **Do** keep brand-rose to ≤10% of any screen's surface — one primary action, one active nav state, a few badges (The One Accent Rule).
- **Do** treat cards as near-flat at rest (`card` shadow only); reserve `card-hover` for genuinely interactive surfaces.
- **Do** pair Montserrat (structure) with Inter (density) exclusively; never introduce a third typeface.
- **Do** verify placeholder and muted-label text (`slate-400`/`slate-500` on white or `surface-subtle`) against the 4.5:1 contrast floor — long analytical sessions make marginal contrast a real fatigue problem, not just a technicality.
- **Do** use semantic colors (success/warning/danger/info) strictly for status, never for decoration.
- **Do** keep the same design language across external analytical screens (companies/trials/assets) and internal ops screens (jobs, MCP logs, governance) — one system, two audiences.

### Don't:
- **Don't** use generic AI-SaaS dashboard clichés: identical card grids, gradient text, tiny uppercase tracked eyebrows above every section, hero-metric templates, decorative glassmorphism, side-stripe borders, or over-rounded (24px+) cards.
- **Don't** style toward Gosset AI or any competitor's specific look — it's a category benchmark only, never a visual reference.
- **Don't** reach for flashy fintech/crypto visual energy (neon glow, bright gold shine, speculative-market motion) anywhere in the product.
- **Don't** add a second saturated accent color competing with brand-rose; if something needs emphasis beyond status, it competes for the same 10% budget.
- **Don't** stack a heavier shadow under a resting card "for depth" — depth in this system comes from the white-card-on-`surface-subtle` contrast, not from shadow weight.
- **Don't** ship a stat-tile grid as the default answer for a new screen; it's the signature component for Overview, not a template to repeat everywhere.
