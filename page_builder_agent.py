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
    label = f"{p.get('category','')}-{p.get('asin','')}"
    price = esc(p.get("price") or "")
    was = p.get("list_price") or ""
    strike = f'<span class="was">{esc(was)}</span>' if was and was != p.get("price") else ""
    img = esc(p.get("image_url") or "")
    title = esc(p.get("title") or "")
    url = esc(p.get("affiliate_url") or "#")
    img_tag = f'<img loading="lazy" src="{img}" alt="{title}">' if img else ""
    return f"""      <a class="card" href="{url}" target="_blank" rel="nofollow sponsored noopener"
         onclick="track('{esc(label)}')">
        {img_tag}
        <div class="card-body">
          <p class="title">{title}</p>
          <p class="price">{price} {strike}</p>
          <span class="cta">View on Amazon →</span>
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
    """Initial page. The CRO agent may freely rewrite anything OUTSIDE the
    PRODUCTS markers (hero, CTA copy, ordering, styles)."""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ViralFinds — trending picks</title>
  {ga4_snippet()}
  <style>
    :root {{ --bg:#0f0f14; --card:#1b1b24; --accent:#ff3b6b; --text:#f4f4f8; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,system-ui,sans-serif; background:var(--bg); color:var(--text); }}
    header {{ padding:28px 16px 8px; text-align:center; }}
    header h1 {{ margin:0; font-size:1.6rem; }}
    header p {{ opacity:.7; margin:.4rem 0 0; }}
    .cat {{ padding:12px 12px 4px; }}
    .cat h2 {{ font-size:1.15rem; margin:16px 4px 8px; }}
    .grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:12px; }}
    .card {{ background:var(--card); border-radius:14px; overflow:hidden; text-decoration:none; color:inherit; display:flex; flex-direction:column; }}
    .card img {{ width:100%; aspect-ratio:1; object-fit:contain; background:#fff; }}
    .card-body {{ padding:10px 12px 14px; display:flex; flex-direction:column; gap:6px; }}
    .title {{ font-size:.82rem; line-height:1.25; margin:0; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
    .price {{ font-weight:700; margin:0; }}
    .was {{ font-weight:400; opacity:.5; text-decoration:line-through; font-size:.8rem; margin-left:4px; }}
    .cta {{ margin-top:auto; background:var(--accent); color:#fff; text-align:center; padding:9px; border-radius:9px; font-size:.85rem; font-weight:600; }}
    footer {{ padding:24px 16px 40px; text-align:center; opacity:.55; font-size:.72rem; }}
    @media(min-width:640px){{ .grid{{grid-template-columns:repeat(4,1fr);}} }}
  </style>
</head>
<body>
  <header>
    <h1>ViralFinds</h1>
    <p>The stuff blowing up right now — updated daily.</p>
  </header>
  <main>
{products_block}
  </main>
  <footer>
    As an Amazon Associate we earn from qualifying purchases. Prices and availability are accurate as of the time shown and may change.
  </footer>
  <script>
    // Fires the affiliate-click event the CRO agent attributes per product.
    function track(label) {{
      if (window.gtag) gtag('event', 'affiliate_click', {{ link_label: label }});
    }}
    // Scroll-depth beacons (25/50/75/100%) for the CRO agent's scroll metric.
    (function() {{
      var fired = {{}};
      window.addEventListener('scroll', function() {{
        var pct = Math.round((window.scrollY + window.innerHeight) / document.body.scrollHeight * 100);
        [25,50,75,100].forEach(function(m) {{
          if (pct >= m && !fired[m]) {{ fired[m] = true;
            if (window.gtag) gtag('event','scroll','depth',{{ percent_scrolled: m + '%' }}); }}
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
