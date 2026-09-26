#!/usr/bin/env python3
"""Reject generated-plugin drift without inspecting unrelated working files."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "plugins.json"


def generated_paths(source: object) -> tuple[list[Path], set[str]]:
    if not isinstance(source, dict) or not isinstance(source.get("plugins"), list):
        raise ValueError("src/plugins.json plugins must be a list")

    paths = [ROOT / ".claude-plugin" / "marketplace.json"]
    plugin_names: set[str] = set()
    for plugin in source["plugins"]:
        if not isinstance(plugin, dict) or not isinstance(plugin.get("name"), str):
            raise ValueError("each plugin must have a name")
        name = plugin["name"]
        if name in plugin_names:
            raise ValueError(f"duplicate plugin name: {name}")
        plugin_names.add(name)
        plugin_root = ROOT / "plugins" / name
        paths.extend((plugin_root / "plugin.json", plugin_root / ".claude-plugin" / "plugin.json"))
        if plugin.get("mcp"):
            paths.extend((plugin_root / "mcp_config.json", plugin_root / ".mcp.json"))
        skills = plugin.get("skills", [])
        if not isinstance(skills, list) or not all(isinstance(skill, str) for skill in skills):
            raise ValueError(f"{name}.skills must be a list of strings")
        paths.extend(plugin_root / "skills" / skill / "SKILL.md" for skill in skills)
        agents = plugin.get("agents", [])
        if not isinstance(agents, list) or not all(isinstance(agent, str) for agent in agents):
            raise ValueError(f"{name}.agents must be a list of strings")
        paths.extend(plugin_root / "agents" / f"{agent}.md" for agent in agents)
    return paths, plugin_names


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=False, text=True, capture_output=True
    )


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    paths, plugin_names = generated_paths(source)
    errors = []

    missing = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
    if missing:
        errors.append(f"missing generated files: {', '.join(sorted(missing))}")

    plugins_root = ROOT / "plugins"
    actual_dirs = {path.name for path in plugins_root.iterdir() if path.is_dir()}
    stale_dirs = actual_dirs - plugin_names
    if stale_dirs:
        errors.append(f"stale plugin directories: {', '.join(sorted(stale_dirs))}")

    for plugin in source["plugins"]:
        name = plugin["name"]
        expected_agents = {f"{agent}.md" for agent in plugin.get("agents", [])}
        agents_root = plugins_root / name / "agents"
        actual_agents = (
            {path.name for path in agents_root.glob("*.md")} if agents_root.is_dir() else set()
        )
        stale_agents = actual_agents - expected_agents
        if stale_agents:
            errors.append(
                f"{name} has stale generated agents: {', '.join(sorted(stale_agents))}"
            )

    pathspecs = [str(path.relative_to(ROOT)) for path in paths]
    diff = git("diff", "--exit-code", "--", *pathspecs)
    if diff.returncode:
        errors.append("generated files differ from their checked-out versions")

    status = git("status", "--porcelain", "--untracked-files=all", "--", *pathspecs)
    if status.returncode:
        errors.append(f"could not inspect generated files: {status.stderr.strip()}")
    elif status.stdout:
        errors.append("generated files have untracked or staged changes:\n" + status.stdout.rstrip())

    if errors:
        raise ValueError("\n".join(errors))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"generated plugin check failed: {error}", file=sys.stderr)
        raise SystemExit(1)
