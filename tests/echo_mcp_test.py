#!/usr/bin/env python3
"""Unit checks for rich-protocol echo fixture responses."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path


SERVER_PATH = Path(__file__).resolve().parents[1] / "spike" / "echo-mcp" / "server.py"
SPEC = importlib.util.spec_from_file_location("echo_mcp", SERVER_PATH)
assert SPEC and SPEC.loader
echo_mcp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(echo_mcp)
echo_mcp.SERVER_NAME = "unit"


def call(request: dict) -> dict:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        echo_mcp.handle(request)
    return json.loads(stdout.getvalue())


initialize = call(
    {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "echo-unit", "version": "0"},
        },
    }
)["result"]
assert initialize["protocolVersion"] == "2025-11-25"

unsupported = call(
    {
        "jsonrpc": "2.0",
        "id": "unsupported",
        "method": "tools/call",
        "params": {"name": "ask", "arguments": {"mode": "form"}},
    }
)["result"]
assert unsupported["content"][0]["text"] == "form elicitation unavailable; use the text fallback: choose compact."

invalid_arguments = call(
    {
        "jsonrpc": "2.0",
        "id": "invalid-arguments",
        "method": "tools/call",
        "params": {"name": "ask", "arguments": {"mode": "form", "unexpected": True}},
    }
)
assert invalid_arguments["error"]["code"] == -32602

call(
    {
        "jsonrpc": "2.0",
        "id": "supported",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {"elicitation": {"form": {}, "url": {}}},
            "clientInfo": {"name": "echo-unit", "version": "0"},
        },
    }
)

tools = call({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})["result"]["tools"]
assert {tool["name"] for tool in tools} == {"render_preview", "status", "ask"}
assert next(tool for tool in tools if tool["name"] == "render_preview")["_meta"]["ui"]["resourceUri"] == "ui://spike/app"

viewer = call({"jsonrpc": "2.0", "id": 2, "method": "resources/read", "params": {"uri": echo_mcp.VIEWER_URI}})["result"]["contents"][0]
assert viewer["mimeType"] == "text/html;profile=mcp-app"
assert "postMessage" in viewer["text"]
for method in ("ui/initialize", "ui/notifications/initialized", "tools/call", "ui/message"):
    assert method in viewer["text"]
assert "event.source !== window.parent" in viewer["text"]
assert "message.error" in viewer["text"]
assert "const bridgeReady = initializeBridge();" in viewer["text"]
assert "await bridgeReady;" in viewer["text"]
assert 'await request("ui/message", {' in viewer["text"]
assert 'content: {type: "text", text: "Spike viewer requested status."}' in viewer["text"]

missing_prompt_path = call(
    {
        "jsonrpc": "2.0",
        "id": "missing-prompt-path",
        "method": "prompts/get",
        "params": {"name": "spike-prompt", "arguments": {}},
    }
)
assert missing_prompt_path["error"]["code"] == -32602

fallback = call({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "render_preview", "arguments": {}}})["result"]["content"]
assert fallback[0]["type"] == "text"
assert fallback[2]["type"] == "resource_link"

for request_id, mode in ((4, "form"), (5, "url")):
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        echo_mcp.handle({"jsonrpc": "2.0", "id": request_id, "method": "tools/call", "params": {"name": "ask", "arguments": {"mode": mode}}})
        elicitation = json.loads(stdout.getvalue())
        echo_mcp.handle({"jsonrpc": "2.0", "id": elicitation["id"], "error": {"code": -32601, "message": "unsupported"}})
    responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert responses[0]["method"] == "elicitation/create"
    assert responses[0]["params"]["mode"] == mode
    assert responses[1]["id"] == request_id
    assert f"{mode} elicitation unavailable" in responses[1]["result"]["content"][0]["text"]
    if mode == "url":
        assert set(responses[0]["params"]) == {"mode", "elicitationId", "url", "message"}

stdout = io.StringIO()
with contextlib.redirect_stdout(stdout):
    echo_mcp.handle(
        {
            "jsonrpc": "2.0",
            "id": "declined-tool",
            "method": "tools/call",
            "params": {"name": "ask", "arguments": {"mode": "form"}},
        }
    )
    elicitation = json.loads(stdout.getvalue())
    echo_mcp.handle(
        {"jsonrpc": "2.0", "id": elicitation["id"], "result": {"action": "decline"}}
    )
declined_responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
assert declined_responses[1]["id"] == "declined-tool"
assert "text fallback: choose compact" in declined_responses[1]["result"]["content"][0]["text"]

stdout = io.StringIO()
with contextlib.redirect_stdout(stdout):
    echo_mcp.handle(
        {
            "jsonrpc": "2.0",
            "id": "malformed-accept-tool",
            "method": "tools/call",
            "params": {"name": "ask", "arguments": {"mode": "form"}},
        }
    )
    elicitation = json.loads(stdout.getvalue())
    echo_mcp.handle(
        {
            "jsonrpc": "2.0",
            "id": elicitation["id"],
            "result": {"action": "accept", "content": {"variant": []}},
        }
    )
malformed_accept_responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
assert malformed_accept_responses[1]["id"] == "malformed-accept-tool"
assert (
    "text fallback: choose compact"
    in malformed_accept_responses[1]["result"]["content"][0]["text"]
)


def start_elicitation(tool_request_id: str) -> dict:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        echo_mcp.handle(
            {
                "jsonrpc": "2.0",
                "id": tool_request_id,
                "method": "tools/call",
                "params": {"name": "ask", "arguments": {"mode": "form"}},
            }
        )
    return json.loads(stdout.getvalue())


first = start_elicitation("first-tool")
second = start_elicitation("second-tool")
call(
    {
        "jsonrpc": "2.0",
        "id": first["id"],
        "result": {"action": "accept", "content": {"variant": "compact"}},
    }
)
third = start_elicitation("third-tool")
assert len({first["id"], second["id"], third["id"]}) == 3
for elicitation in (second, third):
    call({"jsonrpc": "2.0", "id": elicitation["id"], "result": {"action": "cancel"}})

overlap = start_elicitation("overlap-tool")
overlapping_request = call(
    {"jsonrpc": "2.0", "id": overlap["id"], "method": "tools/list", "params": {}}
)
assert {tool["name"] for tool in overlapping_request["result"]["tools"]} == {
    "render_preview",
    "status",
    "ask",
}
assert overlap["id"] in echo_mcp.PENDING_ELICITATIONS
call({"jsonrpc": "2.0", "id": overlap["id"], "result": {"action": "cancel"}})

print("echo MCP unit tests passed")
