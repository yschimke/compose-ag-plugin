# Harness spike fixture

This fixture supports issue [#6](https://github.com/yschimke/compose-ag-plugin/issues/6). It is deliberately separate from shipping plugins and makes no claim about a harness until that harness has run it.

The Antigravity root manifests follow the current official schema URL and omit the older `version` field. The adjacent Claude/Codex manifests retain `name` and `version` because they exercise a separate manifest format.

## Prepare and verify the fixture

From the repository root:

```sh
python3 spike/prepare.py
python3 spike/run-protocol-smoke.py
```

`prepare.py` copies the echo MCP server and hook logger into each ignored
`spike/p*/echo-mcp/` directory, then writes ignored Antigravity `mcp_config.json`
and `hooks.json` files that point to that plugin-local copy. It is safe to run
after moving the checkout; do not install the Antigravity fixtures before
preparation.
The smoke test speaks JSON-RPC directly, confirms both servers expose the
deliberately colliding `render_preview` and `status` tools, and confirms that
`render_preview` supplies a 1×1 PNG image. It is not evidence of any harness
behaviour.

## Run in a harness

Install or enable both `p1` and `p2` using the harness-specific procedure under test. Then perform the question prompts from issue #6 and preserve the evidence:

- Inspect `/tmp/spike-*.json` for `clientInfo` and environment variables (Q8).
- Inspect `/tmp/spike-hooks.log` after a file edit and at end of turn (Q3–Q4).
- Ask the harness to call `render_preview` on `beta` after both plugins are active (Q2 and Q10).
- Ask `spike check` and `rules check` to test discovery (Q6–Q7).

The static marketplace fixture is at `.claude-plugin/marketplace.json`; the same entries are also available as `.agents/plugins/marketplace.json` for Codex marketplace resolution tests. The fixture uses `CLAUDE_PLUGIN_ROOT` only for paths inside each plugin in the Claude/Codex MCP and hook configurations. Its Antigravity config is generated because variable expansion for command paths is itself unverified.

## Hook decisions

`hook-log.sh` only observes by default. Set `SPIKE_HOOK_DECISION=continue` or `SPIKE_HOOK_DECISION=block` before starting a harness to emit the corresponding candidate Stop decision and test Q4. This intentionally keeps fixture installation from blocking normal work.
