# Codex install evidence

> Historical evidence below retains the repository and marketplace names used during the run.
> For current installation and migration instructions, see the
> [Compose Agent Plugins quick start](../../README.md#quick-start).

This record covers the Codex launch checks (#41) that need no model session
and no GUI. Nothing here exercises a model turn, the MCP Apps viewer,
elicitation, prompts, or hook behaviour.

## Environment

- Date: 2026-09-27
- Codex CLI: 0.157.1 (`npm i -g @openai/codex`), Linux x86_64
- Plugin commit: `b5ee775` (`main`)
- Homes: two fresh temporary `CODEX_HOME` directories, one per marketplace
  source, with no authentication. Both marketplaces are named
  `compose-ag-plugin`, so adding the second to the same home replaces the
  first.
- Environment keys set: `CODEX_HOME`. `COMPOSE_PREVIEW_TOKEN` was not set.
- `compose-preview` CLI: not installed

## Install

```sh
codex plugin marketplace add /path/to/compose-ag-plugin      # home 1
codex plugin marketplace add yschimke/compose-ag-plugin      # home 2
codex plugin add compose-catalogs@compose-ag-plugin
codex plugin add compose-preview@compose-ag-plugin
codex plugin list
```

```text
Added marketplace `compose-ag-plugin` from https://github.com/yschimke/compose-ag-plugin.git.
Marketplace `compose-ag-plugin`
<CODEX_HOME>/.tmp/marketplaces/compose-ag-plugin/.claude-plugin/marketplace.json

PLUGIN                              STATUS              VERSION
compose-catalogs@compose-ag-plugin  installed, enabled  0.2.0
compose-preview@compose-ag-plugin   installed, enabled  0.2.0
```

The local-path home gave the same list. Both sources resolved the existing
`.claude-plugin/marketplace.json`, so **`.agents/plugins/marketplace.json`
is not needed** (#7 T2). Plugins were cached under
`<CODEX_HOME>/plugins/cache/compose-ag-plugin/<plugin>/0.2.0`, and each loaded its
`.codex-plugin/plugin.json`. Every command printed a warning that Codex will
not create PATH helper aliases under `/tmp`; this is harmless.

## MCP servers

`codex mcp list` and `codex mcp get <name> --json`:

| Server | Plugin | Transport | Detail |
| --- | --- | --- | --- |
| `compose-preview-catalog` | `compose-catalogs` | `streamable_http` | `https://preview.coo.ee/mcp`; `env_http_headers` maps `X-Compose-Preview-Token` to `COMPOSE_PREVIEW_TOKEN`; auth `Not logged in` |
| `compose-preview-mcp` | `compose-preview` | `stdio` | `compose-preview mcp serve`; no `cwd` or `env` |

The plain `codex mcp list` table shows `-` under "Bearer Token Env Var"; the
header mapping appears only in `--json`.

App-server `mcpServerStatus/list` (via `codex app-server` over stdio) started
both servers the way a session does:

- `compose-preview-catalog`: initialized, `serverInfo` version `3.77.0`,
  capabilities `tools`, `resources`, `prompts`; 41 tools, including
  `render_preview`, `list_projects`, `request_access`, `poll_access` and the
  `ui_builder_*` set. Codex appends "This tool is part of plugin `Compose
  Catalogs`." to each tool description.
- `compose-preview-mcp`: `toolsError: "MCP startup failed: No such file or
  directory (os error 2)"`, because the `compose-preview` CLI is not
  installed. Not verified.

## Skills, agents and hooks

App-server `skills/list`, `plugin/read` and `hooks/list`:

- `compose-catalogs`: skill `compose-catalogs:harness-notes`; no hooks; no
  agents.
- `compose-preview`: skills `compose-preview:harness-notes` and
  `compose-preview:antigravity-viewer-card`; no agents.
- `compose-preview` hooks, from `hooks/codex-hooks.json`, with
  `${CLAUDE_PLUGIN_ROOT}` expanded to the cache root:
  - `sessionStart`, matcher `startup`, `scripts/session-start-summary.sh
    --harness=codex`, timeout 10 s
  - `stop`, `scripts/stop-gate.sh --harness=codex`, timeout 360 s

  Both hooks are `enabled: true`, `source: plugin`, `trustStatus: untrusted`.
- `codex debug prompt-input` listed the same three plugin skills in the
  model-visible skill list.

Neither `plugin/read` result has an agents field, and the generated
`.codex-plugin/plugin.json` declares none, so `design-reviewer` is not
exposed in Codex. The Antigravity-only `antigravity-viewer-card` skill is
visible to Codex.

## Not run

Everything that needs a model or a person: tool calls, image delivery,
whether the `apply_patch` edit hook or Stop continuation fires, hook trust
approval, header delivery with a real `COMPOSE_PREVIEW_TOKEN`, the Codex
Desktop MCP Apps viewer, TUI form elicitation, and prompts.
