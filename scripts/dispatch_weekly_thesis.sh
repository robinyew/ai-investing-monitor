#!/bin/bash
# dispatch_weekly_thesis.sh — Friday Weekly Thesis Brief
# launchd: Friday 17:00 local time
# Pipeline: weekly md → huashu HTML → email

set -euo pipefail

REPO="/Users/leimingyu/Investment/ai-investing-monitor"
LOG_TAG="[$(date '+%Y-%m-%d %H:%M:%S')] weekly_thesis"
REQUESTED_PYTHON="${PYTHON:-}"
PYTHON=""
for CANDIDATE in \
  "$REQUESTED_PYTHON" \
  /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
  /opt/homebrew/bin/python3 \
  "$HOME/.pyenv/shims/python3" \
  /usr/bin/python3
do
  if [ -n "$CANDIDATE" ] && [ -x "$CANDIDATE" ] \
    && "$CANDIDATE" -c "import yaml" >/dev/null 2>&1; then
    PYTHON="$CANDIDATE"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo "$LOG_TAG No Python with PyYAML available" >&2
  exit 1
fi

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
cd "$REPO"

# Claude Code is installed outside launchd's default PATH on this Mac.
if [ -x "$HOME/.local/bin/claude" ]; then
  export CLAUDE_BIN="$HOME/.local/bin/claude"
fi

# Load SMTP and API keys for launchd (no login shell).
# Local generation prefers the authenticated Claude Code CLI; the API key is fallback.
if [ -f "$REPO/.env.local" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO/.env.local"
  set +a
fi

# Also try user profile secrets file if present
if [ -f "$HOME/.config/ai-investing-monitor/env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$HOME/.config/ai-investing-monitor/env"
  set +a
fi

echo "$LOG_TAG Starting weekly thesis brief pipeline..."
echo "$LOG_TAG Python enabled: $PYTHON"
if [ -n "${CLAUDE_BIN:-}" ]; then
  echo "$LOG_TAG Claude Code CLI enabled: $CLAUDE_BIN"
else
  echo "$LOG_TAG Claude Code CLI unavailable; Anthropic API/rules fallback will be used"
fi
"$PYTHON" "$REPO/scripts/run_weekly_thesis_brief.py" "$@" 2>&1 | sed "s/^/$LOG_TAG /"
echo "$LOG_TAG Done."
