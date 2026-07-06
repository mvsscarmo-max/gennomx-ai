# Product

## Register

product

## Users

Primary: B2B life-sciences decision-makers — investors, biotech/pharma corporate development, and consultancies — performing competitive intelligence, due diligence, and asset/trial/target/company analysis to inform investment and R&D decisions. Secondary: internal operations/admin team (data engineers, admins) monitoring ingestion sources, jobs, MCP query logs, and data governance/security.

Context: long analytical sessions scanning dense, relational biomedical data (drug assets, companies, indications, targets, clinical trials, evidence with source traceability). The primary task varies by screen — browsing/filtering a catalog, drilling into a detail page, or (for admins) monitoring pipeline health and access.

## Product Purpose

GennomX AI is proprietary biomedical and competitive-intelligence data infrastructure for life sciences. The dashboard is the operational interface to query, monitor, and govern that data — it is explicitly not a chatbot or report generator; analysis and report generation happen in external host models via MCP. Success looks like: users trust the data enough to base real investment/strategic decisions on it, can navigate dense relational data quickly, and admins can verify data provenance and pipeline health at a glance.

## Brand Personality

Elegant, premium, distinctive — deliberately not "generic AI SaaS." Sophisticated and clean, projecting institutional trust (this is data people will bet money on), while carrying a confident, specific point of view rather than templated dashboard chrome. A "slate institucional" foundation with rose/gold as a considered, sparingly-used premium accent (per docs/07_DASHBOARD_UX.md).

## Anti-references

- Generic AI-generated SaaS dashboard clichés: identical card grids, gradient text, tiny uppercase tracked eyebrows, hero-metric templates, decorative glassmorphism, over-rounded cards, side-stripe borders.
- Gosset AI — used internally only as a conceptual/category benchmark (life-sciences market intelligence), explicitly not a visual style to imitate.
- Flashy fintech/crypto aesthetics (neon, bright gold glow, speculative-market visual energy).

## Design Principles

1. **Confident specificity over templated dashboard chrome** — every screen should feel deliberately designed for biomedical data work, not assembled from generic admin-template parts.
2. **Density with clarity** — tables and detail pages carry heavy relational data; hierarchy and spacing rhythm must keep it scannable during long sessions, not overwhelming.
3. **Institutional trust as the baseline** — this data drives real investment decisions, so polish should read as rigor and provenance, never as decoration for its own sake.
4. **One deliberate accent, used sparingly** — rose/gold marks emphasis and premium moments; it never floods the interface.
5. **Two audiences, one system** — external analytical screens (companies/trials/assets) and internal ops/admin screens (jobs, MCP logs, governance) share one coherent design language.

## Accessibility & Inclusion

No formal WCAG certification required, but contrast and visual fatigue are first-class constraints given long analytical sessions scanning dense tables — body and data-table text should clear comfortable contrast minimums (not just bare AA pass/fail), and saturated colors should be avoided where they would tire the eye over hours of use. Reduced-motion support is expected wherever motion is introduced.
