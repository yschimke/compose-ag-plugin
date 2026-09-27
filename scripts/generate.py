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
HOOK_SOURCE_ROOT = ROOT / "src" / "hooks"
ASSET_SOURCE_ROOT = ROOT / "src" / "assets"
ASSET_LEDGER_NAME = ".generated-assets.json"
ANTIGRAVITY_SCHEMA = "https://antigravity.google/schemas/v1/plugin.json"
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)(?:\."
    r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
CODEX_INTERFACE_STRINGS = (
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def render_codex_manifest(
    *,
    name: str,
    version: str,
    description: str,
    keywords: list[str],
    skills: list[str],
    mcp: list[object],
    interface: object,
    owner: str,
    repository: str,
    license_name: str,
) -> dict[str, object]:
    if not isinstance(interface, dict):
        raise ValueError(f"{name}.interface must be an object")
    rendered_interface: dict[str, object] = {
        field: require_string(interface.get(field), f"{name}.interface.{field}")
        for field in CODEX_INTERFACE_STRINGS
    }
    capabilities = interface.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise ValueError(f"{name}.interface.capabilities must be a non-empty list of strings")
    rendered_capabilities = [
        require_string(capability, f"{name}.interface.capabilities[{index}]")
        for index, capability in enumerate(capabilities)
    ]
    default_prompt = interface.get("defaultPrompt")
    if not isinstance(default_prompt, list) or not 1 <= len(default_prompt) <= 3:
        raise ValueError(
            f"{name}.interface.defaultPrompt must contain 1 to 3 non-empty strings of at most 128 characters"
        )
    rendered_default_prompt = [
        require_string(prompt, f"{name}.interface.defaultPrompt[{index}]")
        for index, prompt in enumerate(default_prompt)
    ]
    if any(len(prompt) > 128 for prompt in rendered_default_prompt):
        raise ValueError(
            f"{name}.interface.defaultPrompt must contain 1 to 3 non-empty strings of at most 128 characters"
        )
    rendered_interface["capabilities"] = rendered_capabilities
    rendered_interface["defaultPrompt"] = rendered_default_prompt

    manifest: dict[str, object] = {
        "author": {"name": owner},
        "description": description,
        "interface": rendered_interface,
        "keywords": keywords,
        "license": license_name,
        "name": name,
        "repository": repository,
        "version": version,
    }
    if skills:
        manifest["skills"] = "./skills/"
    if mcp:
        manifest["mcpServers"] = render_mcp_servers(name, mcp, "codex")
    return manifest


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


def write_hook(plugin_root: Path, command: str) -> None:
    command_path = Path(command)
    if (
        command_path.is_absolute()
        or ".." in command_path.parts
        or command_path.parts[:1] != ("scripts",)
        or len(command_path.parts) != 2
    ):
        raise ValueError(f"hook command must be a plugin-local script: {command}")
    source = HOOK_SOURCE_ROOT / command_path.name
    if not source.is_file():
        raise ValueError(f"missing shared hook source: {source.relative_to(ROOT)}")
    target = plugin_root / command_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    target.chmod(source.stat().st_mode)


def write_asset(plugin_root: Path, asset: str) -> None:
    asset_path = Path(asset)
    if asset_path.is_absolute() or ".." in asset_path.parts or len(asset_path.parts) != 1:
        raise ValueError(f"asset must be a source-root file name: {asset}")
    source = ASSET_SOURCE_ROOT / asset_path
    if not source.is_file():
        raise ValueError(f"missing shared asset source: {source.relative_to(ROOT)}")
    target = plugin_root / "assets" / asset_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())


def render_hooks(plugin_name: str, entries: object) -> dict[str, object]:
    if not isinstance(entries, list):
        raise ValueError(f"{plugin_name}.hooks must be a list")

    hooks: dict[str, list[dict[str, object]]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"{plugin_name}.hooks entries must be objects")
        event = require_string(entry.get("event"), f"{plugin_name}.hooks.event")
        command = require_string(entry.get("command"), f"{plugin_name}.hooks.command")
        matcher = entry.get("matcher")
        timeout = entry.get("timeout")
        if matcher is not None and (not isinstance(matcher, str) or not matcher):
            raise ValueError(f"{plugin_name}.hooks.{event}.matcher must be a non-empty string")
        if timeout is not None and (
            not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0
        ):
            raise ValueError(f"{plugin_name}.hooks.{event}.timeout must be a positive integer")
        command_path = Path(command)
        if (
            command_path.is_absolute()
            or ".." in command_path.parts
            or command_path.parts[:1] != ("scripts",)
            or len(command_path.parts) != 2
        ):
            raise ValueError(f"{plugin_name}.hooks.command must be a plugin-local script")
        if not (HOOK_SOURCE_ROOT / command_path.name).is_file():
            raise ValueError(
                f"missing shared hook source: {(HOOK_SOURCE_ROOT / command_path.name).relative_to(ROOT)}"
            )
        command_hook: dict[str, object] = {
            "command": f"${{CLAUDE_PLUGIN_ROOT}}/{command}",
            "type": "command",
        }
        if timeout is not None:
            command_hook["timeout"] = timeout
        event_hook: dict[str, object] = {"hooks": [command_hook]}
        if matcher is not None:
            event_hook["matcher"] = matcher
        hooks.setdefault(event, []).append(event_hook)
    return {"hooks": hooks}


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


def remove_obsolete_generated_hooks(plugin_root: Path, hooks: list[object]) -> None:
    """Remove only scripts proven to belong to the previously generated hook manifest."""
    manifest = plugin_root / "hooks" / "hooks.json"
    if not manifest.is_file():
        return
    previous = json.loads(manifest.read_text(encoding="utf-8"))
    expected = {
        Path(hook["command"]).name
        for hook in hooks
        if isinstance(hook, dict) and isinstance(hook.get("command"), str)
    }
    prefix = "${CLAUDE_PLUGIN_ROOT}/scripts/"
    for event_entries in previous.get("hooks", {}).values():
        if not isinstance(event_entries, list):
            continue
        for event_entry in event_entries:
            if not isinstance(event_entry, dict):
                continue
            for hook in event_entry.get("hooks", []):
                if not isinstance(hook, dict):
                    continue
                command = hook.get("command")
                if not isinstance(command, str) or not command.startswith(prefix):
                    continue
                relative = command.removeprefix(prefix)
                if not relative or "/" in relative or relative in expected:
                    continue
                (plugin_root / "scripts" / relative).unlink(missing_ok=True)


def synchronize_generated_assets(plugin_root: Path, assets: list[str]) -> None:
    assets_root = plugin_root / "assets"
    ledger = assets_root / ASSET_LEDGER_NAME
    previous: list[str] = []
    if ledger.is_file():
        value = json.loads(ledger.read_text(encoding="utf-8"))
        if (
            not isinstance(value, dict)
            or not isinstance(value.get("assets"), list)
            or not all(isinstance(asset, str) for asset in value["assets"])
        ):
            raise ValueError(f"invalid generated asset ledger: {ledger.relative_to(ROOT)}")
        previous = value["assets"]
    expected = set(assets)
    for asset in previous:
        asset_path = Path(asset)
        if (
            asset_path.is_absolute()
            or ".." in asset_path.parts
            or len(asset_path.parts) != 1
        ):
            raise ValueError(f"invalid generated asset ledger entry: {asset!r}")
        if asset not in expected:
            (assets_root / asset_path).unlink(missing_ok=True)
    if assets:
        write_json(ledger, {"assets": assets})
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
            elif harness == "codex":
                env_headers = entry.get("codexEnvHeaders", {})
                if not isinstance(env_headers, dict) or not all(
                    isinstance(key, str)
                    and key
                    and isinstance(value, str)
                    and value
                    for key, value in env_headers.items()
                ):
                    raise ValueError(
                        f"{plugin_name}.mcp.{name}.codexEnvHeaders must map header names to environment variable names"
                    )
                if set(env_headers) != set(headers):
                    raise ValueError(
                        f"{plugin_name}.mcp.{name}.codexEnvHeaders must cover the same headers as headers"
                    )
                server = {"env_http_headers": env_headers, "type": "http", "url": url}
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
        if SEMVER.fullmatch(version) is None:
            raise ValueError(f"{name}.version must use strict semver")
        description = require_string(plugin.get("description"), f"{name}.description")
        keywords = plugin.get("keywords", [])
        skills = plugin.get("skills", [])
        agents = plugin.get("agents", [])
        hooks = plugin.get("hooks", [])
        assets = plugin.get("assets", [])
        mcp = plugin.get("mcp", [])
        interface = plugin.get("interface")
        if name in names:
            raise ValueError(f"duplicate plugin name: {name}")
        if not isinstance(keywords, list) or not all(isinstance(word, str) for word in keywords):
            raise ValueError(f"{name}.keywords must be a list of strings")
        if not isinstance(skills, list) or not all(isinstance(skill, str) for skill in skills):
            raise ValueError(f"{name}.skills must be a list of strings")
        if not isinstance(agents, list) or not all(isinstance(agent, str) for agent in agents):
            raise ValueError(f"{name}.agents must be a list of strings")
        if not isinstance(hooks, list):
            raise ValueError(f"{name}.hooks must be a list")
        if not isinstance(assets, list) or not all(isinstance(asset, str) for asset in assets):
            raise ValueError(f"{name}.assets must be a list of strings")
        names.add(name)

        root = ROOT / "plugins" / name
        for skill in skills:
            write_skill(root, skill)
        synchronize_generated_agents(root, agents)
        for agent in agents:
            write_agent(root, agent)
        remove_obsolete_generated_hooks(root, hooks)
        synchronize_generated_assets(root, assets)
        for asset in assets:
            write_asset(root, asset)
        if hooks:
            for hook in hooks:
                write_hook(root, hook["command"])
            write_json(root / "hooks" / "hooks.json", render_hooks(name, hooks))
        else:
            (root / "hooks" / "hooks.json").unlink(missing_ok=True)
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
        write_json(
            root / ".codex-plugin" / "plugin.json",
            render_codex_manifest(
                name=name,
                version=version,
                description=description,
                keywords=keywords,
                skills=skills,
                mcp=mcp,
                interface=interface,
                owner=owner,
                repository=repository,
                license_name=license_name,
            ),
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
