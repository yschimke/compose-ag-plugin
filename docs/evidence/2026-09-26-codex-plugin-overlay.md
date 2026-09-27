# Codex compatibility-overlay evidence

This record captures the isolated Codex CLI probe for the compatibility
manifest and package-relative MCP path change. It does not promote unexercised
viewer, elicitation, prompt, or packaged-agent behavior to a pass.

## Environment

- Date: 2026-09-26
- Codex CLI: 0.151.0
- Plugin commit: `dec6a634ab7279f3f22e6d472a48605efadeaaae`
- Mode: ephemeral `codex exec` with an isolated temporary `CODEX_HOME`
- Marketplace: local `spike/` marketplace; cached `p1` and `p2` version 0.0.1
- Canonical-skills commit: n/a; fixture skills only
- Server commit: fixture echo server at plugin commit `dec6a63`
- Image count: 1 returned by `beta/render_preview`
- Follow-up: issues #6 and #18

The temporary home copied only the existing Codex authentication file. Adding
the marketplace and plugins did not modify the user's normal configuration.

## Observations

- Both plugins installed and enabled with their `.codex-plugin/plugin.json`
  overlays. `codex mcp list` resolved each `cwd: "."` to its own cached plugin
  root and listed `alpha` and `beta` as enabled.
- Both SessionStart hooks ran. The probe did not ask the model to repeat their
  shared marker, so it adds no new marker-delivery claim.
- Both echo servers initialized. Their records contained
  `clientInfo.name = codex-mcp-client`, title `Codex`, version `0.151.0`, and
  the environment keys visible to the server.
- Tool sequence: `alpha/status`, then `beta/render_preview`, followed by both
  Stop hooks.
- The first read-only invocation reached both tools but Codex denied the calls
  because its approval policy was `never`. This established exposure only.
  A fresh `--approve-for-me` invocation completed both calls.
- `alpha/status` returned `status from alpha`.
- `beta/render_preview` returned its text fallback, one PNG image item, and one
  `ui://spike/app` resource link. The model reported all three result types.
- The noninteractive terminal did not open an MCP App surface for the person.
  No viewer action, elicitation request, prompt picker, or packaged reviewer was
  exercised in this probe.

This upgrades the prior “MCP server not exposed” observation for Codex CLI on
the tested package revision. It does not establish another harness or satisfy
the two-harness acceptance requirement.
