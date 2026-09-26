#!/usr/bin/env bash
# Logs a hook invocation without changing the host's decision. The harness provides stdin.
set -euo pipefail

event_name="${1:?hook event name is required}"
python3 -c '
import json
import os
import sys
from pathlib import Path

event = sys.argv[1]
stdin = sys.stdin.read()
detection_keys = (
    "ANTIGRAVITY_CLI_ALIAS",
    "CLAUDECODE",
    "CLAUDE_PLUGIN_ROOT",
    "CODEX_THREAD_ID",
    "GEMINI_CLI",
    "OPENCODE",
    "__CFBundleIdentifier",
)
record = {
    "event": event,
    "probe": "SPIKE-SESSION-START" if event == "session-start" else None,
    "environmentKeys": sorted(os.environ),
    "detectionEnvironment": {key: os.environ[key] for key in detection_keys if key in os.environ},
    "stdin": stdin,
}
log_path = Path(os.environ.get("SPIKE_HOOK_LOG_PATH", "/tmp/spike-hooks.log"))
with log_path.open("a", encoding="utf-8") as log:
    log.write(json.dumps(record, sort_keys=True) + "\n")
' "$event_name"

if [[ "$event_name" == "session-start" ]]; then
  printf '%s\n' 'SPIKE-SESSION-START'
fi

# The hosts' decision contracts differ. Keep the default non-blocking so this fixture only observes.
if [[ "${SPIKE_HOOK_DECISION:-}" == "continue" ]]; then
  printf '%s\n' '{"decision":"continue","reason":"run spike check"}'
elif [[ "${SPIKE_HOOK_DECISION:-}" == "block" ]]; then
  printf '%s\n' '{"decision":"block","reason":"run spike check"}'
fi
