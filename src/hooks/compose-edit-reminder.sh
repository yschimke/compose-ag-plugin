#!/bin/sh
# Remind the agent to render after it edits Compose UI (agent rule R1, issue #86).
#
# Runs after a file edit (PostToolUse) in Claude Code and Codex. When an edited
# *.kt file declares a @Composable or @Preview, it adds one line of context
# asking the agent to render an affected preview before calling the change
# done. Skills only load when the model picks them, and the Claude Code eval run
# on #64 showed agents editing Compose UI without rendering even with the skill
# offered; a hook is the one channel that is always seen.
#
# It reminds once per file per session, never blocks, and stays silent on any
# failure of its own: an unknown harness, unreadable input, or no Compose file.

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 0
# shellcheck source=lib/harness.sh
. "$script_dir/lib/harness.sh" || exit 0
harness_detect "$@" 2>/dev/null || exit 0
case "$HARNESS" in
  claude|codex) ;;
  *) exit 0 ;;
esac

temporary_root=$(mktemp -d "${TMPDIR:-/tmp}/compose-preview-edit-reminder.XXXXXX") || exit 0
reader_pid=

cleanup() {
  if [ -n "$reader_pid" ]; then
    kill "$reader_pid" 2>/dev/null || true
    reader_pid=
  fi
  rm -rf "$temporary_root"
}

trap 'cleanup' EXIT
trap 'cleanup; exit 0' HUP INT TERM

# The harness writes one JSON object to stdin. Read it with a 2-second bound so
# a held-open stdin cannot stall the agent after every edit.
# Background jobs get /dev/null as stdin, so hand the real stdin over as fd 3.
hook_input="$temporary_root/input.json"
exec 3<&0
cat <&3 >"$hook_input" 2>/dev/null &
reader_pid=$!
exec 3<&-
reader_ticks=0
while kill -0 "$reader_pid" 2>/dev/null && [ "$reader_ticks" -lt 20 ]; do
  sleep 0.1
  reader_ticks=$((reader_ticks + 1))
done
if kill -0 "$reader_pid" 2>/dev/null; then
  exit 0
fi
wait "$reader_pid" 2>/dev/null
reader_pid=

# json_string_field <key>: the first plain string value of <key> in the input.
json_string_field() {
  sed -n 's/.*"'"$1"'"[[:space:]]*:[[:space:]]*"\([^"\\]*\)".*/\1/p' "$hook_input" | head -n 1
}

case "$(json_string_field tool_name)" in
  Edit|Write|MultiEdit|apply_patch) ;;
  *) exit 0 ;;
esac

hook_cwd=$(json_string_field cwd)
[ -n "$hook_cwd" ] && [ -d "$hook_cwd" ] || hook_cwd=$PWD

session_id=$(json_string_field session_id)
case "$session_id" in
  ''|*[!A-Za-z0-9._:-]*) session_id= ;;
esac
[ "${#session_id}" -le 128 ] || session_id=
state_file=
if [ -n "$session_id" ]; then
  state_root="${TMPDIR:-/tmp}/compose-preview-edit-reminder-$(id -u 2>/dev/null || echo user)"
  state_file="$state_root/$(printf '%s' "$session_id" | tr -c 'A-Za-z0-9._-' '_').files"
fi

# Claude Code names the file in tool_input.file_path; Codex's apply_patch names
# it in the patch text ("*** Update File: <path>\n"). Both end a path with .kt
# followed by a closing quote or an escaped newline.
paths="$temporary_root/paths"
grep -Eo '[^"[:space:]\\]+\.kt("|\\n)' "$hook_input" 2>/dev/null |
  sed 's/"$//; s/\\n$//' | sort -u >"$paths"

reminded=
while IFS= read -r edited_path; do
  case "$edited_path" in
    /*) edited_file=$edited_path ;;
    *) edited_file="$hook_cwd/$edited_path" ;;
  esac
  [ -f "$edited_file" ] || continue
  grep -Eq '@(Composable|Preview)' "$edited_file" 2>/dev/null || continue
  if [ -n "$state_file" ] && grep -Fxq "$edited_file" "$state_file" 2>/dev/null; then
    continue
  fi
  if [ -n "$state_file" ]; then
    mkdir -p "$state_root" 2>/dev/null && chmod 700 "$state_root" 2>/dev/null
    printf '%s\n' "$edited_file" >>"$state_file" 2>/dev/null || true
  fi
  edited_name=$(basename "$edited_file")
  reminded="${reminded:+$reminded, }$edited_name"
done <"$paths"

[ -n "$reminded" ] || exit 0

message="Compose UI changed in $reminded. Before calling this change done, render an affected preview with render_preview and look at the result (R1). If rendering fails or is unavailable, say so instead."
json_message=$(harness_json_string "$message" 2>/dev/null) || exit 0
printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}\n' "$json_message"
