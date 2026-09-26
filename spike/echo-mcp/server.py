#!/usr/bin/env python3
"""Dependency-free stdio MCP server used by the harness compatibility spike."""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path


# A transparent 1×1 PNG. Returning it from render_preview exercises image handling (Q10).
PIXEL = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/"
    "S+xHAAAAAElFTkSuQmCC"
)
SERVER_NAME = sys.argv[1] if len(sys.argv) == 2 else "unnamed"
LOG_PATH = Path(f"/tmp/spike-{os.getpid()}.json")
DETECTION_ENV_KEYS = (
    "ANTIGRAVITY_CLI_ALIAS",
    "CLAUDECODE",
    "CLAUDE_PLUGIN_ROOT",
    "CODEX_THREAD_ID",
    "GEMINI_CLI",
    "OPENCODE",
    "__CFBundleIdentifier",
)


def log_initialize(params: object) -> None:
    client_info = params.get("clientInfo") if isinstance(params, dict) else None
    LOG_PATH.write_text(
        json.dumps(
            {
                "clientInfo": client_info,
                "environmentKeys": sorted(os.environ),
                "detectionEnvironment": {
                    key: os.environ[key] for key in DETECTION_ENV_KEYS if key in os.environ
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def result(request_id: object, value: object) -> None:
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": value}) + "\n")
    sys.stdout.flush()


def error(request_id: object, code: int, message: str) -> None:
    sys.stdout.write(
        json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})
        + "\n"
    )
    sys.stdout.flush()


TOOLS = [
    {
        "name": "render_preview",
        "description": "Return the echo MCP server name and a 1×1 image.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
    {
        "name": "status",
        "description": "Return the echo MCP server name.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
]


def handle(request: object) -> None:
    if not isinstance(request, dict):
        return
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        log_initialize(params)
        result(
            request_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": f"spike-echo-{SERVER_NAME}", "version": "0.1.0"},
            },
        )
    elif method == "tools/list":
        result(request_id, {"tools": TOOLS})
    elif method == "tools/call":
        tool_name = params.get("name") if isinstance(params, dict) else None
        if tool_name == "status":
            result(request_id, {"content": [{"type": "text", "text": f"status from {SERVER_NAME}"}]})
        elif tool_name == "render_preview":
            result(
                request_id,
                {
                    "content": [
                        {"type": "text", "text": f"render_preview from {SERVER_NAME}"},
                        {"type": "image", "data": PIXEL, "mimeType": "image/png"},
                    ]
                },
            )
        else:
            error(request_id, -32602, f"unknown tool: {tool_name}")
    elif request_id is not None:
        error(request_id, -32601, f"unknown method: {method}")


for line in sys.stdin:
    try:
        handle(json.loads(line))
    except json.JSONDecodeError:
        # JSON-RPC parse failures have no reliable request id.
        error(None, -32700, "parse error")
