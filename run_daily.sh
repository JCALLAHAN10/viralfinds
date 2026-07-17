#!/bin/bash
# Daily entry point for the ViralFinds pipeline.
# Loads secrets from .env (never committed) and runs the orchestrator,
# appending all output to pipeline.log so you can see what each run did.

set -euo pipefail
cd "$(dirname "$0")"

if [ -f .env ]; then
  set -a; . ./.env; set +a
fi

export PATH="$HOME/bin:$PATH"   # gh lives in ~/bin

echo "===== run $(date '+%Y-%m-%d %H:%M:%S') =====" >> pipeline.log
python3 orchestrator.py >> pipeline.log 2>&1

# Deploy: only reached if the orchestrator succeeded (set -e above). The
# orchestrator commits per-stage, so commit anything left over, then push
# whenever local main is ahead of origin.
git add -A >> pipeline.log 2>&1
git diff --cached --quiet || git commit -m "Daily update $(date '+%Y-%m-%d')" >> pipeline.log 2>&1
if [ "$(git rev-list --count origin/main..main)" -gt 0 ]; then
  git push origin main >> pipeline.log 2>&1
  echo "deployed to GitHub Pages" >> pipeline.log
else
  echo "no changes to deploy" >> pipeline.log
fi
echo "" >> pipeline.log
