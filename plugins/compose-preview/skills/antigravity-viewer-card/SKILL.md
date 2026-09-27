---
name: antigravity-viewer-card
description: Present a compose-preview render in Antigravity with the packaged portable viewer and its token-free static result fragment, while retaining a complete text fallback.
---

# Antigravity viewer card

Use this skill only when the `compose-preview` plugin is active in Antigravity
and a render result should be shown as an embedded card. Use the exact packaged
`../../assets/compose-preview-viewer.html`; do not author or modify another
viewer.

Follow `../../assets/compose-preview-viewer-fallback.md`. Copy the HTML unchanged
into the current response artifact folder, construct the bounded credential-free
static result fragment from the typed tool result, embed that file URL, and put
the complete text fallback in the same response.

Build the fragment from sanitized copies, never from the original tool-call
arguments. In particular, remove an in-band `token` obtained through
`request_access` / `poll_access` before encoding. Apply the same recursive
credential removal to JSON carried inside text content; if it cannot be parsed
and proved credential-free, omit the card and use the text fallback alone.

If the result cannot be encoded safely, exceeds either size bound, or the asset,
artifact copy, or embed surface is unavailable, return the complete text
fallback alone. Never claim the visual surface was inspected unless it was.
