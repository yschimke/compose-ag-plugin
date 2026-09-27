#!/usr/bin/env python3
"""Time repeated edit -> notify -> render cycles against the local MCP server (#39).

No model involved: this measures the server's edit loop on its own, so agent
overhead can be told apart from render cost.

  python3 scripts/edit-render-bench.py --project ~/path/to/ComposeStarter \\
      --file app/src/main/java/.../MainActivity.kt --preview ListScreenPreview \\
      --find 'text = "Header"' --cycles 5

Each cycle replaces --find with a numbered variant (text = "Header 1", ...),
calls notify_file_changed, then render_preview, and checks the PNG hash
changed. The file is restored at the end, even on failure.

The bench offers the project as its MCP root, so the server registers it. If the
server still reports no daemon launch file, run `compose-preview mcp install`
in the project once first.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path


class Mcp:
    def __init__(self, command, cwd):
        self.root_uri = Path(cwd).resolve().as_uri()
        self.process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self.replies, self.next_id = {}, 1
        self.ready = threading.Condition()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.process.stdout:
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" in message and ("result" in message or "error" in message):
                with self.ready:
                    self.replies[message["id"]] = message
                    self.ready.notify_all()
            elif message.get("method") == "roots/list" and "id" in message:
                self._send({"jsonrpc": "2.0", "id": message["id"],
                            "result": {"roots": [{"uri": self.root_uri, "name": "project"}]}})

    def _send(self, message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def call(self, method, params, timeout=600):
        request_id, self.next_id = self.next_id, self.next_id + 1
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        with self.ready:
            if not self.ready.wait_for(lambda: request_id in self.replies, timeout):
                raise TimeoutError(f"{method} timed out after {timeout}s")
            reply = self.replies.pop(request_id)
        if "error" in reply:
            raise RuntimeError(f"{method}: {reply['error']}")
        return reply["result"]

    def tool(self, name, arguments):
        result = self.call("tools/call", {"name": name, "arguments": arguments})
        text = "\n".join(b.get("text", "") for b in result.get("content", []) if b.get("type") == "text")
        size = len(json.dumps(result))
        if result.get("isError"):
            raise RuntimeError(f"{name}: {text[:300]}")
        return text, size

    def close(self):
        self.process.kill()


def render(mcp, preview):
    start = time.time()
    text, size = mcp.tool("render_preview", {"preview": preview, "inline": False})
    elapsed = time.time() - start
    # The first text block is the render's JSON; more blocks (a stale line, a note) can follow it.
    data, _ = json.JSONDecoder().raw_decode(text[text.index("{"):])
    return data, elapsed, size, text


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True)
    parser.add_argument("--file", required=True, help="source file to edit (relative to --project or absolute)")
    parser.add_argument("--preview", required=True)
    parser.add_argument("--find", required=True, help='exact text to vary, e.g. text = "Header"')
    parser.add_argument("--cycles", type=int, default=5)
    parser.add_argument("--cli", default=shutil.which("compose-preview") or "compose-preview")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    source = Path(args.file) if Path(args.file).is_absolute() else project / args.file
    original = source.read_text()
    if args.find not in original:
        sys.exit(f"--find text not found in {source}")
    base = re.sub(r'"([^"]*)"', lambda m: f'"{m.group(1)} {{n}}"', args.find, count=1)
    if base == args.find:
        sys.exit('--find must contain a quoted string, e.g. text = "Header"')

    mcp = Mcp([args.cli, "mcp", "serve"], cwd=project)
    rows = []
    try:
        mcp.call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {"roots": {"listChanged": False}},
                                "clientInfo": {"name": "edit-render-bench", "version": "1"}}, timeout=120)
        mcp._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        first, cold, size, _ = render(mcp, args.preview)
        workspace = re.match(r"compose-preview://([^/]+)/", first["uri"]).group(1)
        print(f"cold render: {cold:.1f}s  ({size} bytes)  {first['uri']}")
        previous = first.get("sha256")
        for n in range(1, args.cycles + 1):
            source.write_text(original.replace(args.find, base.replace("{n}", str(n)), 1))
            t0 = time.time()
            mcp.tool("notify_file_changed", {"workspaceId": workspace, "path": str(source)})
            t1 = time.time()
            data, elapsed, size, text = render(mcp, args.preview)
            fresh = data.get("sha256") != previous
            stale_note = next((l for l in text.splitlines() if "stale" in l.lower()), "")
            rows.append((n, t1 - t0, elapsed, size, fresh))
            print(f"cycle {n}: notify {t1 - t0:.2f}s  render {elapsed:.1f}s  {size} bytes  "
                  f"{'fresh' if fresh else 'STALE'} {stale_note[:80]}")
            previous = data.get("sha256")
    finally:
        source.write_text(original)
        mcp.close()

    if rows:
        renders = [r[2] for r in rows]
        stale = sum(1 for r in rows if not r[4])
        print(f"\nwarm renders: min {min(renders):.1f}s  median {sorted(renders)[len(renders)//2]:.1f}s  "
              f"max {max(renders):.1f}s  stale {stale}/{len(rows)}  (file restored)")
    sys.exit(1 if not rows or any(not r[4] for r in rows) else 0)


if __name__ == "__main__":
    main()
