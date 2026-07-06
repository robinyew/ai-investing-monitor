#!/bin/bash
# dispatch_hub.sh — Hub Intelligence Brief
# Triggered by launchd at 08:30 ET, Mon–Fri
# PAT stored in macOS Keychain: service=github-pat-ai-investing, account=robinyew

set -euo pipefail

KEYCHAIN_SERVICE="github-pat-ai-investing"
KEYCHAIN_ACCOUNT="robinyew"
LOG_TAG="[$(date '+%Y-%m-%d %H:%M:%S')] dispatch_hub"
BASE="https://api.github.com/repos/robinyew/ai-investing-monitor/actions/workflows"

PAT=$(security find-generic-password -a "$KEYCHAIN_ACCOUNT" -s "$KEYCHAIN_SERVICE" -w 2>/dev/null || true)

if [ -z "$PAT" ]; then
  echo "$LOG_TAG ERROR: PAT not found in Keychain (service=$KEYCHAIN_SERVICE, account=$KEYCHAIN_ACCOUNT)" >&2
  echo "$LOG_TAG Run: security add-generic-password -a $KEYCHAIN_ACCOUNT -s $KEYCHAIN_SERVICE -w ghp_YOUR_TOKEN" >&2
  exit 1
fi

DATE=$(TZ="America/Toronto" date '+%Y-%m-%d')
PAYLOAD="{\"ref\":\"main\",\"inputs\":{\"date\":\"$DATE\",\"publish\":\"true\",\"mode\":\"parallel\"}}"

echo "$LOG_TAG Dispatching Hub Intelligence Brief for $DATE..."
response=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: Bearer $PAT" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$BASE/publish-hub-intelligence.yml/dispatches" \
  -d "$PAYLOAD")

http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -1)

if [ "$http_code" = "204" ]; then
  echo "$LOG_TAG OK Hub (HTTP $http_code)"
else
  echo "$LOG_TAG FAIL Hub (HTTP $http_code): $body" >&2
  exit 1
fi

# Wait for GitHub Actions to finish (Pre-Market Brief + News Scan + Hub ~15 min), then pull
REPO="/Users/leimingyu/Investment/ai-investing-monitor"
echo "$LOG_TAG Waiting 15 min for GitHub Actions to complete..."
sleep 900
echo "$LOG_TAG Pulling today's reports..."
git -C "$REPO" pull --rebase --autostash origin main 2>&1 | sed "s/^/$LOG_TAG /"
echo "$LOG_TAG Pull complete."
