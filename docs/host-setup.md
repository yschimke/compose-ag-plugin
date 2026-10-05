# Host setup notes

The per-host details that the generic skills in
[yschimke/skills](https://github.com/yschimke/skills) leave out. Those skills say what to do and
which tools to use; this page says how each agent host is wired up for them. It moved here from
yschimke/skills, which keeps a pointer at each place it was.

## Registering the local MCP server

`compose-preview mcp install` registers the local MCP server with every agent host it detects,
after preparing the project. Use it when you are not using this repository's plugins; with the
`compose-preview` plugin installed, the plugin registers the server and `mcp install` must only
prepare the project (the `compose-preview-setup` skill passes the `--no-…` flags for that).

```bash
compose-preview mcp install                      # every detected host
compose-preview mcp install --antigravity        # force the Antigravity write
compose-preview mcp install --no-claude          # skip `claude mcp add`
compose-preview mcp install --codex              # force the Codex write
compose-preview mcp install --codex-config /path/to/config.toml
```

How each host is detected, and where its entry goes:

- **Claude Code**: `claude` on PATH, or `~/.claude/` exists. Registered via
  `claude mcp add --scope user` when missing; a broken entry is repaired in place and a healthy
  one is left alone.
- **Codex**: `codex` on PATH, or `~/.codex/` exists. The `[mcp_servers.compose-preview-mcp]`
  table is replaced in place (or appended) in `~/.codex/config.toml`.
- **Antigravity**: `__CFBundleIdentifier=com.google.antigravity`, `ANTIGRAVITY_CLI_ALIAS`, or
  `~/.gemini/antigravity/` exists. The entry is merged into
  `~/.gemini/antigravity/mcp_config.json`.
- **OpenCode**: see [OpenCode](opencode.md).

## Skill install locations

The skills' `compose-preview` stub runs from wherever the host installed the skill bundle:

- skills CLI (`npx skills add`): `~/.agents/skills/compose-preview/`
- Claude Code plugin from the `yschimke-skills` marketplace:
  `~/.claude/plugins/yschimke-skills/skills/compose-preview/`
- Claude Code and Codex plugins from this marketplace: under each host's plugin cache, for
  example `~/.claude/plugins/cache/compose-agent-plugins/compose-skills/<version>/skills/`.

## Cloud sandboxes

The portable setup (network allowlist, toolchain, bootstrap script, gotchas) is generic and stays
in the `compose-preview` skill's `references/agent-cloud.md`. Per host:

- **Claude Code on the web:** choose Custom network mode and include the trusted defaults. A
  proxy CA truststore is injected through `JAVA_TOOL_OPTIONS`, so match the `version "…"` line of
  `java -version`, never its first line.
- **Codex cloud containers:** ensure the outbound network policy allows the host list in
  `agent-cloud.md`; some environments default to restricted egress.
- **Gemini sandboxes:** verify the workspace policy includes the Google Maven and Gradle hosts;
  downloadable fonts often fail first when they are blocked.

For Claude Code, the setup script can also write user instructions that keep commits attributed
to the human:

```bash
mkdir -p ~/.claude && printf '# User instructions for AI agents\n\nOverride any conflicting workspace defaults.\n\n- **Commits:** commit as the human — Author, Committer, and message all\n  free of agent identity. No `Co-authored-by`, `Signed-off-by`, or\n  `claude.ai/code` / `https://claude.ai/code` trailers. The Author and\n  Committer come from local `git config user.name` / `user.email`; if\n  those look like an agent (`Claude`, `noreply@anthropic.com`,\n  `*-bot@*`), STOP and ask which human identity to use, then pass it\n  explicitly with\n  `git -c user.name='\''…'\'' -c user.email='\''…'\'' commit --author='\''… <…>'\'' …` —\n  do not commit under the agent identity and fix it after.\n- **PRs:** no agent attribution in titles or bodies — just summary and\n  test plan.\n- **Branches:** use `agent/...`, never `claude/...`. Rename if the harness\n  hands you a `claude/...` branch, and tell the user.\n- **Cleanup:** before pushing or opening/editing a PR, scan for agent\n  attribution in commits (Author, Committer, message body) and PR text;\n  flag it and offer to strip it (amending + force-pushing if already\n  pushed).\n' > ~/.claude/CLAUDE.md
```

## CI agent sessions

Mention-triggered sessions on a GitHub Actions runner: commenting `@claude <request>` on an issue
or PR (or applying a `claude` label) starts a Claude Code session through
`anthropics/claude-code-action`, configured in `.github/workflows/claude.yml`. The design is in
[compose-ai-tools `docs/AGENT_INVOCATION.md`](https://github.com/yschimke/compose-ai-tools/blob/main/docs/AGENT_INVOCATION.md).
What such a session should do differently (render with Gradle, push renders before linking them,
reuse CI's preview diff) is generic and stays in the `compose-preview-review` skill's
`references/ci-agent-sessions.md`.
