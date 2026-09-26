#!/bin/sh
set -eu

repository_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
# shellcheck source=../plugins/compose-preview/scripts/lib/harness.sh
. "$repository_root/plugins/compose-preview/scripts/lib/harness.sh"

failures=0

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  failures=$((failures + 1))
}

assert_equal() {
  if [ "$1" != "$2" ]; then
    fail "$3 (expected: $1; actual: $2)"
  fi
}

assert_status() {
  expected_status=$1
  actual_status=$2
  description=$3
  if [ "$expected_status" -ne "$actual_status" ]; then
    fail "$description (expected status: $expected_status; actual: $actual_status)"
  fi
}

clear_harness_environment() {
  unset CLAUDECODE CLAUDE_PLUGIN_ROOT CODEX_THREAD_ID __CFBundleIdentifier ANTIGRAVITY_CLI_ALIAS OPENCODE GEMINI_CLI HARNESS
}

check_detection() {
  expected_harness=$1
  shift
  clear_harness_environment
  "$@"
  harness_detect
  assert_equal "$expected_harness" "$HARNESS" "detect $expected_harness"
}

set_claude() { CLAUDECODE=1; export CLAUDECODE; }
set_claude_plugin() { CLAUDE_PLUGIN_ROOT=/tmp/compose-preview; export CLAUDE_PLUGIN_ROOT; }
set_codex() { CODEX_THREAD_ID=thread-1; export CODEX_THREAD_ID; }
set_antigravity_bundle() { __CFBundleIdentifier=com.google.antigravity; export __CFBundleIdentifier; }
set_antigravity_alias() { ANTIGRAVITY_CLI_ALIAS=agy; export ANTIGRAVITY_CLI_ALIAS; }
set_opencode() { OPENCODE=1; export OPENCODE; }
set_gemini() { GEMINI_CLI=1; export GEMINI_CLI; }
set_nothing() { :; }

check_detection claude set_claude
check_detection claude set_claude_plugin
check_detection codex set_codex
check_detection antigravity set_antigravity_bundle
check_detection antigravity set_antigravity_alias
check_detection opencode set_opencode
check_detection gemini set_gemini
check_detection unknown set_nothing

clear_harness_environment
CODEX_THREAD_ID=thread-1
export CODEX_THREAD_ID
harness_detect --harness=antigravity
assert_equal antigravity "$HARNESS" 'explicit harness overrides environment'

if harness_detect --harness=unsupported >/dev/null 2>&1; then
  fail 'unsupported explicit harness must fail'
else
  assert_status 2 "$?" 'unsupported explicit harness status'
fi

if harness_detect --harness= >/dev/null 2>&1; then
  fail 'empty explicit harness must fail'
else
  assert_status 2 "$?" 'empty explicit harness status'
fi

harness_detect --harness=claude
claude_output=$(harness_emit_continue 'continue "carefully" \\ now')
assert_equal '{"decision":"block","reason":"continue \\"carefully\\" \\\\ now"}' "$claude_output" 'Claude output contract'

harness_detect --harness=antigravity
antigravity_output=$(harness_emit_continue 'continue "carefully" \\ now')
assert_equal '{"decision":"continue","reason":"continue \\"carefully\\" \\\\ now"}' "$antigravity_output" 'Antigravity output contract'

for no_stop_harness in codex opencode gemini unknown; do
  harness_detect --harness="$no_stop_harness"
  if harness_emit_continue 'not supported' >/dev/null 2>&1; then
    fail "$no_stop_harness must not emit a Stop-hook response"
  else
    case "$no_stop_harness" in
      codex) assert_status 3 "$?" 'Codex unsupported status' ;;
      *) assert_status 2 "$?" "$no_stop_harness non-target status" ;;
    esac
  fi
done

if [ "$failures" -ne 0 ]; then
  exit 1
fi

printf '%s\n' 'harness tests passed'
