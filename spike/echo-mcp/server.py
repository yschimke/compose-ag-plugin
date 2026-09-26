#!/usr/bin/env python3
"""Dependency-free stdio MCP server used by the harness compatibility spike."""

from __future__ import annotations

import json
import os
import sys
from itertools import count
from pathlib import Path


PIXEL = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/"
    "S+xHAAAAAElFTkSuQmCC"
)
VIEWER_URI = "ui://spike/app"
VIEWER_MIME_TYPE = "text/html;profile=mcp-app"
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
PENDING_ELICITATIONS: dict[object, object] = {}
ELICITATION_IDS = count(1)
CLIENT_ELICITATION_CAPABILITIES: dict[str, object] = {}
CLIENT_ELICITATION_DECLARED = False

VIEWER_HTML = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Spike echo viewer</title></head>
<body>
<p id="status">Echo viewer ready. If this app is unavailable, use the text result.</p>
<button id="action" type="button">Send viewer action</button>
<script>
// Host-neutral JSON-RPC postMessage bridge. Server actions always return text too.
const pending = new Map();
let nextId = 1;
let initialized = false;

function request(method, params) {
  const id = nextId++;
  window.parent.postMessage({jsonrpc: "2.0", id, method, params}, "*");
  return new Promise((resolve, reject) => pending.set(id, {resolve, reject}));
}

function notify(method, params) {
  window.parent.postMessage({jsonrpc: "2.0", method, params}, "*");
}

window.addEventListener("message", event => {
  if (event.source !== window.parent) return;
  const message = event.data;
  if (!message || message.jsonrpc !== "2.0" || !pending.has(message.id)) return;
  const pendingRequest = pending.get(message.id);
  pending.delete(message.id);
  if (message.error) {
    pendingRequest.reject(message.error);
    return;
  }
  pendingRequest.resolve(message.result);
}, {passive: true});

async function initializeBridge() {
  try {
    await request("ui/initialize", {
      appInfo: {name: "spike-echo-viewer", version: "0.1.0"},
      appCapabilities: {},
      protocolVersion: "2026-01-26"
    });
    initialized = true;
    notify("ui/notifications/initialized", {});
  } catch (error) {
    document.getElementById("status").textContent = "Viewer unavailable; use the text fallback.";
    console.error("Failed to initialize the MCP Apps bridge:", error);
  }
}

const bridgeReady = initializeBridge();

document.getElementById("action").addEventListener("click", async () => {
  await bridgeReady;
  if (!initialized) {
    document.getElementById("status").textContent = "Viewer unavailable; use the text fallback.";
    return;
  }
  try {
    const response = await request("tools/call", {name: "status", arguments: {}});
    await request("ui/message", {
      role: "user",
      content: {type: "text", text: "Spike viewer requested status."}
    });
    document.getElementById("status").textContent =
      response.content?.[0]?.text || "Status requested; use the text fallback.";
  } catch (error) {
    document.getElementById("status").textContent = "Status unavailable; use the text fallback.";
    console.error("Viewer action failed:", error);
  }
});
</script></body></html>
"""

TOOLS = [
    {
        "name": "render_preview",
        "description": "Return the echo MCP server name and a 1×1 image, with a viewer resource and text fallback.",
        "inputSchema": {"type": "object", "additionalProperties": False},
        "_meta": {"ui": {"resourceUri": VIEWER_URI}},
    },
    {
        "name": "status",
        "description": "Return the echo MCP server name.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
    {
        "name": "ask",
        "description": "Probe form or URL elicitation and return text if the client declines or cannot elicit.",
        "inputSchema": {
            "type": "object",
            "properties": {"mode": {"type": "string", "enum": ["form", "url"]}},
            "required": ["mode"],
            "additionalProperties": False,
        },
    },
]
PROMPTS = [
    {
        "name": "spike-prompt",
        "description": "Fixture prompt that requests an echo preview for a file.",
        "arguments": [{"name": "path", "description": "A source file path", "required": True}],
    }
]


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


def save_client_capabilities(params: object) -> None:
    global CLIENT_ELICITATION_CAPABILITIES, CLIENT_ELICITATION_DECLARED
    capabilities = params.get("capabilities") if isinstance(params, dict) else None
    elicitation = capabilities.get("elicitation") if isinstance(capabilities, dict) else None
    CLIENT_ELICITATION_DECLARED = isinstance(elicitation, dict)
    CLIENT_ELICITATION_CAPABILITIES = elicitation if isinstance(elicitation, dict) else {}


def supports_elicitation(mode: str) -> bool:
    if mode == "form":
        # Older clients advertised a bare `elicitation: {}` capability before
        # form/url sub-capabilities were standardized.
        return CLIENT_ELICITATION_DECLARED and (
            not CLIENT_ELICITATION_CAPABILITIES or "form" in CLIENT_ELICITATION_CAPABILITIES
        )
    return CLIENT_ELICITATION_DECLARED and "url" in CLIENT_ELICITATION_CAPABILITIES


def send(message: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def result(request_id: object, value: object) -> None:
    send({"jsonrpc": "2.0", "id": request_id, "result": value})


def error(request_id: object, code: int, message: str) -> None:
    send({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})


def text_result(text: str) -> dict[str, object]:
    return {"content": [{"type": "text", "text": text}]}


def handle_elicitation_response(request_id: object, response: dict[str, object]) -> bool:
    if request_id not in PENDING_ELICITATIONS:
        return False
    tool_request_id = PENDING_ELICITATIONS.pop(request_id)
    response_result = response.get("result")
    response_action = response_result.get("action") if isinstance(response_result, dict) else None
    accepted = "error" not in response and response_action == "accept"
    if accepted and tool_request_id["mode"] == "form":
        content = response_result.get("content")
        accepted = (
            isinstance(content, dict)
            and set(content) == {"variant"}
            and isinstance(content.get("variant"), str)
            and content.get("variant") in {"compact", "expanded"}
        )
    if not accepted:
        result(
            tool_request_id["request_id"],
            text_result(f"{tool_request_id['mode']} elicitation unavailable; use the text fallback: choose compact."),
        )
    else:
        result(
            tool_request_id["request_id"],
            text_result(f"{tool_request_id['mode']} elicitation response: {json.dumps(response.get('result'))}"),
        )
    return True


def handle(request: object) -> None:
    if not isinstance(request, dict):
        return
    request_id = request.get("id")
    is_response = "method" not in request and ("result" in request or "error" in request)
    if is_response and handle_elicitation_response(request_id, request):
        return
    method, params = request.get("method"), request.get("params", {})
    if method == "initialize":
        log_initialize(params)
        save_client_capabilities(params)
        result(
            request_id,
            {
                "protocolVersion": "2025-11-25",
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "serverInfo": {"name": f"spike-echo-{SERVER_NAME}", "version": "0.1.0"},
            },
        )
    elif method == "tools/list":
        result(request_id, {"tools": TOOLS})
    elif method == "resources/list":
        result(
            request_id,
            {
                "resources": [
                    {"uri": VIEWER_URI, "name": "Spike echo viewer", "mimeType": VIEWER_MIME_TYPE}
                ]
            },
        )
    elif method == "resources/read":
        uri = params.get("uri") if isinstance(params, dict) else None
        if uri == VIEWER_URI:
            result(
                request_id,
                {
                    "contents": [
                        {"uri": VIEWER_URI, "mimeType": VIEWER_MIME_TYPE, "text": VIEWER_HTML}
                    ]
                },
            )
        else:
            error(request_id, -32602, f"unknown resource: {uri}")
    elif method == "prompts/list":
        result(request_id, {"prompts": PROMPTS})
    elif method == "prompts/get":
        name = params.get("name") if isinstance(params, dict) else None
        if name == "spike-prompt":
            arguments = params.get("arguments", {}) if isinstance(params, dict) else {}
            path = arguments.get("path") if isinstance(arguments, dict) else None
            if not isinstance(path, str) or not path:
                error(request_id, -32602, "spike-prompt requires a non-empty path argument")
                return
            result(
                request_id,
                {
                    "description": "Echo preview prompt",
                    "messages": [
                        {
                            "role": "user",
                            "content": {"type": "text", "text": f"Render an echo preview for {path}."},
                        }
                    ],
                },
            )
        else:
            error(request_id, -32602, f"unknown prompt: {name}")
    elif method == "tools/call":
        tool_name = params.get("name") if isinstance(params, dict) else None
        arguments = params.get("arguments", {}) if isinstance(params, dict) else {}
        if tool_name == "status":
            result(request_id, text_result(f"status from {SERVER_NAME}"))
        elif tool_name == "render_preview":
            result(
                request_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": f"render_preview from {SERVER_NAME}; text fallback remains available.",
                        },
                        {"type": "image", "data": PIXEL, "mimeType": "image/png"},
                        {
                            "type": "resource_link",
                            "uri": VIEWER_URI,
                            "name": "Spike echo viewer",
                            "mimeType": VIEWER_MIME_TYPE,
                        },
                    ]
                },
            )
        elif tool_name == "ask":
            if not isinstance(arguments, dict) or set(arguments) != {"mode"}:
                error(request_id, -32602, "ask requires exactly one argument: mode")
                return
            mode = arguments.get("mode") if isinstance(arguments, dict) else None
            if mode not in {"form", "url"}:
                error(request_id, -32602, "ask requires mode form or url")
                return
            if not supports_elicitation(mode):
                result(
                    request_id,
                    text_result(f"{mode} elicitation unavailable; use the text fallback: choose compact."),
                )
                return
            elicitation_id = f"elicitation-{next(ELICITATION_IDS)}"
            PENDING_ELICITATIONS[elicitation_id] = {"request_id": request_id, "mode": mode}
            if mode == "url":
                elicitation_params = {
                    "mode": "url",
                    "elicitationId": elicitation_id,
                    "url": "https://example.invalid/spike-elicitation",
                    "message": "Choose the echo variant.",
                }
            else:
                elicitation_params = {
                    "mode": "form",
                    "message": "Choose the echo variant.",
                    "requestedSchema": {
                        "type": "object",
                        "properties": {"variant": {"type": "string", "enum": ["compact", "expanded"]}},
                        "required": ["variant"],
                        "additionalProperties": False,
                    },
                }
            send(
                {
                    "jsonrpc": "2.0",
                    "id": elicitation_id,
                    "method": "elicitation/create",
                    "params": elicitation_params,
                }
            )
        else:
            error(request_id, -32602, f"unknown tool: {tool_name}")
    elif method == "ui/message":
        return
    elif request_id is not None:
        error(request_id, -32601, f"unknown method: {method}")


def main() -> None:
    for line in sys.stdin:
        try:
            handle(json.loads(line))
        except json.JSONDecodeError:
            error(None, -32700, "parse error")


if __name__ == "__main__":
    main()
