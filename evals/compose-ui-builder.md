# Compose UI Builder evals

Run these prompts in at least two harnesses with the canonical
`compose-ui-builder` skill installed from `yschimke/skills` and this
repository's `compose-catalogs` wiring enabled.

## Prompts

1. "Design a login screen with email, password and a primary button in M3,
   then give me the Compose code."
2. "Make a Wear OS list screen with a header and 3 buttons."
3. "Change the button to a tonal button."
4. "Make the home screen match this Figma frame: <figma.com/design/…?node-id=…>."

## Expected behaviour

- Acquire the `ui-builder-read`, `ui-builder-write`, and `ui-builder-export`
  grants when needed.
- Fetch a catalog summary first, then details for only the selected components.
- Create or copy a starter design, apply batched operations with a fresh
  operation ID and current base revision, and retry one revision conflict after
  refetching the design.
- Export Compose source and provide the browser design URL.
- For prompt 3, inspect the existing design before applying the focused change.
- For prompt 4, take the frame's screenshot with the Figma tools (never redraw
  it), say that the picture will be stored on the host and get permission, then
  attach it with `ui_builder_set_reference` (`density` from the export scale,
  `sourceUrl` the frame link) and record it with `ui_builder_set_links`. Read
  `facts` before editing — a region or another shape is not pixel-comparable at
  the default fit. Measure with `ui_builder_compare_reference`, apply the
  proposed `operations` a few layers at a time through `ui_builder_apply`,
  compare again until layers report `alreadyAligned`, look with
  `ui_builder_view` (`include: ["reference"]`), and report the remaining
  differences in dp and sp. When the reference tools are not advertised, say
  so and guide the person through **Frame, density and reference** instead.

## Results

Not run. Live service credentials and harness sessions are required.
