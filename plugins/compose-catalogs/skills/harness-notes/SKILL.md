---
name: harness-notes
description: Use whenever you change Compose UI code (composables, @Preview functions, themes) or render Compose previews, catalog components or UI Builder designs. Carries the mandatory cross-harness agent rules for compose-ag-plugin's tools, alongside the canonical yschimke/skills workflows.
---

# Harness notes

Use the canonical `compose-preview` and `compose-ui-builder` skills from
[`yschimke/skills`](https://github.com/yschimke/skills) for workflows. These notes only carry the
rules that must remain consistent across Antigravity, Claude Code, and Codex.

- **R1 — See what the user sees:** inspect the surface where the person will judge a visual change. After editing Compose UI source, call `render_preview` for an affected preview and look at the result before calling the change done; an edit you haven't rendered isn't done. If that surface is unavailable, say so and never claim to have seen the result from source or JSON alone. Never fake a render: no hand-built HTML, CSS or SVG mock of a preview; only real renders count, and a failed render is reported as failed.
- **R2 — Use typed tools with schemas:** prefer validated MCP or CLI operations; if raw JSON is unavoidable, validate it before saving and render it again afterwards.
- **R3 — Keep one canonical home:** read and preserve the design's recorded home, edit there in small batches, announce and reconcile temporary copies, and get approval before moving the home.
- **R4 — Keep discussion at the home:** use server comments for server-homed designs and the linked PR or issue for repo-homed designs, then report unacknowledged comments before finishing.

Pick the server by what is being rendered: the person's own `@Preview`s come from the local
`compose-preview-mcp` server; library components come from `compose-preview-catalog`. R3 and R4
apply to UI Builder designs, not to plain preview renders. Keep a simple render short: in Antigravity,
follow `antigravity-viewer-card` (`render_preview preview=<Name>`, look at the PNG, a few bullets); elsewhere, one
render call and a short reply.

Claude Code ≥2.1.281 supports URL elicitation only on 2026-07-28-protocol connections; otherwise use the text fallback for the access grant.
Claude Code does not load a plugin's `rules/AGENTS.md`; guidance it must always see belongs in a skill or the SessionStart message.

The full, authoritative contract and current tooling gaps are in
[`docs/agent-rules.md`](https://github.com/yschimke/compose-ag-plugin/blob/main/docs/agent-rules.md).
