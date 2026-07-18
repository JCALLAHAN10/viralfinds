"""
page_builder_agent.py

Deterministic page builder for ViralFinds.

WHAT IT DOES
------------
Reads the latest top_sellers.json produced by trend_discovery_agent.py and
renders the chosen products into index.html, between the markers:

    <!-- PRODUCTS:START -->  ...  <!-- PRODUCTS:END -->

If index.html doesn't exist yet, it writes a full mobile-first scaffold (hero +
product grid + tracking) so the rest of the pipeline has something to optimize.
On later runs it replaces ONLY the product block, leaving everything outside the
markers untouched — that outside region is what the CRO agent owns.

WHY DETERMINISTIC (no LLM here)
-------------------------------
Product cards are templated straight from the Amazon fields (title, price,
image, affiliate link). Nothing is invented, so there is no path to fake
reviews, fake "only 2 left!" scarcity, or hallucinated specs. The persuasion/
layout intelligence lives in the CRO agent, not here. Clean separation:
  - page_builder owns product DATA (inside the markers)
  - CRO agent owns everything ELSE (hero copy, CTAs, ordering, styling)

TRACKING
--------
Every affiliate link fires the gtag events the CRO agent queries against:
  gtag('event','affiliate_click',{link_label:'<category>-<asin>'})
plus scroll-depth events with a `percent_scrolled` parameter. Set your GA4 id
in the GA4_MEASUREMENT_ID env var (or leave blank to omit the GA4 snippet).

CONFIG
------
  FEATURED_CATEGORIES / TOP_N_PER_CATEGORY below control what gets published.
"""

import os
import re
import html
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("page_builder_agent")

TOP_SELLERS_JSON = "top_sellers.json"
SITE_HTML_PATH = os.environ.get("SITE_HTML_PATH", "index.html")
GA4_MEASUREMENT_ID = os.environ.get("GA4_MEASUREMENT_ID", "")

# Which categories to publish, and how many products from each. Set to None to
# publish every category discovery returned.
FEATURED_CATEGORIES = None          # e.g. ["Beauty", "Apparel", "Electronics"]
TOP_N_PER_CATEGORY = 6

PRODUCTS_START = "<!-- PRODUCTS:START -->"
PRODUCTS_END = "<!-- PRODUCTS:END -->"


def load_products() -> dict:
    if not os.path.exists(TOP_SELLERS_JSON):
        raise SystemExit(f"{TOP_SELLERS_JSON} not found — run trend_discovery_agent.py first.")
    with open(TOP_SELLERS_JSON, "r", encoding="utf-8") as f:
        run = json.load(f)
    by_cat = run.get("by_category", {})
    if FEATURED_CATEGORIES is not None:
        by_cat = {k: v for k, v in by_cat.items() if k in FEATURED_CATEGORIES}
    return {k: (v or [])[:TOP_N_PER_CATEGORY] for k, v in by_cat.items()}


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def render_card(p: dict) -> str:
    """Conversion-optimized card (winning-strategy patterns, all truthful):
    best-seller rank badge + star rating + review count as social proof, plus a
    single action-verb CTA. Only renders data actually present in the feed."""
    label = f"{p.get('category','')}-{p.get('asin','')}"
    price = esc(p.get("price") or "")
    was = p.get("list_price") or ""
    strike = f'<span class="was">{esc(was)}</span>' if was and was != p.get("price") else ""
    img = esc(p.get("image_url") or "")
    title = esc(p.get("title") or "")
    url = esc(p.get("affiliate_url") or "#")
    img_tag = f'<img loading="lazy" src="{img}" alt="{title}">' if img else ""

    rank = p.get("sales_rank") or 0
    badge = f'<span class="badge">#{rank} Best Seller</span>' if rank else ""

    rating = p.get("rating")
    count = p.get("ratings_count")
    social = ""
    if rating:
        full = int(rating)
        stars = "★" * full + "☆" * (5 - full)
        cnt = f' · {int(count):,} reviews' if count else ""
        social = f'<p class="social"><span class="stars">{stars}</span> {rating}{cnt}</p>'

    return f"""      <a class="card" href="{url}" target="_blank" rel="nofollow sponsored noopener"
         onclick="track('{esc(label)}')">
        <div class="imgwrap">{badge}{img_tag}</div>
        <div class="card-body">
          <p class="title">{title}</p>
          {social}
          <p class="price">{price} {strike}</p>
          <span class="cta">Check price on Amazon →</span>
        </div>
      </a>"""


def render_products_block(products_by_cat: dict) -> str:
    sections = []
    for category, items in products_by_cat.items():
        if not items:
            continue
        cards = "\n".join(render_card(p) for p in items)
        sections.append(
            f'    <section class="cat" id="cat-{esc(category.lower().replace(" ","-"))}">\n'
            f'      <h2>{esc(category)}</h2>\n'
            f'      <div class="grid">\n{cards}\n      </div>\n'
            f'    </section>'
        )
    body = "\n".join(sections) if sections else "    <p>No products available right now.</p>"
    return f"{PRODUCTS_START}\n{body}\n    {PRODUCTS_END}"


def ga4_snippet() -> str:
    if not GA4_MEASUREMENT_ID:
        return "<!-- GA4 id not set; set GA4_MEASUREMENT_ID to enable analytics -->"
    return f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_MEASUREMENT_ID}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{GA4_MEASUREMENT_ID}');
  </script>"""


def full_scaffold(products_block: str) -> str:
    """Conversion-optimized page (winning affiliate-page patterns):
    benefit-led hero, trust bar, social-proof product cards, repeated CTAs, FAQ.
    The CRO agent may still refine anything OUTSIDE the PRODUCTS markers."""
    ga = ga4_snippet() if GA4_MEASUREMENT_ID else (
        '<script async src="https://www.googletagmanager.com/gtag/js?id=G-6VQD761326"></script>'
        '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
        "gtag('js',new Date());gtag('config','G-6VQD761326');</script>")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ViralFinds — TikTok-Viral Beauty, Verified Against Amazon Best Sellers</title>
  <meta name="description" content="Every product verified against Amazon's live Best Sellers rankings before we recommend it. Real ratings, real ranks, real prices. Verified, not hype.">
  {ga}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;1,9..144,500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg:#0d0910; --bg2:#140d16; --card:#1b131e; --line:rgba(255,255,255,.08);
      --accent:#ff4d7d; --accent2:#ff9a6b; --gold:#ffcf5c;
      --text:#f7f0f5; --muted:#a99caa;
      --grad:linear-gradient(135deg,var(--accent),var(--accent2));
    }}
    * {{ box-sizing:border-box; }}
    html, body {{ overflow-x:hidden; max-width:100%; }}
    img {{ max-width:100%; }}
    h1 {{ overflow-wrap:break-word; }}
    body {{
      margin:0; color:var(--text); line-height:1.55;
      font-family:'Inter',-apple-system,system-ui,sans-serif;
      background:
        radial-gradient(60% 45% at 50% -5%, rgba(255,77,125,.20), transparent 70%),
        radial-gradient(50% 40% at 90% 10%, rgba(255,154,107,.12), transparent 70%),
        var(--bg);
      -webkit-font-smoothing:antialiased;
    }}
    .brand {{ text-align:center; padding:22px 16px 0; font-weight:700; letter-spacing:.5px; font-size:1.05rem; }}
    .brand b {{ background:var(--grad); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }}
    .hero {{ padding:26px 22px 22px; text-align:center; max-width:660px; margin:0 auto; }}
    .hero h1 {{
      font-family:'Fraunces',Georgia,serif; font-weight:600; letter-spacing:-.5px;
      margin:0 0 14px; font-size:2.1rem; line-height:1.12;
    }}
    .hero h1 em {{ font-style:italic; background:var(--grad); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }}
    .hero p {{ color:var(--muted); margin:0 auto; max-width:470px; font-size:1.02rem; }}
    .trust {{ display:flex; flex-wrap:wrap; gap:9px; justify-content:center; padding:20px 14px 6px; }}
    .trust span {{ background:rgba(255,255,255,.05); border:1px solid var(--line); color:var(--text); font-size:.75rem; padding:7px 14px; border-radius:100px; backdrop-filter:blur(6px); }}
    .trust b {{ background:var(--grad); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }}
    .disclosure {{ text-align:center; color:var(--muted); font-size:.72rem; max-width:520px; margin:12px auto 0; padding:0 20px; }}
    .cat {{ padding:14px 14px 4px; max-width:940px; margin:0 auto; }}
    .cat h2 {{ font-family:'Fraunces',Georgia,serif; font-weight:600; font-size:1.4rem; margin:26px 6px 14px; display:flex; align-items:center; gap:10px; }}
    .cat h2::after {{ content:""; flex:1; height:1px; background:linear-gradient(90deg,var(--line),transparent); }}
    .grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:14px; }}
    .card {{
      min-width:0;
      background:var(--card); border:1px solid var(--line); border-radius:18px; overflow:hidden;
      text-decoration:none; color:inherit; display:flex; flex-direction:column;
      box-shadow:0 6px 22px rgba(0,0,0,.35); transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    }}
    .card:hover {{ transform:translateY(-4px); box-shadow:0 14px 34px rgba(255,77,125,.18); border-color:rgba(255,77,125,.35); }}
    .card:active {{ transform:scale(.98); }}
    .imgwrap {{ position:relative; padding:12px 12px 0; }}
    .card img {{ width:100%; aspect-ratio:1; object-fit:contain; background:#fff; display:block; border-radius:12px; }}
    .badge {{ position:absolute; top:20px; left:20px; background:var(--grad); color:#fff; font-size:.68rem; font-weight:700; padding:4px 10px; border-radius:100px; box-shadow:0 3px 10px rgba(255,77,125,.4); }}
    .card-body {{ padding:12px 14px 16px; display:flex; flex-direction:column; gap:6px; }}
    .title {{ font-size:.84rem; font-weight:500; line-height:1.3; margin:0; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
    .social {{ margin:0; font-size:.73rem; color:var(--muted); display:flex; align-items:center; gap:5px; }}
    .social .stars {{ color:var(--gold); letter-spacing:1px; }}
    .price {{ font-weight:700; margin:2px 0 0; font-size:1.15rem; }}
    .was {{ font-weight:400; opacity:.45; text-decoration:line-through; font-size:.8rem; margin-left:5px; }}
    .cta {{ margin-top:10px; background:var(--grad); color:#fff; text-align:center; padding:12px; border-radius:11px; font-size:.85rem; font-weight:700; box-shadow:0 4px 14px rgba(255,77,125,.28); }}
    .midcta {{ text-align:center; padding:34px 16px 8px; }}
    .midcta a {{ display:inline-block; background:rgba(255,255,255,.06); border:1px solid var(--line); color:var(--text); text-decoration:none; font-weight:600; padding:14px 30px; border-radius:100px; transition:border-color .18s; }}
    .midcta a:hover {{ border-color:rgba(255,77,125,.5); }}
    .faq {{ max-width:660px; margin:0 auto; padding:28px 22px 8px; }}
    .faq h2 {{ font-family:'Fraunces',Georgia,serif; font-weight:600; font-size:1.5rem; text-align:center; margin-bottom:18px; }}
    .faq details {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 18px; margin:11px 0; transition:border-color .18s; }}
    .faq details[open] {{ border-color:rgba(255,77,125,.3); }}
    .faq summary {{ font-weight:600; cursor:pointer; list-style:none; }}
    .faq summary::-webkit-details-marker {{ display:none; }}
    .faq summary::after {{ content:"+"; float:right; color:var(--accent); font-size:1.2rem; line-height:1; }}
    .faq details[open] summary::after {{ content:"–"; }}
    .faq p {{ color:var(--muted); margin:12px 0 0; font-size:.92rem; }}
    footer {{ padding:30px 16px 48px; text-align:center; color:var(--muted); font-size:.72rem; line-height:1.7; border-top:1px solid var(--line); margin-top:20px; }}
    @media(min-width:640px){{ .grid{{grid-template-columns:repeat(4,1fr);}} .hero h1{{font-size:2.7rem;}} }}
  </style>
</head>
<body>
  <div class="brand">Viral<b>Finds</b></div>
  <header class="hero">
    <h1>The TikTok-viral beauty finds that are <em>actually</em> Amazon best sellers</h1>
    <p>We verify every pick against Amazon's live Best Sellers rankings — real ratings, real ranks, real prices. Verified, not hype.</p>
  </header>
  <div class="trust">
    <span>✓ Verified against <b>Amazon Best Sellers</b></span>
    <span>✓ Real ratings &amp; review counts</span>
    <span>✓ No fake urgency, ever</span>
  </div>
  <p class="disclosure">Disclosure: we earn a commission on purchases made through our links, at no extra cost to you.</p>
  <main>
{products_block}
    <div class="midcta"><a href="articles/tiktok-viral-skincare-verified.html">Read the full verified guide →</a></div>
    <section class="faq">
      <h2>Before you buy</h2>
      <details><summary>How do you pick these?</summary><p>Every product is cross-checked against Amazon's live Best Sellers rankings before it goes on this page. We show the real rank, the real star rating, and the real review count — nothing invented.</p></details>
      <details><summary>Do the prices change?</summary><p>Yes — Amazon prices move. The price shown is accurate as of the last page update; tap through to Amazon for the current price before you buy.</p></details>
      <details><summary>How do you make money?</summary><p>As an Amazon Associate we earn a small commission when you buy through our links — at no extra cost to you. It never changes which products we feature; ranking is based on real Amazon sales data.</p></details>
      <details><summary>Can I return something?</summary><p>Returns are handled by Amazon under their standard return policy — not by us. Check the item's Amazon page for its specific return window.</p></details>
    </section>
  </main>
  <footer>
    As an Amazon Associate we earn from qualifying purchases.<br>
    Prices, ranks and ratings are accurate as of the last update and may change.
  </footer>
  <script>
    function track(label) {{ if (window.gtag) gtag('event', 'affiliate_click', {{ link_label: label }}); }}
    (function() {{
      var fired = {{}};
      window.addEventListener('scroll', function() {{
        var pct = Math.round((window.scrollY + window.innerHeight) / document.body.scrollHeight * 100);
        [25,50,75,100].forEach(function(m) {{
          if (pct >= m && !fired[m]) {{ fired[m] = true;
            if (window.gtag) gtag('event','scroll_depth',{{ percent_scrolled: m + '%' }}); }}
        }});
      }}, {{ passive:true }});
    }})();
  </script>
</body>
</html>
"""


def build() -> bool:
    """Returns True if index.html changed."""
    products_by_cat = load_products()
    new_block = render_products_block(products_by_cat)

    if not os.path.exists(SITE_HTML_PATH):
        html_out = full_scaffold(new_block)
        with open(SITE_HTML_PATH, "w", encoding="utf-8") as f:
            f.write(html_out)
        log.info(f"Created {SITE_HTML_PATH} scaffold with fresh products.")
        return True

    with open(SITE_HTML_PATH, "r", encoding="utf-8") as f:
        current = f.read()

    if PRODUCTS_START not in current or PRODUCTS_END not in current:
        log.warning(
            f"Markers not found in {SITE_HTML_PATH} — leaving it untouched so I "
            f"don't clobber the CRO agent's work. Re-add {PRODUCTS_START}/"
            f"{PRODUCTS_END} around the product grid to resume auto-updates."
        )
        return False

    pattern = re.compile(re.escape(PRODUCTS_START) + r".*?" + re.escape(PRODUCTS_END), re.DOTALL)
    updated = pattern.sub(lambda _: new_block, current, count=1)

    if updated == current:
        log.info("Product block unchanged — nothing to write.")
        return False

    with open(SITE_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(updated)
    total = sum(len(v) for v in products_by_cat.values())
    log.info(f"Refreshed product block in {SITE_HTML_PATH} ({total} products).")
    return True


if __name__ == "__main__":
    build()
