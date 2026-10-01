#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
script="$repository_root/plugins/compose-preview/scripts/compose-edit-reminder.sh"
temporary_root="$(mktemp -d)"
trap 'rm -rf "$temporary_root"' EXIT
export TMPDIR="$temporary_root/tmp"
mkdir -p "$TMPDIR"

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
  local files=$1
  printf '%s' "{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"additionalContext\":\"Compose UI changed in ${files}. Before calling this change done, render an affected preview with render_preview and look at the result (R1). If rendering fails or is unavailable, say so instead.\"}}"
}

project="$temporary_root/project"
mkdir -p "$project/app/src"
printf '%s\n' '@Composable' 'fun Screen() {}' >"$project/app/src/Screen.kt"
printf '%s\n' '@Preview' '@Composable' 'fun ScreenPreview() {}' >"$project/app/src/ScreenPreview.kt"
printf '%s\n' 'fun plain() = 1' >"$project/app/src/Plain.kt"
printf '%s\n' 'plugins { id("x") }' '// @Composable in a comment' >"$project/app/build.gradle.kts"
printf '%s\n' '# Notes' >"$project/README.md"

claude_edit() {
  local session=$1
  local file=$2
  local tool=${3:-Edit}
  printf '{"session_id":"%s","cwd":"%s","hook_event_name":"PostToolUse","tool_name":"%s","tool_input":{"file_path":"%s","old_string":"a","new_string":"b"}}' \
    "$session" "$project" "$tool" "$file"
}

run_hook() {
  local harness=$1
  "$script" "--harness=$harness"
}

output=$(claude_edit s1 "$project/app/src/Screen.kt" | run_hook claude)
assert_equal "$(expected_output 'Screen.kt')" "$output" 'Claude edit of a composable reminds'

output=$(claude_edit s1 "$project/app/src/Screen.kt" | run_hook claude)
assert_equal '' "$output" 'the same file in the same session reminds once'

output=$(claude_edit s2 "$project/app/src/Screen.kt" | run_hook claude)
assert_equal "$(expected_output 'Screen.kt')" "$output" 'a new session reminds again'

output=$(claude_edit s1 "$project/app/src/ScreenPreview.kt" Write | run_hook claude)
assert_equal "$(expected_output 'ScreenPreview.kt')" "$output" 'Write of a preview file reminds'

output=$(claude_edit s3 "$project/app/src/Plain.kt" | run_hook claude)
assert_equal '' "$output" 'Kotlin without Compose is silent'

output=$(claude_edit s3 "$project/app/build.gradle.kts" | run_hook claude)
assert_equal '' "$output" 'Gradle Kotlin scripts are silent'

output=$(claude_edit s3 "$project/README.md" | run_hook claude)
assert_equal '' "$output" 'non-Kotlin files are silent'

output=$(claude_edit s3 "$project/app/src/Screen.kt" Read | run_hook claude)
assert_equal '' "$output" 'non-edit tools are silent'

output=$(claude_edit s3 "$project/app/src/Missing.kt" | run_hook claude)
assert_equal '' "$output" 'a path that does not exist is silent'

output=$(claude_edit s4 "$project/app/src/Screen.kt" | run_hook antigravity)
assert_equal '' "$output" 'Antigravity is not a target'

output=$(claude_edit s4 "$project/app/src/Screen.kt" | "$script" --bogus 2>/dev/null)
assert_equal '' "$output" 'an invalid argument is silent'

# Without a session id there is no state to dedupe against, so every edit reminds.
no_session='{"cwd":"'"$project"'","tool_name":"Edit","tool_input":{"file_path":"'"$project"'/app/src/Screen.kt"}}'
output=$(printf '%s' "$no_session" | run_hook claude)
assert_equal "$(expected_output 'Screen.kt')" "$output" 'no session id reminds'
output=$(printf '%s' "$no_session" | run_hook claude)
assert_equal "$(expected_output 'Screen.kt')" "$output" 'no session id reminds every time'

# Codex sends apply_patch with the patch text; paths are relative to cwd.
codex_patch='{"session_id":"c1","cwd":"'"$project"'","hook_event_name":"PostToolUse","tool_name":"apply_patch","tool_input":{"command":"*** Begin Patch\n*** Update File: app/src/Screen.kt\n@@\n-a\n+b\n*** Update File: app/src/ScreenPreview.kt\n@@\n-a\n+b\n*** Update File: app/src/Plain.kt\n@@\n-a\n+b\n*** End Patch"}}'
output=$(printf '%s' "$codex_patch" | run_hook codex)
assert_equal "$(expected_output 'Screen.kt, ScreenPreview.kt')" "$output" 'Codex apply_patch reminds for each Compose file'

# A held-open stdin must not stall the agent after an edit.
held_stdin="$temporary_root/held-stdin"
mkfifo "$held_stdin"
sleep 6 >"$held_stdin" &
writer_pid=$!
started_at=$(date +%s)
output=$(run_hook claude <"$held_stdin")
elapsed=$(($(date +%s) - started_at))
kill "$writer_pid" 2>/dev/null || true
wait "$writer_pid" 2>/dev/null || true
assert_equal '' "$output" 'held-open stdin is silent'
if ((elapsed >= 5)); then
  printf 'FAIL: held-open stdin took %s seconds\n' "$elapsed" >&2
  exit 1
fi

printf '%s\n' 'compose edit reminder tests passed'
