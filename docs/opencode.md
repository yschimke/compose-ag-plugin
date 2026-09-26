# OpenCode

OpenCode does not use this repository's plugin manifests or marketplace.
Configure its MCP servers directly and install the canonical skills from
`yschimke/skills`.

This guide uses the current OpenCode v2 configuration shape: server definitions live under `mcp.servers`, and `disabled` (rather than `enabled`) controls whether a configured server connects. See the [OpenCode MCP documentation](https://opencode.ai/v2/docs/mcp-servers) for the current contract.

## MCP servers

Create `opencode.jsonc` in the Compose project (or `.opencode/opencode.jsonc`), or add the same object to `~/.config/opencode/opencode.jsonc` for every project. The local `compose-preview-mcp` server requires Java 17, Gradle, and the `compose-preview` CLI on `PATH`.

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "servers": {
      "compose-preview-mcp": {
        "type": "local",
        "command": ["compose-preview", "mcp", "serve"],
        "codemode": false
      },
      "compose-preview-catalog": {
        "type": "remote",
        "url": "https://preview.coo.ee/mcp",
        "headers": {
          "X-Compose-Preview-Token": "{env:COMPOSE_PREVIEW_TOKEN}"
        },
        "codemode": false
      }
    }
  }
}
```

`codemode: false` exposes the individual tools directly. OpenCode prefixes them with the server name, so the two `render_preview` tools are distinct: `compose-preview-mcp_render_preview` and `compose-preview-catalog_render_preview`. Omit `codemode: false` if you prefer OpenCode's default Code Mode grouping.

Check the connections after restarting OpenCode:

```sh
opencode mcp list
```

## Skills

Install the canonical Compose skills through the Skills CLI:

```sh
npx skills add yschimke/skills \
  --skill compose-preview \
  --skill compose-ui-builder \
  --agent opencode \
  --global \
  --yes
```

This repository deliberately carries no copies of `compose-preview` or
`compose-ui-builder`. Their detailed workflows, including catalog access, live
preview rendering, and UI Builder operations, remain in `yschimke/skills` so
all harnesses use one source of truth. Do not install a same-named local copy on
top of them.

Alternatively, from a checkout of `yschimke/skills`, symlink the two skill
directories into OpenCode's global skill directory:

```sh
mkdir -p ~/.config/opencode/skills
ln -s "$(pwd)/skills/compose-preview" ~/.config/opencode/skills/compose-preview
ln -s "$(pwd)/skills/compose-ui-builder" ~/.config/opencode/skills/compose-ui-builder
```

Run those commands from the `yschimke/skills` repository root. OpenCode also
discovers compatible skills at `.claude/skills`, `.agents/skills`,
`~/.claude/skills`, and `~/.agents/skills`; avoid installing another skill with
the same ID unless you mean to override it. See the
[OpenCode skills documentation](https://opencode.ai/v2/docs/skills) for
discovery order and precedence.

## Authentication

The hosted catalog supports either an interactive OAuth grant or a preview-service token.

For OAuth, leave `oauth` unset (it is enabled for remote servers by default), then start the browser flow:

```sh
opencode mcp auth compose-preview-catalog
```

You can also use OpenCode's `/mcps` command and select the catalog server. OpenCode discovers the authorization server, uses PKCE, and stores the resulting credentials outside `opencode.jsonc`.

For token authentication, set the token in the environment before starting OpenCode:

```sh
export COMPOSE_PREVIEW_TOKEN='…'
opencode
```

The config passes it through the `X-Compose-Preview-Token` header. Do not put the token directly in `opencode.jsonc` or commit it. If a token-only deployment must never attempt OAuth, add `"oauth": false` to the `compose-preview-catalog` server entry.
