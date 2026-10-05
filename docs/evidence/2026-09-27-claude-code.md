# Claude Code harness evidence

> Historical evidence below retains the repository and marketplace names used during the run.
> For current installation and migration instructions, see the
> [Compose Agent Plugins quick start](../../README.md#quick-start).

This record preserves the observed Claude Code portion of the issue #6 and
issue #18 compatibility investigation. It distinguishes host behavior from the
direct JSON-RPC fixture smoke test, and print-mode (`claude -p`) limits from
product-level results: nothing below was observed in the interactive terminal
UI.

## Environment

- Date: 2026-09-27
- Claude Code: 2.1.283 (`/opt/node22/bin/claude`)
- Model for probe turns: `haiku` alias (`claude-haiku-4-5-20251001`)
- Plugin repository commit: `16ce9083f538307668174b58ceea9e9eeb9cea8a`
- Mode: noninteractive `claude -p --output-format stream-json --verbose`,
  with a fresh `--session-id` and `--no-session-persistence` for every run
- Plugin home: isolated temporary `CLAUDE_CONFIG_DIR`. Authentication came from
  the environment, so no credential file was copied. The user's normal
  `~/.claude` settings, plugins and `CLAUDE.md` were not modified; their
  modification times were checked afterwards.
- Every run started from a temporary project directory under
  `/tmp/claude-0/ccprobe-*`. The wrapper cleared the parent session's routing
  variables (`CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_REMOTE_SESSION_ID`,
  `CLAUDE_CODE_TEE_SDK_STDOUT`, messaging and sync keys, `CLAUDECODE`) so each
  nested run reported its own `session_id`.

Run metadata required by `evals/README.md`:

- Canonical-skills commit: `yschimke/skills` `03d382ac` (plugin 0.1.5) for Q13
  and Q15 only. All other probes used only the fixture skills.
- Server commit: fixture echo server at plugin commit `16ce908`, plus the
  temporary overlay described below.
- Tool sequence (main probe): p1 SessionStart, p2 SessionStart, `Skill p1:spike`,
  `Skill p2:spike`, `ToolSearch`, `mcp__plugin_p2_beta__render_preview`,
  `mcp__plugin_p1_alpha__render_preview`, `mcp__plugin_p2_beta__ask` (form),
  `mcp__plugin_p2_beta__ask` (url), `Write` (then PostToolUse ×2), `Edit` (then
  PostToolUse ×2), `Agent p1:spike-reviewer`, p2 Stop, p1 Stop.
- Image count: 3 returned (two 1×1 fixture PNGs, one 64×64 overlay PNG).
- Follow-up: issues #6 and #18.
- Nested model runs: 10, total reported cost about 0.37 USD at list price.

## Commands

The wrapper used for every nested command:

```sh
export CLAUDE_CONFIG_DIR=/tmp/claude-0/ccprobe-cfg
unset CLAUDE_CODE_SESSION_ID CLAUDE_CODE_REMOTE_SESSION_ID CLAUDE_CODE_TEE_SDK_STDOUT \
  CLAUDE_CODE_MESSAGING_SOCKET CLAUDE_CODE_MESSAGING_TOKEN CLAUDE_CODE_SYNC_SESSION_REFS \
  CLAUDE_CODE_POST_FOR_SESSION_INGRESS_V2 CLAUDE_CODE_DIAGNOSTICS_FILE CLAUDE_CODE_CHILD_SESSION \
  CLAUDE_PID CLAUDE_AFTER_LAST_COMPACT CLAUDE_CODE_SESSION_ATTENDED CLAUDE_CODE_SYNC_SKILLS \
  CLAUDE_CODE_HOLD_UNANSWERED_PARKED_PERMISSION CLAUDE_CODE_REMOTE_SEND_KEEPALIVES CLAUDECODE
cd "$CCPROJ"   # a /tmp/claude-0/ccprobe-* directory
```

Fixture control and installation (no model turn):

```sh
python3 spike/prepare.py && python3 spike/run-protocol-smoke.py
claude plugin validate spike/p1        # also spike/p2, plugins/*, spike, .
claude plugin marketplace add <checkout>/spike --scope project
claude plugin install p1@compose-ag-plugin-spike --scope project
claude plugin install p2@compose-ag-plugin-spike --scope project
claude plugin marketplace add yschimke/compose-ag-plugin --scope project
claude plugin install compose-preview@compose-ag-plugin --scope project
claude plugin install compose-catalogs@compose-ag-plugin --scope project
claude plugin marketplace add yschimke/skills --scope project
claude plugin install yschimke-skills@yschimke-skills --scope project
claude mcp list
```

Model turns all used this shape, with the prompt and flags listed per probe:

```sh
timeout 300 claude -p "$PROMPT" --output-format stream-json --verbose \
  --include-hook-events --session-id "$(python3 -c 'import uuid;print(uuid.uuid4())')" \
  --no-session-persistence --model haiku --max-budget-usd 1 \
  --plugin-dir /tmp/claude-0/ccprobe-spike/p1 --plugin-dir /tmp/claude-0/ccprobe-spike/p2 \
  --allowedTools '<only the tools the probe needs>' </dev/null
```

## Fixture MCP path and the temporary overlay

With the unmodified fixture installed from the local marketplace, both servers
failed to start. The session `init` event reported
`plugin:p1:alpha` and `plugin:p2:beta` with `status: failed`, and:

```text
$ claude mcp list
plugin:p1:alpha: python3 ./echo-mcp/server.py alpha - × Failed to connect — CONNECTION_CLOSED: Connection closed
plugin:p2:beta: python3 ./echo-mcp/server.py beta - × Failed to connect — CONNECTION_CLOSED: Connection closed
```

A symbolic link from the session project directory to `spike/p1/echo-mcp`
made both servers connect, so Claude Code 2.1.283 resolved the relative
`./echo-mcp/server.py` argument against the session working directory rather
than the plugin root. The fixture's `cwd: "."` therefore does not give a
package-relative server in Claude Code. The product plugins are unaffected:
`compose-preview` launches `compose-preview` from `PATH`, and
`compose-catalogs` is a remote HTTP server.

The MCP model probes (Q2, Q10, Q16, Q18, Q19) therefore used a temporary copy of
`spike/` loaded with `--plugin-dir`, differing from the checkout only in:

- `.mcp.json` args `["${CLAUDE_PLUGIN_ROOT}/echo-mcp/server.py", "<name>"]`
  with no `cwd`;
- the copied `server.py` also records the `initialize` `capabilities` and
  appends each method to a probe log;
- for the second image probe only, the 1×1 PNG replaced by a 64×64 solid red
  PNG.

The checkout's fixture was not changed.

## Observations

### Installation and manifests (Q1, Q5, Q13, Q15)

- `claude plugin marketplace add` accepted the local `spike/` directory and the
  GitHub shorthand `yschimke/compose-ag-plugin`, which cloned over HTTPS without
  a prompt. `claude plugin install` then installed `p1`/`p2` 0.0.1 and
  `compose-preview`/`compose-catalogs` 0.2.0 at project scope. The product
  plugins came from the marketplace's `./plugins/<name>` subdirectory sources.
  No `git-subdir` source type was tested.
- `claude plugin validate` passed for `spike/p1`, `spike/p2`,
  `plugins/compose-preview`, `plugins/compose-catalogs`, and both
  marketplaces, with each plugin directory also holding an Antigravity root
  `plugin.json` and a `.codex-plugin/`. It reported only warnings: missing
  description or author on the fixtures, and an unquoted
  `${CLAUDE_PLUGIN_ROOT}` in the hook commands, including
  `plugins/compose-preview` SessionStart.
- `yschimke/skills` installed as `yschimke-skills` 0.1.5 with 8 skills. Asking to
  render a Compose `@Preview` to PNG loaded `yschimke-skills:compose-preview`.
- With `yschimke-skills` and both wiring plugins enabled, the session listed
  skills `compose-preview:harness-notes`, `compose-catalogs:harness-notes`, and
  `yschimke-skills:*`, plus agents `compose-preview:design-reviewer` and
  `compose-catalogs:design-reviewer`. Every ID was namespaced by plugin, so
  there was no clash. The same reviewer did appear twice under two
  namespaces. The `compose-preview` SessionStart hook returned
  `additionalContext` "Compose Preview needs setup: compose-preview is not
  available on PATH."

### Tools, hooks and identity (Q2, Q3, Q4, Q8)

- The session `init` event listed
  `mcp__plugin_p1_alpha__render_preview` and
  `mcp__plugin_p2_beta__render_preview`, plus the matching `status`, `ask` and
  `access_status` tools. The model called both `render_preview` tools, and each
  returned its own server name.
- PostToolUse ran once per plugin after `Write` and after `Edit`. The log
  recorded `tool_name` `Write` and `Edit`. `MultiEdit` was not exercised.
- With `SPIKE_HOOK_DECISION=block`, each Stop hook returned
  `{"decision":"block","reason":"run spike check"}`. Claude Code fed the reason
  back as a user turn, `Stop hook feedback:\nrun spike check`, and the agent
  continued (it ran both spike skills). `stop_hook_active` was `false` on the
  first Stop and `true` on every later one. After 12 blocked Stop rounds (both
  plugins blocking each time), the host ended the turn with:

  ```text
  A hook blocked the turn from ending 9 consecutive times — overriding and ending turn. For Stop/SubagentStop hooks, check stop_hook_active in the input and return success while it's true. Set CLAUDE_CODE_STOP_HOOK_BLOCK_CAP to raise this limit.
  ```

  The last 9 of those rounds followed the final tool call. This suggests that
  a round with a tool call resets the count, but the probe did not isolate
  that.
- Both echo servers recorded:

  ```json
  "clientInfo": {"name": "claude-code", "title": "Claude Code", "version": "2.1.283",
                 "description": "Anthropic's agentic coding tool", "websiteUrl": "https://claude.com/claude-code"},
  "capabilities": {"elicitation": {}, "roots": {"listChanged": true}},
  "detectionEnvironment": {"CLAUDECODE": "1", "CLAUDE_PLUGIN_ROOT": "<plugin root>"}
  ```

  Compared with the wrapper's own environment, the host added these keys to
  the MCP server process: `CLAUDECODE`, `CLAUDE_PLUGIN_ROOT`,
  `CLAUDE_PLUGIN_DATA`, `CLAUDE_PROJECT_DIR`, `CLAUDE_CODE_SESSION_ID`,
  `CLAUDE_CODE_MESSAGING_SOCKET`, and `CLAUDE_CODE_MESSAGING_TOKEN`. Hook
  processes additionally received `CLAUDE_ENV_FILE`, `CLAUDE_PID`,
  `CLAUDE_CODE_CHILD_SESSION`, and `CLAUDE_CODE_SESSION_ATTENDED`. Only the
  keys are recorded here. Each `CLAUDE_PLUGIN_ROOT` was that plugin's own
  directory.

### Skills, agents and startup (Q6, Q7, Q20, Q21)

- The fixture skills were listed and invoked as `p1:spike` and `p2:spike`,
  namespaced by plugin and skill directory rather than the frontmatter names
  `spike-p1` and `spike-p2`. They returned `SPIKE-P1-LOADED` and
  `SPIKE-P2-LOADED`.
- `rules check` returned `RULES-NONE`. Plugin `rules/AGENTS.md` was not loaded,
  which is expected because it is not a Claude Code plugin component.
- `p1:spike-reviewer` appeared in the session's agent list. Given
  `subagent_type: p1:spike-reviewer` and the prompt "Return your fixture
  verdict.", the subagent returned
  `SPIKE-REVIEWER-LOADED: use the text fallback when no viewer is available.`
- Both SessionStart hooks ran with source `startup` and printed
  `SPIKE-SESSION-START`. Asked for any SessionStart marker in its context, the
  model quoted `SessionStart:startup hook success: SPIKE-SESSION-START`.

### MCP rich features (Q10, Q11, Q16–Q19)

- The fixture's 1×1 PNG did not reach the model. After each `render_preview`
  call the turn logged:

  ```text
  API Error: an image in the conversation could not be processed and was removed. Re-read the file with a different approach if you still need it.
  ```

  The session continued, and the text item and resource link were still
  delivered. With the 64×64 red PNG, the image stayed in the tool result
  without error, and the model described it as "red". It took the size
  "1×1" from the tool description. How the person would see the image in
  the interactive terminal was not observed.
- A temporary plugin with an HTTP server at `http://127.0.0.1:18765/mcp` and
  headers `${SPIKE_HDR_VALUE}`, `${SPIKE_HDR_UNSET:-fallback-used}` and
  `${CLAUDE_PLUGIN_ROOT}` connected. A local echo logged the expanded values
  `probe-value-123`, `fallback-used`, and the plugin directory on every
  request (`server/discover`, `initialize`, `notifications/initialized`,
  `tools/list`).
- `render_preview`'s resource link reached the model as the text item
  `[Resource link: Spike echo viewer] ui://spike/app`. The host called
  `resources/list` at startup but never called `resources/read` for
  `ui://spike/app`, before or after the tool call. Print mode showed no MCP App
  surface. Whether the interactive UI renders the viewer was not run, and no
  viewer action (Q17) could be exercised.
- Claude Code advertised a bare `elicitation: {}` capability with no `url`
  sub-capability. For `ask` in form mode, the fixture therefore sent
  `elicitation/create`. Print mode showed no form, and the tool returned the
  fixture's form text fallback, which requires a non-accept response. URL mode
  was not advertised, so the fixture returned the URL, code and
  `access_status` fallback without sending a request. The interactive
  elicitation UI was not run.
- The host called `prompts/list` on both servers at startup and listed
  `mcp__plugin_p1_alpha__spike-prompt` and
  `mcp__plugin_p2_beta__spike-prompt` among the session's slash commands.
  The model was not told about them, and answered `NONE` when asked. Running
  `claude -p "/mcp__plugin_p1_alpha__spike-prompt Example.kt"` made the
  server receive
  `prompts/get {"name": "spike-prompt", "arguments": {"path": "Example.kt"}}`,
  and the model then tried to call `render_preview`.

## Fixture-only control

`python3 spike/prepare.py && python3 spike/run-protocol-smoke.py` passed on the
same `16ce908` commit. It proves the fixture paths it exercised, not any host
behavior.

## Not run

- Q9, Q12 and Q14 are Antigravity-only.
- Q17 viewer actions, and the interactive rendering of images, MCP Apps and
  elicitation, need the interactive terminal or a Claude app. Print mode does
  not settle them.
- Neither `MultiEdit` nor the Stop `continue` decision was exercised.
