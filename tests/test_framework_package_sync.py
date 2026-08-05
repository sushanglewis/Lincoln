import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_framework_allowlist_matches_package_script():
    node = json.loads(
        subprocess.check_output(
            ["node", str(ROOT / "scripts" / "sync-framework-package.mjs"), "--dump-allowlist"]
        )
    )

    spec = importlib.util.spec_from_file_location(
        "package_lincoln_plugin", ROOT / "scripts" / "package-lincoln-plugin.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert set(node["dirs"]) == set(module.ALLOWLIST_DIRS)
    assert set(node["files"]) == set(module.ALLOWLIST_FILES)
