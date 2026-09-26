# Codex rich-harness evidence

This record preserves the observed Codex portion of the issue #6 and issue #18
compatibility investigation. It distinguishes host behavior from the direct
JSON-RPC fixture smoke test.

## Environment

- Date: 2026-09-26
- Codex CLI: 0.151.0
- Plugin repository commit: `d37dd66d2fa203176fc464db297628dcc48cba5b`
- Mode: noninteractive `codex exec`, ephemeral thread, read-only sandbox
- Plugin home: isolated temporary `CODEX_HOME` with existing authentication
  copied in; the user's normal plugin configuration was not modified

The local `spike/` marketplace was added to that temporary home. Both `p1` and
`p2` then appeared in `codex plugin list --json` as installed and enabled at
version 0.0.1.

Run metadata required by `evals/README.md`:

- Canonical-skills commit: n/a; this probe used only the fixture's `spike-p1`
  and `spike-p2` skills.
- Server commit: fixture echo server at plugin commit `d37dd66d`.
- Tool sequence: p1 SessionStart, p2 SessionStart, read `spike-p1`, read
  `spike-p2`, attempt the prompt-supplied reviewer name (failed), p1 Stop, p2
  Stop. No fixture MCP tool call was available.
- Image count: 0.
- Follow-up: issues #6 and #18.

## Probe

The prompt required observed-only answers, no file edits, both `spike check`
skills, the `spike-reviewer` agent, `spike-prompt`, beta `render_preview`, and
beta `ask` in form and URL modes. It also asked whether the image, MCP App,
elicitation UI, or text fallbacks actually appeared.

Hooks were allowed without an interactive trust prompt because the fixture was
reviewed locally before the run. The command remained in a read-only sandbox.

## Observations

- Both SessionStart hooks ran with their own `CLAUDE_PLUGIN_ROOT`. Each hook
  saw `CODEX_THREAD_ID`, logged the startup event, and emitted the same
  `SPIKE-SESSION-START` marker. The model reported that marker in its startup
  context, proving delivery from at least one hook; identical markers do not
  distinguish which hook output was delivered.
- Both `spike-p1` and `spike-p2` were discovered by name. The model read both
  skill files and returned `SPIKE-P1-LOADED` and `SPIKE-P2-LOADED`.
- Neither `alpha` nor `beta` exposed an MCP tool to the model, and no
  current-session MCP initialize record was produced. Consequently the run
  could not test tool-name collision, image audience, the viewer, viewer
  actions, or either elicitation mode. It also could not exercise the tools'
  text fallbacks. Those cells remain blocked rather than failed.
- `spike-prompt` was not exposed to the noninteractive model. Because
  `codex exec` has no slash-command picker, this does not settle prompt
  discovery in an interactive Codex UI.
- The prompt supplied the `spike-reviewer` name and the model attempted to use
  it, but the host returned `collab spawn failed: no thread with id`. No agent
  verdict was returned, and the attempt does not independently prove that the
  packaged definition was discovered. Q20 remains blocked for this mode.
- Both Stop hooks ran once after the final response and received the actual
  session and turn envelope. No blocking decision was configured for this run.

## Fixture-only control

`python3 spike/prepare.py && python3 spike/run-protocol-smoke.py` passed on the
same commit. The direct client verified both servers, their colliding tool
names, the image plus text/resource-link result, the MCP App resource, both
elicitation fallbacks, and the prompt protocol. That proves the fixture is
internally coherent; it does not upgrade any blocked host result to a pass.

## Unavailable harnesses

- Claude Code 2.1.205: the minimal JSON prompt process was killed with exit 137
  and no output even outside the restricted sandbox. This is an environment
  limitation, not a product result.
- Antigravity: neither the desktop harness nor `agy` is available.
- OpenCode: no executable is installed in the current environment. The earlier
  configuration-parser observation in the matrix remains valid but is not a
  model-turn result.
