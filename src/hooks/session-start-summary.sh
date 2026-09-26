#!/bin/sh
# Emit a safe SessionStart context summary for Claude Code and Codex.
#
# Probe capabilities before invoking them so an older installation remains a
# silent no-op. Every subprocess is bounded independently and receives closed
# stdin, so neither a help probe nor a status command can accidentally become a
# long-running stdio server. Diagnostics may include machine-specific paths,
# configuration details or credentials, so only fixed statuses and the CLI's
# strictly validated summary grammar are surfaced.

probe_timeout_seconds=3
temporary_root=$(mktemp -d "${TMPDIR:-/tmp}/compose-preview-session-start.XXXXXX") || exit 0
probe_pid=

cleanup() {
  if [ -n "$probe_pid" ]; then
    cleanup_probe_pid=$probe_pid
    probe_pid=
    kill "$cleanup_probe_pid" 2>/dev/null || true
    kill -KILL "$cleanup_probe_pid" 2>/dev/null || true
  fi
  rm -rf "$temporary_root"
}

trap 'cleanup' EXIT
trap 'cleanup; exit 129' HUP
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

run_probe() {
  probe_output=$1
  probe_marker=$2
  shift 2
  : >"$probe_output"
  rm -f "$probe_marker"

  "$@" </dev/null >"$probe_output" 2>/dev/null &
  probe_pid=$!
  probe_ticks=0
  probe_tick_limit=$((probe_timeout_seconds * 10))
  while kill -0 "$probe_pid" 2>/dev/null && [ "$probe_ticks" -lt "$probe_tick_limit" ]; do
    sleep 0.1
    probe_ticks=$((probe_ticks + 1))
  done
  if kill -0 "$probe_pid" 2>/dev/null; then
    : >"$probe_marker"
    kill "$probe_pid" 2>/dev/null || true
    probe_grace_ticks=0
    while kill -0 "$probe_pid" 2>/dev/null && [ "$probe_grace_ticks" -lt 5 ]; do
      sleep 0.1
      probe_grace_ticks=$((probe_grace_ticks + 1))
    done
    if kill -0 "$probe_pid" 2>/dev/null; then
      kill -KILL "$probe_pid" 2>/dev/null || true
    fi
  fi
  wait "$probe_pid" 2>/dev/null
  probe_status=$?
  probe_pid=

  if [ -f "$probe_marker" ]; then
    return 124
  fi
  return "$probe_status"
}

emit_context() {
  printf '%s\n' "{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"$1\"}}"
}

context_message=

append_context() {
  if [ -n "$context_message" ]; then
    context_message="$context_message $1"
  else
    context_message=$1
  fi
}

safe_status_summary() {
  grep -Eq '^([0-9]+ unacknowledged design comments?|[0-9]+ unsaved temporary (copy|copies)|design inventory unavailable for [0-9]+ workspace-linked designs?)(; ([0-9]+ unsaved temporary (copy|copies)|design inventory unavailable for [0-9]+ workspace-linked designs?))?(; design inventory unavailable for [0-9]+ workspace-linked designs?)?\.$' "$1"
}

if ! command -v compose-preview >/dev/null 2>&1; then
  emit_context "Compose Preview needs setup: compose-preview is not available on PATH."
  exit 0
fi

help_output="$temporary_root/help.out"
if run_probe "$help_output" "$temporary_root/help.timed-out" compose-preview mcp --help; then
  help_status=0
else
  help_status=$?
fi
if [ "$help_status" -eq 124 ]; then
  append_context "The MCP capability probe timed out."
elif [ "$help_status" -ne 0 ]; then
  append_context "The MCP capability probe failed."
elif grep -Eq '(^|[[:space:]])doctor([[:space:]]|$)' "$help_output"; then
  doctor_output="$temporary_root/doctor.out"
  if run_probe "$doctor_output" "$temporary_root/doctor.timed-out" compose-preview mcp doctor --json; then
    doctor_status=0
  else
    doctor_status=$?
  fi
  if [ "$doctor_status" -eq 124 ]; then
    append_context "MCP doctor timed out."
  elif [ "$doctor_status" -ne 0 ]; then
    append_context "MCP doctor failed."
  fi
fi

design_help_output="$temporary_root/design-help.out"
if run_probe "$design_help_output" "$temporary_root/design-help.timed-out" compose-preview design --help; then
  design_help_status=0
else
  design_help_status=$?
fi
if [ "$design_help_status" -eq 124 ]; then
  append_context "The design-status capability probe timed out."
elif [ "$design_help_status" -ne 0 ]; then
  append_context "The design-status capability probe failed."
elif grep -Eq '(^|[[:space:]])status([[:space:]]|$)' "$design_help_output"; then
  status_output="$temporary_root/status.out"
  workspace_root=${CLAUDE_PROJECT_DIR:-$PWD}
  if run_probe "$status_output" "$temporary_root/status.timed-out" \
    compose-preview design status --workspace "$workspace_root" --summary --timeout 2; then
    status_status=0
  else
    status_status=$?
  fi
  if [ "$status_status" -eq 124 ]; then
    append_context "Workspace design status timed out."
  elif [ "$status_status" -ne 0 ]; then
    append_context "Workspace design status failed."
  elif [ -s "$status_output" ]; then
    status_lines=$(wc -l <"$status_output" | tr -d '[:space:]')
    if [ "$status_lines" = 1 ] && safe_status_summary "$status_output"; then
      status_summary=$(sed -n '1p' "$status_output")
      append_context "$status_summary"
    else
      append_context "Workspace design status returned an unreadable summary."
    fi
  fi
fi

if [ -n "$context_message" ]; then
  emit_context "Compose Preview needs attention: $context_message"
fi
