#!/bin/bash
# Exact-time local trigger for the cloud-backed weekly site publisher.

set -euo pipefail

REPO="robinyew/ai-investing-monitor"
WORKFLOW="publish-weekly-thesis-site.yml"
GH_BIN="${GH_BIN:-/opt/homebrew/bin/gh}"
STAMP="$(date '+%Y-%m-%d %H:%M:%S %Z')"

if [ ! -x "$GH_BIN" ]; then
  GH_BIN="$(command -v gh || true)"
fi
if [ -z "$GH_BIN" ] || [ ! -x "$GH_BIN" ]; then
  echo "[$STAMP] gh CLI not found" >&2
  exit 1
fi

echo "[$STAMP] Dispatching $WORKFLOW on $REPO"
"$GH_BIN" workflow run "$WORKFLOW" -R "$REPO" -f force=false
echo "[$STAMP] Dispatch accepted; GitHub schedule remains the 18:40 fallback"
