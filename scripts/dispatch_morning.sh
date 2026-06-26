#!/bin/bash
# dispatch_morning.sh — Pre-Market Brief + News Scan
# Triggered by launchd at 08:15 ET, Mon–Fri
# PAT stored in macOS Keychain: service=github-pat-ai-investing, account=robinyew

set -euo pipefail

KEYCHAIN_SERVICE="github-pat-ai-investing"
KEYCHAIN_ACCOUNT="robinyew"
LOG_TAG="[$(date '+%Y-%m-%d %H:%M:%S')] dispatch_morning"
BASE="https://api.github.com/repos/robinyew/ai-investing-monitor/actions/workflows"

PAT=$(security find-generic-password -a "$KEYCHAIN_ACCOUNT" -s "$KEYCHAIN_SERVICE" -w 2>/dev/null || true)

if [ -z "$PAT" ]; then
  echo "$LOG_TAG ERROR: PAT not found in Keychain (service=$KEYCHAIN_SERVICE, account=$KEYCHAIN_ACCOUNT)" >&2
  echo "$LOG_TAG Run: security add-generic-password -a $KEYCHAIN_ACCOUNT -s $KEYCHAIN_SERVICE -w ghp_YOUR_TOKEN" >&2
  exit 1
fi

dispatch() {
  local name="$1"
  local workflow="$2"
  local payload="$3"
  echo "$LOG_TAG Dispatching $name..."
  local response
  response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Authorization: Bearer $PAT" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "$BASE/$workflow/dispatches" \
    -d "$payload")
  local http_code
  http_code=$(echo "$response" | tail -1)
  local body
  body=$(echo "$response" | head -1)
  if [ "$http_code" = "204" ]; then
    echo "$LOG_TAG OK $name (HTTP $http_code)"
  else
    echo "$LOG_TAG FAIL $name (HTTP $http_code): $body" >&2
    exit 1
  fi
}

dispatch "Pre-Market Brief" "daily-report.yml" '{"ref":"main"}'
dispatch "News Scan"        "ai-news-scan.yml" '{"ref":"main"}'
