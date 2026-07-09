"""Tests for external agent manifests under .claude/agents/external/."""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_DIR = ROOT / ".claude" / "agents" / "external"
PERMISSIVE_LICENSES = {"mit", "apache-2.0", "bsd-3-clause", "bsd-2-clause", "isc"}


@pytest.fixture
def manifests():
    return list(EXTERNAL_DIR.glob("*.manifest.yaml"))


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}


# ---------------------------------------------------------------------------
# Manifest structure tests
# ---------------------------------------------------------------------------


def test_manifests_exist(manifests):
    assert manifests, f"No manifest files found in {EXTERNAL_DIR}"


@pytest.mark.parametrize("manifest_path", list(EXTERNAL_DIR.glob("*.manifest.yaml")), ids=lambda p: p.name)
def test_manifest_has_required_fields(manifest_path):
    docs = list(yaml.safe_load_all(manifest_path.read_text(encoding="utf-8")))
    data = docs[0] if docs else None
    assert isinstance(data, dict), f"{manifest_path.name}: invalid frontmatter"

    for key in ["schema_version", "framework", "source", "ref", "license", "imported_agents"]:
        assert key in data, f"{manifest_path.name}: missing '{key}'"

    assert isinstance(data["imported_agents"], list)
    assert data["imported_agents"], f"{manifest_path.name}: imported_agents is empty"


@pytest.mark.parametrize("manifest_path", list(EXTERNAL_DIR.glob("*.manifest.yaml")), ids=lambda p: p.name)
def test_manifest_uses_permissive_license(manifest_path):
    docs = list(yaml.safe_load_all(manifest_path.read_text(encoding="utf-8")))
    data = docs[0] if docs else {}
    license_key = str(data.get("license", "")).lower()
    assert license_key in PERMISSIVE_LICENSES, (
        f"{manifest_path.name}: license '{license_key}' is not in the permissive allowlist"
    )


@pytest.mark.parametrize("manifest_path", list(EXTERNAL_DIR.glob("*.manifest.yaml")), ids=lambda p: p.name)
def test_manifest_source_is_https_url(manifest_path):
    docs = list(yaml.safe_load_all(manifest_path.read_text(encoding="utf-8")))
    data = docs[0] if docs else {}
    source = data.get("source", "")
    assert source.startswith("https://github.com/"), (
        f"{manifest_path.name}: source must be a GitHub HTTPS URL"
    )


# ---------------------------------------------------------------------------
# Imported agent existence tests
# ---------------------------------------------------------------------------


def test_all_imported_agent_files_exist():
    for manifest_path in EXTERNAL_DIR.glob("*.manifest.yaml"):
        docs = list(yaml.safe_load_all(manifest_path.read_text(encoding="utf-8")))
        data = docs[0] if docs else {}
        framework = manifest_path.stem.replace(".manifest", "")
        prefix = data.get("prefix", framework)
        agents_subdir = data.get("paths", {}).get("agents", ".claude/agents")

        for imported in data.get("imported_agents", []):
            imported_path = Path(imported)
            basename = imported_path.stem if imported.endswith(".md") else imported_path.name
            slug = basename.lower().replace(" ", "-").replace("_", "-")
            normalized_name = f"{prefix}-{slug}"
            agent_file = EXTERNAL_DIR / framework / "agents" / f"{normalized_name}.md"
            assert agent_file.exists(), (
                f"{manifest_path.name}: imported agent file not found: {agent_file.relative_to(ROOT)}"
            )


# ---------------------------------------------------------------------------
# NOTICES tests
# ---------------------------------------------------------------------------


def test_notices_md_exists():
    notices_path = EXTERNAL_DIR / "NOTICES.md"
    assert notices_path.exists(), "NOTICES.md missing"


def test_notices_md_contains_all_imported_agents():
    notices_path = EXTERNAL_DIR / "NOTICES.md"
    notices_text = notices_path.read_text(encoding="utf-8")

    for manifest_path in EXTERNAL_DIR.glob("*.manifest.yaml"):
        docs = list(yaml.safe_load_all(manifest_path.read_text(encoding="utf-8")))
        data = docs[0] if docs else {}
        framework = manifest_path.stem.replace(".manifest", "")
        prefix = data.get("prefix", framework)

        for imported in data.get("imported_agents", []):
            imported_path = Path(imported)
            basename = imported_path.stem if imported.endswith(".md") else imported_path.name
            slug = basename.lower().replace(" ", "-").replace("_", "-")
            normalized_name = f"{prefix}-{slug}"
            assert f"{normalized_name}.md" in notices_text, (
                f"NOTICES.md missing entry for {normalized_name}"
            )
