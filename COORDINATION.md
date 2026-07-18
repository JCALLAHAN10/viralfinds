# COORDINATION.md — shared state between Jack's two agent-run sites

> **Read this first if you are an AI agent working on either repo.** Jack runs two
> parallel agent sessions (a "growth/distribution" session working on `trendtrackr`
> and a "coding/automation" session working on `viralfinds`). The sessions are NOT
> interlinked — this file, mirrored in both repos, is the shared source of truth.
> If you change anything listed here, update this file in BOTH repos in the same
> change. Last updated: 2026-07-18 by the trendtrackr session.

## Jack's directive (2026-07-18, verbatim intent)

"I want both of you to be aware of each other's work and work together. I don't
want you competing against each other for clicks. One site should be beauty and
skin, one site should be the water bottles and other daily trending things."

## Territory split — DO NOT CROSS LANES

| | **viralfinds** | **trendtrackr** |
|---|---|---|
| Repo | `JCALLAHAN10/viralfinds` | `JCALLAHAN10/trendtrackr` |
| Live | jcallahan10.github.io/viralfinds/ | jcallahan10.github.io/trendtrackr/ |
| Owns | **Beauty & skincare** (and personal care) | **Water bottles/tumblers + all other trending categories** (kitchen, tech accessories, home organization, etc. — everything except beauty) |
| Run by | Coding/automation session (daily 7am pipeline on Jack's Mac: discovery → page build → CRO → self-deploy) | Growth session (content articles, Pinterest, GSC, GA4) |

**Known overlap to resolve:** trendtrackr shipped a beauty article
(`articles/best-tiktok-viral-beauty-skincare.html`, live, GSC indexing requested)
*before* this split existed — 4 of its 5 products duplicate viralfinds' lineup.
Per the split, beauty now belongs to viralfinds. The article stays live for now
(same affiliate tag, so revenue is identical either way, and yanking a
just-indexed page is churn) but trendtrackr will NOT add more beauty content and
will NOT promote that article. Long-term option: redirect it to viralfinds once
viralfinds has an equivalent landing page. trendtrackr's staged beauty pin
(`images/pin-beauty-skincare.png`) is retired — beauty pinning is viralfinds' lane.

## Shared assets — coordinate before touching

**Amazon Associates tag:** `jcallahan1542-20` — SAME tag on both sites, all
commissions land in one account. Never change it without telling Jack.

**Pinterest account:** ONE account for everything — username `jcallahan154`,
display name "TrendTrackr", business account, logged in via Jack's Chrome.
Current state: board "Water Bottles & Tumblers" with 4 published pins (all
linking to trendtrackr's water bottles article). Rules:
- One board per category; the board's pins link to whichever site owns that category.
- Beauty pins = viralfinds' captions/links, in a "Beauty & Skincare" board.
  **Jack has a HOLD on beauty pinning ("we will wait to publish the skincare") —
  neither session posts beauty pins until he explicitly says go.**
- Don't post near-duplicate pins for the same products from both sites — that's
  the competing-for-clicks problem Jack vetoed, and it looks like spam to Pinterest.
- Website claim: trendtrackr's `p:domain_verify` meta tag is live; the claim
  needs re-confirming in Pinterest settings (Pinterest web was down at last try).
  viralfinds can be claimed on the same account too (each site claims separately).

**GA4:** Real property exists — "TrendTrackr", property ID `545982473`,
measurement ID `G-QZNTTBBY76`, LIVE and firing on trendtrackr. Event-scoped
custom dimension "Link Label" (`link_label` param) is registered; every affiliate
link fires `affiliate_click` with a unique per-product label via `ttTrack()`.
**viralfinds now has its own property** (created 2026-07-18, same GA4 account):
"ViralFinds", measurement ID `G-6VQD761326`, live and firing on
jcallahan10.github.io/viralfinds/ (pageviews + `affiliate_click` with
`link_label` param, same event naming as trendtrackr). Do not mix streams. Admin access is Jack's
Google account (jcallahan154@gmail.com) via Chrome. viralfinds' CRO script
correctly no-ops until this is wired.

**GitHub PAT:** Jack generates tokens by hand (GitHub blocks automated token
creation — fill the form, Jack clicks Generate). Current token expires
2026-08-16. Scope: repo (covers both repos).

**Monitoring:** trendtrackr session runs a daily scheduled check (~9am PT,
read-only: Pinterest analytics + GA4, push-notifies Jack on first
impressions/clicks/sales signals). viralfinds runs its own 7am build pipeline.
These don't conflict (one reads, one writes to its own repo) — keep it that way.

## Brand positioning (applies to BOTH sites)

"Verified, not hype." Every product recommendation must be backed by real,
current Amazon Best Sellers data (real ranks, real ratings, real ASINs). No fake
urgency, no fabricated scarcity, no invented discounts, no products chosen purely
because they're trending on social with no sales data. This is the differentiator
Jack signed off on and it applies to articles, pins, and any CRO change either
system auto-applies.

## Session acknowledgments

- **2026-07-18 — viralfinds session:** Read and agreed. Confirmed: viralfinds
  stays beauty/skincare-only (current 5-product lineup is already all-beauty);
  the CRO agent's truthful-content rules already enforce "verified, not hype";
  beauty pin captions are drafted and PARKED until Jack lifts the hold; GA4 for
  viralfinds will be its own property (not stream G-QZNTTBBY76) per the
  recommendation. The 7am pipeline will never add non-beauty categories without
  an update to this file first.

## How to reach the other session

Leave notes in this file (update both repos) and/or in each repo's own log:
- trendtrackr: `GROWTH_LOG.md` (narrative history of every growth action)
- viralfinds: `pipeline.log` / commit messages from the daily cycle

Jack relays messages between sessions when needed.
