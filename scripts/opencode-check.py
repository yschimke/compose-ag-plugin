#!/usr/bin/env python3
"""Check an OpenCode (v1.18+ or v2) setup for the compose-preview skills and MCP servers (#42).

  python3 scripts/opencode-check.py                 # read-only checks, no model
  python3 scripts/opencode-check.py --run --project ~/path/to/app [--preview ListScreenPreview]
                                                    # plus one real model turn, timed

Prints one line per check (ok / FIX / info). Command output that didn't parse is
saved under /tmp/opencode-check/ so it can be shared instead of pasted.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
LOGS = Path(os.environ.get("TMPDIR", "/tmp")) / "opencode-check"
SKILLS = ("compose-preview", "compose-ui-builder")
SERVERS = ("compose-preview-mcp", "compose-preview-catalog")
MIN_V1 = (1, 18)
results = []


def report(status: str, message: str) -> None:
    results.append(status)
    print(f"{status:<4} {message}")


def run(opencode: str, args: list, timeout: int = 60, cwd=None) -> tuple:
    try:
        done = subprocess.run([opencode, *args], capture_output=True, text=True,
                              timeout=timeout, cwd=cwd)
        return done.returncode, done.stdout + done.stderr
    except subprocess.TimeoutExpired as error:
        return 124, f"timed out after {timeout}s\n{error.stdout or ''}"
    except OSError as error:
        return 127, str(error)


def save(name: str, text: str) -> Path:
    LOGS.mkdir(parents=True, exist_ok=True)
    path = LOGS / f"{name}.log"
    path.write_text(text)
    return path


def check_version(opencode: str) -> None:
    _, out = run(opencode, ["--version"])
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", out)
    version = match.group(0) if match else out.strip()[:40]
    major, minor = (int(match.group(1)), int(match.group(2))) if match else (0, 0)
    if major >= 2:
        report("ok", f"opencode {version} ({opencode})")
    elif (major, minor) >= MIN_V1:
        # 1.18.32 (npm `latest`) parses the v2 `mcp.servers` shape that `mcp install` writes.
        report("ok", f"opencode {version} ({opencode}); v1 accepts the mcp.servers config")
    else:
        report("FIX", f"opencode {version or 'unknown'}: needs 1.18 or later "
                      "(install/upgrade per https://opencode.ai/docs)")


def check_skills(opencode: str) -> None:
    root = HOME / ".agents" / "skills"
    for skill in SKILLS:
        present = (root / skill / "SKILL.md").is_file()
        report("ok" if present else "FIX", f"skill {skill} in {root}" if present else
               f"skill {skill} missing: npx skills add yschimke/skills --global --yes "
               "--skill compose-preview --skill compose-ui-builder")
    code, out = run(opencode, ["debug", "skill"])
    if code != 0:
        report("info", f"`opencode debug skill` unavailable (exit {code}); log {save('debug-skill', out)}")
        return
    for skill in SKILLS:
        seen = skill in out
        report("ok" if seen else "FIX", f"opencode discovers skill {skill}" if seen else
               f"opencode does not list skill {skill}; log {save('debug-skill', out)}")


def config_files(project) -> list:
    base = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "opencode"
    names = ("opencode.json", "opencode.jsonc", "config.json")
    files = [base / n for n in names]
    if project:
        files += [Path(project) / n for n in names] + [Path(project) / ".opencode" / n for n in names]
    return [f for f in files if f.is_file()]


def check_config(project) -> None:
    files = config_files(project)
    if not files:
        report("FIX", "no opencode config found; run: compose-preview mcp install --opencode")
        return
    text = "\n".join(f.read_text(errors="replace") for f in files)
    report("info", "config: " + ", ".join(str(f) for f in files))
    for server in SERVERS:
        found = f'"{server}"' in text
        if found:
            report("ok", f"{server} configured")
        elif server != "compose-preview-mcp":
            report("info", f"{server} not in config (optional: hosted catalog)")
        else:
            jsonc = next((f for f in files if not is_strict_json(f)), None)
            if jsonc:
                # `mcp install --opencode` refuses to rewrite JSONC, so re-running it can't fix this.
                report("FIX", f"{server} not in config; {jsonc} is JSONC, which "
                              "`compose-preview mcp install --opencode` will not rewrite. "
                              "Merge this into it by hand:")
                print(local_server_snippet())
            else:
                report("FIX", f"{server} not in config (compose-preview mcp install --opencode)")


def is_strict_json(path: Path) -> bool:
    if path.suffix == ".jsonc":
        return False
    try:
        json.loads(path.read_text(errors="replace"))
        return True
    except ValueError:
        return False


def local_server_snippet() -> str:
    launcher = shutil.which("compose-preview") or "compose-preview"
    entry = {"servers": {"compose-preview-mcp": {
        "type": "local", "command": [launcher, "mcp", "serve"], "codemode": False}}}
    return "\n".join("     " + line for line in json.dumps({"mcp": entry}, indent=2).splitlines())


def check_mcp_list(opencode: str, project) -> None:
    code, out = run(opencode, ["mcp", "list"], timeout=120, cwd=project)
    if code != 0 and not out.strip():
        report("FIX", f"`opencode mcp list` failed (exit {code})")
        return
    log = save("mcp-list", out)
    for server in SERVERS:
        line = next((l for l in out.splitlines() if server in l), "")
        if not line:
            report("info", f"{server}: not listed")
        elif re.search(r"connected|ready|✓", line, re.I) and not re.search(r"fail|error|disconnect", line, re.I):
            report("ok", f"{server}: {line.strip()[:100]}")
        else:
            report("FIX", f"{server}: {line.strip()[:100]} (log {log})")


def model_turn(opencode: str, project: str, preview: str) -> None:
    prompt = (f"render the {preview} preview with the compose-preview-mcp render_preview tool "
              "(inline=false), then reply with 2 bullets and the pngPath")
    start = time.time()
    code, out = run(opencode, ["run", "--format", "json", prompt], timeout=600, cwd=project)
    if code != 0 and "format" in out.lower():  # older/other CLI without --format json
        code, out = run(opencode, ["run", prompt], timeout=600, cwd=project)
    elapsed = time.time() - start
    log = save("run", out)
    tools = re.findall(r'"tool"\s*:\s*"([^"]+)"', out)
    rendered = "render_preview" in out and re.search(r"\.png", out) is not None
    report("ok" if rendered else "FIX",
           f"model turn: {elapsed:.0f}s, exit {code}, render {'seen' if rendered else 'NOT seen'}; log {log}")
    if tools:
        report("info", f"tool calls ({len(tools)}): {', '.join(tools[:12])}")
    budget = elapsed <= 30 and (not tools or len(tools) <= 3)
    report("ok" if budget else "info", "token budget (≤3 calls, ≤30 s, #39): " + ("met" if budget else "missed"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--opencode", default=shutil.which("opencode"), help="opencode binary")
    parser.add_argument("--project", help="Gradle project with @Previews (needed for --run)")
    parser.add_argument("--preview", default="ListScreenPreview")
    parser.add_argument("--run", action="store_true", help="also run one real model turn")
    args = parser.parse_args()
    project = str(Path(args.project).expanduser()) if args.project else None

    print("OpenCode check (#42)")
    if not args.opencode:
        report("FIX", "opencode not on PATH (install: https://opencode.ai/docs)")
        sys.exit(1)
    check_version(args.opencode)
    report("ok" if shutil.which("compose-preview") else "FIX",
           "compose-preview CLI on PATH" if shutil.which("compose-preview") else
           "compose-preview not on PATH (compose-preview update / open a new terminal)")
    check_skills(args.opencode)
    check_config(project)
    check_mcp_list(args.opencode, project)
    if args.run:
        if not project:
            report("FIX", "--run needs --project <gradle project>")
        else:
            model_turn(args.opencode, project, args.preview)
    else:
        print("\nNext: add --run --project <app> for one timed model turn.")
    print(f"Logs: {LOGS}")
    sys.exit(1 if "FIX" in results else 0)


if __name__ == "__main__":
    main()
