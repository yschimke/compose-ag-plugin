# Antigravity git install evidence

> Historical evidence below retains the repository and marketplace names used during the run.
> For current installation and migration instructions, see the
> [Compose Agent Plugins quick start](../../README.md#quick-start).

The repository owner ran these commands by hand on 2026-10-02 and reported the
output; nothing here was inferred from documentation.

## Environment

- Host: macOS
- Antigravity: `agy` CLI 1.2.12 (the version recorded on 2026-09-27; not
  re-checked)
- Plugin repository commit: `main` at the time of the run (not recorded)

## `agy plugin` help

`agy plugin install --help` and `-h` are taken as the install target
("install target must be a directory"). `agy plugin help` lists:

```text
list                   List imported plugins
import [source]        Import plugins from gemini or claude
install <target>       Install a plugin (supports plugin@marketplace)
uninstall <name>       Uninstall a plugin
enable <name>          Enable a plugin
disable <name>         Disable a plugin
validate [path]        Validate a plugin
link <mp> <target>     Generate link to a marketplace
```

## Bare repository URL

```text
$ agy plugin install https://github.com/yschimke/compose-ag-plugin
Cloning plugin from https://github.com/yschimke/compose-ag-plugin.git...
  [ok]    compose-preview
          - skills      : skipped (not found)
          - agents      : skipped (not found)
          - commands    : skipped (not found)
          ✔ mcpServers  : 2 processed
          - hooks       : skipped (not found)
```

`agy plugin list` then showed a second `compose-preview` entry with
`"source": "gemini-cli"` and only `mcpServers`, next to the existing
`"source": "antigravity"` entries. `agy` read the root `gemini-extension.json`
(the catalog and local servers), not a plugin folder.

## Subdirectory URL

```text
$ agy plugin install https://github.com/yschimke/compose-ag-plugin/tree/main/plugins/compose-preview
Cloning plugin from https://github.com/yschimke/compose-ag-plugin.git...
  [ok]    compose-preview
          ✔ skills      : 3 processed
          ✔ agents      : 1 processed
          - commands    : skipped (not found)
          ✔ mcpServers  : 1 processed
          ✔ hooks       : 1 processed
```

The full plugin installed from GitHub without a local checkout.

```text
$ agy plugin uninstall compose-catalogs
Uninstalled plugin "compose-catalogs"
$ agy plugin install https://github.com/yschimke/compose-ag-plugin/tree/main/plugins/compose-catalogs
Cloning plugin from https://github.com/yschimke/compose-ag-plugin.git...
  [ok]    compose-catalogs
          ✔ skills      : 2 processed
          - agents      : skipped (not found)
          - commands    : skipped (not found)
          ✔ mcpServers  : 1 processed
          - hooks       : skipped (not found)
```

`agy plugin list` then showed `compose-catalogs` with `"source": "antigravity"`,
`importedAt` the time of the install, and components `skills` and
`mcpServers`.

In a new session, "show me the Material 3 Button catalog" reached the hosted
catalog through `compose-catalogs`: it rendered the filled `Button` and the
other core button types from `m3-samples`, listed the remaining families, and
described the `m3-catalog` matrix. It took about 2 minutes (the tool calls were
not recorded), and the small catalog PNGs were drawn stretched to the table
width.

```text
$ agy plugin uninstall yschimke-skills
Uninstalled plugin "yschimke-skills"
$ agy plugin install https://github.com/yschimke/skills
Cloning plugin from https://github.com/yschimke/skills.git...
  [ok]    yschimke-skills
          ✔ skills      : 8 processed
          - agents      : skipped (not found)
          - commands    : skipped (not found)
          - mcpServers  : skipped (not found)
          - hooks       : skipped (not found)
```

`yschimke/skills` keeps its Antigravity `plugin.json` at the repository root,
so the bare repository URL is the right target. `agy plugin list` showed
`yschimke-skills` with `"source": "antigravity"` and components `skills`.

After yschimke/skills#121 split the skills into generated bundles, the default
pair installed on its own:

```text
$ agy plugin install https://github.com/yschimke/skills/tree/main/plugins/compose-skills
Cloning plugin from https://github.com/yschimke/skills.git...
  [ok]    compose-skills
          ✔ skills      : 2 processed
          - agents      : skipped (not found)
          - commands    : skipped (not found)
          - mcpServers  : skipped (not found)
          - hooks       : skipped (not found)
```

## Installing over an existing plugin

After the subdirectory install of `compose-preview` above, `agy plugin list`
still showed its earlier record: `importedAt` 2026-09-27 and components
`skills`, `agents`, `mcpServers` (no `hooks`), next to the `gemini-cli` entry
from the bare URL. `compose-catalogs`, uninstalled first, got a fresh record.
Uninstall before reinstalling until it is known whether an install over an
existing plugin replaces its files.

## Not yet run

- `plugin@marketplace` with `link`, and `import claude`.
- A render in a new session after the URL install.
