"""
trend_discovery_agent.py

Amazon top-seller discovery agent for ViralFinds.

WHAT IT DOES
------------
For each category you care about (apparel, beauty, electronics, ...), it queries
the Amazon Product Advertising API (PA-API 5.0), pulls candidate products, ranks
them by Amazon's WebsiteSalesRank (lower = better selling), and writes a cohesive,
per-category list of top sellers with affiliate-tagged links.

You review that list and decide what to publish. This agent does NOT touch your
landing page — it only produces the candidate list.

WHY IT WORKS THIS WAY
---------------------
PA-API 5.0 has no "best sellers" endpoint and no sort-by-sales-rank option. The
only legitimate, ToS-compliant path is: SearchItems within a category's browse
node, request the `BrowseNodeInfo.WebsiteSalesRank` resource per item, then sort
by that rank ourselves. (Scraping Amazon's Best Sellers pages is against their
ToS and will get your account banned — don't.)

Affiliate links: every item's `DetailPageURL` is already tagged with your
PartnerTag by Amazon, so the links in the output are ready to use.

REQUIRED SETUP
--------------
  pip install python-amazon-paapi

Environment variables (all required):
  PAAPI_ACCESS_KEY     Your PA-API access key.
  PAAPI_SECRET_KEY     Your PA-API secret key.
  PAAPI_PARTNER_TAG    Your Associates tracking id, e.g. "viralfinds-20".
  PAAPI_COUNTRY        Marketplace country code, e.g. "US" (default "US").

RATE LIMITS
-----------
Fresh Associates accounts start at ~1 request/second and 8,640 requests/day.
That budget goes up as you make sales. This script throttles to stay under the
1 req/sec floor. With ~9 categories x a few pages each you're well within budget.
"""

import os
import json
import time
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime

try:
    from amazon_paapi import AmazonApi
    PAAPI_AVAILABLE = True
except ImportError:
    PAAPI_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("trend_discovery_agent")

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

PAAPI_ACCESS_KEY = os.environ.get("PAAPI_ACCESS_KEY")
PAAPI_SECRET_KEY = os.environ.get("PAAPI_SECRET_KEY")
PAAPI_PARTNER_TAG = os.environ.get("PAAPI_PARTNER_TAG")
PAAPI_COUNTRY = os.environ.get("PAAPI_COUNTRY", "US")

# How many result pages to pull per category (10 items/page, max 10 pages).
PAGES_PER_CATEGORY = 2
# Keep only this many top-ranked items per category in the final list.
TOP_N_PER_CATEGORY = 10
# Seconds between API calls — stay under the 1 req/sec floor for new accounts.
THROTTLE_SECONDS = 1.1

OUTPUT_JSON = "top_sellers.json"
OUTPUT_MARKDOWN = "top_sellers.md"

# --------------------------------------------------------------------------
# CATEGORIES  →  Amazon US browse node IDs
# --------------------------------------------------------------------------
# NOTE: Browse node IDs are for the US marketplace and DO drift over time.
# Verify/adjust with a GetBrowseNodes call if a category comes back empty.
# You can also narrow any of these by swapping in a more specific sub-node
# (e.g. "Women's Fashion" instead of all Clothing) once you see what sells.

CATEGORIES = {
    "Apparel":       "7141123011",   # Clothing, Shoes & Jewelry
    "Beauty":        "3760911",      # Beauty & Personal Care
    "Electronics":   "172282",       # Electronics
    "Home & Kitchen":"1055398",      # Home & Kitchen
    "Toys & Games":  "165793011",    # Toys & Games
    "Health":        "3760901",      # Health & Household
    "Sports":        "3375251",      # Sports & Outdoors
    "Pet Supplies":  "2619533011",   # Pet Supplies
    "Office":        "1064954",      # Office Products
}

# Resources to request from PA-API for each item.
SEARCH_RESOURCES = [
    "ItemInfo.Title",
    "ItemInfo.ByLineInfo",
    "ItemInfo.Features",
    "Offers.Listings.Price",
    "Offers.Listings.SavingBasis",
    "Images.Primary.Medium",
    "BrowseNodeInfo.WebsiteSalesRank",
]

# --------------------------------------------------------------------------
# DATA MODEL
# --------------------------------------------------------------------------

@dataclass
class Product:
    asin: str
    title: str
    brand: str = ""
    price: str = ""
    list_price: str = ""
    sales_rank: int = 0          # lower = sells better; 0 means "unknown"
    image_url: str = ""
    affiliate_url: str = ""      # DetailPageURL, already partner-tagged
    category: str = ""


@dataclass
class DiscoveryRun:
    generated_at: str
    country: str
    by_category: dict = field(default_factory=dict)   # {"Beauty": [Product, ...]}


# --------------------------------------------------------------------------
# SAFE ATTRIBUTE ACCESS
# --------------------------------------------------------------------------
# The PA-API response object is deeply nested and any branch can be None, so
# every field read goes through these guarded helpers instead of dotting in
# directly (which would blow up on the first missing attribute).

def _dig(obj, *path, default=None):
    for attr in path:
        if obj is None:
            return default
        obj = getattr(obj, attr, None)
    return obj if obj is not None else default


def parse_item(item, category: str) -> Product:
    asin = getattr(item, "asin", "") or ""
    title = _dig(item, "item_info", "title", "display_value", default="(untitled)")
    brand = _dig(item, "item_info", "by_line_info", "brand", "display_value", default="")

    listings = _dig(item, "offers", "listings", default=[]) or []
    first = listings[0] if listings else None
    price = _dig(first, "price", "display_amount", default="")
    list_price = _dig(first, "saving_basis", "display_amount", default="")

    # WebsiteSalesRank can live at the item level or per browse-node. Take the
    # lowest (best) rank we can find, since 0/None means "not ranked here."
    rank = _dig(item, "browse_node_info", "website_sales_rank", "sales_rank", default=0) or 0

    image_url = _dig(item, "images", "primary", "medium", "url", default="")
    affiliate_url = getattr(item, "detail_page_url", "") or ""

    return Product(
        asin=asin, title=title, brand=brand, price=price, list_price=list_price,
        sales_rank=int(rank) if rank else 0, image_url=image_url,
        affiliate_url=affiliate_url, category=category,
    )


# --------------------------------------------------------------------------
# DISCOVERY
# --------------------------------------------------------------------------

def fetch_category(amazon: "AmazonApi", name: str, browse_node: str) -> list:
    products = {}
    for page in range(1, PAGES_PER_CATEGORY + 1):
        try:
            result = amazon.search_items(
                browse_node_id=browse_node,
                item_count=10,
                item_page=page,
                sort_by="Featured",           # closest proxy; we re-rank below
                resources=SEARCH_RESOURCES,
            )
        except Exception as e:
            log.warning(f"[{name}] page {page} failed: {e}")
            time.sleep(THROTTLE_SECONDS)
            continue

        for item in (getattr(result, "items", None) or []):
            p = parse_item(item, name)
            if p.asin:
                products[p.asin] = p   # dedupe across pages by ASIN
        time.sleep(THROTTLE_SECONDS)

    ranked = sorted(
        products.values(),
        # Ranked items first (ascending), unranked (0) pushed to the bottom.
        key=lambda p: p.sales_rank if p.sales_rank > 0 else float("inf"),
    )
    log.info(f"[{name}] {len(ranked)} unique products, keeping top {TOP_N_PER_CATEGORY}.")
    return ranked[:TOP_N_PER_CATEGORY]


def run_discovery() -> DiscoveryRun:
    amazon = AmazonApi(
        PAAPI_ACCESS_KEY, PAAPI_SECRET_KEY, PAAPI_PARTNER_TAG, PAAPI_COUNTRY,
        throttling=THROTTLE_SECONDS,
    )
    run = DiscoveryRun(generated_at=datetime.utcnow().isoformat(), country=PAAPI_COUNTRY)
    for name, node in CATEGORIES.items():
        log.info(f"Fetching category: {name} (node {node})")
        run.by_category[name] = [asdict(p) for p in fetch_category(amazon, name, node)]
    return run


# --------------------------------------------------------------------------
# OUTPUT
# --------------------------------------------------------------------------

def write_outputs(run: DiscoveryRun) -> None:
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(asdict(run), f, indent=2)

    lines = [f"# Top sellers by category", f"_Generated {run.generated_at} ({run.country})_", ""]
    for category, items in run.by_category.items():
        lines.append(f"## {category}")
        if not items:
            lines.append("_No results — check the browse node id for this category._\n")
            continue
        for i, p in enumerate(items, 1):
            rank = p["sales_rank"] or "—"
            price = p["price"] or "?"
            lines.append(f"{i}. **{p['title'][:80]}** — {price}  ")
            lines.append(f"   rank {rank} · {p['brand'] or 'no brand'} · [link]({p['affiliate_url']})")
        lines.append("")

    with open(OUTPUT_MARKDOWN, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    log.info(f"Wrote {OUTPUT_JSON} and {OUTPUT_MARKDOWN}.")


# --------------------------------------------------------------------------
# ENTRY POINT
# --------------------------------------------------------------------------

MANUAL_FEED_JSON = "manual_products.json"


def load_manual_feed() -> "DiscoveryRun | None":
    """Fallback for accounts still behind Amazon's 3-sales PA-API gate.

    Reads hand-picked products from manual_products.json (same schema as the
    API output) so the rest of the pipeline — page builder, CRO agent, daily
    cron — runs identically in manual and automatic mode. Entries with an
    empty title or affiliate_url are skipped so the template's blank rows
    never reach the page.
    """
    if not os.path.exists(MANUAL_FEED_JSON):
        return None
    with open(MANUAL_FEED_JSON, "r", encoding="utf-8") as f:
        feed = json.load(f)
    by_cat = {}
    for category, items in (feed.get("by_category") or {}).items():
        kept = []
        for p in (items or []):
            if not (p.get("title") and p.get("affiliate_url")):
                continue
            # Fill any fields the user deleted so downstream renderers never KeyError.
            kept.append({**asdict(Product(asin="", title="")), **p, "category": category})
        if kept:
            by_cat[category] = kept
    if not by_cat:
        return None
    run = DiscoveryRun(generated_at=datetime.utcnow().isoformat(), country=PAAPI_COUNTRY)
    run.by_category = by_cat
    return run


def main() -> None:
    missing = [k for k, v in {
        "PAAPI_ACCESS_KEY": PAAPI_ACCESS_KEY,
        "PAAPI_SECRET_KEY": PAAPI_SECRET_KEY,
        "PAAPI_PARTNER_TAG": PAAPI_PARTNER_TAG,
    }.items() if not v]

    if missing:
        manual = load_manual_feed()
        if manual is not None:
            log.info(
                f"PA-API keys not set ({', '.join(missing)}) — using MANUAL feed "
                f"from {MANUAL_FEED_JSON} ({sum(len(v) for v in manual.by_category.values())} products). "
                f"Automatic discovery takes over the day the keys go into .env."
            )
            write_outputs(manual)
            return
        raise SystemExit(
            f"Missing env vars: {', '.join(missing)} — and {MANUAL_FEED_JSON} has no "
            f"filled-in products to fall back on. Add products there or set the keys."
        )

    if not PAAPI_AVAILABLE:
        raise SystemExit("Install the SDK first:  pip install python-amazon-paapi")

    run = run_discovery()
    write_outputs(run)
    total = sum(len(v) for v in run.by_category.values())
    log.info(f"Done. {total} candidate products across {len(run.by_category)} categories.")


if __name__ == "__main__":
    main()
