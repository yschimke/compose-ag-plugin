# Compose Catalogs

Discover Jetpack Compose components, inspect their properties, and render
catalog variants. The plugin connects your agent to the hosted Compose Preview
MCP service, which serves the Material 3 and Wear OS component catalogs and the
UI Builder design tools. It needs no local toolchain.

This folder is generated from
[`yschimke/compose-agent-plugins`](https://github.com/yschimke/compose-agent-plugins);
see that repository's README for install steps in each harness.

## What it contains

- An MCP server entry, `compose-preview-catalog`, for the remote server at
  `https://preview.coo.ee/mcp` (Streamable HTTP).
- The registered Compose Preview app for Codex and ChatGPT. Its in-chat viewer
  shows preview-server renders and review controls; the full UI Builder remains
  the separate editor linked from that viewer.
- The `harness-notes` skill, which summarizes the
  [agent rules](https://github.com/yschimke/compose-agent-plugins/blob/main/docs/agent-rules.md)
  for the active harness.
- No agents. The read-only `design-reviewer` agent ships in `compose-preview`
  and uses this plugin's tools when both are installed.

It has no hooks and runs no local programs.

## Data it sends

Every catalog, render and UI Builder tool call goes to `preview.coo.ee`, which
the plugin author operates. A call carries the tool arguments: component and
preview names, device settings, and any design document or comment text you ask
the agent to create or change there. Nothing is sent until the agent calls one
of those tools.

The optional **Compose Preview token** is sent as the `X-Compose-Preview-Token`
header. In Claude Code you enter it when you enable the plugin; it is stored in
the system credential store. Leave it blank to use the service's interactive
access grant instead.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
