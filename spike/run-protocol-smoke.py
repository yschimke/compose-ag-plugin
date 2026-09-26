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
    process.stdin.write(
        json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}) + "\n"
    )
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
        initialize = request(
            process,
            1,
            "initialize",
            {
                "protocolVersion": "2025-11-25",
                "capabilities": {"elicitation": {"form": {}, "url": {}}},
                "clientInfo": {"name": "spike-smoke", "version": "0"},
            },
        )
        assert initialize["serverInfo"]["name"] == f"spike-echo-{server_name}"
        assert initialize["protocolVersion"] == "2025-11-25"
        assert {"tools", "resources", "prompts"} <= set(initialize["capabilities"])
        tools = request(process, 2, "tools/list", {})["tools"]
        tools_by_name = {tool["name"]: tool for tool in tools}
        assert set(tools_by_name) == {"render_preview", "status", "ask"}
        assert tools_by_name["render_preview"]["_meta"]["ui"]["resourceUri"] == "ui://spike/app"
        status = request(process, 3, "tools/call", {"name": "status", "arguments": {}})
        assert status["content"][0]["text"] == f"status from {server_name}"
        preview = request(process, 4, "tools/call", {"name": "render_preview", "arguments": {}})
        assert preview["content"][1]["type"] == "image"
        resources = request(process, 5, "resources/list", {})["resources"]
        assert resources == [{"uri": "ui://spike/app", "name": "Spike echo viewer", "mimeType": "text/html;profile=mcp-app"}]
        viewer = request(process, 6, "resources/read", {"uri": "ui://spike/app"})["contents"][0]
        assert viewer["mimeType"] == "text/html;profile=mcp-app"
        for method in ("ui/initialize", "ui/notifications/initialized", "tools/call", "ui/message"):
            assert method in viewer["text"]
        assert "event.source !== window.parent" in viewer["text"] and "message.error" in viewer["text"]
        assert "const bridgeReady = initializeBridge();" in viewer["text"]
        assert "await bridgeReady;" in viewer["text"]
        assert 'await request("ui/message", {' in viewer["text"]
        assert 'content: {type: "text", text: "Spike viewer requested status."}' in viewer["text"]
        prompt = request(process, 7, "prompts/get", {"name": "spike-prompt", "arguments": {"path": "Example.kt"}})
        assert prompt["messages"][0]["content"]["text"] == "Render an echo preview for Example.kt."
        assert request(process, 8, "prompts/list", {})["prompts"][0]["name"] == "spike-prompt"
        assert preview["content"][0]["type"] == "text"
        assert preview["content"][2]["type"] == "resource_link"
        assert process.stdin and process.stdout
        for request_id, mode in ((10, "form"), (11, "url")):
            process.stdin.write(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "method": "tools/call",
                        "params": {"name": "ask", "arguments": {"mode": mode}},
                    }
                )
                + "\n"
            )
            process.stdin.flush()
            elicitation = json.loads(process.stdout.readline())
            assert elicitation["method"] == "elicitation/create"
            assert elicitation["params"]["mode"] == mode
            if mode == "form":
                assert elicitation["params"]["requestedSchema"]["properties"]["variant"]["enum"] == ["compact", "expanded"]
            else:
                assert set(elicitation["params"]) == {"mode", "elicitationId", "url", "message"}
            process.stdin.write(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": elicitation["id"],
                        "result": {"action": "accept", "content": {"variant": "compact"}},
                    }
                )
                + "\n"
            )
            process.stdin.flush()
            elicitation_result = json.loads(process.stdout.readline())
            assert elicitation_result["id"] == request_id
            assert mode in elicitation_result["result"]["content"][0]["text"]
    finally:
        process.terminate()
        process.wait(timeout=5)


def run_fallback(plugin: str, server_name: str) -> None:
    server = ROOT / plugin / "echo-mcp" / "server.py"
    process = subprocess.Popen(
        [sys.executable, str(server), server_name],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        request(
            process,
            1,
            "initialize",
            {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "spike-fallback-smoke", "version": "0"},
            },
        )
        form = request(
            process,
            2,
            "tools/call",
            {"name": "ask", "arguments": {"mode": "form"}},
        )["content"][0]["text"]
        assert "compact or expanded" in form
        url = request(
            process,
            3,
            "tools/call",
            {"name": "ask", "arguments": {"mode": "url"}},
        )["content"][0]["text"]
        assert "https://example.invalid/spike-elicitation" in url
        assert "verification code SPIKE-CODE" in url
        assert "poll access status with the status tool" in url
    finally:
        process.terminate()
        process.wait(timeout=5)


for plugin, name in (("p1", "alpha"), ("p2", "beta")):
    run(plugin, name)
    run_fallback(plugin, name)
print("spike MCP protocol smoke test passed for alpha and beta")
