# Compose Preview

Iterate on local Jetpack Compose `@Preview` functions with live rendering and
accessibility checks. The plugin connects your agent to the `compose-preview`
command-line tool, which renders previews from your own Gradle project on your
machine.

This folder is generated from
[`yschimke/compose-agent-plugins`](https://github.com/yschimke/compose-agent-plugins);
see that repository's README for install steps in each harness.

## Requirements

Java 17, a Gradle project with `@Preview` functions, and the `compose-preview`
CLI on `PATH`. Install the CLI with the script in
[`yschimke/skills`](https://github.com/yschimke/skills). The plugin does not
download or install it.

## What it contains and runs

- An MCP server entry, `compose-preview-mcp`, that starts
  `compose-preview mcp serve` from your `PATH` over stdio. It builds and renders
  your project locally with Gradle.
- A `SessionStart` hook, `scripts/session-start-summary.sh`, that asks the
  `compose-preview` CLI for its status and reports only fixed status words and
  counts.
- A `Stop` hook, `scripts/stop-gate.sh`, that does nothing unless you set
  `COMPOSE_PREVIEW_GATE=1`. When enabled, it runs `git`, `compose-preview show`
  and `compose-preview a11y` on previews in changed Kotlin files, and keeps the
  agent working only when one fails to render or has accessibility errors.
- The `harness-notes` and `antigravity-viewer-card` skills, the read-only
  `design-reviewer` agent, and the preview viewer bundle in `assets/`. The
  viewer is the unmodified `compose-preview-viewer.html` from a
  compose-preview-server release; its provenance file pins the tag and SHA-256.

## Data it sends

The plugin itself sends nothing over the network. Rendering runs on your
machine. Gradle may download your project's own dependencies, as any build of
that project would.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
