#!/usr/bin/env python3
"""Check that the release PR's version sources agree before it can merge."""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
version = (root / "version.txt").read_text().strip()
assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version), f"invalid release version: {version}"
manifest = json.loads((root / ".release-please-manifest.json").read_text())
assert manifest == {".": version}, "release manifest and version.txt disagree"
config = json.loads((root / "release-please-config.json").read_text())
assert config["release-type"] == "simple"
assert config["versioning"] == "always-bump-minor"
assert set(config["packages"]) == {"."}
source = json.loads((root / "src/plugins.json").read_text())
assert all(plugin["version"] == version for plugin in source["plugins"]), "plugin versions disagree"
assert source["gemini"]["version"] == version, "Gemini extension version disagrees"
# registry.version belongs to compose-preview-server and must not follow this release.
paths = {entry["jsonpath"] for entry in config["packages"]["."]["extra-files"]}
assert paths == {"$.plugins[*].version", "$.gemini.version"}, "release must only bump local plugin versions"
print("Release metadata agrees")
