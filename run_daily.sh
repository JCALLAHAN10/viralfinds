#!/bin/bash
# Daily entry point for the ViralFinds pipeline.
# Loads secrets from .env (never committed) and runs the orchestrator,
# appending all output to pipeline.log so you can see what each run did.

set -euo pipefail
cd "$(dirname "$0")"

if [ -f .env ]; then
  set -a; . ./.env; set +a
fi

echo "===== run $(date '+%Y-%m-%d %H:%M:%S') =====" >> pipeline.log
python3 orchestrator.py >> pipeline.log 2>&1
echo "" >> pipeline.log
