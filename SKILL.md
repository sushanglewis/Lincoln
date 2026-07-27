---
name: Lincoln
description: Lincoln AI-Native R&D workflow system — terminal installer and agent harness templates
---

# Lincoln

After this skill is installed, launch the guided terminal installer to set up Lincoln in your project:

```bash
npx lincoln-install
```

The installer will walk you through selecting an agent harness (Claude Code, Cursor, Codex, OpenCode, etc.), optional dependencies, and project configuration. For CI or scripting, use `--no-tui --format json` or `--yes --dry-run`.

For the agent-mediated setup flow, ask your Agent to run `/lc-setup` instead.
