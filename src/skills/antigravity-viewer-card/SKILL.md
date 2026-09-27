---
name: antigravity-viewer-card
description: Show a render of the person's own Compose previews in Antigravity — one render_preview call with preview=<FunctionName> on the local compose-preview-mcp server, a look at the PNG, then the card and a few bullets.
---

# Rendering previews in Antigravity

**Render first, explore later.** Your first tool call is `render_preview`.
Only if it fails do you look anything up.

1. Call `render_preview` on the **local** `compose-preview-mcp` server with
   `preview` set to the function name the person used, for example
   `preview: "ListScreenPreview"`. Nothing else is needed first: the server
   registers the workspace, finds the preview and writes the card.
   Never use the `compose-preview-catalog` server for project previews: it
   only holds library catalogs.
2. Look at the PNG at `pngPath` with the file viewer, so you see what the
   person sees (R1).
3. Reply with the `embed` line from the result, 2–4 bullets describing what
   you saw, and this summary, filled **only** from the result. Write
   "unavailable" for anything missing; don't look it up.

   ```text
   Render: <uri>
   Image: <widthPx> × <heightPx>; hash <sha256>
   ```

   If the result lists `otherMatches`, name them in one line.

**After editing a preview's source**, call `render_preview` with the same
`preview` again; the server recompiles. Never run `./gradlew`, clean, or delete
build folders. If the image still shows the old code, call `render_preview`
once more with `force: {"reason": "<what you edited>"}`; if it is still stale,
say so and stop.

That's the whole task. Don't read other skill, asset or source files, search
the session or `brain/` folders, call `status`, `register_project` or
`list_previews` first, or print base64.

**Older servers** (the result has `pngPath` but no `embed`): run
`python3 ~/.gemini/config/plugins/compose-preview/assets/compose-preview-card.py '<result JSON text>'`
and use the line it prints. If `preview` is rejected, call `list_previews`
once, then `render_preview` with the `uri` and `inline=false`.

Do more (variants, accessibility, source locations) only when the person asks.
