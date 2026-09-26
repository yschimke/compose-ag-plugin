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

expected_prefix='Compose design status: unacknowledged comments unavailable; MCP doctor '
expected_suffix='; unsaved temporary copies unavailable.'

expected_output() {
  local status=$1
  printf '%s' "{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"${expected_prefix}${status}${expected_suffix}\"}}"
}

missing_output="$(PATH="$temporary_root/missing" "$script")"
assert_equal "$(expected_output unavailable)" "$missing_output" 'missing CLI status'

fake_bin="$temporary_root/bin"
mkdir "$fake_bin"
fake_cli="$fake_bin/compose-preview"

printf '%s\n' '#!/bin/sh' 'if [ "$1 $2" = "mcp --help" ]; then exit 0; fi' 'exit 1' >"$fake_cli"
chmod +x "$fake_cli"
unsupported_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal "$(expected_output unavailable)" "$unsupported_output" 'unsupported doctor status'

printf '%s\n' '#!/bin/sh' 'if [ "$1 $2" = "mcp --help" ]; then echo doctor; exit 0; fi' 'exit 0' >"$fake_cli"
chmod +x "$fake_cli"
ok_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal "$(expected_output ok)" "$ok_output" 'healthy doctor status'

printf '%s\n' '#!/bin/sh' 'if [ "$1 $2" = "mcp --help" ]; then echo doctor; exit 0; fi' 'printf "%s\\n" "COMPOSE_PREVIEW_TOKEN=must-not-leak" >&2' 'exit 1' >"$fake_cli"
failed_output="$(PATH="$fake_bin:$PATH" "$script")"
assert_equal "$(expected_output failed)" "$failed_output" 'failed doctor status'
if [[ "$failed_output" == *must-not-leak* ]]; then
  printf '%s\n' 'FAIL: doctor diagnostics must not leak into the SessionStart summary' >&2
  exit 1
fi

printf '%s\n' 'session start summary tests passed'
