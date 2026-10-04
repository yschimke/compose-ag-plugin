#!/usr/bin/env python3
"""Run antigravity-install.py against a fake agy holding the 2026-10-02 state (#39)."""

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "antigravity-install.py"

# A fake `agy plugin` that keeps its imports in $AGY_STATE. `uninstall` removes
# one entry per call, as two same-named entries need two uninstalls.
FAKE_AGY = r'''#!/usr/bin/env python3
import json, os, sys
state = os.environ["AGY_STATE"]
imports = json.load(open(state))
args = sys.argv[2:]
with open(state + ".log", "a") as log:
    log.write(" ".join(args) + "\n")
if args[0] == "list":
    print(json.dumps({"imports": imports}, indent=2))
elif args[0] == "uninstall":
    for i, entry in enumerate(imports):
        if entry["name"] == args[1]:
            del imports[i]
            print(f'Uninstalled plugin "{args[1]}"')
            break
elif args[0] == "install":
    name = args[1].rstrip("/").rsplit("/", 1)[-1]
    imports.append({"name": name, "source": "antigravity", "importedAt": "now"})
    print(f"  [ok]    {name}")
json.dump(imports, open(state, "w"))
'''

BEFORE = [
    {"name": "compose-preview", "source": "antigravity", "importedAt": "2026-09-27T10:16:45Z"},
    {"name": "compose-preview", "source": "gemini-cli", "importedAt": "2026-10-02T15:35:11Z"},
    {"name": "compose-catalogs", "source": "antigravity", "importedAt": "2026-10-02T15:40:53Z"},
    {"name": "yschimke-skills", "source": "antigravity", "importedAt": "2026-10-02T15:45:30Z"},
]


def run(tmp: Path, *args: str) -> tuple[subprocess.CompletedProcess, list[dict], list[str]]:
    state = tmp / "state.json"
    state.write_text(json.dumps(BEFORE))
    log = tmp / "state.json.log"
    log.unlink(missing_ok=True)
    env = dict(os.environ, AGY_STATE=str(state), PATH=f"{tmp}{os.pathsep}{os.environ['PATH']}")
    result = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=env)
    calls = [line for line in log.read_text().splitlines() if line != "list"]
    return result, json.loads(state.read_text()), calls


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        agy = tmp / "agy"
        agy.write_text(FAKE_AGY)
        agy.chmod(agy.stat().st_mode | stat.S_IEXEC)
        # pkill is not needed for the test and must not touch real processes.
        (tmp / "pkill").write_text("#!/bin/sh\nexit 1\n")
        (tmp / "pkill").chmod(0o755)

        result, after, calls = run(tmp)
        assert result.returncode == 0, result.stdout + result.stderr
        assert sorted((e["name"], e["source"]) for e in after) == [
            ("compose-catalogs", "antigravity"),
            ("compose-preview", "antigravity"),
            ("compose-skills", "antigravity"),
        ], after
        assert all(e["importedAt"] == "now" for e in after), after
        assert calls.count("uninstall compose-preview") == 2, calls
        assert "uninstall yschimke-skills" in calls, calls
        assert calls[-1] == "enable compose-preview", calls
        installs = [c for c in calls if c.startswith("install ")]
        assert installs == [
            "install https://github.com/yschimke/skills/tree/main/plugins/compose-skills",
            "install https://github.com/yschimke/compose-agent-plugins/tree/main/plugins/compose-preview",
            "install https://github.com/yschimke/compose-agent-plugins/tree/main/plugins/compose-catalogs",
        ], installs

        result, after, calls = run(tmp, "--dry-run")
        assert result.returncode == 0, result.stdout + result.stderr
        assert after == BEFORE and calls == [], calls
        assert "$ agy plugin install https://github.com/yschimke/compose-agent-plugins/tree/main/plugins/compose-preview" in result.stdout
    print("antigravity install tests passed")


if __name__ == "__main__":
    main()
