#!/usr/bin/env python3
"""Check compose-preview-card.py builds a viewer card with an inline result block."""

import base64
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "plugins" / "compose-preview" / "assets" / "compose-preview-card.py"
VIEWER = HELPER.with_name("compose-preview-viewer.html")


def png(width: int, height: int, extra: bytes = b"") -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    raw = b"".join(b"\x00" + b"\xff\x00\x00" * width for _ in range(height))
    body = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    if extra:
        body += chunk(b"tEXt", extra)
    return b"\x89PNG\r\n\x1a\n" + body + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def run(argument: str, home: Path, conversation: str = "") -> subprocess.CompletedProcess:
    # A relative TMPDIR still has to produce an absolute file:// URI.
    env = dict(os.environ, HOME=str(home), TMPDIR="tmp")
    env.pop("ANTIGRAVITY_CONVERSATION_ID", None)
    if conversation:
        env["ANTIGRAVITY_CONVERSATION_ID"] = conversation
    return subprocess.run(
        [sys.executable, str(HELPER), argument], capture_output=True, text=True, env=env, cwd=home
    )


with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    (home / "tmp").mkdir()
    brain = home / ".gemini" / "antigravity" / "brain" / "conv-1"
    brain.mkdir(parents=True)

    # A text chunk carrying `</script>` proves the block can't be closed early.
    image = png(4, 3, b"Comment\x00</script><script>alert(1)</script><!--")
    image_path = home / "render.png"
    image_path.write_bytes(image)
    sha = hashlib.sha256(image).hexdigest()
    render = {
        "uri": "compose-preview://ws/_app/com.example.PreviewKt.Sample_Devices - Small Round",
        "pngPath": str(image_path),
        "widthPx": 4,
        "heightPx": 3,
        "sha256": sha,
        "changed": True,
        "durationMs": 12,
    }

    result = run(json.dumps(render), home, "conv-1")
    assert result.returncode == 0, result.stderr
    card = brain / f"compose-preview-card-{sha[:12]}.html"
    assert result.stdout.strip() == f'<agent-embed src="{card.as_uri()}"></agent-embed>', result.stdout
    html = card.read_text(encoding="utf-8")
    viewer = VIEWER.read_text(encoding="utf-8")
    assert html.startswith(viewer), "the viewer is copied unchanged"
    block = html[len(viewer):]
    match = re.fullmatch(
        r'<script type="application/json" id="compose-preview-result">(.*)</script>\n',
        block,
        re.S,
    )
    assert match, block[:200]
    payload = match.group(1)
    assert "<" not in payload, "every < is escaped"
    envelope = json.loads(payload)
    assert envelope["version"] == 1
    assert envelope["arguments"] == {"uri": render["uri"]}
    image_block, text_block = envelope["result"]["content"]
    assert image_block == {
        "type": "image",
        "data": base64.b64encode(image).decode("ascii"),
        "mimeType": "image/png",
    }
    assert json.loads(text_block["text"]) == {
        "uri": render["uri"],
        "widthPx": 4,
        "heightPx": 3,
        "sha256": sha,
    }
    assert "pngPath" not in payload

    # Outside Antigravity the card goes to the temp dir.
    result = run(json.dumps(render), home)
    assert result.returncode == 0, result.stderr
    assert (home / "tmp" / card.name).is_file()
    assert result.stdout.strip() == f'<agent-embed src="{(home / "tmp" / card.name).resolve().as_uri()}"></agent-embed>'

    # Refusals: each exits 2 with a reason and writes nothing.
    def refused(argument: str, reason: str) -> None:
        result = run(argument, home, "conv-1")
        assert result.returncode == 2, (argument, result)
        assert reason in result.stderr, result.stderr
        assert result.stdout == ""

    refused("not json", "not the render_preview JSON text")
    refused(json.dumps({"pngPath": str(image_path)}), "no uri")
    refused(json.dumps(dict(render, pngPath=None)), "no readable pngPath")
    refused(json.dumps(dict(render, sha256="0" * 64)), "no longer matches")
    not_png = home / "not.png"
    not_png.write_bytes(b"GIF89a")
    refused(json.dumps(dict(render, pngPath=str(not_png), sha256=None)), "not a PNG")
    big = png(1, 1, b"Comment\x00" + os.urandom(400_000).hex().encode()[:400_000])
    big_path = home / "big.png"
    big_path.write_bytes(big)
    refused(
        json.dumps(dict(render, pngPath=str(big_path), sha256=hashlib.sha256(big).hexdigest())),
        "too large",
    )

print("card helper tests passed")
