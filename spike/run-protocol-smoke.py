#!/usr/bin/env python3
"""Exercise the fixture directly; this is a protocol baseline, not a harness result."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def request(process: subprocess.Popen[str], request_id: int, method: str, params: dict) -> dict:
    assert process.stdin and process.stdout
    process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}) + "\n")
    process.stdin.flush()
    response = json.loads(process.stdout.readline())
    assert response["id"] == request_id, response
    return response["result"]


def run(plugin: str, server_name: str) -> None:
    server = ROOT / plugin / "echo-mcp" / "server.py"
    process = subprocess.Popen(
        [sys.executable, str(server), server_name],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        initialize = request(process, 1, "initialize", {"clientInfo": {"name": "spike-smoke", "version": "0"}})
        assert initialize["serverInfo"]["name"] == f"spike-echo-{server_name}"
        tools = request(process, 2, "tools/list", {})["tools"]
        assert {tool["name"] for tool in tools} == {"render_preview", "status"}
        status = request(process, 3, "tools/call", {"name": "status", "arguments": {}})
        assert status["content"][0]["text"] == f"status from {server_name}"
        preview = request(process, 4, "tools/call", {"name": "render_preview", "arguments": {}})
        assert preview["content"][1]["type"] == "image"
    finally:
        process.terminate()
        process.wait(timeout=5)


for plugin, name in (("p1", "alpha"), ("p2", "beta")):
    run(plugin, name)
print("spike MCP protocol smoke test passed for alpha and beta")
