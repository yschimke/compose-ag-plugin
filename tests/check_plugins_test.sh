#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
temporary_root="$(mktemp -d)"
fixture="$temporary_root/repository"
trap 'rm -rf "$temporary_root"' EXIT

mkdir "$fixture"
tar -C "$repository_root" --exclude=.git -cf - . | tar -C "$fixture" -xf -
git -C "$fixture" init --quiet
git -C "$fixture" config user.email test@example.invalid
git -C "$fixture" config user.name 'Plugin test'
git -C "$fixture" add .
git -C "$fixture" commit --quiet -m 'test fixture'

touch "$fixture/unrelated-user-note.txt"
"$fixture/scripts/check-plugins.sh"

python3 -c '
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
expected = "${COMPOSE_PREVIEW_TOKEN:-}"
for relative in ("plugins/compose-catalogs/.mcp.json", "plugins/compose-catalogs/mcp_config.json"):
    data = json.loads((root / relative).read_text(encoding="utf-8"))
    actual = data["mcpServers"]["compose-preview-catalog"]["headers"]["X-Compose-Preview-Token"]
    if actual != expected:
        raise SystemExit(f"{relative}: expected {expected!r}, got {actual!r}")
' "$fixture"

cp "$fixture/src/plugins.json" "$fixture/src/plugins.json.valid-version"
for invalid_version in next '1.2.3٣'; do
  cp "$fixture/src/plugins.json.valid-version" "$fixture/src/plugins.json"
  python3 -c '
import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
data = json.loads(source.read_text(encoding="utf-8"))
data["plugins"][0]["version"] = sys.argv[2]
source.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
' "$fixture/src/plugins.json" "$invalid_version"
  if python3 "$fixture/scripts/generate.py" >"$fixture/invalid-version.out" 2>"$fixture/invalid-version.err"; then
    printf '%s\n' "FAIL: non-semver Codex plugin version $invalid_version must fail generation" >&2
    exit 1
  fi
  grep -q 'version must use strict semver' "$fixture/invalid-version.err"
done
mv "$fixture/src/plugins.json.valid-version" "$fixture/src/plugins.json"

cp "$fixture/src/plugins.json" "$fixture/src/plugins.json.valid-interface"
for invalid_interface_field in displayName capability defaultPrompt; do
  cp "$fixture/src/plugins.json.valid-interface" "$fixture/src/plugins.json"
  python3 -c '
import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
field = sys.argv[2]
data = json.loads(source.read_text(encoding="utf-8"))
interface = data["plugins"][0]["interface"]
if field == "capability":
    interface["capabilities"][0] = "   "
elif field == "defaultPrompt":
    interface["defaultPrompt"][0] = "   "
else:
    interface[field] = "   "
source.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
' "$fixture/src/plugins.json" "$invalid_interface_field"
  if python3 "$fixture/scripts/generate.py" >"$fixture/invalid-interface.out" 2>"$fixture/invalid-interface.err"; then
    printf '%s\n' "FAIL: whitespace-only Codex interface field $invalid_interface_field must fail generation" >&2
    exit 1
  fi
  grep -q 'must be a non-empty string' "$fixture/invalid-interface.err"
done
mv "$fixture/src/plugins.json.valid-interface" "$fixture/src/plugins.json"

for plugin in compose-catalogs compose-preview; do
  reviewer="$fixture/plugins/$plugin/agents/design-reviewer.md"
  test -f "$reviewer"
  grep -q '^name: design-reviewer$' "$reviewer"
  grep -Fq '"Bash(gh pr view:*)"' "$reviewer"
  grep -Fq '"Bash(gh pr comment:*)"' "$reviewer"
  grep -Fq '"Bash(gh issue view:*)"' "$reviewer"
  grep -Fq '"Bash(gh issue comment:*)"' "$reviewer"
  if grep -Eq '"(Bash|Edit|Write)"' "$reviewer"; then
    printf '%s\n' 'FAIL: reviewer must not receive unrestricted mutation tools' >&2
    exit 1
  fi
done

hook="$fixture/plugins/compose-preview/hooks/hooks.json"
test -f "$hook"
grep -q '"SessionStart"' "$hook"
grep -q 'session-start-summary.sh' "$hook"
python3 -c '
import json
import sys
from pathlib import Path

entry = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["hooks"]["SessionStart"][0]
assert entry["matcher"] == "startup", entry
assert entry["hooks"][0]["timeout"] == 10, entry
' "$hook"

# The hook generator is event-generic so the future opt-in Stop gate can use
# the same source-of-truth rather than bypassing generated manifests.
cp "$fixture/src/plugins.json" "$fixture/src/plugins.json.before-stop"
printf '%s\n' '#!/bin/sh' 'exit 0' >"$fixture/src/hooks/future-stop.sh"
chmod +x "$fixture/src/hooks/future-stop.sh"
python3 -c '
import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
data = json.loads(source.read_text(encoding="utf-8"))
preview = next(plugin for plugin in data["plugins"] if plugin["name"] == "compose-preview")
preview["hooks"].append({"event": "Stop", "command": "scripts/future-stop.sh", "timeout": 15})
source.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
' "$fixture/src/plugins.json"
python3 "$fixture/scripts/generate.py"
python3 -c '
import json
import sys
from pathlib import Path

hooks = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["hooks"]
assert hooks["Stop"][0]["hooks"][0] == {
    "command": "${CLAUDE_PLUGIN_ROOT}/scripts/future-stop.sh",
    "timeout": 15,
    "type": "command",
}
' "$hook"
test -x "$fixture/plugins/compose-preview/scripts/future-stop.sh"
mv "$fixture/src/plugins.json.before-stop" "$fixture/src/plugins.json"
rm "$fixture/src/hooks/future-stop.sh"
python3 "$fixture/scripts/generate.py"
test ! -e "$fixture/plugins/compose-preview/scripts/future-stop.sh"

stale_hook="$fixture/plugins/compose-preview/scripts/obsolete-hook.sh"
printf '%s\n' '#!/bin/sh' 'exit 0' >"$stale_hook"
if "$fixture/scripts/check-plugins.sh" >"$fixture/stale-hook.out" 2>"$fixture/stale-hook.err"; then
  printf '%s\n' 'expected stale generated hook check to fail' >&2
  exit 1
fi
grep -q 'compose-preview has stale generated hooks: obsolete-hook.sh' "$fixture/stale-hook.err"
rm "$stale_hook"

cp "$fixture/src/plugins.json" "$fixture/src/plugins.json.saved"
python3 -c '
import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
data = json.loads(source.read_text(encoding="utf-8"))
next(plugin for plugin in data["plugins"] if plugin["name"] == "compose-preview")["hooks"] = []
source.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
' "$fixture/src/plugins.json"
python3 "$fixture/scripts/generate.py"
if test -e "$fixture/plugins/compose-preview/scripts/session-start-summary.sh"; then
  printf '%s\n' 'FAIL: generator must remove scripts from its previous hook manifest' >&2
  exit 1
fi
test ! -e "$fixture/plugins/compose-preview/hooks/hooks.json"
if python3 "$fixture/scripts/check_generated.py" >"$fixture/deleted-hook.out" 2>"$fixture/deleted-hook.err"; then
  printf '%s\n' 'FAIL: deleted generated hooks must fail the drift check' >&2
  exit 1
fi
grep -q 'generated files differ from their checked-out versions' "$fixture/deleted-hook.err"
mv "$fixture/src/plugins.json.saved" "$fixture/src/plugins.json"
python3 "$fixture/scripts/generate.py"

handwritten_agent="$fixture/plugins/compose-preview/agents/handwritten-reviewer.md"
printf '%s\n' 'handwritten' >"$handwritten_agent"
python3 -c '
import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
data = json.loads(source.read_text(encoding="utf-8"))
next(plugin for plugin in data["plugins"] if plugin["name"] == "compose-preview")["agents"] = []
source.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
' "$fixture/src/plugins.json"
python3 "$fixture/scripts/generate.py"
if test -e "$fixture/plugins/compose-preview/agents/design-reviewer.md"; then
  printf '%s\n' 'FAIL: generator must remove agents recorded in its ledger' >&2
  exit 1
fi
if ! test -e "$handwritten_agent"; then
  printf '%s\n' 'FAIL: generator must preserve hand-written agents absent from its ledger' >&2
  exit 1
fi

mkdir "$fixture/plugins/stale-plugin"
if "$fixture/scripts/check-plugins.sh" >/dev/null 2>&1; then
  printf '%s\n' 'FAIL: stale plugin directory must fail generated drift check' >&2
  exit 1
fi
rmdir "$fixture/plugins/stale-plugin"

git -C "$fixture" rm --cached --quiet -r plugins/compose-preview
if "$fixture/scripts/check-plugins.sh" >/dev/null 2>&1; then
  printf '%s\n' 'FAIL: untracked generated plugin files must fail generated drift check' >&2
  exit 1
fi

printf '%s\n' 'plugin drift tests passed'
