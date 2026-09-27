---
name: antigravity-viewer-card
description: How to show a compose-preview render in Antigravity. Antigravity already displays MCP image results to the person and the agent, so reply with a short description and the text summary; do not build a viewer card.
---

# Showing renders in Antigravity

Antigravity shows the image a `render_preview` call returns, both to the person
and to you. That image is the render surface. Keep the reply short:

1. Describe what you see in the rendered image (R1), in a few bullets.
2. Add the text summary from `../../assets/compose-preview-viewer-fallback.md`.

Do **not** build an `<agent-embed>` card from the packaged viewer. Antigravity
renders cards as `iframe srcdoc` (compose-ag-plugin#6 Q9): the URL fragment and
query are dropped, so the viewer never receives its static result and only shows
"MCP Apps bridge is unavailable". Also do not:

- show the image again (as markdown, HTML or a card): it is already visible,
  and a second copy is scaled to the full chat width;
- search your own session or `brain/` files to reconstruct a tool result;
- copy, re-encode or print base64 image data, or paste an embed tag as text;
- run extra shell commands only to measure or re-save the image.

If the person asks to compare variants, render them with the typed tools and
describe each one. A viewer card returns once the viewer reads an inline result
block; until then the text summary is the only fallback.
