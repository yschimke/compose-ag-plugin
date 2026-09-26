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
Gradle, and the `compose-preview` CLI on the workstation. Its opt-in Stop gate
remains gated by issue #6. The rendering workflow itself comes from the
canonical `compose-preview` skill in `yschimke/skills`.

Both wiring plugins include the same generated `harness-notes` micro-skill. It
summarizes R1–R4 for the active harness and points back to the full contract; it
does not duplicate the canonical Compose workflows. Edit its single source at
[`src/skills/harness-notes/SKILL.md`](src/skills/harness-notes/SKILL.md), then
run the generator.

Every plugin follows the [agent rules](docs/agent-rules.md): the agent sees what the user sees, edits through typed tools with schemas, edits a design at its one canonical home, and keeps discussion there.

See the [harness compatibility matrix](docs/harness-matrix.md) for the verified installation and runtime behaviour of each harness.

## Install

```sh
# Antigravity
# Install the canonical skills. Harness discovery is still being verified in #6.
npx skills add yschimke/skills --skill compose-preview \
  --skill compose-ui-builder --agent antigravity --global --yes
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

Antigravity discovery of the Skills CLI's installed files is still being
verified in issue #6; do not assume that installing the wiring plugin also
installs the canonical skills.
For OpenCode MCP configuration, skill installation, and authentication, see
[OpenCode](docs/opencode.md).

The [agent rule evals](evals/agent-rules.md) and the other cross-harness prompts that verify the upstream skills together with this
wiring live in [`evals/`](evals/README.md).

## Development

Run the repository gate before sending a change:

```sh
scripts/check-plugins.sh
```
