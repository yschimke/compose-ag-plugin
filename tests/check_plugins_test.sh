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
