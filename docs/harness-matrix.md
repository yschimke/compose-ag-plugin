# Harness matrix

This matrix records only observed results for the compatibility investigation in [issue #6](https://github.com/yschimke/compose-ag-plugin/issues/6). A blank result has not been inferred from documentation or another harness.

## Fixture baseline

On 2026-09-26, `python3 spike/prepare.py && python3 spike/run-protocol-smoke.py` passed locally. The direct JSON-RPC client verified that both `alpha` and `beta` expose `render_preview` and `status`; `render_preview` returns a text item and a 1×1 PNG image. This establishes the fixture only, not host behaviour.

The fixture’s Antigravity `plugin.json` uses the current official v1 schema URL and no `version` field. That differs from the older issue text, which used `version`; the product scaffold follows the same current shape.

## Harness results

| Question | Antigravity | Claude Code | Codex | OpenCode | Evidence |
| --- | --- | --- | --- | --- | --- |
| Q1: Git subdirectory or marketplace installation | Not run | Not run | Not run | n/a | — |
| Q2: Duplicate MCP tool names | Not run | Not run | Not run | Not run | — |
| Q3: File-edit hooks and tool names | Not run | Not run | Not run | Not run | — |
| Q4: Stop-hook continuation or blocking | Not run | Not run | Not run | n/a | — |
| Q5: Root `plugin.json` coexistence | Not run | Not run | ✅ Codex 0.151.0 | n/a | A temporary `CODEX_HOME` installed both generated product plugins through the Claude-compatible marketplace while their directories also contained Antigravity v1 root manifests. |
| Q6: `rules/AGENTS.md` discovery | Not run | Not run | Not run | n/a | — |
| Q7: Skill discovery | Not run | Not run | Not run | Not run | — |
| Q8: MCP client identity and environment | Not run | Not run | Not run | Not run | — |
| Q9: Local PNG in Generative UI | Not run | n/a | n/a | n/a | — |
| Q10: MCP image rendering audience | Not run | Not run | Not run | Not run | — |
| Q11: Environment expansion in remote headers | Not run | Not run | Not run | Not run | — |
| Q12: Skiko/Wasm under Generative UI CSP | Not run | n/a | n/a | n/a | — |
| Q13: Existing `yschimke-skills` marketplace | n/a | n/a | Install ✅; trigger not run | n/a | Codex 0.151.0 added `yschimke/skills`, installed `yschimke-skills` 0.1.4, and cached all 8 `SKILL.md` files. No model turn tested triggering. |
| Q14: Canonical skills from `~/.agents/skills` or Skills CLI | Not run | n/a | n/a | n/a | — |
| Q15: Canonical skills plus wiring plugins coexist | Not run | Not run | Install/list ✅; trigger not run | Not run | Codex 0.151.0 enabled `yschimke-skills`, `compose-catalogs`, and `compose-preview` together. The wiring plugins contain no skills, so their packages introduced no duplicate skill IDs. |

## Additional observations

- OpenCode 2.0.10 accepted two separately named local MCP server definitions in
  a temporary project config. No server startup, tool call, or model turn ran,
  so Q2 remains untested.
- Codex 0.151.0 installed both product plugins from this checkout as a local
  marketplace. A GitHub marketplace URL and git subdirectory source were not
  tested, so Q1 remains untested.

## Reproduction

Prepare the fixture, install both `spike/p1` and `spike/p2` with the harness-specific flow under test, then retain the command, harness version, prompt, and relevant `/tmp/spike-*.json` or `/tmp/spike-hooks.log` output with each completed cell. See [`spike/README.md`](../spike/README.md) for the fixture setup and prompts.
