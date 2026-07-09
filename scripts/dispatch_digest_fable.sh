#!/bin/bash
# dispatch_digest_fable.sh — Daily Decision Digest (Fable Preview)
# Triggered by launchd at 09:05 ET, Mon–Fri — parallel preview alongside the
# official 09:00 rules digest. Same workflow, engine=fable.
# PAT stored in macOS Keychain: service=github-pat-ai-investing, account=robinyew

set -euo pipefail

KEYCHAIN_SERVICE="github-pat-ai-investing"
KEYCHAIN_ACCOUNT="robinyew"
LOG_TAG="[$(date '+%Y-%m-%d %H:%M:%S')] dispatch_digest_fable"
BASE="https://api.github.com/repos/robinyew/ai-investing-monitor/actions/workflows"

PAT=$(security find-generic-password -a "$KEYCHAIN_ACCOUNT" -s "$KEYCHAIN_SERVICE" -w 2>/dev/null || true)

if [ -z "$PAT" ]; then
  echo "$LOG_TAG ERROR: PAT not found in Keychain (service=$KEYCHAIN_SERVICE, account=$KEYCHAIN_ACCOUNT)" >&2
  exit 1
fi

DATE=$(TZ="America/Toronto" date '+%Y-%m-%d')
PAYLOAD="{\"ref\":\"main\",\"inputs\":{\"date\":\"$DATE\",\"engine\":\"fable\",\"dry_run\":\"false\"}}"

echo "$LOG_TAG Dispatching Fable Preview Digest for $DATE..."
response=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: Bearer $PAT" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$BASE/daily-decision-digest.yml/dispatches" \
  -d "$PAYLOAD")

http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -1)

if [ "$http_code" = "204" ]; then
  echo "$LOG_TAG OK Fable Preview (HTTP $http_code)"
else
  echo "$LOG_TAG FAIL Fable Preview (HTTP $http_code): $body" >&2
  exit 1
fi

# Wait for both digest workflows to finish (fable model call ~7 min), then pull
# the committed digest copies (reports/digest/) to the local repo.
REPO="/Users/leimingyu/Investment/ai-investing-monitor"
echo "$LOG_TAG Waiting 10 min for digest workflows to complete..."
sleep 600
echo "$LOG_TAG Pulling digest copies..."
git -C "$REPO" pull --rebase --autostash origin main 2>&1 | sed "s/^/$LOG_TAG /"
echo "$LOG_TAG Pull complete."
