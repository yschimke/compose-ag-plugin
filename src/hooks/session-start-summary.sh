#!/bin/sh
# Emit a safe SessionStart context summary for Claude Code and Codex.
#
# A future CLI may expose `compose-preview mcp doctor --json`. Probe the MCP
# help before invoking it: current releases do not have that subcommand, which
# is not actionable and therefore produces no session context. Both subprocesses
# are bounded independently and receive closed stdin so `mcp --help` cannot
# accidentally become a long-running stdio server. Diagnostics may include
# machine-specific paths or configuration details, so only a fixed status is
# surfaced. The current CLI/MCP contracts expose no session-level inventory of
# workspace-linked design comments or temporary copies; #18 remains open until
# those facts can be reported without guessing from local files.

probe_timeout_seconds=3
temporary_root=$(mktemp -d "${TMPDIR:-/tmp}/compose-preview-session-start.XXXXXX") || exit 0
probe_pid=

cleanup() {
  if [ -n "$probe_pid" ]; then
    cleanup_probe_pid=$probe_pid
    probe_pid=
    kill "$cleanup_probe_pid" 2>/dev/null || true
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
  emit_context "Compose Preview needs attention: the MCP capability probe timed out."
  exit 0
fi
if [ "$help_status" -ne 0 ] ||
  ! grep -Eq '(^|[[:space:]])doctor([[:space:]]|$)' "$help_output"; then
  exit 0
fi

doctor_output="$temporary_root/doctor.out"
if run_probe "$doctor_output" "$temporary_root/doctor.timed-out" compose-preview mcp doctor --json; then
  doctor_status=0
else
  doctor_status=$?
fi
if [ "$doctor_status" -eq 0 ]; then
  exit 0
fi
if [ "$doctor_status" -eq 124 ]; then
  emit_context "Compose Preview needs attention: MCP doctor timed out."
else
  emit_context "Compose Preview needs attention: MCP doctor failed."
fi
