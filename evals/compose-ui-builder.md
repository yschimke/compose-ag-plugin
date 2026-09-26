# Compose UI Builder evals

Run these prompts in at least two harnesses with the canonical
`compose-ui-builder` skill installed from `yschimke/skills` and this
repository's `compose-catalogs` wiring enabled.

## Prompts

1. "Design a login screen with email, password and a primary button in M3,
   then give me the Compose code."
2. "Make a Wear OS list screen with a header and 3 buttons."
3. "Change the button to a tonal button."

## Expected behaviour

- Acquire the `ui-builder-read`, `ui-builder-write`, and `ui-builder-export`
  grants when needed.
- Fetch a catalog summary first, then details for only the selected components.
- Create or copy a starter design, apply batched operations with a fresh
  operation ID and current base revision, and retry one revision conflict after
  refetching the design.
- Export Compose source and provide the browser design URL.
- For prompt 3, inspect the existing design before applying the focused change.

## Results

Not run. Live service credentials and harness sessions are required.
