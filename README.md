# Compose Antigravity Plugins

Compose `@Preview` rendering, accessibility checks and remote component
catalogs for Antigravity, Claude Code, Codex and OpenCode. This repository
holds only the MCP and harness wiring; the Compose skills stay canonical in
[`yschimke/skills`](https://github.com/yschimke/skills).

Something not working? See [Troubleshooting](docs/troubleshooting.md).
What works where: [status for launch](docs/harness-matrix.md#status-for-launch).

## Quick start

Local rendering (`compose-preview`) needs Java 17, a Gradle project with
`@Preview`s, and the `compose-preview` CLI on `PATH`:

```sh
curl -fsSL https://raw.githubusercontent.com/yschimke/skills/main/scripts/install.sh | bash -s -- --cli-only
compose-preview --version   # open a new terminal first if this is not found
```

`compose-catalogs` (hosted Material 3 and Wear catalogs, UI Builder) needs no
local toolchain. Then pick your harness. In every harness, open your Compose
project and try: **"render the `ListScreenPreview`"** (use one of your own
preview function names).

### Antigravity

```sh
# From one parent folder (e.g. ~/workspace), so both clones sit side by side.
git clone https://github.com/yschimke/skills
git clone https://github.com/yschimke/compose-ag-plugin
agy plugin install ./skills
agy plugin install ./compose-ag-plugin/plugins/compose-preview
agy plugin enable compose-preview
# Optional: hosted Material 3 / Wear catalogs and UI Builder.
agy plugin install ./compose-ag-plugin/plugins/compose-catalogs
# Verify
python3 compose-ag-plugin/scripts/antigravity-check.py
```

Install skills from the `yschimke/skills` clone (its root `plugin.json`; this
route is still being verified), not with `npx skills add … --agent antigravity`:
Antigravity 1.2.12 does not load `~/.agents/skills` (issue #6 Q14). The wiring
plugins do not install the canonical skills.

### Claude Code

```text
/plugin marketplace add yschimke/skills
/plugin install yschimke-skills@yschimke-skills
/plugin marketplace add yschimke/compose-ag-plugin
/plugin install compose-preview@compose-ag-plugin
/plugin install compose-catalogs@compose-ag-plugin
```

Verify: restart, then `/mcp` lists `plugin:compose-preview:compose-preview-mcp`
as connected. Enabling `compose-catalogs` asks for an optional Compose Preview
token; Claude Code does not read `COMPOSE_PREVIEW_TOKEN` from the environment.

### Codex

```sh
codex plugin marketplace add yschimke/skills
codex plugin marketplace add yschimke/compose-ag-plugin
# Then enable yschimke-skills, compose-preview and compose-catalogs from /plugins.
```

Verify: `codex mcp list` shows `compose-preview-mcp` and
`compose-preview-catalog`. Approve the plugin hooks when Codex marks them
untrusted.

### OpenCode

OpenCode has no plugin marketplace; install the skills and register the server:

```sh
npx skills add yschimke/skills --global --yes --skill compose-preview --skill compose-ui-builder
compose-preview mcp install --opencode
# Verify
python3 scripts/opencode-check.py   # from a clone of this repository
```

See [OpenCode](docs/opencode.md) for the catalog server and authentication.

## Updating

```sh
compose-preview update   # CLI (and PATH)
npx skills update        # skills installed with npx
```

- Claude Code and Codex: update the marketplaces and plugins from `/plugin`
  or `/plugins`.
- Antigravity copies plugins at install time. From the same parent folder, run
  `git -C skills pull && git -C compose-ag-plugin pull`, then run the
  `agy plugin install` lines again.
- If renders look out of date after an update, clear the server cache
  (`rm -rf ~/.cache/composeai/preview-mcp`) and restart the harness. This is
  needed until yschimke/compose-ai-tools#5602 ships.

## Plugins

`compose-catalogs` connects agents to remote discovery and rendering of Compose
Material 3 and Wear components, plus semantic UI-builder authoring and Kotlin
export. It has no local toolchain prerequisite because it connects to the
hosted preview MCP service. Access uses an optional token (`COMPOSE_PREVIEW_TOKEN`,
or the plugin's token setting in Claude Code) or the service's interactive grant
flow.

`compose-preview` supplies the local `compose-preview mcp serve` connection for
iterative Compose rendering and accessibility checks. It requires Java 17,
Gradle, and the `compose-preview` CLI on the workstation. It also ships an
opt-in [Stop gate](#compose-preview-stop-gate). The rendering workflow itself
comes from the canonical `compose-preview` skill in `yschimke/skills`.

Both wiring plugins include the same generated `harness-notes` micro-skill. It
summarizes R1–R4 for the active harness and points back to the full contract; it
does not duplicate the canonical Compose workflows. Edit its single source at
[`src/skills/harness-notes/SKILL.md`](src/skills/harness-notes/SKILL.md), then
run the generator.

`compose-preview` additionally carries the Antigravity-only viewer-card
micro-skill. Keeping that instruction out of `compose-catalogs` avoids
advertising a local artifact that the remote-catalog plugin does not package.

Both plugins also ship the shared, read-only `design-reviewer` agent for Claude
Code and Antigravity. It performs semantic, accessibility, font-scale, and
device checks in its own context, then returns a short verdict with viewer or
artifact links so rendered image payloads do not consume the main conversation.
Antigravity 1.2.12 discovered and ran a plugin fixture agent (issue #6 Q20);
Codex support remains unverified.

`compose-preview` also ships the portable viewer bundle at
`assets/compose-preview-viewer.html`, the unmodified `compose-preview-viewer.html`
asset from the compose-preview-server v3.77.0 release; the adjacent provenance
file pins that release tag, its source commit, the SHA-256, and the stable MCP
Apps UI protocol revision. Antigravity renders `<agent-embed>` cards as
`iframe srcdoc`, which drops the URL fragment the viewer reads (issue #6 Q9), so
`assets/compose-preview-card.py` appends the result to a copy of the viewer as
an inline `<script type="application/json" id="compose-preview-result">` block
instead. It reads the PNG from the `pngPath` that `render_preview` returns with
`inline=false`, so the agent never prints base64. The `antigravity-viewer-card`
skill runs it; `assets/compose-preview-viewer-fallback.md` has the contract and
the text fallback.

Every plugin follows the [agent rules](docs/agent-rules.md): the agent sees what the user sees, edits through typed tools with schemas, edits a design at its one canonical home, and keeps discussion there.

The generated manifests make the same plugin directories usable by every
harness. The generator also writes each plugin's `README.md` and `LICENSE`, the
Cursor manifests, the root `gemini-extension.json`, and the MCP Registry
`server.json`; see [Distribution](docs/distribution.md) for the listings they
serve. Edit [`src/plugins.json`](src/plugins.json) and run
`python3 scripts/generate.py`; never edit a manifest directly.

The [agent rule evals](evals/agent-rules.md) and the other cross-harness
prompts that verify the upstream skills together with this wiring live in
[`evals/`](evals/README.md).

## Compose Preview Stop gate

The `compose-preview` plugin's Stop hook does nothing unless
`COMPOSE_PREVIEW_GATE=1` is set in the environment the harness starts hooks
with. When it is set, the hook looks at previews declared in `*.kt` files that
differ from `HEAD` or are untracked. It runs `compose-preview show --json` and
`compose-preview a11y --json --fail-on errors`. It keeps the agent working
only when one of those previews:

- fails to render; or
- has accessibility errors. Warnings do not count.

It never blocks on image, hash or pixel changes, because a migration is
expected to change pixels (#10).

The gate lets the agent stop in these cases:

- a Stop hook already continued this turn (`stop_hook_active`);
- two turns in a row were already blocked in this session;
- `compose-preview`, `git` or `python3` is missing;
- the CLI fails, times out, or prints output the gate cannot parse.

Each CLI call is bounded by `COMPOSE_PREVIEW_GATE_TIMEOUT` seconds (default
150). A Gradle build that fails before it reports any previews counts as a tool
error, not a render failure.

When `ui-builder/designs/index.json` exists, the gate also asks
`compose-preview design status` about unacknowledged design comments (R4) and
unsaved temporary copies (R3). It reports them to the person but never blocks
because of them.

Each harness gets its own generated hook manifest, and every command passes
its harness explicitly:

- Claude Code (`hooks/hooks.json`, `--harness=claude`) and Codex
  (`hooks/codex-hooks.json`, `--harness=codex`) use the
  `{"decision":"block","reason":…}` response.
- Antigravity (the root `hooks.json`, `--harness=antigravity`) uses
  `{"decision":"continue","reason":…}`. It has no SessionStart event, so it
  gets only the Stop gate, run from the installed copy under
  `~/.gemini/config/plugins/compose-preview`. Its Stop payload has no
  `stop_hook_active` and #6 Q4 observed no host cap, so the two-turn cap,
  keyed by `conversationId`, is the only loop guard. The gate finds the
  checkout from the first `workspacePaths` entry. Antigravity has no
  non-blocking Stop message, so the design reminder is not shown there. A live
  Antigravity block has not been recorded yet (#39).

## Development

Run the repository gate before sending a change:

```sh
scripts/check-plugins.sh
```

Other scripts:

- `python3 scripts/antigravity-check.py`: plugin copies, card helper, CLI
  `inline=false` support, duplicate global MCP entries, stale servers.
- `python3 scripts/opencode-check.py [--run --project …]`: skills, MCP config,
  `opencode mcp list`, and optionally one timed model turn.
- `python3 scripts/edit-render-bench.py --help`: time the edit → notify →
  render loop against the local server without a model.
