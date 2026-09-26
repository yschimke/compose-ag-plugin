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
