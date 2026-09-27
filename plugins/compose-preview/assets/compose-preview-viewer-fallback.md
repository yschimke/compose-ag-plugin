# Compose Preview viewer handoff

`compose-preview-viewer.html` is the portable viewer bundle released as the
`compose-preview-viewer.html` asset of `compose-preview-server` v3.75.0, copied
byte-for-byte. Its release tag, source commit, and SHA-256 are recorded in
`compose-preview-viewer.provenance.json`. Do not create, edit, or substitute a
second Antigravity card.

## Static result contract

Copy the viewer unchanged into the HTML artifact folder for the current
response. From the typed render tool call, build this compact JSON envelope:

```json
{"version":1,"arguments":{},"result":{"content":[]}}
```

- `arguments` is a sanitized copy of the render call's argument object. A
  cold-start grant passed as `arguments.token` after `request_access` /
  `poll_access` is for the live call only: delete it before building this
  envelope.
- `result` is its complete MCP `CallToolResult`, including `isError` when set,
  after the same credential sanitization. If a text content block contains JSON, parse,
  sanitize, and compactly re-encode that JSON rather than treating it as an
  opaque safe string.
- Recursively omit credential-shaped keys such as `token`, `authorization`,
  `password`, `secret`, `cookie`, and `apiKey` from both copies. Never put
  credentials in a URL. If any value cannot be proved credential-free, omit the
  card and return the complete text fallback alone.
- Encode the UTF-8 JSON as unpadded base64url. Both the encoded fragment and the
  decoded UTF-8 payload must be at most 500,000 bytes/characters.

Then embed this exact form with the absolute artifact path and encoded envelope
substituted:

```html
<agent-embed src="file:///<absolute-artifact-path>/compose-preview-viewer.html#compose-preview-result=<unpadded-base64url-envelope>"></agent-embed>
```

Static mode does not initialize the MCP Apps bridge, issue authenticated reads,
or expose viewer actions. It displays an inline image block when the result has
one. For text, structured, error, or resource-link-only results it displays the
complete fallback content and the replayable resource URI rather than silently
showing an empty card.

## Required text fallback

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

If the envelope is malformed, credential-bearing, or over either bound—or if
copying, embedding, or the card surface is unavailable—send that text fallback
alone. Do not claim that the person or agent saw the render unless the available
surface was actually inspected. Keep viewer actions equivalent to their typed
tool calls or stable identifiers in the fallback; do not claim an action
occurred merely because it was requested.
