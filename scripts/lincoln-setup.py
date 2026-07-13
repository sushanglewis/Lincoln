#!/usr/bin/env python3
"""Lincoln setup CLI — invoked by Claude, not by end users directly.

This script is the implementation backend for the `lc-setup` skill.
It discovers missing dependencies from `.claude/skills/dependencies.yaml`,
installs external skills/CLIs, and initializes repository configuration.

Usage (called by Claude):
    python scripts/lincoln-setup.py check
    python scripts/lincoln-setup.py install-skills
    python scripts/lincoln-setup.py install-clis
    python scripts/lincoln-setup.py init-repo-config --owner <owner> --name <repo>
    python scripts/lincoln-setup.py init-project
    python scripts/lincoln-setup.py mark-step --step init_project --status completed
    python scripts/lincoln-setup.py is-setup-complete
    python scripts/lincoln-setup.py bootstrap
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Ensure the project root is on sys.path so `scripts` is importable when this
# script is invoked directly.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts import lincoln_dependency_manager, lincoln_harness_adapter


# Steps tracked in `.context/lc-setup-state.yaml`.
_SETUP_STATE_PATH = Path(".context") / "lc-setup-state.yaml"


def confirm(prompt: str, auto_yes: bool = False) -> bool:
    """Ask the user for confirmation, or return True when auto_yes is set."""
    if auto_yes:
        print(f"{prompt} [Y/n] (auto-yes)")
        return True
    try:
        answer = input(f"{prompt} [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in ("y", "yes", "all")


def _load_state(root: Path) -> dict[str, Any]:
    """Load the per-repo setup state file, returning an empty dict if absent."""
    state_file = root / _SETUP_STATE_PATH
    if not state_file.exists():
        return {"steps": {}}
    try:
        import yaml

        data = yaml.safe_load(state_file.read_text(encoding="utf-8")) or {}
        data.setdefault("steps", {})
        return data
    except Exception as exc:
        print(f"⚠️ Failed to read {state_file}: {exc}; starting with empty state.")
        return {"steps": {}}


def _save_state(root: Path, state: dict[str, Any]) -> None:
    """Persist the per-repo setup state file."""
    import yaml

    state_file = root / _SETUP_STATE_PATH
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _mark_step(root: Path, step: str, status: str) -> None:
    """Record that a setup step has been attempted or completed."""
    state = _load_state(root)
    state["steps"][step] = {"status": status}
    _save_state(root, state)


def is_setup_complete(root: Path) -> bool:
    """Return True when all setup steps have been recorded as completed."""
    state = _load_state(root)
    steps = state.get("steps", {})
    required = ("skills", "clis", "repo_config", "init_project")
    return all(steps.get(s, {}).get("status") == "completed" for s in required)


def _github_owner_name_from_remote(root: Path) -> tuple[str, str] | None:
    """Try to infer GitHub owner/name from `git remote get-url origin`."""
    import subprocess

    try:
        proc = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return None
        url = proc.stdout.strip()
        # Match git@github.com:owner/repo.git or https://github.com/owner/repo.git
        match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", url)
        if match:
            return match.group(1), match.group(2)
    except Exception:
        pass
    return None


def run_check(args: argparse.Namespace) -> int:
    """Check all declared dependencies and print a summary."""
    root = Path(args.root).resolve()
    platform_name = lincoln_dependency_manager.detect_platform()

    try:
        manifest = lincoln_dependency_manager.load_dependencies(root)
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1

    skills_dir = Path.home() / ".claude" / "skills"
    missing_skills = lincoln_dependency_manager.check_skills(manifest, root, skills_dir)
    missing_clis = lincoln_dependency_manager.check_clis(manifest, platform_name)

    required_missing = [m for m in missing_skills + missing_clis if m.get("required")]
    optional_missing = [m for m in missing_skills + missing_clis if not m.get("required")]

    if required_missing:
        print("❌ Required dependencies missing:")
        for dep in required_missing:
            print(f"  - {dep['name']} ({dep['type']})")
            if dep.get("install_command"):
                print(f"    Install: {dep['install_command']}")
            if dep.get("install_note"):
                print(f"    Note: {dep['install_note']}")

    if optional_missing:
        print("\nℹ️ Optional dependencies missing:")
        for dep in optional_missing:
            print(f"  - {dep['name']} ({dep['type']})")
            if dep.get("install_command"):
                print(f"    Install: {dep['install_command']}")

    if not required_missing and not optional_missing:
        print("✅ All declared dependencies are present.")
        return 0

    return 1 if required_missing else 0


def detect_legacy_skills(skills_dir: Path) -> list[str]:
    """Return old `lincoln-*` skill dir names left over from before the lc-* rename."""
    if not skills_dir.is_dir():
        return []
    return sorted(p.name for p in skills_dir.iterdir() if p.is_dir() and p.name.startswith("lincoln-"))


def _warn_legacy_skills(skills_dir: Path) -> None:
    legacy = detect_legacy_skills(skills_dir)
    if not legacy:
        return
    print("\n⚠️ 检测到旧版技能目录(已重命名为 lc-* 系列,不再维护):")
    for name in legacy:
        print(f"   - {skills_dir / name}")
    print("   迁移方式:确认无本地改动后手动删除上述目录,重新运行 lc-setup。")


def run_install_skills(args: argparse.Namespace) -> int:
    """Install missing external skills and plugins."""
    root = Path(args.root).resolve()
    platform_name = lincoln_dependency_manager.detect_platform()

    try:
        manifest = lincoln_dependency_manager.load_dependencies(root)
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1

    skills_dir = Path.home() / ".claude" / "skills"
    _warn_legacy_skills(skills_dir)
    missing = lincoln_dependency_manager.check_skills(manifest, root, skills_dir)

    if not missing:
        print("✅ All skills already present.")
        _mark_step(root, "skills", "completed")
        return 0

    auto_yes = args.yes or args.dry_run
    offline_cache = Path(args.offline_cache) if args.offline_cache else None
    all_ok = True

    for dep in missing:
        if not dep.get("default_install", dep.get("required", True)):
            print(f"⏭️ Skipping optional {dep['name']} (not default_install).")
            continue

        cmd = dep.get("install_command")
        if not cmd:
            print(f"⚠️ No install command for {dep['name']}; skipping.")
            all_ok = False
            continue

        prompt = f"Install {dep['name']} ({dep['type']})? Command: {cmd}"
        if not confirm(prompt, auto_yes=auto_yes):
            print(f"⏭️ Skipped {dep['name']}.")
            all_ok = False
            continue

        if dep["type"] in ("skill", "plugin"):
            result = lincoln_dependency_manager.install_skill(
                dep["name"],
                dep["source"],
                dep.get("ref", ""),
                skills_dir,
                offline_cache=offline_cache,
                dry_run=args.dry_run,
            )
        else:
            result = lincoln_dependency_manager.install_cli(dep["name"], cmd, dry_run=args.dry_run)

        if result.get("installed"):
            print(f"✅ Installed {dep['name']}.")
        elif result.get("skipped"):
            print(f"⏭️ {dep['name']} already up to date.")
        elif result.get("dry_run"):
            print(f"🔍 Dry-run: would have installed {dep['name']}.")
        else:
            print(f"❌ Failed to install {dep['name']}: {result.get('error', 'unknown error')}")
            all_ok = False

    if all_ok:
        _mark_step(root, "skills", "completed")
        return 0
    return 1


def run_install_clis(args: argparse.Namespace) -> int:
    """Install missing CLI dependencies."""
    root = Path(args.root).resolve()
    platform_name = lincoln_dependency_manager.detect_platform()

    try:
        manifest = lincoln_dependency_manager.load_dependencies(root)
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1

    missing = lincoln_dependency_manager.check_clis(manifest, platform_name)
    if not missing:
        print("✅ All CLI dependencies already present.")
        _mark_step(root, "clis", "completed")
        return 0

    auto_yes = args.yes
    all_ok = True

    for dep in missing:
        cmd = dep.get("install_command")
        if not cmd:
            print(f"⚠️ No install command for {dep['name']} on this platform.")
            print(f"   Manual install note: {dep.get('install_note', 'N/A')}")
            all_ok = False
            continue

        prompt = f"Install {dep['name']} ({dep['binary']})? Command: {cmd}"
        if not confirm(prompt, auto_yes=auto_yes):
            print(f"⏭️ Skipped {dep['name']}.")
            all_ok = False
            continue

        result = lincoln_dependency_manager.install_cli(dep["name"], cmd, dry_run=args.dry_run)
        if result.get("installed"):
            print(f"✅ Installed {dep['name']}.")
        elif result.get("dry_run"):
            print(f"🔍 Dry-run: would have installed {dep['name']}.")
        else:
            print(f"❌ Failed to install {dep['name']}: {result.get('error', 'unknown error')}")
            all_ok = False

    if all_ok:
        _mark_step(root, "clis", "completed")
        return 0
    return 1


def run_init_repo_config(args: argparse.Namespace) -> int:
    """Initialize `.github/openspec-config.yml` with real owner/name."""
    root = Path(args.root).resolve()
    config_path = root / ".github" / "openspec-config.yml"

    owner = args.owner
    name = args.name
    branch = args.branch

    if not owner or not name:
        inferred = _github_owner_name_from_remote(root)
        if inferred:
            default_owner, default_name = inferred
            owner = owner or default_owner
            name = name or default_name

    if not owner or not name:
        print("❌ Could not determine GitHub owner/name.")
        print("   Please provide --owner and --name, or ensure origin remote points to GitHub.")
        return 1

    if args.dry_run:
        print(f"🔍 Dry-run: would write {config_path} with owner={owner}, name={name}, branch={branch}.")
        return 0

    result = lincoln_dependency_manager.init_openspec_config(owner, name, branch, config_path)
    if result.get("updated"):
        print(f"✅ Updated {config_path}: {owner}/{name} ({branch}).")
        _mark_step(root, "repo_config", "completed")
        return 0
    if result.get("skipped"):
        print(f"ℹ️ {config_path} already contains real values; leaving unchanged.")
        _mark_step(root, "repo_config", "completed")
        return 0

    print(f"❌ Failed to update {config_path}: {result.get('error', 'unknown error')}")
    return 1


def run_init_project(args: argparse.Namespace) -> int:
    """Run scripts/init-project.sh to create directories and initial commit."""
    root = Path(args.root).resolve()
    script = root / "scripts" / "init-project.sh"

    if not script.exists():
        print(f"❌ {script} not found.")
        return 1

    prompt = f"Run {script} to initialize the project directory structure?"
    if not args.yes and not confirm(prompt, auto_yes=False):
        print("⏭️ Skipped project initialization.")
        return 1

    if args.dry_run:
        print(f"🔍 Dry-run: would run {script}")
        _mark_step(root, "init_project", "completed")
        return 0

    try:
        proc = subprocess.run(
            ["bash", str(script)],
            cwd=root,
            check=False,
        )
    except Exception as exc:
        print(f"❌ Failed to run {script}: {exc}")
        return 1

    if proc.returncode != 0:
        print(f"❌ {script} exited with code {proc.returncode}")
        return proc.returncode

    _mark_step(root, "init_project", "completed")
    print("✅ Project initialization complete.")
    return 0


def run_mark_step(args: argparse.Namespace) -> int:
    """Record a setup step status in .context/lc-setup-state.yaml."""
    root = Path(args.root).resolve()
    _mark_step(root, args.step, args.status)
    print(f"✅ Marked step '{args.step}' as '{args.status}'.")
    return 0


def run_is_setup_complete(args: argparse.Namespace) -> int:
    """Exit 0 when all required setup steps are marked completed."""
    root = Path(args.root).resolve()
    if is_setup_complete(root):
        print("✅ Lincoln setup is complete.")
        return 0
    print("⏳ Lincoln setup is not complete.")
    return 1


def run_bootstrap(args: argparse.Namespace) -> int:
    """Run the full setup flow: skills, CLIs, config, project init."""
    root = Path(args.root).resolve()
    print("🚀 Starting Lincoln bootstrap...\n")

    # 1. Install skills (includes plugins declared as skill/plugin type).
    print("==> Installing skills and plugins...")
    code = run_install_skills(args)
    if code != 0:
        print("\n⚠️ Skill installation incomplete. Resolve the issues above and re-run bootstrap.")
        return code

    # 2. Install CLIs.
    print("\n==> Installing CLI dependencies...")
    code = run_install_clis(args)
    if code != 0:
        print("\n⚠️ CLI installation incomplete. Resolve the issues above and re-run bootstrap.")
        return code

    # 3. Initialize repo config.
    print("\n==> Initializing repository configuration...")
    code = run_init_repo_config(args)
    if code != 0:
        return code

    # 4. Initialize project directories.
    print("\n==> Initializing project...")
    code = run_init_project(args)
    if code != 0:
        return code

    # 5. Generate harness adapter artifacts (optional).
    if getattr(args, "harness", None):
        print("\n==> Generating harness adapter artifacts...")
        code = run_generate_harness(args)
        if code != 0:
            return code

    print("\n🎉 Lincoln bootstrap completed.")
    return 0


def _add_harness_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--harness",
        action="append",
        default=None,
        help="Generate harness adapter artifacts (codex|opencode; repeatable)",
    )
    p.add_argument("--project-dir", default=None, help="Target project dir (default: --root)")
    p.add_argument("--home-dir", default=None, help="Target home dir (default: real home)")


def run_generate_harness(args: argparse.Namespace) -> int:
    """Generate codex/opencode artifacts from .claude/ via harness manifests."""
    root = Path(args.root).resolve()
    project_dir = Path(args.project_dir).resolve() if args.project_dir else root
    home_dir = Path(args.home_dir).resolve() if args.home_dir else Path.home()
    harnesses = args.harness or []
    for name in harnesses:
        try:
            if getattr(args, "dry_run", False):
                print(f"[dry-run] would generate harness '{name}' into {project_dir} / {home_dir}")
                continue
            written = lincoln_harness_adapter.generate(root, name, project_dir, home_dir)
            print(f"✅ Harness '{name}': {len(written)} artifacts generated.")
            for path in written:
                print(f"   - {path}")
        except lincoln_harness_adapter.HarnessAdapterError as exc:
            print(f"❌ Harness '{name}' failed: {exc}", file=sys.stderr)
            return 2
    return 0


def _add_common_args(p: argparse.ArgumentParser) -> None:
    """Add flags that every subcommand understands."""
    p.add_argument("--root", default=".", help="Project root directory (default: current dir)")
    p.add_argument("--yes", action="store_true", help="Auto-confirm all installations")
    p.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")
    p.add_argument("--offline-cache", default=None, help="Directory with cached skill clones")


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lc-setup",
        description="Lincoln dependency and configuration setup backend.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    check_p = subparsers.add_parser("check", help="Check declared dependencies")
    _add_common_args(check_p)

    skills_p = subparsers.add_parser("install-skills", help="Install missing skills and plugins")
    _add_common_args(skills_p)

    clis_p = subparsers.add_parser("install-clis", help="Install missing CLI dependencies")
    _add_common_args(clis_p)

    init_p = subparsers.add_parser("init-repo-config", help="Initialize .github/openspec-config.yml")
    _add_common_args(init_p)
    init_p.add_argument("--owner", default=None, help="GitHub repository owner")
    init_p.add_argument("--name", default=None, help="GitHub repository name")
    init_p.add_argument("--branch", default="main", help="Default branch (default: main)")

    project_p = subparsers.add_parser("init-project", help="Run scripts/init-project.sh")
    _add_common_args(project_p)

    mark_p = subparsers.add_parser("mark-step", help="Mark a setup step status")
    _add_common_args(mark_p)
    mark_p.add_argument("--step", required=True, help="Step name")
    mark_p.add_argument("--status", default="completed", help="Step status")

    complete_p = subparsers.add_parser("is-setup-complete", help="Exit 0 if setup is complete")
    _add_common_args(complete_p)

    boot_p = subparsers.add_parser("bootstrap", help="Run the full setup flow")
    _add_common_args(boot_p)
    boot_p.add_argument("--owner", default=None, help="GitHub repository owner")
    boot_p.add_argument("--name", default=None, help="GitHub repository name")
    boot_p.add_argument("--branch", default="main", help="Default branch (default: main)")
    _add_harness_args(boot_p)

    harness_p = subparsers.add_parser(
        "generate-harness", help="Generate codex/opencode adapter artifacts"
    )
    _add_common_args(harness_p)
    _add_harness_args(harness_p)

    parsed = parser.parse_args(args)

    handlers = {
        "check": run_check,
        "install-skills": run_install_skills,
        "install-clis": run_install_clis,
        "init-repo-config": run_init_repo_config,
        "init-project": run_init_project,
        "mark-step": run_mark_step,
        "is-setup-complete": run_is_setup_complete,
        "bootstrap": run_bootstrap,
        "generate-harness": run_generate_harness,
    }

    return handlers[parsed.command](parsed)


if __name__ == "__main__":
    sys.exit(main())
