#!/usr/bin/env python3
"""Validate the repository's generated plugin manifest contracts using Python stdlib."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from generate import ANTIGRAVITY_SCHEMA, SKILL_SOURCE_ROOT, render_mcp_servers


ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SCHEMA_ANNOTATIONS = {"$schema", "title"}
SCHEMA_ASSERTIONS = {
    "additionalProperties",
    "const",
    "items",
    "pattern",
    "properties",
    "required",
    "type",
}
JSON_SCHEMA_TYPES = {"array", "boolean", "integer", "null", "number", "object", "string"}


def read_json(path: Path) -> object:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def matches_json_type(value: object, expected: str) -> bool:
    """Return whether a Python JSON value has the requested JSON Schema type."""
    match expected:
        case "object":
            return isinstance(value, dict)
        case "array":
            return isinstance(value, list)
        case "string":
            return isinstance(value, str)
        case "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        case "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        case "boolean":
            return isinstance(value, bool)
        case "null":
            return value is None
        case _:
            raise ValueError(f"unsupported JSON Schema type: {expected}")


def validate_schema_shape(schema: object, *, manifest_path: Path, schema_path: str = "$") -> None:
    """Verify that every node in a vendored schema uses the supported subset."""
    if not isinstance(schema, dict):
        raise ValueError(f"{manifest_path}: schema at {schema_path} must be an object")
    unsupported = set(schema) - SCHEMA_ANNOTATIONS - SCHEMA_ASSERTIONS
    if unsupported:
        names = ", ".join(sorted(unsupported))
        raise ValueError(f"{manifest_path}: unsupported schema keywords at {schema_path}: {names}")

    expected_type = schema.get("type")
    if expected_type is not None:
        if not isinstance(expected_type, str):
            raise ValueError(f"{manifest_path}: schema type at {schema_path} must be a string")
        if expected_type not in JSON_SCHEMA_TYPES:
            raise ValueError(
                f"{manifest_path}: unsupported JSON Schema type at {schema_path}: {expected_type}"
            )

    pattern = schema.get("pattern")
    if pattern is not None:
        if not isinstance(pattern, str):
            raise ValueError(f"{manifest_path}: pattern at {schema_path} must be a string")
        try:
            re.compile(pattern)
        except re.error as error:
            raise ValueError(f"{manifest_path}: invalid pattern at {schema_path}: {error}") from error

    required = schema.get("required", [])
    if not isinstance(required, list) or not all(isinstance(field, str) for field in required):
        raise ValueError(f"{manifest_path}: required at {schema_path} must be a string array")

    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise ValueError(f"{manifest_path}: properties at {schema_path} must be an object")
    for name, child_schema in properties.items():
        validate_schema_shape(
            child_schema,
            manifest_path=manifest_path,
            schema_path=f"{schema_path}.{name}",
        )

    if "items" in schema:
        validate_schema_shape(
            schema["items"],
            manifest_path=manifest_path,
            schema_path=f"{schema_path}[]",
        )

    additional = schema.get("additionalProperties", True)
    if isinstance(additional, dict):
        validate_schema_shape(
            additional,
            manifest_path=manifest_path,
            schema_path=f"{schema_path}.*",
        )
    elif not isinstance(additional, bool):
        raise ValueError(
            f"{manifest_path}: additionalProperties at {schema_path} must be a boolean or schema"
        )


def _validate_value_against_schema(
    value: object, schema: dict[str, object], *, manifest_path: Path, value_path: str
) -> None:
    expected_type = schema.get("type")
    if isinstance(expected_type, str):
        if not matches_json_type(value, expected_type):
            raise ValueError(f"{manifest_path}: {value_path} must have type {expected_type}")

    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{manifest_path}: {value_path} must equal {schema['const']!r}")

    pattern = schema.get("pattern")
    if pattern is not None:
        if not isinstance(value, str):
            raise ValueError(f"{manifest_path}: pattern at {value_path} requires strings")
        assert isinstance(pattern, str)
        if re.search(pattern, value) is None:
            raise ValueError(f"{manifest_path}: {value_path} does not match {pattern!r}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        assert isinstance(required, list)
        missing = [field for field in required if field not in value]
        if missing:
            raise ValueError(
                f"{manifest_path}: {value_path} is missing required fields: {', '.join(missing)}"
            )

        properties = schema.get("properties", {})
        assert isinstance(properties, dict)
        for name, child_schema in properties.items():
            if name in value:
                assert isinstance(child_schema, dict)
                _validate_value_against_schema(
                    value[name],
                    child_schema,
                    manifest_path=manifest_path,
                    value_path=f"{value_path}.{name}",
                )

        additional = schema.get("additionalProperties", True)
        extras = set(value) - set(properties)
        if additional is False and extras:
            names = ", ".join(sorted(extras))
            raise ValueError(f"{manifest_path}: {value_path} has additional properties: {names}")
        if isinstance(additional, dict):
            for name in extras:
                _validate_value_against_schema(
                    value[name],
                    additional,
                    manifest_path=manifest_path,
                    value_path=f"{value_path}.{name}",
                )

    if isinstance(value, list) and "items" in schema:
        item_schema = schema["items"]
        assert isinstance(item_schema, dict)
        for index, item in enumerate(value):
            _validate_value_against_schema(
                item,
                item_schema,
                manifest_path=manifest_path,
                value_path=f"{value_path}[{index}]",
            )


def validate_against_schema(
    value: object, schema: object, *, manifest_path: Path, value_path: str = "$"
) -> None:
    """Validate every assertion keyword used by the vendored manifest schemas.

    This is deliberately a small stdlib validator rather than a partial draft
    implementation. Failing on unknown keywords prevents a future schema edit
    from silently declaring a constraint that CI does not enforce.
    """
    validate_schema_shape(schema, manifest_path=manifest_path, schema_path=value_path)
    assert isinstance(schema, dict)
    _validate_value_against_schema(
        value,
        schema,
        manifest_path=manifest_path,
        value_path=value_path,
    )


def validate_manifest_schema(manifest: object, schema_file: str, path: Path) -> None:
    validate_against_schema(
        manifest,
        read_json(ROOT / "schemas" / schema_file),
        manifest_path=path,
    )


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
        validate_manifest_schema(antigravity, "antigravity-plugin.schema.json", root / "plugin.json")
        validate_manifest_schema(
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
            shared_source = SKILL_SOURCE_ROOT / skill_path.parent.name / "SKILL.md"
            if not shared_source.is_file():
                raise ValueError(
                    f"{skill_path}: missing shared source {shared_source.relative_to(ROOT)}"
                )
            if skill_path.read_bytes() != shared_source.read_bytes():
                raise ValueError(f"{skill_path}: generated copy differs from shared source")
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
