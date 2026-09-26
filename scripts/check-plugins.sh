#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repository_root"

python3 scripts/generate.py
git diff --exit-code -- . ':!src/plugins.json'

while IFS= read -r -d '' json_file; do
  python3 -m json.tool "$json_file" >/dev/null
done < <(find . -name '*.json' -not -path './.git/*' -print0)

python3 scripts/validate_manifests.py
tests/harness_test.sh
python3 tests/spike_fixture_test.py
