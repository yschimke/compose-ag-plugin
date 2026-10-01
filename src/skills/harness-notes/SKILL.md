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

UI Builder loop, one call each where the server advertises them: `ui_builder_check_design` (schema,
catalog and accessibility findings by node; pass `operations` to dry-run an edit) before showing a
design; `ui_builder_render_design_matrix` for every device size as one picture; `ui_builder_await_decision`
(`waitSeconds: 0` to poll) for a person's approve/reject; `ui_builder_set_implementation` and
`ui_builder_implementation_status` to tie the design to its PR. Read each reply's `summary` first.

Pick the server by what is being rendered: the person's own `@Preview`s come from the local
`compose-preview-mcp` server; library components come from `compose-preview-catalog`. R3 and R4
apply to UI Builder designs, not to plain preview renders. Keep a simple render short: in Antigravity,
follow `antigravity-viewer-card` (`render_preview preview=<Name>`, look at the PNG, a few bullets); elsewhere, one
render call and a short reply.

In a chat surface (Claude in Slack, Teams), the person sees only text and attachments. Each render from
the hosted catalog carries a signed https PNG (an `Image: <url>` line, `imageUrl`, `contactSheet.url`)
that is valid for 10 minutes: attach or link that, and never describe an image from memory. To offer
alternatives, call `catalog_render_matrix` with `observe=png`, post its numbered contact sheet with the
options, and take the person's reply ("2") as the choice. Reactions and buttons are not input there. For
R4, post the design link and a summary of unacknowledged comments rather than treating thread replies as
design comments. No server event wakes a chat agent, so follow up through a PR subscription or by polling
`ui_builder_await_comments` / `ui_builder_await_decision` with `waitSeconds: 0`.

Claude Code ≥2.1.281 supports URL elicitation only on 2026-07-28-protocol connections; otherwise use the text fallback for the access grant.
Claude Code does not load a plugin's `rules/AGENTS.md`; guidance it must always see belongs in a skill or the SessionStart message.

The full, authoritative contract and current tooling gaps are in
[`docs/agent-rules.md`](https://github.com/yschimke/compose-ag-plugin/blob/main/docs/agent-rules.md).
