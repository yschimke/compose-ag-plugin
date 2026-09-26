#!/usr/bin/env python3
"""Check the portable viewer's required bridge timeout and generated copy."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "assets" / "compose-preview-viewer.html"
GENERATED = ROOT / "plugins" / "compose-preview" / "assets" / "compose-preview-viewer.html"


source = SOURCE.read_text(encoding="utf-8")
assert GENERATED.read_text(encoding="utf-8") == source

required = (
    "const REQUEST_TIMEOUT_MS = 5000;",
    "const RESOURCE_READ_TIMEOUT_MS = 65000;",
    "function request(method, params, timeoutMs = REQUEST_TIMEOUT_MS)",
    "const timer = window.setTimeout(() => {",
    "if (!pending.delete(id)) return;",
    "request timed out after ${timeoutMs} ms",
    "window.clearTimeout(request.timer);",
    "RESOURCE_READ_TIMEOUT_MS,",
    "Viewer unavailable; use the complete text fallback.",
    "Use the complete text fallback in the surrounding response.",
)
for marker in required:
    assert marker in source, marker

assert source.index("const timer = window.setTimeout") < source.index("window.parent.postMessage")

print("viewer asset tests passed")
