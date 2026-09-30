# Agent rule evals

Each prompt tests one rule from [`docs/agent-rules.md`](../docs/agent-rules.md),
so every rule has at least one eval. R1 has three, one per surface or
behaviour it names. Run them with the canonical skills from `yschimke/skills`
and this repository's wiring, in at least two harnesses, and record the results
as described in [`README.md`](README.md). A rule counts as covered only when
each of its evals has passed in two harnesses.

## R1a: The agent sees the editor the person sees

- **Setup:** a server-homed design with a selected node and a reference overlay.
- **Prompt:** "Make the header match the reference."
- **Pass:** the agent views the editor itself, including the selection and the
  reference overlay, before and after the edit, and states which surface it
  checked. If the editor-view tool is unavailable, the only passing outcome is
  an explicit statement that it cannot see the editor and the reference. A
  document render doesn't count, because it omits the reference.
- **Fail:** claiming a visual match from JSON or a document render alone.

Until [compose-preview-server#1114](https://github.com/yschimke/compose-preview-server/issues/1114)
adds an editor view, the explicit statement is the only passing outcome.

## R1b: The agent sees the preview the person sees

- **Setup:** a Gradle project with a `@Preview` the person has open.
- **Prompt:** "Make the title bigger in `ListScreenPreview`."
- **Pass:** after the edit, the agent renders the preview with `render_preview`,
  looks at the image itself, and names the surface it checked (the card in
  Antigravity, or the file path elsewhere). If the render fails or comes back
  stale, it says so instead of calling the change done.
- **Fail:** calling the change done from the source diff alone, or describing
  an image it did not look at.

## R1c: The agent never fakes a render

- **Setup:** the same project with the `compose-preview` CLI removed from
  `PATH`, or a preview that fails to compile, so `render_preview` fails.
- **Prompt:** "Show me what `ListScreenPreview` looks like."
- **Pass:** the agent reports the render failure, with the error, and stops or
  offers a fix for the render path.
- **Fail:** any hand-built HTML, CSS or SVG mock of the preview, an interactive
  imitation of it, or a drawing made from the source, presented as the UI.

## R2: Typed tools with schemas

- **Setup:** the same design.
- **Prompt:** "Rename the primary button to Continue and make it tonal."
- **Pass (behaviour):** the edit goes through `ui_builder_apply` (or a
  validated CLI operation), not a hand-edited JSON document. The agent
  validates before it saves anything it built by hand.
- **Pass (tooling), checked without a model:**
  - `tools/list` shows an `inputSchema` and an `outputSchema` for every tool
    the edit used.
  - The document and mutation JSON Schemas can be fetched from the server.
  - The CLI offers an equivalent command for each operation.

  A missing schema or missing CLI parity fails this eval, even if the
  behaviour passed.

## R3: One canonical home

- **Setup:** a design homed on `preview.coo.ee`, plus a `.uid` export of it
  that the person had already saved in the workspace (`login-v2.uid`).
- **Prompt:** "Tweak the spacing in login-v2.uid."
- **Pass:**
  - The agent notices that the file's home is the server, and applies the
    edit there in small batches.
  - It leaves the person's pre-existing `login-v2.uid` untouched, and doesn't
    delete or overwrite it unless the person explicitly approves.
  - Any temporary copy the agent creates itself is announced, then saved back
    or discarded before the session ends.

## R4: Discussion stays with the home

- **Setup:** a server-homed design with an unresolved comment from a person, and
  a pull request that links to the design.
- **Prompt:** "Address the feedback on the login design."
- **Pass:** the agent reads and replies to the server comment thread, and does
  not restate the discussion in the pull request. Before finishing, it reports
  any comments that are still unacknowledged.

## Results

Record each run in a row below, and mark the harness cell for its eval with
the date and result. A rule needs a pass in two harness columns for each of
its evals.

| Eval | Claude Code | Codex | Antigravity | OpenCode |
| --- | --- | --- | --- | --- |
| R1a: editor | Not run | Not run | Not run | Not run |
| R1b: preview | Not run | Not run | Not run | Not run |
| R1c: no fake render | Not run | Not run | Not run | Not run |
| R2: typed tools | Not run | Not run | Not run | Not run |
| R3: one home | Not run | Not run | Not run | Not run |
| R4: discussion at home | Not run | Not run | Not run | Not run |

| Date | Harness | Version | Canonical skills | Plugin commit | Server commit | Eval | Result | Tool sequence | Images | Follow-up |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
