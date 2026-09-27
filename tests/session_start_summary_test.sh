#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
script="$repository_root/plugins/compose-preview/scripts/session-start-summary.sh"
temporary_root="$(mktemp -d)"
trap 'rm -rf "$temporary_root"' EXIT

assert_equal() {
  local expected=$1
  local actual=$2
  local description=$3
  if [[ "$expected" != "$actual" ]]; then
    printf 'FAIL: %s (expected: %s; actual: %s)\n' "$description" "$expected" "$actual" >&2
    exit 1
  fi
}

expected_output() {
  local message=$1
  printf '%s' "{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"${message}\"}}"
}

missing_output="$(PATH="$temporary_root/missing:/usr/bin:/bin" "$script")"
assert_equal "$(expected_output 'Compose Preview needs setup: compose-preview is not available on PATH.')" "$missing_output" 'missing CLI guidance'

fake_bin="$temporary_root/bin"
mkdir "$fake_bin"
fake_cli="$fake_bin/compose-preview"

printf '%s\n' '#!/bin/sh' 'if [ "$1 $2" = "mcp --help" ] || [ "$1 $2" = "design --help" ]; then exit 0; fi' 'exit 1' >"$fake_cli"
chmod +x "$fake_cli"
unsupported_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal '' "$unsupported_output" 'unsupported doctor is a silent no-op'

printf '%s\n' '#!/bin/sh' 'if [ "$1 $2" = "mcp --help" ]; then exit 23; fi' 'if [ "$1 $2" = "design --help" ]; then exit 0; fi' 'exit 0' >"$fake_cli"
chmod +x "$fake_cli"
failed_help_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal "$(expected_output 'Compose Preview needs attention: The MCP capability probe failed.')" "$failed_help_output" 'failed help guidance'

printf '%s\n' '#!/bin/sh' 'if [ "$1 $2" = "mcp --help" ]; then echo doctor; exit 0; fi' 'if [ "$1 $2" = "design --help" ]; then exit 0; fi' 'exit 0' >"$fake_cli"
chmod +x "$fake_cli"
ok_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal '' "$ok_output" 'healthy doctor is a silent no-op'

printf '%s\n' '#!/bin/sh' 'if [ "$1 $2" = "mcp --help" ]; then exit 0; fi' 'if [ "$1 $2" = "design --help" ]; then exit 23; fi' 'if [ "$1" = "--help" ]; then echo design; exit 0; fi' 'exit 0' >"$fake_cli"
chmod +x "$fake_cli"
failed_design_help_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal "$(expected_output 'Compose Preview needs attention: The design-status capability probe failed.')" "$failed_design_help_output" 'failed design help guidance'

printf '%s\n' '#!/bin/sh' 'if [ "$1 $2" = "mcp --help" ]; then exit 0; fi' 'if [ "$1 $2" = "design --help" ]; then exit 23; fi' 'if [ "$1" = "--help" ]; then echo mcp; exit 0; fi' 'exit 1' >"$fake_cli"
chmod +x "$fake_cli"
old_cli_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal '' "$old_cli_output" 'older CLI without design is a silent no-op'

printf '%s\n' '#!/bin/sh' 'if [ "$1 $2" = "mcp --help" ]; then echo doctor; exit 0; fi' 'if [ "$1 $2" = "design --help" ]; then exit 0; fi' 'printf "%s\\n" "COMPOSE_PREVIEW_TOKEN=must-not-leak" >&2' 'exit 1' >"$fake_cli"
failed_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal "$(expected_output 'Compose Preview needs attention: MCP doctor failed.')" "$failed_output" 'failed doctor guidance'
if [[ "$failed_output" == *must-not-leak* ]]; then
  printf '%s\n' 'FAIL: doctor diagnostics must not leak into the SessionStart summary' >&2
  exit 1
fi

# The released status command contributes only its fixed, redacted summary grammar.
status_args="$temporary_root/status-args"
printf '%s\n' \
  '#!/bin/sh' \
  'if [ "$1 $2" = "mcp --help" ]; then echo doctor; exit 0; fi' \
  'if [ "$1 $2" = "mcp doctor" ]; then exit 0; fi' \
  'if [ "$1 $2" = "design --help" ]; then echo status; exit 0; fi' \
  'if [ "$1 $2" = "design status" ]; then printf "%s\n" "$*" >"$STATUS_ARGS"; echo "2 unacknowledged design comments; 1 unsaved temporary copy; design inventory unavailable for 1 workspace-linked design."; exit 0; fi' \
  'exit 1' >"$fake_cli"
chmod +x "$fake_cli"
status_output="$(STATUS_ARGS="$status_args" CLAUDE_PROJECT_DIR="$temporary_root/project with spaces" PATH="$fake_bin:$PATH" "$script")"
assert_equal "$(expected_output 'Compose Preview needs attention: 2 unacknowledged design comments; 1 unsaved temporary copy; design inventory unavailable for 1 workspace-linked design.')" "$status_output" 'actionable workspace design status'
assert_equal "design status --workspace $temporary_root/project with spaces --summary --timeout 2" "$(cat "$status_args")" 'status workspace and bound'

# Even stdout is treated as untrusted until it matches the complete summary grammar.
printf '%s\n' \
  '#!/bin/sh' \
  'if [ "$1 $2" = "mcp --help" ]; then exit 0; fi' \
  'if [ "$1 $2" = "design --help" ]; then echo status; exit 0; fi' \
  'if [ "$1 $2" = "design status" ]; then echo "COMPOSE_PREVIEW_TOKEN=must-not-leak"; exit 0; fi' \
  'exit 0' >"$fake_cli"
chmod +x "$fake_cli"
unsafe_status_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal "$(expected_output 'Compose Preview needs attention: Workspace design status returned an unreadable summary.')" "$unsafe_status_output" 'unsafe status summary is replaced'
if [[ "$unsafe_status_output" == *must-not-leak* ]]; then
  printf '%s\n' 'FAIL: status stdout must not leak into the SessionStart summary' >&2
  exit 1
fi

# Status failures and diagnostics collapse to one fixed sentence.
printf '%s\n' \
  '#!/bin/sh' \
  'if [ "$1 $2" = "mcp --help" ]; then exit 0; fi' \
  'if [ "$1 $2" = "design --help" ]; then echo status; exit 0; fi' \
  'if [ "$1 $2" = "design status" ]; then echo "credential=must-not-leak" >&2; exit 19; fi' \
  'exit 0' >"$fake_cli"
chmod +x "$fake_cli"
failed_status_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal "$(expected_output 'Compose Preview needs attention: Workspace design status failed.')" "$failed_status_output" 'failed status guidance'
if [[ "$failed_status_output" == *must-not-leak* ]]; then
  printf '%s\n' 'FAIL: status diagnostics must not leak into the SessionStart summary' >&2
  exit 1
fi

# Both probes must see EOF even if the hook itself inherits a held-open stdin.
printf '%s\n' \
  '#!/bin/sh' \
  'if read -r unexpected; then exit 97; fi' \
  'if [ "$1 $2" = "mcp --help" ]; then echo doctor; fi' \
  'if [ "$1 $2" = "design --help" ]; then exit 0; fi' \
  'exit 0' >"$fake_cli"
chmod +x "$fake_cli"
held_stdin="$temporary_root/held-stdin"
mkfifo "$held_stdin"
(
  exec 3>"$held_stdin"
  sleep 10
) &
writer_pid=$!
started_at=$(date +%s)
stdin_output="$(PATH="$fake_bin:$PATH" "$script" <"$held_stdin")"
elapsed=$(($(date +%s) - started_at))
kill "$writer_pid" 2>/dev/null || true
wait "$writer_pid" 2>/dev/null || true
assert_equal '' "$stdin_output" 'closed stdin is a silent healthy result'
if ((elapsed >= 3)); then
  printf 'FAIL: closed-stdin probe took %s seconds\n' "$elapsed" >&2
  exit 1
fi

# A capability probe that never exits must still return before the hook timeout.
printf '%s\n' \
  '#!/bin/sh' \
  'if [ "$1 $2" = "mcp --help" ]; then while :; do :; done; fi' \
  'exit 0' >"$fake_cli"
chmod +x "$fake_cli"
started_at=$(date +%s)
hung_help_output="$(PATH="$fake_bin:$PATH" "$script")"
elapsed=$(($(date +%s) - started_at))
assert_equal "$(expected_output 'Compose Preview needs attention: The MCP capability probe timed out.')" "$hung_help_output" 'hung help guidance'
if ((elapsed < 2 || elapsed >= 8)); then
  printf 'FAIL: help timeout took %s seconds\n' "$elapsed" >&2
  exit 1
fi

# The workspace status call has the same hard process bound as the existing doctor call.
printf '%s\n' \
  '#!/bin/sh' \
  'if [ "$1 $2" = "mcp --help" ]; then exit 0; fi' \
  'if [ "$1 $2" = "design --help" ]; then echo status; exit 0; fi' \
  'if [ "$1 $2" = "design status" ]; then while :; do :; done; fi' \
  'exit 0' >"$fake_cli"
chmod +x "$fake_cli"
started_at=$(date +%s)
hung_status_output="$(PATH="$fake_bin:$PATH" "$script")"
elapsed=$(($(date +%s) - started_at))
assert_equal "$(expected_output 'Compose Preview needs attention: Workspace design status timed out.')" "$hung_status_output" 'hung status guidance'
if ((elapsed < 2 || elapsed >= 8)); then
  printf 'FAIL: status timeout took %s seconds\n' "$elapsed" >&2
  exit 1
fi

# Several individually bounded slow probes must still leave time for the hook to emit context
# before the manifest's 10-second deadline.
printf '%s\n' \
  '#!/bin/sh' \
  'sleep 2' \
  'if [ "$1 $2" = "mcp --help" ]; then echo doctor; exit 0; fi' \
  'if [ "$1 $2" = "mcp doctor" ]; then exit 0; fi' \
  'if [ "$1 $2" = "design --help" ]; then echo status; exit 0; fi' \
  'if [ "$1 $2" = "design status" ]; then echo "1 unacknowledged design comment."; exit 0; fi' \
  'exit 0' >"$fake_cli"
chmod +x "$fake_cli"
started_at=$(date +%s)
cumulative_output="$(PATH="$fake_bin:$PATH" "$script")"
elapsed=$(($(date +%s) - started_at))
assert_equal "$(expected_output 'Compose Preview needs attention: Workspace design status timed out.')" "$cumulative_output" 'cumulative hook deadline guidance'
if ((elapsed < 6 || elapsed >= 10)); then
  printf 'FAIL: cumulative hook deadline took %s seconds\n' "$elapsed" >&2
  exit 1
fi

# A capability probe that ignores SIGTERM must be escalated to SIGKILL.
printf '%s\n' \
  '#!/bin/sh' \
  'trap "" TERM' \
  'if [ "$1 $2" = "mcp --help" ]; then while :; do :; done; fi' \
  'exit 0' >"$fake_cli"
chmod +x "$fake_cli"
started_at=$(date +%s)
stubborn_help_output="$(PATH="$fake_bin:$PATH" "$script")"
elapsed=$(($(date +%s) - started_at))
assert_equal "$(expected_output 'Compose Preview needs attention: The MCP capability probe timed out.')" "$stubborn_help_output" 'SIGTERM-ignoring help guidance'
if ((elapsed < 2 || elapsed >= 8)); then
  printf 'FAIL: SIGTERM-ignoring help timeout took %s seconds\n' "$elapsed" >&2
  exit 1
fi

# Doctor has its own bound rather than relying only on the outer hook timeout.
printf '%s\n' \
  '#!/bin/sh' \
  'if [ "$1 $2" = "mcp --help" ]; then echo doctor; exit 0; fi' \
  'if [ "$1 $2" = "design --help" ]; then exit 0; fi' \
  'while :; do :; done' >"$fake_cli"
chmod +x "$fake_cli"
started_at=$(date +%s)
hung_doctor_output="$(PATH="$fake_bin:$PATH" "$script")"
elapsed=$(($(date +%s) - started_at))
assert_equal "$(expected_output 'Compose Preview needs attention: MCP doctor timed out.')" "$hung_doctor_output" 'hung doctor guidance'
if ((elapsed < 2 || elapsed >= 8)); then
  printf 'FAIL: doctor timeout took %s seconds\n' "$elapsed" >&2
  exit 1
fi

printf '%s\n' 'session start summary tests passed'
