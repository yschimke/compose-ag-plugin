# Rich harness integration evals

These evals cover the harness-facing features tracked in issue #18. Run them
with the canonical skills from `yschimke/skills`, the relevant wiring plugin,
and the server commit under test. Record what the person saw separately from
what the model received; a protocol fixture or static source inspection is not
a host pass.

## Cases

| ID | Feature and prompt | Pass condition |
| --- | --- | --- |
| H1 | Render a preview with the viewer enabled: “Show this preview and tell me exactly which surface you inspected.” | The person sees the viewer or linked viewer, the agent can inspect the same render plus structure, and both sides identify the same artifact/revision. |
| H2 | Exercise every shipped viewer mode: before/after, accessibility overlay, matrix, comment pins, and an A2UI document. | Each mode renders without losing the complete text result, and the agent can identify the active mode from the same artifact the person sees. |
| H3 | In the viewer, select a node, choose a variant, post a comment, and open the editor. | Every action reaches the intended typed tool or conversation channel once, reports success or an actionable error, and never treats a UI-only state change as saved design state. |
| H4 | Change the underlying preview while the viewer is open. | `resources/subscribe` refreshes the existing surface to the new artifact/revision without silently mixing old structure with a new image. |
| H5 | Trigger a form elicitation for variant choice. | A supporting host shows the form and returns a schema-valid choice; an unsupported host receives a complete text choice and can continue without guessing. |
| H6 | Trigger a URL elicitation for access. | A supporting host presents the URL flow without putting credentials in chat; an unsupported host receives the authorization URL and polling instructions as complete text. |
| H7 | Invoke `preview-file`, `review-design`, `migrate-wear-m3`, and `design-status`. | Each supported prompt is discoverable and produces the documented typed workflow; an unsupported prompt surface has an equivalent written invocation. |
| H8 | Ask the packaged design reviewer to run accessibility, font-scale, round-device, and semantic-diff sweeps. | The subagent runs in its own context and returns a concise verdict plus viewer/artifact links; images do not flood the parent conversation. |
| H9 | Start a workspace session with a healthy or unhealthy MCP server, linked unacknowledged comments, and an unsaved temporary copy. | The startup hook emits one bounded summary containing only actionable states; a no-op session stays silent. |
| H10 | Request a result that has both editor-node and source-line destinations. | Output contains valid deep links for every destination actually available and plainly omits or explains unavailable destinations. |
| H11 | Repeat H1, H3, H5, and H6 with MCP Apps and elicitation unavailable. | The text result is complete enough to understand the render and finish the workflow; it never claims that a viewer or interaction was shown. |

## Recorded runs

| Date | Harness | Version | Plugin commit | Cases | Result | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-09-26 | Codex exec | 0.151.0 | `d37dd66d` | H1, H3, H5–H9, H11 fixture probes | Blocked; H9 transport subprobe passed | Both spike plugins installed; skills and lifecycle hooks loaded. Fixture MCP tools did not, so viewer, action, elicitation, prompt, and fallback cases could not run. The reviewer invocation failed with `no thread with id`. SessionStart delivered the exact marker and both Stop observers ran, but the full H9 state summary was not exercised. See [evidence](../docs/evidence/2026-09-26-codex-rich-harness.md). |
| 2026-09-26 | Claude Code | 2.1.205 | `d37dd66d` | — | Environment unavailable | A minimal JSON prompt was killed with exit 137 and no output, including outside the restricted sandbox. This is not a product result. |
| 2026-09-26 | Antigravity | unavailable | `d37dd66d` | — | Environment unavailable | Neither the desktop harness nor `agy` is available. |
| 2026-09-26 | OpenCode | unavailable | `d37dd66d` | — | Environment unavailable | No OpenCode executable is installed; the matrix's earlier config-parser observation is not a model-turn eval. |

The direct protocol smoke test passes for the rich fixture, including complete
fallback payloads. It is a fixture control only. H1–H8 and H10–H11 still need
real host runs, H9 still needs its full state scenarios, and every behavioral
feature still needs a second harness even after a Codex run passes.
