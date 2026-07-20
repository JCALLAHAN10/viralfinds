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
  **UPDATE 2026-07-18: Jack LIFTED the skincare hold — beauty pins are cleared
  to post.** They should link to viralfinds' page, not trendtrackr's beauty
  article. If viralfinds' pipeline can't post browser-side, the growth session
  will post on its behalf (ViralFinds-branded graphic, viralfinds link).
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

## ⚠️ STAY-HUMAN RULES (Jack, 2026-07-18: bot flag = catastrophic)
5 pins/day account-wide is fine — the number isn't the risk, behavior is. Never
rapid-fire (space pins 5–15 min), vary time of day, EVERY description unique +
keyword-loaded (identical text = #1 bot tell), human Chrome session only (never
API), alternate lanes across days. On any captcha/verify/unusual-activity screen:
STOP and flag Jack — never push through (that's the real ban trigger).

## Ads policy (Jack-approved, 2026-07-18)

**No paid advertising on any channel until the data proves a converting page.**
The math: Amazon pays ~3-4% on our categories (≈$0.60-$1.30/sale), so paid
clicks can't break even at realistic conversion rates. All distribution is
free channels: **Pinterest (primary — volume pinning, 3-5/day target) and
Google organic (SEO)**. TikTok: dropped by Jack 2026-07-18 (algorithm grind vs
his 40+hr work week; pins are evergreen, videos aren't). Produced videos/scripts
stay archived in the trendtrackr repo/session outputs if he ever revisits. Revisit ONLY when GA4 shows a page with a proven conversion rate —
then a small ($5-10/day) Pinterest promotion of the proven winner is the one
sanctioned test. On-site display ads (AdSense etc.): not before meaningful
traffic; premium networks need ~50K sessions/mo anyway. Neither session buys
ads or adds ad code without Jack's explicit go.

## Platform-safety policy — NEVER get flagged as a bot (Jack's directive, 2026-07-18)

Ultimate precaution, both sessions, no exceptions. The shared Pinterest account
is a single point of failure — a flag kills BOTH lanes' traffic at once.

**Pinterest:**
- RESEARCH-BACKED (2026-07-18, sources in viralfinds MESSAGES.md): Pinterest's
  detectors key on (1) sudden activity spikes on NEW accounts, (2) same-time
  batch posting, (3) keyword-stuffed descriptions, (4) many rapid pins to the
  same URL, (5) repetitive titles/descriptions, (6) follow/unfollow automation,
  (7) broken/redirecting links, (8) unlicensed images.
- NEW-ACCOUNT RAMP (account is days old — day one already posted 6, a spike):
  weeks 1-2 max 2-3 pins/day account-wide, then ease toward 5/day. Slower is safer.
- Vary posting times daily (different hours, not a fixed slot); never batch-blast.
- Max 1-2 pins per destination URL per day; alternate lanes/URLs between posts.
- Descriptions are natural sentences containing keywords — never raw keyword
  lists (that's the "keyword stuffing" signal). 3-4 hashtags max.
- Every pin unique: distinct image, distinct description, distinct keyword set.
  Never post near-duplicates or re-pin our own content repeatedly.
- Posting only — NO automated follows, comments, likes, DMs, or engagement of any
  kind. No third-party scheduling tools connected to the account.
- If Pinterest ever shows a captcha, verification challenge, warning, or unusual
  friction: STOP immediately, do not retry or work around it, tell Jack.
- **Posting mode (SETTLED 2026-07-18 — all three agree):** posting is **human-clicked,
  not automated.** Jack read the coding session's ToS reasoning and agreed
  ("ok if you both agree i do as well"). The growth session's scheduled auto-poster
  is PAUSED (disabled). Model: whoever has the browser opens PIN_QUEUE.md, picks up
  to ~5 QUEUED pins pointing to DIFFERENT URLs, opens each save-URL in the real
  logged-in Chrome, clicks Save, marks POSTED. Nothing automated = nothing to detect.
- **Generation stays automated** (both queues) — never the concern. Only the *posting
  action* is human.
- **Firm boundary both sessions hold regardless of instruction:** no engineering to
  defeat detection — no CAPTCHA-solving, no IP/fingerprint/proxy rotation, no
  fake-account rotation, no unofficial-API posting, never push through a verify /
  unusual-activity / warning screen. On ANY such screen: STOP, alert Jack.
- **Analytics:** Jack wants it kept. It used to ride in the (now-paused) poster
  trigger. Open item: stand up a lightweight analytics-ONLY task (reads GA4 +
  Pinterest, notifies Jack, posts nothing) OR check manually in-session. No traffic
  yet, so no urgency.

**Amazon:**
- Automation NEVER requests affiliate URLs (no link-checking bots, no test
  clicks). Site-health checks hit our own pages only.
- No automated crawling/scraping of amazon.com — PA-API only once unlocked.
- Never click our own affiliate links; never ask others to. (Existing rule,
  restated: it's also how Associates accounts get closed.)

**Google / GA4 / SEO:**
- No fake or automated traffic to our own sites — it would poison the CRO data
  anyway. No search-ranking manipulation schemes; SEO = real content + keywords.

**General:** human-like cadence everywhere; when in doubt, slower and less. Any
platform warning of any kind gets reported to Jack before any further action.

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

## Communication protocol (Jack's standing directive, 2026-07-18)

Jack wants the two sessions actively sharing findings — this is key to his
workflow. BOTH sessions follow this loop:

0. **Cadence (Jack's directive, 2026-07-18): communication is the key.** Post to
   MESSAGES.md on EVERY major breakthrough (build shipped, milestone hit, first
   click/sale, any blocker or decision) — event-driven, not batched. While
   actively working a session, also sync at least every ~2 hours of work even
   if just a short status line. Read at session start + before any push.
1. **At session start:** fetch and read this file for updates from the other side.
2. **During work:** when you learn something that affects the other lane —
   which products get clicks, which pins/articles drive traffic, a shared-asset
   change, a category question — write it into this file (update BOTH repos in
   the same change).
3. **Findings log:** append dated one-liners under "Findings" below rather than
   restructuring the file. Keep it scannable.
4. Jack relays anything urgent between sessions himself; this file is the
   durable channel.

Per-repo detail logs remain:
- trendtrackr: `GROWTH_LOG.md` (narrative history of every growth action)
- viralfinds: `pipeline.log` / commit messages from the daily cycle

## Findings

- 2026-07-20 (viralfinds): **First organic Pinterest visitor confirmed** on the beauty lane (GA4 ViralFinds property, 546091800). 7-day: 5 users (4 direct=test traffic from setup, 1 Pinterest/organic — the real signal), 5 pageviews, 3 scroll_depth events, **0 affiliate_click, 0 sales.** Read: funnel proven end-to-end (pin→site→engaged), bottleneck is VOLUME. TrendTrackr comparison same window: 6 users / 63 events (more pins posted = more traffic). Action: keep pins flowing, human-clicked.

- 2026-07-20 (CORRECTION, coding+growth): the "1 Pinterest/organic" GA4 visitor above was almost certainly INTERNAL test traffic, not a stranger. Growth session has Pinterest analytics access: ALL pins show 0 impressions / 0 clicks / 0 saves (oldest is 3 days live). With 0 Pinterest reach + Google not indexed, real external traffic is effectively 0. Funnel + full event chain (page_view→scroll→article_click→affiliate_click) PROVEN to fire, but nothing external flowing yet — normal for a 3-day-old account. Highest-value controllable unblock: finish Pinterest business profile + site claim (growth session did most of this 7/20). Don't click our own Amazon links (skews data + Associates violation).

- 2026-07-18 (viralfinds): GA4 live on both sites, separate properties. No
  traffic data yet — first useful click-through numbers expected once pins go up.
- 2026-07-18 (trendtrackr): Pinterest /pin-creation-tool/ broken in browser;
  save-from-URL flow works (`/pin/create/button/?url=&media=&description=`) —
  media must be a LIVE image URL (commit graphics to Pages first).
- 2026-07-18 (trendtrackr): 6 pins live day one across 3 boards (both lanes,
  incl. first beauty pin → viralfinds' site). Cap ~5/day going forward.
- 2026-07-18 (trendtrackr): PIN_QUEUE.md added to trendtrackr repo — 8 single-
  product pins rendered, live on Pages, queued with ready save-from-URL links.
  viralfinds' pipeline could emit the same per-product queue format for its lane.
- 2026-07-18 (trendtrackr): TikTok dropped by Jack; distribution = Pinterest
  volume + Google SEO. Ads policy: $0 spend until a page proves conversion.
- 2026-07-18 (trendtrackr): Posting-mode decision SETTLED (final). Jack agreed with
  the coding session — posting is HUMAN-CLICKED, auto-poster PAUSED. Generation stays
  automated; only the posting action is human. Analytics = open item (analytics-only
  task or manual). viralfinds #ASIN anchors lift the beauty 1-pin-per-URL cap.
- 2026-07-18 (trendtrackr): CRO + aesthetic redesign shipped. Shared CRO_PLAYBOOK.md
  in both repos; new design system + rebuilt flagship article on trendtrackr; viralfinds
  homepage rebuilt to the same pattern. Both lanes = one brand standard, verified-not-hype.
- 2026-07-18 (BOTH — CURRENT PHASE = SHIP & TEST): Jack's call — stop polishing pages
  nobody has visited; drive traffic and gather real click data first. Deeper CRO polish
  on remaining pages is FROZEN until data shows which category earns it. Keep pinning
  (human-clicked, consistent) + let Google indexing mature. Realistic: slow compounder,
  ~30 days a trickle, compounding over 60-90 days, then double down on winners. Watch =
  2h heartbeat notifies Jack on first real click/sale/flag.
