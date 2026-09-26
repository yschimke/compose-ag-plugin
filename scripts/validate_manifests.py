#!/usr/bin/env python3
"""Validate the repository's generated plugin manifest contracts using Python stdlib."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from generate import ANTIGRAVITY_SCHEMA, render_mcp_servers


ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def read_json(path: Path) -> object:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def require_schema_fields(manifest: object, schema_file: str, path: Path) -> None:
    schema = read_json(ROOT / "schemas" / schema_file)
    if not isinstance(manifest, dict) or not isinstance(schema, dict):
        raise ValueError(f"{path}: manifest and schema must be objects")
    required = schema.get("required", [])
    missing = [field for field in required if field not in manifest]
    if missing:
        raise ValueError(f"{path}: missing required schema fields: {', '.join(missing)}")


def validate_skill(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 3 or lines[0] != "---":
        raise ValueError(f"{path}: missing YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ValueError(f"{path}: unterminated YAML frontmatter") from error
    fields = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip().strip('"')
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not NAME.fullmatch(name) or len(name) > 64:
        raise ValueError(f"{path}: name must be lowercase hyphen-case and at most 64 characters")
    if not description or len(description) > 1024:
        raise ValueError(f"{path}: description must be 1 to 1024 characters")


def main() -> None:
    source = read_json(ROOT / "src" / "plugins.json")
    if not isinstance(source, dict):
        raise ValueError("src/plugins.json must be an object")
    plugins = source["plugins"]
    if not isinstance(plugins, list):
        raise ValueError("src/plugins.json plugins must be a list")

    expected_marketplace = []
    for plugin in plugins:
        name = plugin["name"]
        root = ROOT / "plugins" / name
        expected_skills = {
            root / "skills" / skill / "SKILL.md" for skill in plugin.get("skills", [])
        }
        actual_skills = set(root.glob("skills/*/SKILL.md"))
        if actual_skills != expected_skills:
            unexpected = sorted(str(path.relative_to(ROOT)) for path in actual_skills - expected_skills)
            missing = sorted(str(path.relative_to(ROOT)) for path in expected_skills - actual_skills)
            details = []
            if unexpected:
                details.append(f"unexpected skills: {', '.join(unexpected)}")
            if missing:
                details.append(f"missing skills: {', '.join(missing)}")
            raise ValueError(f"{root}: {'; '.join(details)}")
        antigravity = read_json(root / "plugin.json")
        claude = read_json(root / ".claude-plugin" / "plugin.json")
        require_schema_fields(antigravity, "antigravity-plugin.schema.json", root / "plugin.json")
        require_schema_fields(
            claude, "claude-plugin.schema.json", root / ".claude-plugin" / "plugin.json"
        )
        expected_antigravity = {
            "$schema": ANTIGRAVITY_SCHEMA,
            "description": plugin["description"],
            "name": name,
        }
        expected_core = {key: plugin[key] for key in ("name", "version", "description")}
        if antigravity != expected_antigravity:
            raise ValueError(f"{root}/plugin.json does not match the Antigravity contract")
        if any(claude.get(key) != value for key, value in expected_core.items()):
            raise ValueError(f"{root}/.claude-plugin/plugin.json does not match the Claude/Codex contract")
        if claude.get("author") != {"name": source["owner"]}:
            raise ValueError(f"{root}/.claude-plugin/plugin.json has an invalid author")
        if claude.get("repository") != source["repository"] or claude.get("license") != source["license"]:
            raise ValueError(f"{root}/.claude-plugin/plugin.json has invalid package metadata")
        if claude.get("keywords") != plugin.get("keywords", []):
            raise ValueError(f"{root}/.claude-plugin/plugin.json has invalid keywords")
        for skill_path in expected_skills:
            validate_skill(skill_path)
        mcp = plugin.get("mcp", [])
        if mcp:
            antigravity_mcp = read_json(root / "mcp_config.json")
            claude_mcp = read_json(root / ".mcp.json")
            if antigravity_mcp != {
                "mcpServers": render_mcp_servers(name, mcp, "antigravity")
            }:
                raise ValueError(f"{root}/mcp_config.json does not match the MCP contract")
            if claude_mcp != {"mcpServers": render_mcp_servers(name, mcp, "claude")}:
                raise ValueError(f"{root}/.mcp.json does not match the MCP contract")
        elif (root / "mcp_config.json").exists() or (root / ".mcp.json").exists():
            raise ValueError(f"{root} contains stale MCP configuration")
        expected_marketplace.append(
            {"description": plugin["description"], "name": name, "source": f"./plugins/{name}"}
        )

    marketplace = read_json(ROOT / ".claude-plugin" / "marketplace.json")
    if marketplace != {
        "name": "compose-ag-plugin",
        "owner": {"name": source["owner"]},
        "plugins": expected_marketplace,
    }:
        raise ValueError(".claude-plugin/marketplace.json does not match the marketplace contract")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(f"plugin validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
