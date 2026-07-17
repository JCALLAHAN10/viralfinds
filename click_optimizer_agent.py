"""
click_optimizer_agent.py — the self-improvement stage of the ViralFinds pipeline.

Runs once per daily cycle (invoked by orchestrator.py after the page build).
Pulls engagement data, asks Claude for small, testable, truthful layout/copy
improvements, auto-applies only low-risk high-confidence ones, and queues the
rest in review_queue.json for human sign-off.

Gracefully no-ops (exit 0) until its prerequisites exist:
  ANTHROPIC_API_KEY   in .env — powers the recommendation engine.
  GA4_PROPERTY_ID     in .env — real engagement data. Until GA4 is wired into
  GA4_CREDENTIALS_JSON  the page, there is nothing to optimize against, and
                        this stage skips rather than inventing changes.

Fixes vs. the original draft:
  - sessions==0 no longer slips past the minimum-sample-size guard.
  - Recommendations must include current_html (verbatim snippet) so auto-apply
    matches exactly or queues — it never guesses.
  - Reversibility is real: the orchestrator git-commits every stage, so any
    applied change is one `git revert` away.
  - Model updated to claude-sonnet-5.
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("click_optimizer_agent")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID")
GA4_CREDENTIALS_JSON = os.environ.get("GA4_CREDENTIALS_JSON")
SITE_HTML_PATH = os.environ.get("SITE_HTML_PATH", "./index.html")

LOOKBACK_DAYS = 7
MIN_SESSIONS_FOR_CONFIDENCE = 200
REVIEW_QUEUE_PATH = "review_queue.json"
RUN_HISTORY_PATH = "run_history.jsonl"
CLAUDE_MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """You are a conversion-rate-optimization (CRO) subagent for a TikTok-viral /
Amazon-affiliate landing page whose primary audience is teens (13-19) browsing
on mobile. Your one job is to look at real engagement data and the current page
HTML, then propose a small set of concrete, testable layout/copy changes that
should increase click-through rate on affiliate links without increasing bounce
rate.

Hard rules:
1. Every recommendation must reference a specific element that exists in the
   HTML you were given, and include current_html: the EXACT verbatim snippet
   to be replaced, copied character-for-character from the provided markup.
2. Changes must be small and reversible: copy tweaks, badge additions,
   reordering, contrast changes. No redesigns, no new pages, no structural
   rewrites, and never touch <script> blocks, tracking calls, or link URLs.
3. Every recommendation must cite the specific data point motivating it.
4. risk_level: "low" = pure copy/badge/styling; "medium" = reordering or CTA
   placement; "high" = anything else.
5. confidence 0.0-1.0 from strength of supporting data; cap at 0.4 when the
   sample is below the stated minimum.
6. Output ONLY through the provided tool call.
7. If the data supports no confident change this cycle, return an empty
   recommendations array rather than inventing changes.
8. Never recommend anything that would mislead a user (fake scarcity, fake
   review counts, manipulated numbers). Only reposition, restyle, or reword
   TRUTHFUL information already present in the data."""

RECOMMENDATION_TOOL = {
    "name": "submit_cro_recommendations",
    "description": "Submit structured landing-page optimization recommendations.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "target_selector": {"type": "string"},
                        "current_html": {
                            "type": "string",
                            "description": "Exact verbatim HTML snippet to replace, copied from the provided markup.",
                        },
                        "proposed_html": {
                            "type": "string",
                            "description": "The exact replacement HTML.",
                        },
                        "supporting_metric": {"type": "string"},
                        "expected_impact": {"type": "string"},
                        "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": [
                        "target_selector", "current_html", "proposed_html",
                        "supporting_metric", "expected_impact", "risk_level", "confidence",
                    ],
                },
            },
        },
        "required": ["summary", "recommendations"],
    },
}


@dataclass
class PerformanceSnapshot:
    window_start: str
    window_end: str
    sessions: int = 0
    bounce_rate: float = 0.0
    avg_engagement_seconds: float = 0.0
    product_ctr: dict = field(default_factory=dict)
    site_avg_ctr: float = 0.0


def fetch_ga4_snapshot() -> PerformanceSnapshot:
    end = datetime.utcnow().date()
    start = end - timedelta(days=LOOKBACK_DAYS)
    snapshot = PerformanceSnapshot(window_start=str(start), window_end=str(end))

    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest, Dimension, Metric, DateRange,
    )
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", GA4_CREDENTIALS_JSON)
    client = BetaAnalyticsDataClient()

    overview = client.run_report(RunReportRequest(
        property=GA4_PROPERTY_ID,
        metrics=[Metric(name="sessions"), Metric(name="bounceRate"),
                 Metric(name="averageSessionDuration")],
        date_ranges=[DateRange(start_date=str(start), end_date=str(end))],
    ))
    if overview.rows:
        row = overview.rows[0]
        snapshot.sessions = int(float(row.metric_values[0].value))
        snapshot.bounce_rate = float(row.metric_values[1].value)
        snapshot.avg_engagement_seconds = float(row.metric_values[2].value)

    ctr = client.run_report(RunReportRequest(
        property=GA4_PROPERTY_ID,
        dimensions=[Dimension(name="customEvent:link_label")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date=str(start), end_date=str(end))],
    ))
    clicks = {r.dimension_values[0].value: int(r.metric_values[0].value)
              for r in ctr.rows if r.dimension_values[0].value}
    if snapshot.sessions and clicks:
        snapshot.product_ctr = {k: round(v / snapshot.sessions, 4) for k, v in clicks.items()}
        snapshot.site_avg_ctr = round(
            sum(snapshot.product_ctr.values()) / len(snapshot.product_ctr), 4)
    return snapshot


def call_claude(snapshot: PerformanceSnapshot, html: str) -> dict:
    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    user_msg = (
        f"Performance data (rolling {LOOKBACK_DAYS}-day window):\n\n"
        f"{json.dumps(asdict(snapshot), indent=2)}\n\n"
        f"Minimum sample size for confident action: {MIN_SESSIONS_FOR_CONFIDENCE} sessions.\n\n"
        f"Current landing page HTML:\n\n```html\n{html}\n```\n\n"
        f"Submit recommendations via submit_cro_recommendations."
    )
    response = client.messages.create(
        model=CLAUDE_MODEL, max_tokens=4096, system=SYSTEM_PROMPT,
        tools=[RECOMMENDATION_TOOL],
        tool_choice={"type": "tool", "name": "submit_cro_recommendations"},
        messages=[{"role": "user", "content": user_msg}],
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_cro_recommendations":
            return block.input
    raise RuntimeError("Claude did not return the expected tool_use block.")


def process_recommendations(result: dict) -> None:
    with open(SITE_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()
    applied, queued = [], []

    for rec in result.get("recommendations", []):
        current = rec.get("current_html", "")
        eligible = (rec["risk_level"] == "low" and rec["confidence"] >= 0.65
                    and current and html.count(current) == 1
                    and "<script" not in current.lower())
        if eligible:
            html = html.replace(current, rec["proposed_html"], 1)
            applied.append(rec)
        else:
            queued.append(rec)

    if applied:
        with open(SITE_HTML_PATH, "w", encoding="utf-8") as f:
            f.write(html)
        log.info(f"Auto-applied {len(applied)} low-risk change(s).")
    if queued:
        existing = []
        if os.path.exists(REVIEW_QUEUE_PATH):
            with open(REVIEW_QUEUE_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing.extend(queued)
        with open(REVIEW_QUEUE_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        log.info(f"Queued {len(queued)} change(s) for human review.")

    with open(RUN_HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "summary": result.get("summary", ""),
            "applied_count": len(applied),
            "queued_count": len(queued),
        }) + "\n")


def main() -> None:
    if not ANTHROPIC_API_KEY:
        log.info("CRO stage idle: ANTHROPIC_API_KEY not set in .env — skipping cleanly.")
        return
    if not (GA4_PROPERTY_ID and GA4_CREDENTIALS_JSON):
        log.info("CRO stage idle: GA4 not configured — no real data to optimize against, skipping.")
        return

    snapshot = fetch_ga4_snapshot()
    if snapshot.sessions < MIN_SESSIONS_FOR_CONFIDENCE:
        log.info(f"Only {snapshot.sessions} sessions in last {LOOKBACK_DAYS}d "
                 f"(need {MIN_SESSIONS_FOR_CONFIDENCE}) — skipping to avoid acting on noise.")
        return

    with open(SITE_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()
    result = call_claude(snapshot, html)
    log.info(f"CRO summary: {result.get('summary')}")
    process_recommendations(result)


if __name__ == "__main__":
    main()
