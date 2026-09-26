---
name: harness-notes
description: Apply the mandatory cross-harness agent rules whenever compose-ag-plugin supplies Compose catalog, UI Builder, or preview tools; use alongside the canonical yschimke/skills workflows.
---

# Harness notes

Use the canonical `compose-preview` and `compose-ui-builder` skills from
[`yschimke/skills`](https://github.com/yschimke/skills) for workflows. These notes only carry the
rules that must remain consistent across Antigravity, Claude Code, and Codex.

- **R1 — See what the user sees:** inspect the surface where the person will judge a visual change; if that surface is unavailable, say so and never claim to have seen the result from source or JSON alone.
- **R2 — Use typed tools with schemas:** prefer validated MCP or CLI operations; if raw JSON is unavoidable, validate it before saving and render it again afterwards.
- **R3 — Keep one canonical home:** read and preserve the design's recorded home, edit there in small batches, announce and reconcile temporary copies, and get approval before moving the home.
- **R4 — Keep discussion at the home:** use server comments for server-homed designs and the linked PR or issue for repo-homed designs, then report unacknowledged comments before finishing.

## Antigravity viewer card

When the compose-preview plugin is active in Antigravity and its
../../assets/compose-preview-viewer.html asset is available, use that exact
portable bundle for render cards; do not author a second card. Follow
../../assets/compose-preview-viewer-fallback.md: copy the HTML unchanged into
the current response artifact folder, embed that artifact with agent-embed, and
include the complete text fallback in the same response. If the asset, artifact
copy, or bridge is unavailable, return the text fallback alone and state that
the visual surface was not inspected.

The full, authoritative contract and current tooling gaps are in
[`docs/agent-rules.md`](https://github.com/yschimke/compose-ag-plugin/blob/main/docs/agent-rules.md).
