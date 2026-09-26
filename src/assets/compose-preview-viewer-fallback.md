# Compose Preview viewer handoff

`compose-preview-viewer.html` is the portable viewer bundle from
`compose-preview-server`. Do not create, edit, or substitute a second
Antigravity card. Copy this file unchanged into the HTML artifact folder for
the current response, then include this exact form in the response with the
absolute artifact path substituted:

```html
<agent-embed src="file:///<absolute-artifact-path>/compose-preview-viewer.html"></agent-embed>
```

The card is optional presentation, never the only result. In the same response,
always provide this complete text fallback, using the values returned by the
typed render or UI Builder tool:

```text
Text fallback
Render: <preview ID or URI>
Artifact: <resource link, local file path, or unavailable>
Image: <width> × <height>; hash <hash or unavailable>
Selection: <selected matrix variant or not selected>
Accessibility: <summary or unavailable>
Design/source: <editor-node link or stable node/ref>; <source path and line or unavailable>
```

If copying, embedding, or the card bridge is unavailable, send that text
fallback alone. Do not claim that the person or agent saw the render unless the
available surface was actually inspected. Keep viewer actions equivalent to
their typed tool calls or stable identifiers in the fallback; do not claim an
action occurred merely because it was requested.
