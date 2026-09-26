#!/usr/bin/env bash
# Logs a hook invocation without changing the host's decision. The harness provides stdin.
set -euo pipefail

event_name="${1:?hook event name is required}"
payload="$(cat)"
python3 - "$event_name" "$payload" <<'PY'
import json
import os
import sys
from pathlib import Path

event, stdin = sys.argv[1:]
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
    "environmentKeys": sorted(os.environ),
    "detectionEnvironment": {key: os.environ[key] for key in detection_keys if key in os.environ},
    "stdin": stdin,
}
with Path("/tmp/spike-hooks.log").open("a", encoding="utf-8") as log:
    log.write(json.dumps(record, sort_keys=True) + "\n")
PY

# The hosts' decision contracts differ. Keep the default non-blocking so this fixture only observes.
if [[ "${SPIKE_HOOK_DECISION:-}" == "continue" ]]; then
  printf '%s\n' '{"decision":"continue","reason":"run spike check"}'
elif [[ "${SPIKE_HOOK_DECISION:-}" == "block" ]]; then
  printf '%s\n' '{"decision":"block","reason":"run spike check"}'
fi
