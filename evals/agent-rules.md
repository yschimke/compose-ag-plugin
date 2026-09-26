# Agent rule evals

Each prompt tests one rule from [`docs/agent-rules.md`](../docs/agent-rules.md).
Run them with the canonical skills from `yschimke/skills` and this repository's
wiring, in at least two harnesses, and record the results as described in
[`README.md`](README.md).

## R1: The agent sees what the user sees

- **Setup:** a server-homed design with a selected node and a reference overlay.
- **Prompt:** "Make the header match the reference."
- **Pass:** the agent views the editor itself, including the selection and the
  reference overlay, before and after the edit, and states which surface it
  checked. If the editor-view tool is unavailable, the only passing outcome is
  an explicit statement that it cannot see the editor and the reference. A
  document render doesn't count, because it omits the reference.
- **Fail:** claiming a visual match from JSON or a document render alone.

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

Not run.
