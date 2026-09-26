#!/usr/bin/env python3
"""Prepare self-contained fixture plugins for local harness installation."""

from __future__ import annotations

import json
import shutil
import shlex
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ECHO_MCP = ROOT / "echo-mcp"

for plugin, server_name in (("p1", "alpha"), ("p2", "beta")):
    plugin_root = ROOT / plugin
    plugin_echo_mcp = plugin_root / "echo-mcp"
    shutil.rmtree(plugin_echo_mcp, ignore_errors=True)
    shutil.copytree(ECHO_MCP, plugin_echo_mcp)

    server = plugin_echo_mcp / "server.py"
    hook_logger = plugin_echo_mcp / "hook-log.sh"
    path = plugin_root / "mcp_config.json"
    path.write_text(
        json.dumps(
            {"mcpServers": {server_name: {"command": "python3", "args": [str(server), server_name]}}},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    hook_config = {
        plugin: {
            "enabled": True,
            "PostToolUse": [
                {
                    "matcher": "write_to_file|replace_file_content|multi_replace_file_content",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{shlex.quote(str(hook_logger))} post-tool-use",
                        }
                    ],
                }
            ],
            "Stop": [
                {"type": "command", "command": f"{shlex.quote(str(hook_logger))} stop"}
            ],
        }
    }
    (ROOT / plugin / "hooks.json").write_text(
        json.dumps(hook_config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
