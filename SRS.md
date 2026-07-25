# System Requirements Specification (SRS)
## Akriti Diagnostics Center - Lab Management System

...

### 6.1 User Interface & Design System (Redesigned)
The system employs the "Clinical Workbench" design language, prioritizing clinical precision, quiet confidence, trustworthiness, and care. 

#### 6.1.1 Aesthetic Philosophy
- **Concept:** A sterile, precise, and highly functional clinical environment, rejecting generic SaaS minimal dashboards.
- **Vibe:** Expensive, trustworthy, and precision-crafted.
- **Lighting / Dark Mode:** Designed to mimic a "radiology reading room" aesthetic in dark mode.

#### 6.1.2 Color Palette (H&E Stains Inspired)
- **Primary (Navy):** `#0a192f` (Inspired by Hematoxylin - deep nuclear blue). Used for primary actions, headers, and emphasis.
- **Primary Tint:** `#e6f1ff` (Light background for primary contrast).
- **Danger (Rose):** `#C0392B` (Inspired by Eosin - vibrant pink/red). Used exclusively for critical alerts and abnormal flags.
- **Backgrounds:** `var(--color-bg)` is used for solid, opaque layered surfaces (no glassmorphism).

#### 6.1.3 Typography
- **Display:** `Public Sans` - Used for primary headings, dashboard metrics, and module titles.
- **Body:** `Inter` (or system UI fonts) - Used for dense data, descriptions, and standard text.
- **Clinical Data:** `IBM Plex Mono` - Applied to patient IDs, clinical values, decimals, and dates to ensure strict vertical alignment (tabular lining).

#### 6.1.4 UI Components & Layout
- **Containers:** Solid fills, high-contrast borders (1px solid), and crisp shadows. Border radius is tight (`var(--radius-md)` / `var(--radius-lg)`).
- **Dashboard Stats:** Rendered as a `Clinical Ledger Grid` (tabular layout with tight padding and monospaced values) rather than floating cards.
- **Signature Element (Clinical Range Visualizer):** Lab results and report parameter entries must utilize a bullet-chart-style visualizer to plot the patient's value against the reference range (normal zone, high/low markers) in real-time, enforcing the "clinical precision" theme.

#### 6.1.5 Interactivity & Motion
- Fast, snappy, and restrained. Transitions are set to `0.15s` (fast) or `0.2s` (smooth). Over-animation is avoided to maintain a serious tool aesthetic. Keyboard focus rings are prominent and colored with the Primary Navy.

...
