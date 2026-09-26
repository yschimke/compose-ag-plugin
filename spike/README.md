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
`render_preview` supplies a 1×1 PNG image. It also verifies the fixture's
MCP App resource, text fallback, `elicitation/create`, and prompts. It is not
evidence of any harness behaviour.

## Run in a harness

Install or enable both `p1` and `p2` using the harness-specific procedure under test. Then perform the question prompts from issue #6 and preserve the evidence:

- Inspect `/tmp/spike-*.json` for `clientInfo` and environment variables (Q8).
- Inspect `/tmp/spike-hooks.log` after a file edit and at end of turn (Q3–Q4).
- Ask the harness to call `render_preview` on `beta` after both plugins are active (Q2 and Q10).
- Ask `spike check` and `rules check` to test discovery (Q6–Q7).
- Call `render_preview`, confirm its text fallback remains visible, then use
  the viewer button to probe its `tools/call` to `status` and `ui/message`
  postMessage bridge (Q16–Q17).
- Call `ask` with both `mode: form` and `mode: url`; if no interaction appears,
  verify that form mode offers the `compact` and `expanded` choices in text,
  while URL mode supplies the authorization URL, verification code, and status
  polling instruction; call `access_status` to complete that fallback (Q18).
  List and get `spike-prompt` to probe prompts (Q19).
- Ask for the `spike-reviewer` fixture from plugin `p1` (Q20). In Claude Code
  and Codex, confirm the SessionStart hook both logs and prints
  `SPIKE-SESSION-START` so the model can be asked to repeat it (Q21).

The static marketplace fixture is at `.claude-plugin/marketplace.json`; the same entries are also available as `.agents/plugins/marketplace.json` for Codex marketplace resolution tests. The fixture uses `CLAUDE_PLUGIN_ROOT` only for paths inside each plugin in the Claude/Codex MCP and hook configurations. Its Antigravity config is generated because variable expansion for command paths is itself unverified.

## Hook decisions

`hook-log.sh` only observes by default. Set `SPIKE_HOOK_DECISION=continue` or `SPIKE_HOOK_DECISION=block` before starting a harness to emit the corresponding candidate Stop decision and test Q4. This intentionally keeps fixture installation from blocking normal work.

## Rich-protocol fixture fallbacks

The echo server attaches `ui://spike/app` as `text/html;profile=mcp-app` to the
existing `render_preview` tool through `_meta.ui.resourceUri`. That tool always
returns text and a `resource_link` as its fallback. The app performs the
portable `ui/initialize` then `ui/notifications/initialized` handshake, checks
that messages came from `window.parent`, handles JSON-RPC errors, and sends
well-formed `tools/call` and `ui/message` messages. It is fixture code rather
than an assertion that a host supports MCP Apps.

`ask` sends `elicitation/create` in both form and URL modes and reports a
complete text choice when a client declines or cannot support elicitation. It
uses MCP protocol `2025-11-25`, which supports URL mode. `prompts/list` and
`prompts/get` provide the `spike-prompt` probe. Plugin `p1` includes an
`agents/spike-reviewer.md` discovery fixture, and its SessionStart hook records
and prints the `SPIKE-SESSION-START` marker. Every result remains usable as
text.

The server sends form elicitation only after the client advertises
`elicitation.form` (or the legacy bare `elicitation: {}`), and URL elicitation
only after `elicitation.url`; otherwise `ask` returns the text fallback without
sending a server-to-client request.
