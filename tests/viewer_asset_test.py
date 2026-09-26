#!/usr/bin/env python3
"""Check the portable viewer contract, provenance, bounds, and generated copy."""

import base64
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "assets" / "compose-preview-viewer.html"
GENERATED = ROOT / "plugins" / "compose-preview" / "assets" / "compose-preview-viewer.html"
PROVENANCE = ROOT / "src" / "assets" / "compose-preview-viewer.provenance.json"
GENERATED_PROVENANCE = (
    ROOT / "plugins" / "compose-preview" / "assets" / "compose-preview-viewer.provenance.json"
)
FALLBACK = ROOT / "src" / "assets" / "compose-preview-viewer-fallback.md"
MAX_STATIC_RESULT_BYTES = 500_000


source_bytes = SOURCE.read_bytes()
source = source_bytes.decode("utf-8")
assert GENERATED.read_bytes() == source_bytes
assert len(source_bytes) <= MAX_STATIC_RESULT_BYTES

provenance_bytes = PROVENANCE.read_bytes()
provenance = json.loads(provenance_bytes)
assert GENERATED_PROVENANCE.read_bytes() == provenance_bytes
assert provenance == {
    "repository": "https://github.com/yschimke/compose-preview-server",
    "pullRequest": "https://github.com/yschimke/compose-preview-server/pull/1135",
    "commit": "93952d3b8ac89f81f462c1d2f8b5f4d894bb9e23",
    "path": "mcp-app/compose-preview-viewer.html",
    # Stable MCP Apps UI protocol revision:
    # https://github.com/modelcontextprotocol/ext-apps/tree/main/specification/2026-01-26
    "mcpAppsProtocolVersion": "2026-01-26",
    "sha256": "7d3802af7a051dcae025ae38bc7e631066bff96eeec03d97fdf571ec5785664a",
}
assert hashlib.sha256(source_bytes).hexdigest() == provenance["sha256"]
assert f"protocolVersion: '{provenance['mcpAppsProtocolVersion']}'," in source

required = (
    "const REQUEST_TIMEOUT_MS = 5000;",
    "const RESOURCE_READ_TIMEOUT_MS = 65000;",
    "function request(method, params, timeoutMs = REQUEST_TIMEOUT_MS)",
    "const timer = window.setTimeout(() => {",
    "if (!pending.delete(id)) return;",
    "request timed out after ${timeoutMs} ms",
    "window.clearTimeout(request.timer);",
    "RESOURCE_READ_TIMEOUT_MS,",
    "const STATIC_RESULT_PARAM = 'compose-preview-result';",
    "const MAX_STATIC_RESULT_BYTES = 500000;",
    "encoded.length > MAX_STATIC_RESULT_BYTES",
    "binary.length > MAX_STATIC_RESULT_BYTES",
    "envelope.version !== 1",
    "credentialKeyIn(envelope)",
    "function credentialKeyInUri(key, value)",
    "if (url.username || url.password)",
    "for (const [parameter] of url.searchParams)",
    "|cookie|session)/i",
    "const bridgeReady = staticMode ? Promise.resolve() : initializeBridge();",
    "protocolVersion: '2026-01-26',",
    "Viewer unavailable; use the complete text fallback.",
    "Use the complete text fallback in the surrounding response.",
)
for marker in required:
    assert marker in source, marker

assert source.index("const timer = window.setTimeout") < source.index("window.parent.postMessage")

envelope = {
    "version": 1,
    "arguments": {"uri": "compose-preview://workspace/sample"},
    "result": {
        "content": [
            {"type": "text", "text": '{"sha256":"abc","widthPx":100,"heightPx":200}'},
            {
                "type": "resource_link",
                "uri": "compose-preview://workspace/sample",
                "name": "sample",
                "mimeType": "image/png",
            },
        ]
    },
}
encoded = base64.urlsafe_b64encode(
    json.dumps(envelope, separators=(",", ":")).encode("utf-8")
).decode("ascii").rstrip("=")
assert "=" not in encoded
assert len(encoded) <= MAX_STATIC_RESULT_BYTES
assert len(json.dumps(envelope, separators=(",", ":")).encode("utf-8")) <= MAX_STATIC_RESULT_BYTES

fallback = FALLBACK.read_text(encoding="utf-8")
assert "#compose-preview-result=<unpadded-base64url-envelope>" in fallback
assert "500,000" in fallback
assert "complete MCP `CallToolResult`" in fallback
assert "complete text fallback" in fallback

print("viewer asset tests passed")
