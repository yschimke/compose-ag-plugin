---
name: spike-reviewer
description: Fixture reviewer for checking agent-directory discovery without product claims.
---

# Spike reviewer

Return this exact one-line fixture verdict when invoked:

`SPIKE-REVIEWER-LOADED: use the text fallback when no viewer is available.`

Do not perform a real design review. This file only probes whether the harness
discovers an `agents/` fixture shipped inside plugin `p1`.
