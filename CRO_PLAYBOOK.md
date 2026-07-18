# CRO + Aesthetic Playbook — shared blueprint for BOTH lanes

The winning-page structure both trendtrackr and viralfinds implement, from CRO research 2026-07-18. Every tactic is truthful (survives a reader clicking through and finding reality matches the page). Manipulative tactics are banned (§9). Live reference implementation: trendtrackr `articles/best-viral-water-bottles-tumblers.html` + the shared classes in `css/style.css` (quick-picks/qp-grid/qp-card, badge/badge--overall/value/budget/premium, compare-wrap/table.compare, product/rank/rating/verdict, how-we-picked, btn/btn--block/btn--sm, cta-note, toc, disclosure-inline).

## 1. Above-the-fold (verdict-first, not intro-first)
H1 (category + year + count) → one-sentence FTC disclosure BEFORE any affiliate link → byline + "Updated [month year]" → **Quick Picks verdict box** (2–4 award-labeled winners, each: badge + name + one-line reason + "Check Price on Amazon" button) → jump-link TOC. Intro ≤2 sentences above Quick Picks; "How we picked" goes below.

## 2. Per-product block (identical template, in order)
Numbered rank + inline award badge → H3 name → ★ rating + review count verbatim (real number, never round to 5.0) → one-line "who it's for" verdict → pros/cons (3–4 pros, 1–2 HONEST cons — cons build trust) → price context ("Check current price", never a hardcoded number) → full-width primary CTA → one line doubt-remover microcopy.

## 3. CTA buttons
3–4 word benefit copy — "Check Price on Amazon" (never "Buy Now"). ONE exclusive high-contrast accent color for CTAs only (we use amber `--cta`). Full-width mobile, min 44–48px tap target. One primary button per block; repeat down the page + in Quick Picks. All affiliate links `rel="nofollow sponsored noopener" target="_blank"`.

## 4. Comparison table
Below Quick Picks. Columns: Product · Award · ★ rating+count · "Best for…" · CTA in every row. Horizontal-scroll wrapper on mobile (`.compare-wrap`).

## 5. Trust signals (all truthful)
Real ratings + counts verbatim; "How we picked" method block; freshness stamp; honest cons; FTC disclosure above fold in plain language; Best-Seller-Rank claims only if currently true + dated. No mismatched checkout/SSL/money-back badges.

## 6. Scannability
Ranked numbered blocks, consistent rhythm, generous whitespace, TOC jump links, short scannable paragraphs.

## 7. Mobile & speed
LCP ≤2.5s / INP ≤200ms / CLS ≤0.1. Every img explicit width/height; `loading="lazy"` below fold; `fetchpriority="high"` on hero; WebP/AVIF + srcset; `font-display:swap`.

## 8. Priority order
1) Quick Picks + CTA buttons. 2) Fix CTAs. 3) Image dims + lazy + WebP. 4) Standardize product block. 5) Disclosure above fold. 6) Ratings+counts everywhere. 7) Comparison table. 8) How-we-picked + freshness + cons. 9) TOC. 10) Sticky mobile CTA.

## 9. Do NOT use (banned — brand + FTC)
Fake/resetting countdown timers; fake stock/scarcity; fabricated urgency; invented discounts / fake "was" prices; fake/AI/altered reviews or inflated ratings (FTC 2024 rule); rounding real ratings to 5.0; confirmshaming / disguised ads / trick nav; mismatched trust badges.
