# Antigravity harness evidence

This record preserves the observed Antigravity portion of the issue #6 and
issue #18 compatibility investigation. The repository owner ran every step by
hand and reported the results; nothing here was inferred from documentation or
from another harness. Host behavior is kept separate from the direct JSON-RPC
fixture smoke test.

## Environment

- Date: 2026-09-27
- Host: macOS
- Antigravity: `agy` CLI 1.2.12
- Model: Gemini 3.8 Flash High
- The Homebrew `agy` shim was initially broken: it pointed at a missing app
  binary. The owner fixed it before the runs below.
- Plugin install location: `~/.gemini/config/plugins/<name>`. Installed
  plugins are copied there.
- Artifact and session folder: `~/.gemini/antigravity/brain/<conversation-id>/`

Run metadata required by `evals/README.md`:

- Canonical-skills commit: n/a. The fixture probes used only the fixture skills;
  Q14 used the Skills CLI's `compose-preview` from `yschimke/skills` (skills
  CLI 1.7.0), which was not loaded.
- Plugin repository commit and server commit: not recorded.
- Tool sequence: not recorded as one ordered run. The fixture probes covered
  plugin install, `rules check`, `spike check`, `call_mcp_tool`
  `render_preview`, `ask` in form and URL modes, file edits with
  `write_to_file` and `replace_file_content`, the spike-reviewer subagent,
  and Stop.
- Images: the fixture's 1×1 PNG, plus real renders from the product plugins.
- Follow-up: issues #6 and #18; yschimke/compose-preview-server#1160; #35.

## Commands

Fixture control and installation:

```sh
python3 spike/prepare.py && python3 spike/run-protocol-smoke.py   # passed
agy plugin install ./spike/p1
agy plugin install ./spike/p2
agy plugin enable p1
agy plugin enable p2
agy plugin validate ./spike/p1
```

Canonical skills through the Skills CLI (Q14):

```sh
npx skills add yschimke/skills --skill compose-preview --agent antigravity --global --yes
```

Product plugins, from a checkout of this repository:

```sh
agy plugin install ./plugins/compose-catalogs
agy plugin install ./plugins/compose-preview
```

Prompts used in the Antigravity session included `rules check`,
`spike check`, and `Use the spike-reviewer agent from p1`.

## Observations

### Installation and manifests (Q1, Q5, Q14)

- `agy plugin install ./spike/p1` and `./spike/p2` installed from a local path.
  The output listed the skills, agents, commands, `mcpServers` and hooks it
  processed. `agy plugin enable p1` and `agy plugin enable p2` printed nothing,
  which is fine. The git URL form was not tried.
- `agy plugin validate ./spike/p1` reported no complaints while the plugin
  directory also held `.claude-plugin/` and `.codex-plugin/`.
- `npx skills add yschimke/skills --skill compose-preview --agent antigravity
  --global --yes` (skills 1.7.0) installed to `~/.agents/skills/compose-preview`.
  Antigravity 1.2.12 did not load it. A new session listed only these skills:
  `agy-customizations`, `android-cli`, `antigravity-guide`, `generative_ui`,
  `migrate-workflows`, `spike-p1` and `spike-p2`.
  `~/.gemini/antigravity/skills` exists, but a copy there was not tested.
- skills.sh flagged `compose-preview` as "Gen High Risk / Socket 1 alert / Snyk
  Med Risk". This is recorded as a note only.

### Tools, hooks and identity (Q2, Q3, Q4, Q8)

- There was no clash between the two fixture servers. Antigravity namespaces
  servers as `<plugin>_<server>` (`p1_alpha`, `p2_beta`), and the model calls
  tools through a generic `call_mcp_tool(ServerName=…, ToolName=…)`. The
  product plugins followed the same pattern:
  `compose-catalogs_compose-preview-catalog`, and
  `compose-preview-mcp/render_preview` shown in the UI.
- post-tool-use hooks fired. The file-edit tool names were `write_to_file` and
  `replace_file_content`, inside a `toolCall` object. Payload keys:
  `artifactDirectoryPath`, `conversationId`, `error`, `modelName`, `stepIdx`,
  `toolCall`, `transcriptPath`, `workspacePaths`.
- A Stop hook returning `{"decision":"continue","reason":…}` kept the agent
  going. The UI showed `Stop hook blocked termination: run spike check`.
  No built-in cap was observed: about 30 Stop events were logged, the agent
  kept re-running, and it then started grepping the home directory for
  `SPIKE_HOOK_DECISION` until the owner stopped it.
- Stop payload keys: `artifactDirectoryPath`, `conversationId`, `error`,
  `executionNum`, `fullyIdle`, `modelName`, `terminationReason`,
  `transcriptPath`, `workspacePaths`. There is no `stop_hook_active`.
  `executionNum` was 0 in almost every event (once 1), so it is not a re-entry
  counter. `terminationReason` was `NO_TOOL_CALL` or `ERROR`, and `fullyIdle`
  was mostly `true`. An Antigravity Stop gate therefore needs its own
  per-`conversationId` loop state.
- The MCP servers recorded:

  ```json
  "clientInfo": {"name": "antigravity-client", "version": "v1.0.0"}
  ```

  The hook environment included these keys (values not recorded):
  `__CFBundleIdentifier`, `ANTIGRAVITY_CONVERSATION_ID`,
  `AGY_BROWSER_ACTIVE_PORT_FILE`, `AGY_BROWSER_WS_URL`, and
  `CHROME_DEVTOOLS_MCP_JS`. The MCP server environment capture was empty, so
  it is not recorded.

### Skills, agents and startup (Q6, Q7, Q20, Q21)

- `rules check` returned `RULES-P1-LOADED RULES-P2-LOADED`. Plugin
  `rules/AGENTS.md` is loaded; Claude Code does not do this.
- `spike check` returned `SPIKE-P1-LOADED SPIKE-P2-LOADED`. Skills also appear
  as slash commands under their frontmatter names, `/spike-p1` and
  `/spike-p2`. Claude Code uses `<plugin>:<skill directory>` names instead.
- Plugin `agents/` are discovered. `Use the spike-reviewer agent from p1` ran a
  subagent that returned
  `SPIKE-REVIEWER-LOADED: use the text fallback when no viewer is available.`
- No SessionStart-equivalent hook event fired. Only Stop and post-tool-use
  events were logged.

### Generative UI and MCP rich features (Q9, Q10, Q16–Q19)

- `<agent-embed>` renders the HTML file's content as an `iframe srcdoc`. In a
  probe card, `location.href` was `about:srcdoc`; `hash` and `search` were
  empty for `#a=1`, `?a=1` and a plain URL; `protocol` was `about:`; and
  `window.parent !== window`. Scripts run. `data:` images render. `https:`
  images load (a gstatic PNG showed `LOADED`). `file:///` and relative images
  do not render. There is no MCP Apps bridge.
- The MCP `ImageContent` from `render_preview` is shown to the person (the
  fixture's 1×1 red pixel scaled up; real renders show normally) and reaches
  the model. Antigravity saved it as `media_0.png`, and the model described a
  Wear `ListScreenPreview` correctly.
- The MCP App viewer resource was not rendered: the tool result showed the
  image plus text only. Q17 viewer actions are therefore n/a.
- Neither form nor URL elicitation is supported. Both returned the fixture's
  text fallback: `form elicitation unavailable; choose a variant in text…`,
  and the URL variant with its link, code and `access_status` instruction.
- MCP prompts are listed as slash commands `mcp:p1_alpha:spike-prompt` and
  `mcp:p2_beta:spike-prompt`. Invoking one was not tested.

## Product plugins

- `compose-catalogs` installed with 1 skill, 1 agent, 1 MCP server and no
  hooks. It listed 38 remote catalogs and rendered an M3 Button. The image
  arrived inline as base64. To show it, the agent dug the base64 out of its
  `brain/` session files and re-typed it in a shell heredoc to write a PNG,
  which was costly. This is tracked in yschimke/compose-preview-server#1160
  (signed `https` image URL).
- `compose-preview` installed with 2 skills, 1 agent, 1 MCP server and no hooks,
  because the Stop gate is not generated for Antigravity. With a Wear
  ComposeStarter project, registration worked, 17 previews were discovered
  (the `WearPreviewDevices` × `WearPreviewFontScales` expansion), and
  `render_preview` worked.
- The old `antigravity-viewer-card` skill made the agent very chatty: it
  grepped session logs, printed the whole PNG as a base64 fragment at about
  one line per second for minutes, and printed the `<agent-embed>` tag as a
  code block that never rendered. #35 fixes that. The text fallback was
  complete, including the source path and line.

## Fixture-only control

The fixtures were prepared with `python3 spike/prepare.py`, and
`python3 spike/run-protocol-smoke.py` passed. It proves the fixture paths it exercised, not any
host behavior.

## Not run

- Q11 (environment expansion in remote headers) and Q12 (Skiko/Wasm under the
  Generative UI CSP).
- Q15 (canonical skills and wiring plugins together).
- Q17, because no viewer rendered.
- Installing from a git URL, invoking an MCP prompt, and copying the canonical
  skills into `~/.gemini/antigravity/skills`.
