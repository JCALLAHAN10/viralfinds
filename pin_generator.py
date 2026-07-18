"""
pin_generator.py — generates branded Pinterest pin graphics + PIN_QUEUE.md entries
for every product in the manual feed.

Part of the cross-session Pinterest loop (see MESSAGES.md / COORDINATION.md):
this side GENERATES pins; the growth session's daily task POSTS them from
PIN_QUEUE.md, within the ~5 pins/day account-wide cap.

Design rules (shared brand standards, per COORDINATION.md):
  - Own graphics only — never Amazon/manufacturer product photography (licensing).
  - Only truthful data already in the feed (real ratings/counts from Amazon
    Best Sellers). No invented urgency or discounts. "Verified, not hype."
  - 1000x1500 (2:3, Pinterest's preferred ratio), ViralFinds brand style.
  - Descriptions keyword-front-loaded (Pinterest SEO beats hashtags).

Run: python3 pin_generator.py   (re-run whenever the product feed changes;
skips products whose pin already exists unless --force)
"""

import json
import os
import sys
import urllib.parse
from PIL import Image, ImageDraw, ImageFont

SITE_URL = "https://jcallahan10.github.io/viralfinds/"
ASSETS_DIR = "assets"
QUEUE_PATH = "PIN_QUEUE.md"
BOARD = "Beauty & Skincare Finds"

W, H = 1000, 1500
BG, CARD, TEXT, MUTED, ACCENT = "#0f0f13", "#1a1a22", "#f4f4f8", "#9a9aa8", "#ff4d6d"

FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"


def f(size, bold=True):
    return ImageFont.truetype(FONT if bold else FONT_REG, size)


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def slugify(title):
    s = "".join(c.lower() if c.isalnum() else "-" for c in title)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")[:40]


def render_pin(p, path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Brand header
    d.text((60, 70), "Viral", font=f(64), fill=TEXT)
    d.text((60 + d.textlength("Viral", font=f(64)), 70), "Finds", font=f(64), fill=ACCENT)
    d.text((60, 150), "TIKTOK-VIRAL BEAUTY  ·  VERIFIED, NOT HYPE", font=f(28), fill=MUTED)

    # Eyebrow
    d.rounded_rectangle([60, 260, 560, 320], 14, fill=ACCENT)
    d.text((80, 273), "AMAZON BEST SELLER  #%d" % p.get("sales_rank", 0), font=f(30), fill=BG)

    # Title (wrapped)
    y = 380
    for line in wrap(d, p["title"], f(58), W - 120)[:5]:
        d.text((60, y), line, font=f(58), fill=TEXT)
        y += 74

    # Rating card — truthful numbers only
    y += 40
    d.rounded_rectangle([60, y, W - 60, y + 240], 20, fill=CARD)
    # Arial has no star glyphs — draw them as polygons instead
    import math
    def star(cx, cy, r, fill):
        pts = []
        for i in range(10):
            ang = math.pi / 2 + i * math.pi / 5
            rad = r if i % 2 == 0 else r * 0.42
            pts.append((cx + rad * math.cos(ang), cy - rad * math.sin(ang)))
        d.polygon(pts, fill=fill)
    filled = int(p["rating"])  # floor — never visually overstate the rating
    for i in range(5):
        star(130 + i * 75, y + 70, 30, ACCENT if i < filled else "#3a3a44")
    d.text((100, y + 115), f'{p["rating"]} out of 5  ·  {p["ratings_count"]:,} real Amazon ratings',
           font=f(36, bold=False), fill=TEXT)
    y += 300

    # Price
    d.text((60, y), p["price"], font=f(96), fill=TEXT)
    d.text((60 + d.textlength(p["price"], font=f(96)) + 30, y + 45),
           "on Amazon", font=f(36, bold=False), fill=MUTED)
    y += 160

    # Verification line
    for line in wrap(d, "Verified against Amazon's live Best Sellers rankings before we recommend it.",
                     f(34, bold=False), W - 120):
        d.text((60, y), line, font=f(34, bold=False), fill=MUTED)
        y += 46

    # CTA footer
    d.rounded_rectangle([60, H - 220, W - 60, H - 110], 20, fill=ACCENT)
    d.text((W // 2, H - 165), "See all 5 verified beauty picks  →",
           font=f(40), anchor="mm", fill=BG)
    d.text((W // 2, H - 70), "jcallahan10.github.io/viralfinds", font=f(30, bold=False),
           anchor="mm", fill=MUTED)

    img.save(path, "PNG")


# Per-product keyword clusters (Jack's directive: maximize tag/keyword coverage).
# Pinterest ranks on keywords in descriptions, so these go inline + a few hashtags.
KEYWORDS = {
    "B074PVTPBW": ("acne patches, pimple patches, hydrocolloid patches, acne treatment, "
                   "clear skin, skincare routine, breakout fix", "#acnetreatment #skincare #clearskin"),
    "B00T0C9XRK": ("mascara, drugstore makeup, eye makeup, lashes, false lash effect, "
                   "makeup must haves, affordable makeup", "#mascara #makeup #beautyfinds"),
    "B0B2RM68G2": ("face mask, overnight mask, collagen mask, K-beauty, korean skincare, "
                   "glass skin, hydrating skincare, self care night", "#kbeauty #facemask #glassskin"),
    "B071914GGL": ("toner, exfoliating toner, glycolic acid, skincare routine, glowing skin, "
                   "brightening skincare, affordable skincare", "#skincareroutine #glowingskin #theordinary"),
    "B09V7Z4TJG": ("toner pads, pore care, K-beauty, korean skincare, exfoliating pads, "
                   "skincare routine, smooth skin, glass skin", "#kbeauty #skincare #porecare"),
}


def save_url(p, media_url):
    kw, tags = KEYWORDS.get(p["asin"], ("beauty finds, skincare", "#beautyfinds"))
    desc = (f'TikTok Viral Beauty 2026: {p["title"]} — {p["rating"]}★, '
            f'{p["ratings_count"]:,} ratings, verified against Amazon\'s live Best '
            f'Sellers rankings. {kw}. All 5 verified TikTok-viral beauty picks on '
            f'ViralFinds. TikTok made me buy it, viral Amazon finds, beauty must haves. '
            f'{tags} #tiktokmademebuyit #amazonfinds')
    q = urllib.parse.urlencode({"url": SITE_URL, "media": media_url, "description": desc})
    return f"https://www.pinterest.com/pin/create/button/?{q}"


def main():
    force = "--force" in sys.argv
    os.makedirs(ASSETS_DIR, exist_ok=True)
    feed = json.load(open("manual_products.json"))
    entries = []
    for p in feed["by_category"].get("Beauty", []):
        if not (p.get("title") and p.get("rating")):
            continue
        slug = slugify(p["title"])
        path = os.path.join(ASSETS_DIR, f"pin-{slug}.png")
        if force or not os.path.exists(path):
            render_pin(p, path)
            print(f"rendered {path}")
        media = f"{SITE_URL}assets/pin-{slug}.png"
        entries.append((p["title"], save_url(p, media)))

    with open(QUEUE_PATH, "w") as fh:
        fh.write(
            "# PIN_QUEUE.md — ViralFinds beauty pins (posted by the growth session's daily task)\n\n"
            "> Board: **Beauty & Skincare Finds** · Account-wide cap ~5 pins/day across BOTH\n"
            "> lanes — growth session schedules the drip. Mark POSTED with date when done.\n"
            "> Media URLs are live on the viralfinds Pages site (committed in assets/).\n\n")
        for title, url in entries:
            fh.write(f"## {title}\n- Board: {BOARD}\n- Save URL: {url}\n- Status: QUEUED\n\n")
    print(f"{QUEUE_PATH}: {len(entries)} pins queued")


if __name__ == "__main__":
    main()
