---
name: antigravity-viewer-card
description: Show a render of the person's own Compose previews in Antigravity with one render_preview call on the local compose-preview-mcp server, then a few bullets. Antigravity already displays the returned image.
---

# Rendering previews in Antigravity

For a preview in the person's project:

1. Call `render_preview` on the **local** `compose-preview-mcp` server. If you
   don't know the preview ID, call `list_previews` on that same server once.
   Never use the `compose-preview-catalog` server for project previews: it only
   holds library catalogs.
2. Reply with 2–4 bullets describing what the image shows (R1), then this
   summary, filled **only** from the render result. Write "unavailable" for
   anything the result didn't include; don't look it up.

   ```text
   Render: <preview id>
   Image: <width> × <height>; hash <hash>
   ```

That's the whole task. Antigravity already shows the returned image to the
person and to you, so don't:

- read other skill or asset files first;
- search source files, the session or `brain/` folders, or run shell commands;
- show the image again, build an `<agent-embed>` card, or print base64. Cards
  are `iframe srcdoc` and can't receive the result (compose-ag-plugin#6 Q9).

Do more (variants, accessibility, source locations) only when the person asks.
