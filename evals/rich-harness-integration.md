# Rich harness integration evals

These evals cover the harness-facing features tracked in issue #18. Run them
with the canonical skills from `yschimke/skills`, the relevant wiring plugin,
and the server commit under test. Record what the person saw separately from
what the model received; a protocol fixture or static source inspection is not
a host pass.

The last column is the pass condition when the host shows no MCP Apps and
answers no elicitation, as in the Antigravity and OpenCode rows of the
[harness matrix](../docs/harness-matrix.md). A host that supports neither
feature is judged only on that column. The per-feature evals will be added with
the viewer work (compose-preview-server#1119).

## Cases

| ID | Feature and prompt | Pass condition | No MCP Apps, no elicitation |
| --- | --- | --- | --- |
| H1 | Render a preview with the viewer enabled: “Show this preview and tell me exactly which surface you inspected.” | The person sees the viewer or linked viewer, the agent can inspect the same render plus structure, and both sides identify the same artifact/revision. | The text result names the artifact (URI or file path), revision, dimensions, hash and accessibility summary. The agent still looks at the image itself and says no viewer was shown. |
| H2 | Exercise every shipped viewer mode: before/after, accessibility overlay, matrix, comment pins, and an A2UI document. | Each mode renders without losing the complete text result, and the agent can identify the active mode from the same artifact the person sees. | Each mode's content arrives as text: before/after hashes, the accessibility findings, matrix cells with hashes, the comment list, and the A2UI document path. The agent never says a mode was displayed. |
| H3 | In the viewer, select a node, choose a variant, post a comment, and open the editor. | Every action reaches the intended typed tool or conversation channel once, reports success or an actionable error, and never treats a UI-only state change as saved design state. | The result lists the exact typed tool call for each action, with the node ID, variant, comment text and editor link. The agent makes a call only when the person asks for it, and never says an action happened from the viewer. |
| H4 | Change the underlying preview while the viewer is open. | `resources/subscribe` refreshes the existing surface to the new artifact/revision without silently mixing old structure with a new image. | The agent re-renders and reports the new revision and hash. It never claims a live refresh. |
| H5 | Trigger a form elicitation for variant choice. | A supporting host shows the form and returns a schema-valid choice; an unsupported host receives a complete text choice and can continue without guessing. | A closed list of choices as text. The agent waits for the person's answer and doesn't pick one itself. |
| H6 | Trigger a URL elicitation for access. | A supporting host presents the URL flow without putting credentials in chat; an unsupported host receives the authorization URL and polling instructions as complete text. | The authorization URL, verification code and polling step (`poll_access` or `access_status`) as text. No token is asked for or shown in chat. |
| H7 | Invoke `preview-file`, `review-design`, `migrate-wear-m3`, and `design-status`. | Each supported prompt is discoverable and produces the documented typed workflow; an unsupported prompt surface has an equivalent written invocation. | Same as the pass condition: prompts use neither feature. |
| H8 | Ask the packaged design reviewer to run accessibility, font-scale, round-device, semantic-diff and catalog-guidelines sweeps. | Use the authoritative reviewer criteria in [`rich-integration.md`](rich-integration.md#design-reviewer-agent) and [guidelines G1–G8](design-guidelines.md): a supporting host runs the subagent in its own context; an unsupported host runs the same checklist in the current context, reports that limitation, and records a fallback result rather than a packaged-agent discovery pass. | The verdict carries file paths instead of viewer links. Otherwise the same as the supporting column. |
| H9 | Start a workspace session with a healthy or unhealthy MCP server, linked unacknowledged comments, and an unsaved temporary copy. | The startup hook emits one bounded summary containing only actionable states; a no-op session stays silent. | Same as the pass condition: the summary is already text. |
| H10 | Request a result that has both editor-node and source-line destinations. | Output contains valid deep links for every destination actually available and plainly omits or explains unavailable destinations. | Links are plain URLs. The node ref and source path and line are present even when a link is missing. |
| H11 | Repeat H1, H3, H5, and H6 with MCP Apps and elicitation unavailable. | The text result is complete enough to understand the render and finish the workflow; it never claims that a viewer or interaction was shown. | This case is the fallback run of H1, H3, H5 and H6; use their entries in this column. |

## Recorded runs

| Date | Harness | Version | Canonical skills | Plugin commit | Server commit | Cases | Result | Tool sequence | Images | Follow-up | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-26 | Codex exec | 0.151.0 | n/a — fixture skills only | `d37dd66d` | fixture server at `d37dd66d` | H1, H3, H5–H9, H11 fixture probes | Blocked; lifecycle transport observed | p1 SessionStart → p2 SessionStart → read `spike-p1` → read `spike-p2` → attempt named reviewer (failed) → p1 Stop → p2 Stop; no fixture MCP tool call | 0 | #6, #18 | Both spike plugins installed; skills and lifecycle hooks loaded. Fixture MCP tools did not, so viewer, action, elicitation, prompt, and fallback cases could not run. The named reviewer invocation failed with `no thread with id` without establishing packaged-agent discovery. SessionStart delivered the shared fixture marker from at least one of the two logged hooks, and both Stop observers ran; none of H9's state-summary conditions was exercised. See [evidence](../docs/evidence/2026-09-26-codex-rich-harness.md). |
| 2026-09-27 | Claude Code `-p` | 2.1.283 | n/a — fixture skills only (`yschimke/skills` 0.1.5 for install and coexistence only) | `16ce908` | fixture server at `16ce908` with a temporary `${CLAUDE_PLUGIN_ROOT}` path overlay | H1, H5–H9, H11 fixture probes | Partial; print mode, no UI surfaces | p1/p2 SessionStart → `p1:spike` → `p2:spike` → beta `render_preview` → alpha `render_preview` → beta `ask` form → beta `ask` url → `Write` → `Edit` → `Agent p1:spike-reviewer` → p2/p1 Stop | 3 | #6, #18 | The resource link reached the model as text and the viewer was never read (H1 not met). The form `elicitation/create` was not answered in print mode and URL mode was not advertised, so both returned their complete text fallbacks (H5/H6/H11 fallback path). `/mcp__plugin_p1_alpha__spike-prompt` sent `prompts/get` (H7 fixture). The packaged reviewer returned its exact verdict (H8 discovery). The SessionStart marker reached context (H9 state summary not exercised). See [evidence](../docs/evidence/2026-09-27-claude-code.md). |
| 2026-09-27 | Antigravity (`agy`, by hand) | 1.2.12, Gemini 3.8 Flash High | n/a — fixture skills only (Skills CLI `compose-preview` installed but not loaded) | not recorded | fixture server; product plugins `compose-preview` and `compose-catalogs` | H1, H5–H9, H11 fixture probes; product render | Partial; no MCP Apps, elicitation or SessionStart | Order not recorded. Probes: p1/p2 install, `rules check`, `spike check`, `call_mcp_tool` `render_preview`, `ask` form and url, `write_to_file`/`replace_file_content`, spike-reviewer subagent, Stop (`continue`, about 30 times until stopped by the owner) | fixture 1×1 PNG plus product renders | #6, #18, #35, compose-preview-server#1160 | The render image reached both the person and the model, but the MCP App viewer was not rendered and `<agent-embed>` cards are `iframe srcdoc` with no bridge (H1 not met). Form and URL elicitation both returned their complete text fallbacks (H5/H6/H11 fallback path). MCP prompts were listed as `mcp:p1_alpha:spike-prompt` but not invoked (H7 discovery only). The packaged reviewer returned its exact verdict (H8 discovery). No SessionStart-equivalent hook fired (H9 not met). With a Wear project, `compose-preview` discovered 17 previews and rendered them, and its text fallback was complete. See [evidence](../docs/evidence/2026-09-27-antigravity.md). |
| 2026-09-26 | Claude Code | 2.1.205 | n/a — harness did not start | `d37dd66d` | n/a | — | Environment unavailable | n/a | n/a | #6, #18 | A minimal JSON prompt was killed with exit 137 and no output, including outside the restricted sandbox. This is not a product result. |
| 2026-09-26 | Antigravity | unavailable | n/a — harness unavailable | `d37dd66d` | n/a | — | Environment unavailable | n/a | n/a | #6, #18 | Neither the desktop harness nor `agy` is available. |
| 2026-09-26 | OpenCode | unavailable | n/a — harness unavailable | `d37dd66d` | n/a | — | Environment unavailable | n/a | n/a | #6, #18 | No OpenCode executable is installed; the matrix's earlier config-parser observation is not a model-turn eval. |

The direct protocol smoke test passed at the recorded `d37dd66d` revision for
both elicitation-capable exchanges. A separate fixture-only rerun at `c0f4f04`
verified the explicit form/URL text fallbacks with elicitation omitted from
client capabilities. A further fixture-only rerun at `9c3d633` added the
dedicated `access_status` operation and exercised it after the URL/code
fallback, proving that the documented polling step is executable. These
controls are not host passes. H1–H8 and H10–H11 still
need real host runs, H9 still needs its full state scenarios, and every
behavioral feature still needs a second harness even after a Codex run passes.
