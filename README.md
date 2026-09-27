# Compose Antigravity Plugins

This repository packages the MCP and harness wiring for Compose tooling in
Antigravity, Claude Code, and Codex. The Compose agent skills remain canonical
in [`yschimke/skills`](https://github.com/yschimke/skills); this repository does
not copy or fork them. The generated manifests make the same plugin directories
usable by all three harnesses. Edit [`src/plugins.json`](src/plugins.json) and
run `python3 scripts/generate.py` rather than editing a manifest directly.

## Plugins

`compose-catalogs` connects agents to remote discovery and rendering of Compose
Material 3 and Wear components, plus semantic UI-builder authoring and Kotlin
export. It has no local toolchain prerequisite because it connects to the
hosted preview MCP service. Access uses `COMPOSE_PREVIEW_TOKEN` or the service's
interactive grant flow.

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

To check an Antigravity install (plugin copies, card helper, CLI `inline=false`
support, duplicate global MCP entries), run `python3 scripts/antigravity-check.py`.

Every plugin follows the [agent rules](docs/agent-rules.md): the agent sees what the user sees, edits through typed tools with schemas, edits a design at its one canonical home, and keeps discussion there.

See the [harness compatibility matrix](docs/harness-matrix.md) for the verified installation and runtime behaviour of each harness.

## Install

```sh
# Antigravity
# Install the canonical skills as a plugin from a clone of yschimke/skills
# (its root plugin.json). To be verified; see the note below.
git clone https://github.com/yschimke/skills
agy plugin install ./skills
# Clone this repository, then install either local plugin directory.
agy plugin install ./plugins/compose-catalogs
agy plugin install ./plugins/compose-preview
agy plugin enable compose-preview

# Claude Code
/plugin marketplace add yschimke/skills
/plugin install yschimke-skills@yschimke-skills
/plugin marketplace add yschimke/compose-ag-plugin
/plugin install compose-catalogs@compose-ag-plugin
/plugin install compose-preview@compose-ag-plugin

# Codex
codex plugin marketplace add yschimke/skills
codex plugin marketplace add yschimke/compose-ag-plugin
# Then enable yschimke-skills, compose-catalogs, and compose-preview from /plugins.
```

In Antigravity, install the canonical skills from `yschimke/skills` as an
Antigravity plugin through that repository's root `plugin.json`
(`agy plugin install <clone of yschimke/skills>`); this route is to be
verified. Do not use the Skills CLI there: Antigravity 1.2.12 did not load
skills that `npx skills add … --agent antigravity` installed to
`~/.agents/skills` (issue #6 Q14). Installing the wiring plugin does not
install the canonical skills.
For OpenCode MCP configuration, skill installation, and authentication, see
[OpenCode](docs/opencode.md).

The [agent rule evals](evals/agent-rules.md) and the other cross-harness prompts that verify the upstream skills together with this
wiring live in [`evals/`](evals/README.md).

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

Claude Code and Codex each get their own generated hook manifest, whose
commands pass `--harness=claude` or `--harness=codex`. Both harnesses use the
`{"decision":"block","reason":…}` response. The script can also emit
Antigravity's `{"decision":"continue","reason":…}`, but no Antigravity hook is
generated yet. In Antigravity 1.2.12, #6 Q4 showed that `continue` keeps the
agent working with no observed cap, and its Stop payload has neither
`stop_hook_active` nor a re-entry counter, so an Antigravity gate needs its
own per-`conversationId` loop state first.

## Development

Run the repository gate before sending a change:

```sh
scripts/check-plugins.sh
```
