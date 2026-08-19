---
name: Lincoln
description: Lincoln AI-Native R&D workflow system — global npm plugin and agent harness templates
---

# Lincoln

After this skill is installed, set up Lincoln globally on your machine:

```bash
npm install -g @sushanglewis/lincoln
lincoln install --yes
```

`npm install -g` installs the CLI and bundled framework payload. `lincoln install --yes` syncs hooks, agents, skills, scripts, and the full runtime framework to `~/.claude/`, `~/.codex/`, and `~/.opencode/`.

You can also target specific harnesses:

```bash
lincoln install --yes --harnesses claude-code,opencode
```

To update an existing Lincoln installation while preserving your user data, run:

```bash
lincoln update
```

Use `--dry-run` to preview changes or `--no-tui --format json` for scripted updates.

For the agent-mediated setup flow, ask your Agent to run `/lc-setup` instead.

> **Deprecated**: the old `npx lincoln-install` / `npx lincoln-update` wrappers are still present but no longer recommended. If your project previously used the vendored framework model, run `lincoln migrate-project --yes` to switch to the global plugin model.
