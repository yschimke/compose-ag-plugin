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

printf '%s\n' '#!/bin/sh' 'if [ "$1 $2" = "mcp --help" ]; then exit 0; fi' 'exit 1' >"$fake_cli"
chmod +x "$fake_cli"
unsupported_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal '' "$unsupported_output" 'unsupported doctor is a silent no-op'

printf '%s\n' '#!/bin/sh' 'if [ "$1 $2" = "mcp --help" ]; then exit 23; fi' 'exit 0' >"$fake_cli"
chmod +x "$fake_cli"
failed_help_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal "$(expected_output 'Compose Preview needs attention: the MCP capability probe failed.')" "$failed_help_output" 'failed help guidance'

printf '%s\n' '#!/bin/sh' 'if [ "$1 $2" = "mcp --help" ]; then echo doctor; exit 0; fi' 'exit 0' >"$fake_cli"
chmod +x "$fake_cli"
ok_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal '' "$ok_output" 'healthy doctor is a silent no-op'

printf '%s\n' '#!/bin/sh' 'if [ "$1 $2" = "mcp --help" ]; then echo doctor; exit 0; fi' 'printf "%s\\n" "COMPOSE_PREVIEW_TOKEN=must-not-leak" >&2' 'exit 1' >"$fake_cli"
failed_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal "$(expected_output 'Compose Preview needs attention: MCP doctor failed.')" "$failed_output" 'failed doctor guidance'
if [[ "$failed_output" == *must-not-leak* ]]; then
  printf '%s\n' 'FAIL: doctor diagnostics must not leak into the SessionStart summary' >&2
  exit 1
fi

# Both probes must see EOF even if the hook itself inherits a held-open stdin.
printf '%s\n' \
  '#!/bin/sh' \
  'if read -r unexpected; then exit 97; fi' \
  'if [ "$1 $2" = "mcp --help" ]; then echo doctor; fi' \
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
assert_equal "$(expected_output 'Compose Preview needs attention: the MCP capability probe timed out.')" "$hung_help_output" 'hung help guidance'
if ((elapsed < 2 || elapsed >= 8)); then
  printf 'FAIL: help timeout took %s seconds\n' "$elapsed" >&2
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
assert_equal "$(expected_output 'Compose Preview needs attention: the MCP capability probe timed out.')" "$stubborn_help_output" 'SIGTERM-ignoring help guidance'
if ((elapsed < 2 || elapsed >= 8)); then
  printf 'FAIL: SIGTERM-ignoring help timeout took %s seconds\n' "$elapsed" >&2
  exit 1
fi

# Doctor has its own bound rather than relying only on the outer hook timeout.
printf '%s\n' \
  '#!/bin/sh' \
  'if [ "$1 $2" = "mcp --help" ]; then echo doctor; exit 0; fi' \
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
