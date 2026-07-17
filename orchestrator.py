"""
orchestrator.py

The daily pipeline for ViralFinds. Runs, in order:

    1. trend_discovery_agent.py   -> pulls Amazon top sellers -> top_sellers.json
    2. page_builder_agent.py      -> renders products into index.html
    3. click_optimizer_agent.py   -> CRO agent optimizes copy/layout (if present)

After each stage that changes files, it makes a git commit. That commit trail is
your undo button under full-auto: if a run makes the site worse, `git log` shows
exactly what each agent did and `git revert <hash>` rolls back one stage.

If a stage fails, the pipeline stops and does NOT commit a broken state — better
to leave yesterday's working site up than publish a half-built one.

The CRO agent (click_optimizer_agent.py) is optional: if you haven't saved it
into this folder yet, that stage is skipped with a note and the rest still runs.

USAGE
-----
  python orchestrator.py

Point your daily cron/launchd job at this file. Required env vars are the union
of what the three agents need (PAAPI_* for discovery, ANTHROPIC_API_KEY +
SITE_HTML_PATH for the CRO stage, GA4_MEASUREMENT_ID optional for tracking).
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("orchestrator")

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

STAGES = [
    ("discovery", "trend_discovery_agent.py", True),   # required
    ("build",     "page_builder_agent.py",    True),   # required
    ("cro",       "click_optimizer_agent.py", False),  # optional until you save it
]


def run_stage(name: str, script: str) -> None:
    path = os.path.join(HERE, script)
    log.info(f"=== stage: {name} ({script}) ===")
    subprocess.run([PY, path], cwd=HERE, check=True)


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.name=ViralFinds Bot", "-c", "user.email=bot@viralfinds.local", *args],
        cwd=HERE, check=False, capture_output=True, text=True,
    )


def commit(message: str) -> None:
    git("add", "-A")
    status = git("status", "--porcelain")
    if not status.stdout.strip():
        log.info("  nothing changed — no commit.")
        return
    result = git("commit", "-m", message)
    if result.returncode == 0:
        log.info(f"  committed: {message}")
    else:
        log.warning(f"  git commit failed: {result.stderr.strip()}")


def main() -> None:
    stamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    log.info(f"Pipeline start {stamp}")

    for name, script, required in STAGES:
        path = os.path.join(HERE, script)
        if not os.path.exists(path):
            if required:
                log.error(f"Required stage '{name}' missing ({script}) — aborting.")
                sys.exit(1)
            log.info(f"Optional stage '{name}' not present ({script}) — skipping.")
            continue
        try:
            run_stage(name, script)
        except subprocess.CalledProcessError as e:
            log.error(f"Stage '{name}' failed (exit {e.returncode}) — stopping before commit.")
            sys.exit(e.returncode)
        commit(f"{name}: {stamp}")

    log.info("Pipeline complete. Review with: git -C %s log --oneline" % HERE)


if __name__ == "__main__":
    main()
