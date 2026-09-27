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
| Q1: Git subdirectory or marketplace installation | Not run | ✅ Claude Code 2.1.283: local path and GitHub marketplace | Not run | n/a | Claude Code: `claude plugin marketplace add` accepted the local `spike/` directory and `yschimke/compose-ag-plugin` (HTTPS clone, no prompt); `claude plugin install` installed both fixtures and both product plugins from their `./plugins/<name>` subdirectory sources. No `git-subdir` source was tested. [Claude Code evidence](evidence/2026-09-27-claude-code.md). |
| Q2: Duplicate MCP tool names | Not run | ✅ No clash in Claude Code 2.1.283 | Partial: both servers exposed in Codex 0.151.0 | Not run | With compatibility overlays and package-relative MCP working directories, both cached servers initialized. Direct calls to `alpha/status` and `beta/render_preview` completed, proving distinct server namespaces; the same colliding tool was not called on both servers. [Evidence](evidence/2026-09-26-codex-plugin-overlay.md). Claude Code: the model saw `mcp__plugin_p1_alpha__render_preview` and `mcp__plugin_p2_beta__render_preview` and called both. The fixture's `cwd: "."` server failed to start, so this ran with a temporary `${CLAUDE_PLUGIN_ROOT}` path overlay. [Claude Code evidence](evidence/2026-09-27-claude-code.md). |
| Q3: File-edit hooks and tool names | Not run | ✅ Claude Code 2.1.283 | Not run | Not run | Claude Code: PostToolUse ran for each plugin after `Write` and after `Edit`; the log recorded `tool_name` `Write` and `Edit`. `MultiEdit` was not exercised. [Claude Code evidence](evidence/2026-09-27-claude-code.md). |
| Q4: Stop-hook continuation or blocking | Not run | ✅ Claude Code 2.1.283; cap 9 | Not run | n/a | Claude Code: `{"decision":"block","reason":…}` from Stop fed the reason back as `Stop hook feedback` and the agent kept working. `stop_hook_active` was `false` on the first Stop, then `true`. The host overrode after "9 consecutive" blocks (configurable with `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`). [Claude Code evidence](evidence/2026-09-27-claude-code.md). |
| Q5: Root `plugin.json` coexistence | Not run | ✅ Claude Code 2.1.283 | ✅ Codex 0.151.0 | n/a | A temporary `CODEX_HOME` installed both generated product plugins through the Claude-compatible marketplace while their directories also contained Antigravity v1 root manifests. Claude Code: `claude plugin validate` passed (warnings only) for both fixtures, both product plugins and both marketplaces while their directories also held the Antigravity root manifests and `.codex-plugin/`; installs also worked. |
| Q6: `rules/AGENTS.md` discovery | Not run | Not loaded (not a Claude Code component) | Not run | n/a | Claude Code 2.1.283 answered `RULES-NONE` to `rules check`; plugin `rules/AGENTS.md` is not a Claude Code plugin component. |
| Q7: Skill discovery | Not run | ✅ Claude Code 2.1.283 as `p1:spike`, `p2:spike` | ✅ Codex exec 0.151.0 | Not run | The model loaded `spike-p1` and `spike-p2` by those names and returned both exact markers. [Evidence](evidence/2026-09-26-codex-rich-harness.md). Claude Code: skills were namespaced as `<plugin>:<skill directory>`, not by the frontmatter names `spike-p1`/`spike-p2`, and returned both markers. [Claude Code evidence](evidence/2026-09-27-claude-code.md). |
| Q8: MCP client identity and environment | Not run | ✅ Claude Code 2.1.283 | ✅ Codex 0.151.0 | Not run | Both servers recorded `clientInfo.name = codex-mcp-client`, title `Codex`, version `0.151.0`, and the environment keys visible to the server. [Evidence](evidence/2026-09-26-codex-plugin-overlay.md). Claude Code: `clientInfo.name = claude-code`, title `Claude Code`, version `2.1.283`; capabilities `elicitation: {}` and `roots.listChanged`. Server environment added `CLAUDECODE=1`, `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA` and `CLAUDE_PROJECT_DIR`. [Claude Code evidence](evidence/2026-09-27-claude-code.md). |
| Q9: Local PNG in Generative UI | Not run | n/a | n/a | n/a | — |
| Q10: MCP image rendering audience | Not run | Partial: model ✅ for 64×64; 1×1 rejected | Partial: image result reached Codex 0.151.0 | Not run | `beta/render_preview` completed and the model observed its image item, text fallback, and `resource_link`; the noninteractive terminal did not establish how a person sees the image. [Evidence](evidence/2026-09-26-codex-plugin-overlay.md). Claude Code 2.1.283: the fixture's 1×1 PNG was removed with "an image in the conversation could not be processed" while its text and link still arrived; a 64×64 PNG reached the model, which reported its colour. The person-facing view was not observed in print mode. [Claude Code evidence](evidence/2026-09-27-claude-code.md). |
| Q11: Environment expansion in remote headers | Not run | ✅ Claude Code 2.1.283 | Not run | Not run | Claude Code: in a plugin `.mcp.json` HTTP server, `${VAR}`, `${VAR:-default}` and `${CLAUDE_PLUGIN_ROOT}` in `headers` all arrived expanded at a local echo. [Claude Code evidence](evidence/2026-09-27-claude-code.md). |
| Q12: Skiko/Wasm under Generative UI CSP | Not run | n/a | n/a | n/a | — |
| Q13: Existing `yschimke-skills` marketplace | n/a | Install ✅; trigger ✅ | Install ✅; trigger not run | n/a | Codex 0.151.0 added `yschimke/skills`, installed `yschimke-skills` 0.1.4, and cached all 8 `SKILL.md` files. No model turn tested triggering. Claude Code 2.1.283 added `yschimke/skills`, installed `yschimke-skills` 0.1.5 with 8 skills, and a Compose `@Preview` request loaded `yschimke-skills:compose-preview`. |
| Q14: Canonical skills from `~/.agents/skills` or Skills CLI | Not run | n/a | n/a | n/a | — |
| Q15: Canonical skills plus wiring plugins coexist | Not run | ✅ Claude Code 2.1.283 | Install/list ✅; trigger not run | Not run | Codex 0.151.0 enabled `yschimke-skills`, `compose-catalogs`, and `compose-preview` together. The wiring plugins contain only the shared `harness-notes` skill, so they introduced no duplicate canonical Compose skill IDs. Claude Code: with all three enabled, every skill and agent was plugin-namespaced (`yschimke-skills:*`, `compose-preview:harness-notes`, `compose-catalogs:harness-notes`), so no ID clashed; `design-reviewer` is listed once per wiring plugin. |
| Q16: MCP App viewer resource rendering | Not run | Not rendered in print mode | Partial: resource link reached Codex 0.151.0 | Not run | `beta/render_preview` returned its image, text fallback, and `ui://spike/app` resource link, but `codex exec` did not open or render an MCP App surface for the person. [Evidence](evidence/2026-09-26-codex-plugin-overlay.md). Claude Code 2.1.283 `-p`: the resource link reached the model as text `[Resource link: Spike echo viewer] ui://spike/app`; the host ran `resources/list` but never `resources/read` for the viewer. The interactive UI was not run. |
| Q17: Viewer postMessage actions | Not run | Not run | Not run | Not run | The noninteractive probe did not open the viewer or invoke its bridge actions. Claude Code print mode opened no viewer, so its bridge could not be exercised. |
| Q18: `elicitation/create` | Not run | Partial: `elicitation: {}` advertised; print mode fell back | Tool exposed; interaction not run | Not run | Both servers exposed `ask`, but this probe did not call either elicitation mode. Claude Code 2.1.283 advertised form-only elicitation. The fixture sent a form `elicitation/create`, print mode showed nothing, and the tool returned the text fallback; URL mode was not advertised and returned the URL/code fallback. The interactive UI was not run. |
| Q19: `prompts/list` and `prompts/get` | Not run | ✅ Claude Code 2.1.283 | Not run in interactive UI | Not run | Both MCP servers initialized, but the noninteractive probe did not exercise prompt discovery and has no slash-command picker; this is not a product-level negative result. Claude Code listed `/mcp__plugin_p1_alpha__spike-prompt` and the beta equivalent as slash commands after `prompts/list`; invoking one in `-p` sent `prompts/get` with `path: Example.kt`. [Claude Code evidence](evidence/2026-09-27-claude-code.md). |
| Q20: Plugin `agents/` reviewer discovery | Not run | ✅ Claude Code 2.1.283 | Blocked in Codex exec 0.151.0 | Not run | One session exposed no invocable `spike-reviewer`; in another, the prompt supplied the name and the attempted spawn failed. Neither run established packaged-agent discovery. [Evidence](evidence/2026-09-26-codex-rich-harness.md). Claude Code listed `p1:spike-reviewer` as an Agent type; spawning it returned the exact fixture verdict. [Claude Code evidence](evidence/2026-09-27-claude-code.md). |
| Q21: SessionStart hook marker | n/a | ✅ Claude Code 2.1.283 | ✅ Codex exec 0.151.0 | n/a | Logs prove both plugin hooks ran with plugin-specific roots; a later run's model repeating their shared marker proves at least one output reached context. Both Stop observers also ran once. [Evidence](evidence/2026-09-26-codex-rich-harness.md). Claude Code: both SessionStart hooks ran with source `startup`; the model quoted `SessionStart:startup hook success: SPIKE-SESSION-START`. [Claude Code evidence](evidence/2026-09-27-claude-code.md). |

## Additional observations

- OpenCode 2.0.10 accepted two separately named local MCP server definitions in
  a temporary project config. No server startup, tool call, or model turn ran,
  so Q2 remains untested.
- Codex 0.151.0 installed both product plugins from this checkout as a local
  marketplace. A GitHub marketplace URL and git subdirectory source were not
  tested, so Q1 remains untested.
- An earlier isolated Codex session, before the compatibility overlays and
  package-relative MCP working directories, loaded skills and hooks but no MCP
  servers. At plugin commit `dec6a63`, a fresh isolated install initialized
  both servers and completed approved `alpha/status` and
  `beta/render_preview` calls. This establishes Codex CLI transport, not MCP
  App presentation, elicitation, prompts, or packaged-agent discovery. See the
  [exact probe evidence](evidence/2026-09-26-codex-plugin-overlay.md).
- Claude Code 2.1.205 could not be exercised in an earlier environment: the
  minimal JSON prompt was killed with exit 137. Claude Code 2.1.283 ran on
  2026-09-27 in `claude -p` print mode with an isolated `CLAUDE_CONFIG_DIR`; its
  column records only that mode. Print mode has no viewer, picker or form, so
  its Q16–Q18 results are not product-level negatives. See the
  [Claude Code evidence](evidence/2026-09-27-claude-code.md).
- Claude Code 2.1.283 resolved the fixture's relative MCP argument
  `./echo-mcp/server.py` against the session directory, ignoring `cwd: "."`,
  so both fixture servers failed to connect as shipped. Package-relative
  servers need `${CLAUDE_PLUGIN_ROOT}` in `args` for Claude Code. The
  generated product plugins do not use a relative server path.
- Neither the Antigravity desktop harness nor `agy` is available here. The
  current environment also has no OpenCode executable. Their unrun cells stay
  explicit rather than inheriting results from another harness.

## Reproduction

Prepare the fixture, install both `spike/p1` and `spike/p2` with the harness-specific flow under test, then retain the command, harness version, prompt, and relevant `/tmp/spike-*.json` or `/tmp/spike-hooks.log` output with each completed cell. See [`spike/README.md`](../spike/README.md) for the fixture setup and prompts.
