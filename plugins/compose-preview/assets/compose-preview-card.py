#!/usr/bin/env python3
"""Build an Antigravity preview card from a local render_preview result.

Antigravity shows `<agent-embed src="file://...">` by reading the file into an
`<iframe srcdoc>`, so the viewer can't be handed a URL fragment. Instead this
copies the released viewer and appends the static result as an inline
`<script type="application/json" id="compose-preview-result">` block, which the
viewer (compose-preview-server v3.77.0+) reads in static mode.

Input is the JSON text that `render_preview` returns with `inline=false`:
    {"uri": "...", "pngPath": "...", "widthPx": 1, "heightPx": 1, "sha256": "..."}
Pass it as the only argument. The PNG is read from disk, so the image bytes
never pass through the model.

Prints the `<agent-embed>` line to paste into the reply. Exits non-zero with a
one-line reason when a card can't be built; the reply then goes without one.
"""

import base64
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

MAX_STATIC_RESULT_BYTES = 500_000
VIEWER = Path(__file__).resolve().with_name("compose-preview-viewer.html")


def fail(message: str) -> "NoReturn":  # noqa: F821
    print(f"compose-preview-card: {message}; reply without a card", file=sys.stderr)
    sys.exit(2)


def output_dir() -> Path:
    # Antigravity keeps per-conversation artifacts under brain/<conversation id>.
    conversation = os.environ.get("ANTIGRAVITY_CONVERSATION_ID", "").strip()
    if conversation and "/" not in conversation and conversation not in (".", ".."):
        directory = Path.home() / ".gemini" / "antigravity" / "brain" / conversation
        if directory.is_dir():
            return directory
    return Path(tempfile.gettempdir()).resolve()


def build_envelope(render: dict, png: bytes) -> dict:
    summary = {
        key: render[key]
        for key in ("uri", "widthPx", "heightPx", "sha256")
        if key in render
    }
    return {
        "version": 1,
        "arguments": {"uri": render["uri"]},
        "result": {
            "content": [
                {
                    "type": "image",
                    "data": base64.b64encode(png).decode("ascii"),
                    "mimeType": "image/png",
                },
                {"type": "text", "text": json.dumps(summary, separators=(",", ":"))},
            ]
        },
    }


def inline_block(envelope: dict) -> str:
    payload = json.dumps(envelope, separators=(",", ":"), ensure_ascii=False)
    if len(payload.encode("utf-8")) > MAX_STATIC_RESULT_BYTES:
        fail("the render is too large for a card (over 500,000 bytes)")
    # `<` for every `<` keeps `</script>` and `<!--` out of the block;
    # JSON.parse turns it back into `<`.
    payload = payload.replace("<", "\\u003c")
    return (
        '<script type="application/json" id="compose-preview-result">'
        f"{payload}</script>\n"
    )


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        fail("pass the render_preview inline=false JSON text as the only argument")
    try:
        render = json.loads(argv[1])
    except json.JSONDecodeError:
        fail("the argument is not the render_preview JSON text")
    if not isinstance(render, dict) or not isinstance(render.get("uri"), str):
        fail("the render result has no uri")
    png_path = render.get("pngPath")
    if not isinstance(png_path, str) or not Path(png_path).is_file():
        fail("the render result has no readable pngPath (call render_preview with inline=false)")
    png = Path(png_path).read_bytes()
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        fail("pngPath is not a PNG")
    expected = render.get("sha256")
    if isinstance(expected, str) and hashlib.sha256(png).hexdigest() != expected.lower():
        fail("the PNG on disk no longer matches the render's sha256")
    if not VIEWER.is_file():
        fail(f"viewer not found at {VIEWER}")

    viewer = VIEWER.read_text(encoding="utf-8")
    card = viewer + inline_block(build_envelope(render, png))
    digest = hashlib.sha256(png).hexdigest()[:12]
    target = output_dir() / f"compose-preview-card-{digest}.html"
    target.write_text(card, encoding="utf-8")
    print(f'<agent-embed src="{target.as_uri()}"></agent-embed>')


if __name__ == "__main__":
    main(sys.argv)
