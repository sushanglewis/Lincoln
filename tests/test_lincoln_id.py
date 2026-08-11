"""Tests for scripts/lincoln_id.py."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
ID_SCRIPT = ROOT / "scripts" / "lincoln_id.py"
PROCESS_SLUG = "issue-id-test"
TEST_ROOT = ROOT / PROCESS_SLUG


@pytest.fixture(scope="function", autouse=True)
def _clean_test_root():
    """Ensure a clean sandbox under the repo root for every test."""
    for path in list(ROOT.glob(f"{PROCESS_SLUG}*")):
        if path.is_dir():
            shutil.rmtree(path)
    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    state_path = TEST_ROOT / "workflow-stage.yaml"
    state_path.write_text(
        f"""schema_version: 2.0.0
workflow:
  template: interview-to-knowledge
current_run:
  variables:
    process_slug: {PROCESS_SLUG}
nodes: []
recovery: {{}}
""",
        encoding="utf-8",
    )
    (TEST_ROOT / ".lincoln" / "one-id").mkdir(parents=True, exist_ok=True)
    yield
    for path in list(ROOT.glob(f"{PROCESS_SLUG}*")):
        if path.is_dir():
            shutil.rmtree(path)


def run_id(*args: str, cwd: Path = ROOT) -> tuple[int, str, str]:
    result = subprocess.run(
        [sys.executable, str(ID_SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def write_index(id_type: str, data: dict) -> None:
    path = TEST_ROOT / ".lincoln" / "one-id" / f"{id_type}s.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=True), encoding="utf-8")


def read_index(id_type: str) -> dict:
    path = TEST_ROOT / ".lincoln" / "one-id" / f"{id_type}s.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def test_create_page_entry() -> None:
    """Create a page ID entry."""
    rc, stdout, stderr = run_id(
        "create",
        "page/checkout-cart",
        "--title",
        "购物车",
        "--path",
        "pages/prototype/web/checkout-cart/page.html",
        "--relation",
        "feature/checkout-redesign",
    )
    assert rc == 0, stderr
    assert "Created/updated page/checkout-cart" in stdout
    data = read_index("page")
    assert "page/checkout-cart" in data
    assert data["page/checkout-cart"]["title"] == "购物车"
    assert data["page/checkout-cart"]["path"] == "pages/prototype/web/checkout-cart/page.html"
    assert "feature/checkout-redesign" in data["page/checkout-cart"]["features"]


def test_lookup_existing_id() -> None:
    """Lookup returns the stored entry."""
    write_index(
        "feature",
        {
            "feature/checkout-redesign": {
                "title": "结账流程改版",
                "pages": ["page/checkout-cart", "page/checkout-payment"],
            }
        },
    )
    rc, stdout, stderr = run_id("lookup", "feature/checkout-redesign")
    assert rc == 0, stderr
    assert "结账流程改版" in stdout
    assert "page/checkout-cart" in stdout


def test_lookup_missing_id() -> None:
    """Lookup of unknown ID returns non-zero."""
    rc, stdout, stderr = run_id("lookup", "feature/no-such")
    assert rc != 0
    assert "NOT FOUND" in stdout


def test_list_by_type() -> None:
    """List filters by ID type."""
    write_index(
        "page",
        {
            "page/checkout-cart": {"title": "购物车"},
            "page/checkout-payment": {"title": "支付"},
        },
    )
    write_index("feature", {"feature/checkout-redesign": {"title": "改版"}})
    rc, stdout, stderr = run_id("list", "--type", "page")
    assert rc == 0, stderr
    assert "page/checkout-cart" in stdout
    assert "page/checkout-payment" in stdout
    assert "feature/checkout-redesign" not in stdout


def test_list_all_types() -> None:
    """List without --type returns IDs across all types."""
    write_index("page", {"page/a": {"title": "A"}})
    write_index("feature", {"feature/b": {"title": "B"}})
    rc, stdout, stderr = run_id("list")
    assert rc == 0, stderr
    assert "page/a" in stdout
    assert "feature/b" in stdout


def test_related_collects_cross_references() -> None:
    """Related walks cross-references between index files."""
    write_index(
        "feature",
        {
            "feature/checkout-redesign": {
                "title": "结账流程改版",
                "pages": ["page/checkout-cart"],
                "stories": ["story/checkout-guest-pay"],
            }
        },
    )
    write_index("page", {"page/checkout-cart": {"title": "购物车", "fields": ["field/coupon-code"]}})
    write_index("story", {"story/checkout-guest-pay": {"title": "Guest checkout"}})
    write_index("field", {"field/coupon-code": {"title": "Coupon code"}})

    rc, stdout, stderr = run_id("related", "feature/checkout-redesign")
    assert rc == 0, stderr
    assert "page/checkout-cart" in stdout
    assert "story/checkout-guest-pay" in stdout
    assert "field/coupon-code" in stdout


def test_create_rejects_invalid_id() -> None:
    """Invalid ID format is rejected."""
    rc, stdout, stderr = run_id("create", "bad-id")
    assert rc != 0
    assert "Invalid ID" in stderr


def test_create_rejects_unknown_type() -> None:
    """Unknown ID type is rejected."""
    rc, stdout, stderr = run_id("create", "widget/foo")
    assert rc != 0
    assert "Unknown ID type" in stderr


def test_update_existing_entry_preserves_fields() -> None:
    """Updating an entry merges new fields with existing ones."""
    write_index("feature", {"feature/x": {"title": "X", "pages": ["page/a"]}})
    rc, stdout, stderr = run_id(
        "create",
        "feature/x",
        "--title",
        "X Updated",
        "--relation",
        "page/b",
    )
    assert rc == 0, stderr
    data = read_index("feature")
    assert data["feature/x"]["title"] == "X Updated"
    assert "page/a" in data["feature/x"]["pages"]
    assert "page/b" in data["feature/x"]["pages"]
