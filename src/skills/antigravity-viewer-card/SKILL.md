---
name: antigravity-viewer-card
description: Show a render of the person's own Compose previews in Antigravity as a viewer card — render_preview with inline=false on the local compose-preview-mcp server, one helper command, a look at the PNG, then a few bullets.
---

# Rendering previews in Antigravity

For a preview in the person's project:

1. Call `render_preview` on the **local** `compose-preview-mcp` server with
   `inline=false`. If you don't know the preview ID, call `list_previews` on
   that same server once.
   Never use the `compose-preview-catalog` server for project previews: it
   only holds library catalogs.
2. Run the card helper once, passing the JSON text from that result unchanged,
   in single quotes:

   ```sh
   python3 ~/.gemini/config/plugins/compose-preview/assets/compose-preview-card.py '<render_preview JSON text>'
   ```

   (It lives in this plugin's `assets/` folder, two folders up from this
   file.) It prints one `<agent-embed …>` line.
3. Look at the PNG at `pngPath` with the file viewer, so you see what the
   person sees (R1). `inline=false` returns no pixels.
4. Reply with the `<agent-embed …>` line, 2–4 bullets describing what you saw, and
   this summary, filled **only** from the render result. Write "unavailable"
   for anything the result didn't include; don't look it up.

   ```text
   Render: <preview id>
   Image: <width> × <height>; hash <hash>
   ```

If `render_preview` rejects `inline`, the result has no `pngPath`, or the
helper fails, call `render_preview` again without `inline=false` (Antigravity
shows that image itself) and reply with the bullets and summary, no card.

That's the whole task. Don't:

- read other skill or asset files first;
- search source files, the session or `brain/` folders, or run other shell
  commands;
- open or edit the card file, or print base64. The helper reads the PNG from
  disk, so the image never passes through you.

Do more (variants, accessibility, source locations) only when the person asks.
