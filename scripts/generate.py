#!/usr/bin/env python3
"""Generate cross-harness plugin manifests from src/plugins.json."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "plugins.json"
SKILL_SOURCE_ROOT = ROOT / "src" / "skills"
AGENT_SOURCE_ROOT = ROOT / "src" / "agents"
AGENT_LEDGER_NAME = ".generated-agents.json"
ANTIGRAVITY_SCHEMA = "https://antigravity.google/schemas/v1/plugin.json"
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def write_skill(plugin_root: Path, skill: str) -> None:
    if not SKILL_NAME.fullmatch(skill):
        raise ValueError(f"invalid skill name: {skill}")
    source = SKILL_SOURCE_ROOT / skill / "SKILL.md"
    if not source.is_file():
        raise ValueError(f"missing shared skill source: {source.relative_to(ROOT)}")
    target = plugin_root / "skills" / skill / "SKILL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def write_agent(plugin_root: Path, agent: str) -> None:
    if not SKILL_NAME.fullmatch(agent):
        raise ValueError(f"invalid agent name: {agent}")
    source = AGENT_SOURCE_ROOT / f"{agent}.md"
    if not source.is_file():
        raise ValueError(f"missing shared agent source: {source.relative_to(ROOT)}")
    target = plugin_root / "agents" / f"{agent}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def synchronize_generated_agents(plugin_root: Path, agents: list[str]) -> None:
    agents_root = plugin_root / "agents"
    ledger = agents_root / AGENT_LEDGER_NAME
    previous: list[str] = []
    if ledger.is_file():
        value = json.loads(ledger.read_text(encoding="utf-8"))
        if (
            not isinstance(value, dict)
            or not isinstance(value.get("agents"), list)
            or not all(isinstance(agent, str) for agent in value["agents"])
        ):
            raise ValueError(f"invalid generated agent ledger: {ledger.relative_to(ROOT)}")
        previous = value["agents"]
    expected = {f"{agent}.md" for agent in agents}
    for agent in previous:
        agent_path = Path(agent)
        if agent_path.is_absolute() or ".." in agent_path.parts or len(agent_path.parts) != 1:
            raise ValueError(f"invalid generated agent ledger entry: {agent!r}")
        if agent not in expected:
            (agents_root / agent_path).unlink(missing_ok=True)
    if agents:
        write_json(ledger, {"agents": sorted(expected)})
    else:
        ledger.unlink(missing_ok=True)


def render_mcp_servers(plugin_name: str, entries: object, harness: str) -> dict[str, object]:
    if not isinstance(entries, list):
        raise ValueError(f"{plugin_name}.mcp must be a list")

    servers: dict[str, object] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"{plugin_name}.mcp entries must be objects")
        name = require_string(entry.get("name"), f"{plugin_name}.mcp.name")
        kind = require_string(entry.get("kind"), f"{plugin_name}.mcp.{name}.kind")
        if name in servers:
            raise ValueError(f"{plugin_name}.mcp contains duplicate server {name}")
        if kind == "stdio":
            command = require_string(entry.get("command"), f"{plugin_name}.mcp.{name}.command")
            args = entry.get("args", [])
            env = entry.get("env")
            if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
                raise ValueError(f"{plugin_name}.mcp.{name}.args must be a list of strings")
            server: dict[str, object] = {"args": args, "command": command}
            if env is not None:
                if not isinstance(env, dict) or not all(
                    isinstance(key, str) and isinstance(value, str) for key, value in env.items()
                ):
                    raise ValueError(f"{plugin_name}.mcp.{name}.env must map strings to strings")
                server["env"] = env
        elif kind == "http":
            url = require_string(entry.get("url"), f"{plugin_name}.mcp.{name}.url")
            headers = entry.get("headers", {})
            if not isinstance(headers, dict) or not all(
                isinstance(key, str) and isinstance(value, str) for key, value in headers.items()
            ):
                raise ValueError(f"{plugin_name}.mcp.{name}.headers must map strings to strings")
            if harness == "antigravity":
                server = {"headers": headers, "serverUrl": url}
            else:
                server = {"headers": headers, "type": "http", "url": url}
        else:
            raise ValueError(f"{plugin_name}.mcp.{name}.kind must be stdio or http")
        servers[name] = server
    return servers


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    repository = require_string(source.get("repository"), "repository")
    license_name = require_string(source.get("license"), "license")
    owner = require_string(source.get("owner"), "owner")
    plugins = source.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        raise ValueError("plugins must be a non-empty list")

    marketplace_plugins = []
    names: set[str] = set()
    for plugin in plugins:
        if not isinstance(plugin, dict):
            raise ValueError("each plugin must be an object")
        name = require_string(plugin.get("name"), "plugin.name")
        version = require_string(plugin.get("version"), f"{name}.version")
        description = require_string(plugin.get("description"), f"{name}.description")
        keywords = plugin.get("keywords", [])
        skills = plugin.get("skills", [])
        agents = plugin.get("agents", [])
        mcp = plugin.get("mcp", [])
        if name in names:
            raise ValueError(f"duplicate plugin name: {name}")
        if not isinstance(keywords, list) or not all(isinstance(word, str) for word in keywords):
            raise ValueError(f"{name}.keywords must be a list of strings")
        if not isinstance(skills, list) or not all(isinstance(skill, str) for skill in skills):
            raise ValueError(f"{name}.skills must be a list of strings")
        if not isinstance(agents, list) or not all(isinstance(agent, str) for agent in agents):
            raise ValueError(f"{name}.agents must be a list of strings")
        names.add(name)

        root = ROOT / "plugins" / name
        for skill in skills:
            write_skill(root, skill)
        synchronize_generated_agents(root, agents)
        for agent in agents:
            write_agent(root, agent)
        write_json(
            root / "plugin.json",
            {"$schema": ANTIGRAVITY_SCHEMA, "description": description, "name": name},
        )
        write_json(
            root / ".claude-plugin" / "plugin.json",
            {
                "author": {"name": owner},
                "description": description,
                "keywords": keywords,
                "license": license_name,
                "name": name,
                "repository": repository,
                "version": version,
            },
        )
        marketplace_plugins.append(
            {"description": description, "name": name, "source": f"./plugins/{name}"}
        )
        if mcp:
            write_json(
                root / "mcp_config.json",
                {"mcpServers": render_mcp_servers(name, mcp, "antigravity")},
            )
            write_json(
                root / ".mcp.json",
                {"mcpServers": render_mcp_servers(name, mcp, "claude")},
            )
        else:
            (root / "mcp_config.json").unlink(missing_ok=True)
            (root / ".mcp.json").unlink(missing_ok=True)

    write_json(
        ROOT / ".claude-plugin" / "marketplace.json",
        {"name": "compose-ag-plugin", "owner": {"name": owner}, "plugins": marketplace_plugins},
    )


if __name__ == "__main__":
    main()
