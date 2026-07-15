"""scripts/bump_version.py 的确定性单元测试(#68)。

tmp_path 中合成 .version-bump.json + manifest fixture;另有一条对真实仓库的
锁步守护测试,保证事实源与 4 个真实 manifest 永不漂移。
"""

import json

import pytest
from scripts import bump_version

ROOT = bump_version.ROOT

SOURCE_DATA = {
    "version": "1.0.0",
    "manifests": [
        {"path": "a.json", "pointers": ["/version"]},
        {"path": "b.json", "pointers": ["/plugins/0/version", "/version"]},
        {"path": "lock.json", "pointers": ["/version", "/packages//version"]},
    ],
}


def make_repo(tmp_path, version="1.0.0"):
    (tmp_path / ".version-bump.json").write_text(
        json.dumps({**SOURCE_DATA, "version": version}), encoding="utf-8"
    )
    (tmp_path / "a.json").write_text(json.dumps({"name": "x", "version": version}))
    (tmp_path / "b.json").write_text(
        json.dumps({"plugins": [{"name": "x", "version": version}], "version": version})
    )
    (tmp_path / "lock.json").write_text(
        json.dumps({"version": version, "packages": {"": {"version": version}}})
    )
    return tmp_path


def test_parse_pointer_decodes_segments():
    assert bump_version.parse_pointer("/plugins/0/version") == ["plugins", "0", "version"]
    assert bump_version.parse_pointer("/packages//version") == ["packages", "", "version"]
    assert bump_version.parse_pointer("/a~1b/c~0d") == ["a/b", "c~d"]
    with pytest.raises(ValueError):
        bump_version.parse_pointer("version")


def test_resolve_walks_lists_and_empty_keys():
    doc = {"plugins": [{"version": "1.0.0"}], "packages": {"": {"version": "1.0.0"}}}
    parent, key = bump_version.resolve(doc, ["plugins", "0", "version"])
    assert parent == {"version": "1.0.0"} and key == "version"
    parent, key = bump_version.resolve(doc, ["packages", "", "version"])
    assert key == "version" and parent["version"] == "1.0.0"


def test_check_passes_on_lockstep(tmp_path):
    root = make_repo(tmp_path)
    data = bump_version.load_source(root)
    assert bump_version.cmd_check(data, root) == 0


def test_check_fails_on_drift(tmp_path, capsys):
    root = make_repo(tmp_path)
    (root / "b.json").write_text(
        json.dumps({"plugins": [{"name": "x", "version": "0.9.0"}], "version": "1.0.0"})
    )
    data = bump_version.load_source(root)
    assert bump_version.cmd_check(data, root) == 1
    assert "/plugins/0/version" in capsys.readouterr().err


def test_check_fails_when_manifest_missing(tmp_path):
    root = make_repo(tmp_path)
    (root / "a.json").unlink()
    data = bump_version.load_source(root)
    with pytest.raises(SystemExit):
        bump_version.cmd_check(data, root)


def test_bump_updates_every_pointer_and_source(tmp_path):
    root = make_repo(tmp_path)
    data = bump_version.load_source(root)
    assert bump_version.cmd_bump(data, root, "2.0.0") == 0

    lock = json.loads((root / "lock.json").read_text(encoding="utf-8"))
    assert lock["version"] == "2.0.0"
    assert lock["packages"][""]["version"] == "2.0.0"
    bumped = bump_version.load_source(root)
    assert bumped["version"] == "2.0.0"
    assert bump_version.cmd_check(bumped, root) == 0


def test_bump_rejects_invalid_semver(tmp_path):
    root = make_repo(tmp_path)
    data = bump_version.load_source(root)
    with pytest.raises(SystemExit):
        bump_version.cmd_bump(data, root, "v2.0")


def test_main_unknown_args_returns_usage_error(tmp_path):
    assert bump_version.main(["bump_version.py"], tmp_path) == 2


def test_real_repo_versions_are_in_lockstep():
    """真实仓库守护:.version-bump.json 与 4 个 manifest 必须一致。"""
    assert bump_version.main(["bump_version.py", "--check"], ROOT) == 0
