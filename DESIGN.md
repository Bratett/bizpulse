# Design System — BizPulse AI

## Product Context
- **What this is:** AI-powered financial management PWA for Ghanaian SMEs
- **Who it's for:** Small business owners currently on paper-based systems — smartphone-first, Accra-based, varying tech literacy
- **Space/industry:** African fintech / SME accounting — peers include Paystack, Flutterwave, Built Accounting, MTN MoMo
- **Project type:** App UI (dashboard + data entry), not a marketing site

## Aesthetic Direction
- **Direction:** Industrial/Utilitarian — function-first, data-dense but readable
- **Decoration level:** Intentional — subtle warmth through background tints and number formatting, not gradients or illustrations
- **Mood:** A trusted accountant's clean desk. Calm, structured, professional. Financial clarity, not payment velocity. The user should feel "someone organized has my back."
- **Reference sites:** Paystack dashboard, Flutterwave dashboard, Mercury banking, Linear (for density inspiration)

## Typography
- **Display/Hero:** Plus Jakarta Sans 700/800 — geometric warmth, professional without being corporate. NOT Inter/Poppins/Montserrat.
- **Body:** DM Sans 400/500 — clean, excellent readability at small sizes, pairs well with Plus Jakarta Sans
- **UI/Labels:** DM Sans 500/600
- **Data/Tables:** JetBrains Mono 400/500/600 — tabular-nums, precise alignment for financial figures
- **Code:** JetBrains Mono
- **Loading:** Google Fonts CDN `https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap`
- **Scale:**
  - `text-xs`: 12px / DM Sans
  - `text-sm`: 14px / DM Sans
  - `text-base`: 16px / DM Sans
  - `text-lg`: 18px / DM Sans
  - `text-xl`: 20px / Plus Jakarta Sans
  - `text-2xl`: 24px / Plus Jakarta Sans
  - `text-3xl`: 30px / Plus Jakarta Sans (mobile hero)
  - `text-4xl`: 36px / Plus Jakarta Sans (desktop hero)
  - `text-5xl`: 48px / JetBrains Mono (Net Income hero number)

## Color
- **Approach:** Restrained + warm — color is rare and meaningful, not decorative
- **Primary:** `#1B4332` — deep forest green. Trust, stability, growth. Used for nav, headings, primary actions.
- **Primary Light:** `#2D6A4F` — lighter green for hover states and secondary emphasis.
- **Accent:** `#D4A017` — kente gold. Ghanaian cultural warmth, prosperity. Used sparingly for badges, highlights, special actions.
- **Accent Light:** `#E6B422` — lighter gold for hover states.
- **Surface:** `#FAFAF5` — warm off-white. NOT cold gray-50. Page background.
- **Surface Raised:** `#FFFFFF` — white. For elevated containers (nav bar, modals).
- **Neutrals (warm grays):**
  - Text Primary: `#1C1917`
  - Text Secondary: `#44403C`
  - Text Muted: `#78716C`
  - Text Faint: `#A8A29E`
  - Border: `#D6D3D1`
  - Border Light: `#E7E5E4`
  - Background Alt: `#F5F5F4`
- **Semantic:**
  - Success: `#166534` / bg: `#F0FDF4`
  - Warning: `#92400E` / bg: `#FFFBEB`
  - Error: `#991B1B` / bg: `#FEF2F2`
  - Info: `#1E40AF` / bg: `#EFF6FF`
- **Dark mode strategy:** Swap surfaces to warm dark (`#1C1917`), raise to `#292524`. Reduce color saturation 10-20%. Green primary becomes `#4ADE80`. Gold stays warm.

## Spacing
- **Base unit:** 4px
- **Density:** Comfortable — not cramped like a trading terminal, not spacious like a marketing site
- **Scale:** 2xs(2px) xs(4px) sm(8px) md(16px) lg(24px) xl(32px) 2xl(48px) 3xl(64px)

## Layout
- **Approach:** Grid-disciplined — strict alignment, predictable structure. Financial data needs consistency above all.
- **Grid:** 12-column on desktop (>1024px), 4-column on tablet (640-1024px), 1-column on mobile (<640px)
- **Max content width:** 1080px
- **Border radius:**
  - Inputs/buttons: `4px` (sm)
  - Containers/cards: `8px` (md) — used sparingly, NOT on every data section
  - Modals/dialogs: `12px` (lg)
  - Avatars/pills: `9999px` (full)
- **Nav:** Fixed sidebar on desktop (224px wide, primary green background, white text, gold accent dot on active item). Bottom tab bar on mobile (4 tabs max, 56px height). Mobile top bar for brand + business name.

## Motion
- **Approach:** Minimal-functional — only transitions that aid comprehension
- **Easing:** enter(ease-out) exit(ease-in) move(ease-in-out)
- **Duration:** micro(50-100ms) short(150-250ms) medium(250-400ms) long(400-700ms)
- **Approved motions:**
  - Number count-up animation on P&L Net Income hero (medium duration)
  - Subtle fade on page transitions (short duration)
  - Skeleton shimmer on loading states (continuous)
  - Toast slide-in from top (short duration)
- **Banned motions:** Bounce, spring, wiggle, confetti, particle effects. This is a financial app.

## Component Vocabulary

### P&L Dashboard (the "aha moment")
- **Net Income Hero:** Centered, large (`text-5xl` JetBrains Mono), colored green/red. Profit indicator arrow + one-sentence summary below. This is the most important element on any screen.
- **Revenue/Expense Sections:** Dense data rows (NOT cards). Account name left-aligned, amount right-aligned in monospace. Section header uppercase, small, muted. Total row with heavy top border.
- **Monthly Trend:** Inline table below data sections. Months as rows, Revenue/Expenses/Net as columns.

### Transaction Entry
- **Form pattern:** Stacked fields, not multi-column. Amount input prominent (largest field). Category as dropdown. Date as native date input.
- **Success feedback:** Green toast from top, 3-second auto-dismiss.

### Empty States
- Warm, not clinical. Include the user's business name if available.
- Primary CTA button. Secondary explanation text.
- Example: "Welcome, Kofi! Add your first transaction to see your business come alive."

### Error States
- Never show fake zeros when data fails to load.
- Show clear error message + retry action.
- Example: "We couldn't load your report. Tap to retry."

### Loading States
- Skeleton loaders matching the actual layout shape. NOT a spinner.

## Accessibility
- **Standard:** WCAG 2.1 AA
- **Contrast:** 4.5:1 minimum for body text, 3:1 for large text (>18px bold)
- **Touch targets:** 44px minimum height/width on all interactive elements
- **Keyboard:** Full tab navigation through all interactive elements. Visible focus ring (`outline: 2px solid var(--primary)`)
- **ARIA:** Landmarks on `<main>`, `<nav>`. `role="alert"` on error/success messages. Labels on all form inputs.
- **Screen readers:** All icons have `aria-label`. Financial amounts include currency in `aria-label` (e.g., "Net income: 2,930 Ghana cedis").

## Localization
- **Currency:** GHS with thousand separators. Format: `GHS 1,234.56`
- **Dates:** DD MMM YYYY (e.g., "15 Mar 2026") for display. ISO YYYY-MM-DD for inputs.
- **Language:** English primary. Prepared for Twi, Ga, Ewe in Phase 2 (NLP service).

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-26 | Initial design system created | Created by /design-consultation based on African fintech research + BizPulse product context |
| 2026-03-26 | Industrial/Utilitarian aesthetic | Financial intelligence ≠ payment app. Calm desk, not busy wallet. |
| 2026-03-26 | Plus Jakarta Sans + DM Sans + JetBrains Mono | Warm geometric display + clean body + precise monospace data. Avoids overused Inter/Poppins. |
| 2026-03-26 | Deep green + kente gold palette | Forest green = trust/growth. Gold = Ghanaian cultural identity, prosperity. |
| 2026-03-26 | No-cards data display | Dense rows with hierarchy instead of card-everything. Matches accountant's desk metaphor. |
| 2026-03-26 | Kente gold accent (RISK) | Unusual for fintech. Culturally distinctive. Instantly recognizable as Ghanaian. |
| 2026-03-26 | Sidebar nav on desktop, bottom tabs on mobile | Sidebar scales to 6-8 items as features grow. Bottom tabs match MTN MoMo pattern users already know. |
