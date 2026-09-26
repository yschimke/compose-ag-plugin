#!/bin/sh
# Emit a safe SessionStart context summary for Claude Code and Codex.
#
# A future CLI may expose `compose-preview mcp doctor --json`. Probe the MCP
# help before invoking it: current releases do not have that subcommand, which
# is "unavailable", not a failed doctor check. Diagnostics may include
# machine-specific paths or configuration details, so only the exit status is
# surfaced. The current CLI/MCP contracts expose no session-level inventory of
# workspace-linked design comments or temporary copies; report those facts
# plainly instead of guessing from local files.

if command -v compose-preview >/dev/null 2>&1 &&
  compose-preview mcp --help 2>/dev/null | grep -Eq '(^|[[:space:]])doctor([[:space:]]|$)'; then
  if compose-preview mcp doctor --json >/dev/null 2>&1; then
    doctor_status=ok
  else
    doctor_status=failed
  fi
else
  doctor_status=unavailable
fi

summary="Compose design status: unacknowledged comments unavailable; MCP doctor ${doctor_status}; unsaved temporary copies unavailable."
printf '%s\n' "{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"${summary}\"}}"
