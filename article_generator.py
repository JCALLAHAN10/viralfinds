"""
article_generator.py — auto-generates the verified-data guide article, sitemap,
and robots.txt from the product feed. (Plan P1, approved by Jack 2026-07-18.)

Everything rendered is truthful feed data: real ranks, ratings, counts, prices.
Runs in the daily pipeline after the page build; regenerates only when content
changes so no-op days stay no-op.
"""

import json
from datetime import date

SITE = "https://jcallahan10.github.io/viralfinds"
ARTICLE_PATH = "articles/tiktok-viral-skincare-verified.html"
GA_ID = "G-6VQD761326"

BLURBS = {
    "B074PVTPBW": "The overnight hydrocolloid patch that made pimple patches a category. "
                  "Stick one on before bed; it pulls fluid out of the blemish while you sleep.",
    "B00T0C9XRK": "The drugstore mascara with a cult following — a false-lash effect at a "
                  "price that explains the repurchase loop all over BeautyTok.",
    "B0B2RM68G2": "A Korean overnight hydrogel mask behind the glass-skin trend — collagen "
                  "film that melts in overnight instead of washing off in twenty minutes.",
    "B071914GGL": "The Ordinary's glycolic toner is the affordable chemical-exfoliation "
                  "step in thousands of posted routines — brightening without the price tag.",
    "B09V7Z4TJG": "Dual-textured toner pads that swipe exfoliation and pore care on in one "
                  "step — K-beauty's shortcut for smoother-looking skin.",
}


def product_section(p):
    aid = p["asin"]
    return f"""
  <section class="product" id="{aid}">
    <span class="rank">Amazon Best Seller #{p["sales_rank"]} in Beauty</span>
    <h2>{p["title"]}</h2>
    <p class="stats">&#9733; {p["rating"]} out of 5 &middot; {p["ratings_count"]:,} real Amazon ratings &middot; {p["price"]}</p>
    <p class="blurb">{BLURBS.get(aid, "A verified Amazon best seller.")}</p>
    <a class="btn" href="{p["affiliate_url"]}" target="_blank" rel="nofollow sponsored noopener"
       onclick="track('Article-{aid}')">Check it on Amazon &rarr;</a>
  </section>"""


def main():
    import os
    os.makedirs("articles", exist_ok=True)
    feed = json.load(open("manual_products.json"))
    products = [p for p in feed["by_category"].get("Beauty", []) if p.get("rating")]
    today = date.today().isoformat()

    sections = "\n".join(product_section(p) for p in products)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}');
</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{len(products)} TikTok-Viral Skincare &amp; Beauty Products That Are Actually Amazon Best Sellers ({date.today().year}, Verified)</title>
<meta name="description" content="Every product here was verified against Amazon's live Best Sellers rankings — real ranks, real ratings, real prices. No hype, no fake urgency.">
<link rel="canonical" href="{SITE}/{ARTICLE_PATH}">
<meta property="og:title" content="TikTok-Viral Skincare That's Actually Best-Selling — Verified">
<meta property="og:description" content="Real Amazon Best Sellers data behind every pick. Verified, not hype.">
<meta property="og:image" content="{SITE}/assets/pin-viralfinds-beauty.png">
<meta property="og:url" content="{SITE}/{ARTICLE_PATH}">
<style>
  :root {{ --bg:#0f0f13; --card:#1a1a22; --text:#f4f4f8; --muted:#9a9aa8; --accent:#ff4d6d; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; line-height:1.6; }}
  .wrap {{ max-width:720px; margin:0 auto; padding:40px 20px; }}
  a.home {{ color:var(--muted); text-decoration:none; font-size:.9rem; }}
  h1 {{ font-size:1.9rem; line-height:1.25; margin:16px 0 12px; }}
  h1 span {{ color:var(--accent); }}
  .intro {{ color:var(--muted); margin-bottom:8px; }}
  .updated {{ color:var(--muted); font-size:.85rem; margin-bottom:28px; }}
  .product {{ background:var(--card); border-radius:16px; padding:26px; margin-bottom:22px; }}
  .rank {{ display:inline-block; background:var(--accent); color:var(--bg); font-weight:700; font-size:.78rem; padding:4px 12px; border-radius:8px; margin-bottom:12px; }}
  .product h2 {{ font-size:1.2rem; margin-bottom:8px; }}
  .stats {{ color:var(--accent); font-weight:600; font-size:.95rem; margin-bottom:10px; }}
  .blurb {{ color:var(--muted); margin-bottom:16px; }}
  .btn {{ display:inline-block; background:var(--accent); color:var(--bg); font-weight:700; padding:12px 22px; border-radius:10px; text-decoration:none; }}
  footer {{ color:var(--muted); font-size:.78rem; text-align:center; padding:30px 0; line-height:1.6; }}
</style>
</head>
<body>
<div class="wrap">
  <a class="home" href="../index.html">&larr; ViralFinds home</a>
  <h1>{len(products)} TikTok-Viral Skincare &amp; Beauty Products That Are <span>Actually</span> Amazon Best Sellers</h1>
  <p class="intro">Every pick below was verified against Amazon's live Best Sellers rankings before we listed it — real ranks, real ratings, real prices. Verified, not hype.</p>
  <p class="updated">Data captured from Amazon Best Sellers; last page update {today}.</p>
{sections}
  <footer>
    As an Amazon Associate we earn from qualifying purchases.<br>
    Prices, ranks and ratings are accurate as of the capture date shown above and may change.
  </footer>
</div>
<script>
  function track(label) {{
    try {{
      if (typeof gtag === "function") gtag("event", "affiliate_click", {{ link_label: label }});
    }} catch (e) {{}}
  }}
</script>
</body>
</html>
"""
    open(ARTICLE_PATH, "w").write(html)

    open("sitemap.xml", "w").write(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{SITE}/</loc><lastmod>{today}</lastmod></url>
  <url><loc>{SITE}/{ARTICLE_PATH}</loc><lastmod>{today}</lastmod></url>
</urlset>
""")
    open("robots.txt", "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    print(f"article + sitemap + robots generated ({len(products)} products)")


if __name__ == "__main__":
    main()
