#!/usr/bin/env python3
"""Exercise a release bump through the real manifest generator."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseTest(unittest.TestCase):
    def test_release_bump_regenerates_local_versions_without_bumping_server(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            source_path = root / "src/plugins.json"
            source = json.loads(source_path.read_text())
            registry = source["registry"].copy()
            for plugin in source["plugins"]:
                plugin["version"] = "0.4.0"
            source["gemini"]["version"] = "0.4.0"
            source_path.write_text(json.dumps(source, indent=2) + "\n")
            (root / "version.txt").write_text("0.4.0\n")
            (root / ".release-please-manifest.json").write_text('{".": "0.4.0"}\n')
            subprocess.run(["python3", "scripts/check-release.py"], cwd=root, check=True)
            subprocess.run(["python3", "scripts/generate.py"], cwd=root, check=True)
            subprocess.run(["python3", "scripts/validate_manifests.py"], cwd=root, check=True)
            for plugin in source["plugins"]:
                for relative in [".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json"]:
                    manifest = json.loads((root / "plugins" / plugin["name"] / relative).read_text())
                    self.assertEqual("0.4.0", manifest["version"], relative)
            self.assertEqual("0.4.0", json.loads((root / "gemini-extension.json").read_text())["version"])
            self.assertEqual(registry["version"], json.loads((root / "server.json").read_text())["version"])
            self.assertEqual(registry, json.loads(source_path.read_text())["registry"])
            # Forgetting the source bump must fail before a release PR can merge.
            source["plugins"][0]["version"] = "0.3.0"
            source_path.write_text(json.dumps(source))
            result = subprocess.run(["python3", "scripts/check-release.py"], cwd=root, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("plugin versions disagree", result.stderr)


if __name__ == "__main__":
    unittest.main()
