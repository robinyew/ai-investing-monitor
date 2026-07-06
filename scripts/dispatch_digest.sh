#!/bin/bash
# dispatch_digest.sh — Daily Decision Digest
# Triggered by launchd at 09:00 ET, Mon–Fri (after all three reports + hub pull)
# PAT stored in macOS Keychain: service=github-pat-ai-investing, account=robinyew

set -euo pipefail

KEYCHAIN_SERVICE="github-pat-ai-investing"
KEYCHAIN_ACCOUNT="robinyew"
LOG_TAG="[$(date '+%Y-%m-%d %H:%M:%S')] dispatch_digest"
BASE="https://api.github.com/repos/robinyew/ai-investing-monitor/actions/workflows"

PAT=$(security find-generic-password -a "$KEYCHAIN_ACCOUNT" -s "$KEYCHAIN_SERVICE" -w 2>/dev/null || true)

if [ -z "$PAT" ]; then
  echo "$LOG_TAG ERROR: PAT not found in Keychain (service=$KEYCHAIN_SERVICE, account=$KEYCHAIN_ACCOUNT)" >&2
  echo "$LOG_TAG Run: security add-generic-password -a $KEYCHAIN_ACCOUNT -s $KEYCHAIN_SERVICE -w ghp_YOUR_TOKEN" >&2
  exit 1
fi

DATE=$(TZ="America/Toronto" date '+%Y-%m-%d')
PAYLOAD="{\"ref\":\"main\",\"inputs\":{\"date\":\"$DATE\",\"dry_run\":\"false\"}}"

echo "$LOG_TAG Dispatching Daily Decision Digest for $DATE..."
response=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: Bearer $PAT" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$BASE/daily-decision-digest.yml/dispatches" \
  -d "$PAYLOAD")

http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -1)

if [ "$http_code" = "204" ]; then
  echo "$LOG_TAG OK Digest (HTTP $http_code)"
else
  echo "$LOG_TAG FAIL Digest (HTTP $http_code): $body" >&2
  exit 1
fi
