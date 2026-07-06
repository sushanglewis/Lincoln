import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-main-merge-hygiene.py"


spec = importlib.util.spec_from_file_location("merge_hygiene", SCRIPT)
merge_hygiene = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(merge_hygiene)


def test_rejects_process_package_artifacts():
    bad = merge_hygiene.violations([
        "checkout-redesign/workflow-stage.yaml",
        "checkout-redesign/requirements/session/requirements.md",
        "checkout-redesign/docs/research/options.md",
    ])
    assert len(bad) == 3


def test_allows_durable_assets():
    assert merge_hygiene.violations([
        "products/app/src/main.py",
        "oss/projects.yaml",
        "knowledge/03-features/checkout.md",
        "scripts/stage_loader.py",
    ]) == []
