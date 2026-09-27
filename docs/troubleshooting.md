# Troubleshooting

Each entry is a problem we have hit, what causes it, and the fix. In
Antigravity, run `python3 scripts/antigravity-check.py` first: it checks most of
these. In OpenCode, run `python3 scripts/opencode-check.py`.

## `compose-preview: command not found`

- **New install:** the installer adds `~/.local/bin` to your bash, zsh and fish
  startup files. Open a new terminal, or restart the harness so it inherits the
  new `PATH`. With fish, check that `~/.local/bin` is in `fish_user_paths`.
- **Worked before, then stopped:** `~/.local/bin/compose-preview` may be a
  broken link. An older `npx skills add`/`update` wiped the CLI it pointed at
  (fixed in yschimke/skills#101). Reinstall the CLI only:

  ```sh
  curl -fsSL https://raw.githubusercontent.com/yschimke/skills/main/scripts/install.sh | bash -s -- --cli-only
  ```

## Two `compose-preview` servers in Antigravity

`compose-preview mcp install` also writes a global `compose-preview-mcp` entry
to `~/.gemini/antigravity/mcp_config.json` (or `~/.gemini/config/mcp_config.json`)
that duplicates the plugin's server. Delete any `compose-preview*` entry from
`mcpServers` in that file and restart Antigravity. Tracked in
yschimke/compose-ai-tools#5584.

## Stale `mcp serve` processes

After a CLI update, servers from the old version can keep running and answer
instead of the new one. List them and kill the old ones, then restart the
harness:

```sh
ps -axo pid=,command= | grep 'compose-preview.*mcp serve'
```

## Antigravity card says "bridge unavailable"

The card came from an old plugin that expected an MCP Apps bridge, which
Antigravity does not have. Antigravity copies plugins at install time, so
`git pull` alone does not update them. Reinstall:

```sh
agy plugin install ./plugins/compose-preview
agy plugin install ./plugins/compose-catalogs
```

## The render does not show my edit

Needs the next compose-preview-server release after 3.78.0, which re-renders
after the edit notification without a Gradle build (plugin side: #49). Update with
`compose-preview update`. Don't run Gradle yourself, and don't ask the agent to;
that only slows the loop. If renders still look out of date, clear the server
cache and restart the harness:

```sh
rm -rf ~/.cache/composeai/preview-mcp
```

This step is needed until yschimke/compose-ai-tools#5602 ships.

## The agent greps and reads docs before rendering

A routine "render the `<PreviewName>`" should be one `render_preview` call and
a short reply. If the agent registers projects, greps for the preview or reads
skills first, the plugin or server is old. Run `compose-preview update`, update
the plugin (reinstall in Antigravity), and start a new session.

## OpenCode config was not updated

`compose-preview mcp install --opencode` never rewrites a `.jsonc` file or a
file with comments. It prints the snippet and the file it belongs in instead;
paste it in by hand. See [OpenCode](opencode.md#let-the-cli-write-the-local-server).

## Codex hooks are marked untrusted

Codex registers the plugin's SessionStart and Stop hooks as `untrusted` until
you approve them. Approve them when Codex asks, or from `/plugins`. The Stop
gate stays off unless `COMPOSE_PREVIEW_GATE=1` is set.

## "Semantics unavailable" or pixel-only checks

The agent reports that `compose/semantics` is not available on the local
daemon and checks layout from the bitmap instead. This costs more tokens, and
`crop` by `testTag` and `diff_semantics` stop working. Tracked in
yschimke/compose-preview-server#1166; no workaround yet.
