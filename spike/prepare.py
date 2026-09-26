#!/usr/bin/env python3
"""Write the Antigravity fixture MCP configs with this checkout's absolute server path."""

from __future__ import annotations

import json
import shlex
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SERVER = ROOT / "echo-mcp" / "server.py"
HOOK_LOGGER = ROOT / "echo-mcp" / "hook-log.sh"

for plugin, server_name in (("p1", "alpha"), ("p2", "beta")):
    path = ROOT / plugin / "mcp_config.json"
    path.write_text(
        json.dumps(
            {"mcpServers": {server_name: {"command": "python3", "args": [str(SERVER), server_name]}}},
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
                            "command": f"{shlex.quote(str(HOOK_LOGGER))} post-tool-use",
                        }
                    ],
                }
            ],
            "Stop": [
                {"type": "command", "command": f"{shlex.quote(str(HOOK_LOGGER))} stop"}
            ],
        }
    }
    (ROOT / plugin / "hooks.json").write_text(
        json.dumps(hook_config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
