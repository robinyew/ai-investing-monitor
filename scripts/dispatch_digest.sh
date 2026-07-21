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
# Official digest now runs on the LLM path (Opus 4.8, engine=fable = LLM+rules fallback).
PAYLOAD="{\"ref\":\"main\",\"inputs\":{\"date\":\"$DATE\",\"engine\":\"fable\",\"dry_run\":\"false\"}}"

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

# Wait for the digest workflow to finish (Opus call ~1-2 min + commit), then pull
# the committed digest copy (reports/digest/) to the local repo.
REPO="/Users/leimingyu/Investment/ai-investing-monitor"
echo "$LOG_TAG Waiting 10 min for digest workflow to complete..."
sleep 600
echo "$LOG_TAG Pulling digest copy..."
git -C "$REPO" pull --rebase --autostash origin main 2>&1 | sed "s/^/$LOG_TAG /"
echo "$LOG_TAG Pull complete."
