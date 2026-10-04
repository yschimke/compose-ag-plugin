# Cross-repository marketplace entry (2026-10-04)

Question: can this repository's marketplace list the canonical skill bundles from
`yschimke/skills`, so a person adds one marketplace instead of two?

## Fixture

A scratch marketplace whose only entry points into the other repository:

```json
{"name": "xrepo-test", "owner": {"name": "test"}, "plugins": [
  {"name": "compose-skills", "description": "t",
   "source": {"source": "git-subdir", "url": "https://github.com/yschimke/skills.git",
              "path": "plugins/compose-skills"}}
]}
```

## Claude Code 2.1.289 (isolated `HOME`)

- `claude plugin validate .`: passed. The only warning was the fixture's missing marketplace
  description.
- `claude plugin marketplace add <dir>`, then `claude plugin install compose-skills@xrepo-test`:
  installed `compose-skills` 0.1.8, recorded at `gitCommitSha`
  `3ec4985cbfc0ebba0bafd6fb43c7f098b841163f`. The cache held only the subdirectory, with
  `skills/compose-preview/SKILL.md` (and its `references/` and `scripts/`) and
  `skills/compose-ui-builder/SKILL.md`.

## Codex CLI 0.160.0 (isolated `CODEX_HOME`)

- `codex plugin marketplace add <dir>` read `.claude-plugin/marketplace.json`.
- `codex plugin list` showed `compose-skills@xrepo-test` with source
  `https://github.com/yschimke/skills.git, path plugins/compose-skills`.
- `codex plugin add compose-skills@xrepo-test` installed 0.1.8 with both `SKILL.md` files.

## Not covered

- No model turn ran, so skill triggering through this route is not re-checked. Q13 and Q15
  cover the same skill content installed the older way.
- Cursor and Antigravity were not tried. Antigravity installs by URL and never reads this
  marketplace. Cursor's marketplace keeps local plugins only until a smoke test covers it.
- The entries track the default branch of `yschimke/skills`. Pinning a `ref` is supported by
  `src/plugins.json` but not used.
