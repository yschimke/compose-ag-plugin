# Rich integration evals

Run every prompt once with MCP Apps and elicitation enabled, then once in the
documented fallback mode with both unavailable. Record the harness/version,
server commit, plugin commit, resource links, viewer actions, prompts used, and
whether the person and agent inspected the same render. Static protocol tests
do not count as a pass.

## Viewer and shared evidence

Prompt: "Render this preview, show me the shared viewer, and tell me which
semantic node contains the primary action."

Pass when the person receives the viewer/resource link, the agent inspects the
same render, and the text fallback still contains the render identity,
dimensions, hash, artifact location, and accessibility summary.

## Viewer actions

Prompt: "Select the primary action in the viewer, switch to the largest font
variant, add a comment pin, and open that node in the editor."

Pass when all supported actions reach typed tools and return current state.
Fallback mode must list the exact equivalent tool calls or identifiers and a
usable editor link without claiming an action occurred.

## Forms and URL elicitation

Prompt: "I made a temporary design copy. Ask whether to save it back or discard
it, then request access to the remote design."

Pass when form elicitation offers the closed R3 choice and URL elicitation opens
the scoped access flow. Fallback mode must present the same choices, approval
URL, and verification code as complete text; it must not request an operator
token.

## Prompts

Invoke `preview-file`, `review-design`, `migrate-wear-m3`, and `design-status`.

Pass when each prompt is discoverable, validates required arguments, and
produces a workflow consistent with the canonical skills. A harness without
prompt discovery must be given equivalent copyable text instructions.

## Design-reviewer agent

Prompt: "Delegate review of this Wear migration. Keep images out of the main
conversation and return the verdict and evidence links."

Pass when the packaged `design-reviewer` runs accessibility, semantic,
small-round-device, and maximum-font-scale checks in its own context and returns
the compact documented verdict. If packaged-agent discovery is unavailable,
run the same checklist in the current context and report that limitation.

## Session start

Start a session in a workspace with one unacknowledged design comment, one
unsaved temporary copy, and a failing `compose-preview mcp doctor` check.

Pass when supported harnesses expose one concise summary naming all three
conditions without leaking credentials or dumping full diagnostics. In an
unsupported harness, `design-status` must return the same complete summary.

Until the CLI/MCP exposes workspace-linked comment acknowledgements and
temporary-copy inventory to a session hook, the summary must label those two
dimensions `unavailable`; it must not infer them from local files. The doctor
dimension may report only `ok`, `failed`, or `unavailable`; it invokes
`compose-preview mcp doctor --json` only when `compose-preview mcp --help`
advertises `doctor`, and must not include either command's output. Current CLI
releases do not advertise it, so they report `unavailable` rather than `failed`.

## Deep links

Prompt: "Show where this accessibility finding lives in both the design and
source."

Pass when output preserves server-supplied editor-node and source-line links.
When either link is unavailable, output must include the stable node/ref and
source path/line data that exists and explicitly name the missing link.
