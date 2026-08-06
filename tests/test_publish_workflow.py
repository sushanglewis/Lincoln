import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "publish-lincoln.yml"


def test_publish_lincoln_workflow_is_valid_yaml():
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    assert data["name"] == "Publish @sushanglewis/lincoln"
    assert "push" in data["on"]
    assert data["on"]["push"]["tags"] == ["lincoln-v*"]


def test_workflow_verifies_package_version():
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    job = data["jobs"]["publish"]
    names = [step["name"] for step in job["steps"]]
    assert "Verify package version matches tag" in names


def test_workflow_runs_tests_and_build():
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    job = data["jobs"]["publish"]
    names = [step["name"] for step in job["steps"]]
    assert "Typecheck" in names
    assert "Test" in names
    assert "Build" in names
    assert "Publish to npm" in names


def test_version_bump_includes_lincoln_package():
    source = json.loads((ROOT / ".version-bump.json").read_text())
    paths = {m["path"] for m in source["manifests"]}
    assert "packages/lincoln/package.json" in paths
