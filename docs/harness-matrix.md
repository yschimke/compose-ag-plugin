# Harness matrix

This matrix records only observed results for the compatibility investigation in [issue #6](https://github.com/yschimke/compose-ag-plugin/issues/6). A blank result has not been inferred from documentation or another harness.

## Fixture baseline

On 2026-09-26, `python3 spike/prepare.py && python3 spike/run-protocol-smoke.py` passed locally. The direct JSON-RPC client verified that both `alpha` and `beta` expose `render_preview` and `status`; `render_preview` returns a text item and a 1×1 PNG image. This establishes the fixture only, not host behaviour.

The fixture’s Antigravity `plugin.json` follows Google's
[official plugin manifest documentation](https://antigravity.google/docs/plugins#manifest-file-plugin-json):
the v1 schema URL, a required `name`, an optional `description`, and no `version` field. That differs
from the older issue text, which used `version`; the product scaffold follows the documented shape.
The documentation both recommends the `$schema` property and shows it in the canonical example,
although the full schema printed on that page omits `$schema` from `properties`. The vendored schema
keeps `$schema` as a constant so the documented example validates while a different schema URL does
not.

## Harness results

| Question | Antigravity | Claude Code | Codex | OpenCode | Evidence |
| --- | --- | --- | --- | --- | --- |
| Q1: Git subdirectory or marketplace installation | Not run | Not run | Not run | n/a | — |
| Q2: Duplicate MCP tool names | Not run | Not run | Partial: both servers exposed in Codex 0.151.0 | Not run | With compatibility overlays and package-relative MCP working directories, both cached servers initialized. Direct calls to `alpha/status` and `beta/render_preview` completed, proving distinct server namespaces; the same colliding tool was not called on both servers. [Evidence](evidence/2026-09-26-codex-plugin-overlay.md). |
| Q3: File-edit hooks and tool names | Not run | Not run | Not run | Not run | — |
| Q4: Stop-hook continuation or blocking | Not run | Not run | Not run | n/a | — |
| Q5: Root `plugin.json` coexistence | Not run | Not run | ✅ Codex 0.151.0 | n/a | A temporary `CODEX_HOME` installed both generated product plugins through the Claude-compatible marketplace while their directories also contained Antigravity v1 root manifests. |
| Q6: `rules/AGENTS.md` discovery | Not run | Not run | Not run | n/a | — |
| Q7: Skill discovery | Not run | Not run | ✅ Codex exec 0.151.0 | Not run | The model loaded `spike-p1` and `spike-p2` by those names and returned both exact markers. [Evidence](evidence/2026-09-26-codex-rich-harness.md). |
| Q8: MCP client identity and environment | Not run | Not run | ✅ Codex 0.151.0 | Not run | Both servers recorded `clientInfo.name = codex-mcp-client`, title `Codex`, version `0.151.0`, and the environment keys visible to the server. [Evidence](evidence/2026-09-26-codex-plugin-overlay.md). |
| Q9: Local PNG in Generative UI | Not run | n/a | n/a | n/a | — |
| Q10: MCP image rendering audience | Not run | Not run | Partial: image result reached Codex 0.151.0 | Not run | `beta/render_preview` completed and the model observed its image item, text fallback, and `resource_link`; the noninteractive terminal did not establish how a person sees the image. [Evidence](evidence/2026-09-26-codex-plugin-overlay.md). |
| Q11: Environment expansion in remote headers | Not run | Not run | Not run | Not run | — |
| Q12: Skiko/Wasm under Generative UI CSP | Not run | n/a | n/a | n/a | — |
| Q13: Existing `yschimke-skills` marketplace | n/a | n/a | Install ✅; trigger not run | n/a | Codex 0.151.0 added `yschimke/skills`, installed `yschimke-skills` 0.1.4, and cached all 8 `SKILL.md` files. No model turn tested triggering. |
| Q14: Canonical skills from `~/.agents/skills` or Skills CLI | Not run | n/a | n/a | n/a | — |
| Q15: Canonical skills plus wiring plugins coexist | Not run | Not run | Install/list ✅; trigger not run | Not run | Codex 0.151.0 enabled `yschimke-skills`, `compose-catalogs`, and `compose-preview` together. The wiring plugins contain only the shared `harness-notes` skill, so they introduced no duplicate canonical Compose skill IDs. |
| Q16: MCP App viewer resource rendering | Not run | Not run | Partial: resource link reached Codex 0.151.0 | Not run | `beta/render_preview` returned its image, text fallback, and `ui://spike/app` resource link, but `codex exec` did not open or render an MCP App surface for the person. [Evidence](evidence/2026-09-26-codex-plugin-overlay.md). |
| Q17: Viewer postMessage actions | Not run | Not run | Not run | Not run | The noninteractive probe did not open the viewer or invoke its bridge actions. |
| Q18: `elicitation/create` | Not run | Not run | Tool exposed; interaction not run | Not run | Both servers exposed `ask`, but this probe did not call either elicitation mode. |
| Q19: `prompts/list` and `prompts/get` | Not run | Not run | Not run in interactive UI | Not run | Both MCP servers initialized, but the noninteractive probe did not exercise prompt discovery and has no slash-command picker; this is not a product-level negative result. |
| Q20: Plugin `agents/` reviewer discovery | Not run | Not run | Blocked in Codex exec 0.151.0 | Not run | One session exposed no invocable `spike-reviewer`; in another, the prompt supplied the name and the attempted spawn failed. Neither run established packaged-agent discovery. [Evidence](evidence/2026-09-26-codex-rich-harness.md). |
| Q21: SessionStart hook marker | n/a | Not run | ✅ Codex exec 0.151.0 | n/a | Logs prove both plugin hooks ran with plugin-specific roots; a later run's model repeating their shared marker proves at least one output reached context. Both Stop observers also ran once. [Evidence](evidence/2026-09-26-codex-rich-harness.md). |

## Additional observations

- OpenCode 2.0.10 accepted two separately named local MCP server definitions in
  a temporary project config. No server startup, tool call, or model turn ran,
  so Q2 remains untested.
- Codex 0.151.0 installed both product plugins from this checkout as a local
  marketplace. A GitHub marketplace URL and git subdirectory source were not
  tested, so Q1 remains untested.
- An earlier isolated Codex session, before the compatibility overlays and
  package-relative MCP working directories, loaded skills and hooks but no MCP
  servers. At plugin commit `56a1d59`, a fresh isolated install initialized
  both servers and completed approved `alpha/status` and
  `beta/render_preview` calls. This establishes Codex CLI transport, not MCP
  App presentation, elicitation, prompts, or packaged-agent discovery. See the
  [exact probe evidence](evidence/2026-09-26-codex-plugin-overlay.md).
- Claude Code 2.1.205 could not be exercised in this environment. The command
  `claude -p 'Reply only CLAUDE-OK' --output-format json` was killed with exit
  137 and no output, including outside the restricted sandbox. This is an
  environment limitation, not a Claude Code compatibility result.
- Neither the Antigravity desktop harness nor `agy` is available here. The
  current environment also has no OpenCode executable. Their unrun cells stay
  explicit rather than inheriting results from another harness.

## Reproduction

Prepare the fixture, install both `spike/p1` and `spike/p2` with the harness-specific flow under test, then retain the command, harness version, prompt, and relevant `/tmp/spike-*.json` or `/tmp/spike-hooks.log` output with each completed cell. See [`spike/README.md`](../spike/README.md) for the fixture setup and prompts.
