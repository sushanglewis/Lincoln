"""scripts/update_readme_version.py 的确定性单元测试。

tmp_path 中合成 .version-bump.json + 双 README fixture;覆盖锁步更新、幂等、
--check 漂移检测(只报告不写文件)、拒绝降级与缺失文件的错误路径。
"""

import json

import pytest
from scripts import update_readme_version as urv

ZH_README = """# Lincoln

## 最新版本

[![Release](https://img.shields.io/badge/release-v{version}-blue)](RELEASE.md)

**v{version}** 已发布：一些中文描述。

查看完整发布说明:[RELEASE.md](RELEASE.md)
"""

EN_README = """# Lincoln

## Latest Release

[![Release](https://img.shields.io/badge/release-v{version}-blue)](RELEASE.md)

**v{version}** is released: some English description.

Lincoln is released under the [MIT License](LICENSE).
"""


def make_repo(tmp_path, source_version="1.2.0", readme_version=None):
    readme_version = readme_version or source_version
    (tmp_path / ".version-bump.json").write_text(
        json.dumps({"version": source_version, "manifests": []}), encoding="utf-8"
    )
    (tmp_path / "README.md").write_text(
        ZH_README.format(version=readme_version), encoding="utf-8"
    )
    (tmp_path / "README.en.md").write_text(
        EN_README.format(version=readme_version), encoding="utf-8"
    )
    return tmp_path


def test_update_rewrites_badge_and_callout_in_both_readmes(tmp_path):
    root = make_repo(tmp_path, source_version="1.2.0", readme_version="0.9.0")
    assert urv.main(["update_readme_version.py"], root) == 0

    zh = (root / "README.md").read_text(encoding="utf-8")
    en = (root / "README.en.md").read_text(encoding="utf-8")
    assert "release-v1.2.0-blue" in zh and "release-v1.2.0-blue" in en
    assert "**v1.2.0** 已发布" in zh
    assert "**v1.2.0** is released" in en
    assert "0.9.0" not in zh and "0.9.0" not in en


def test_update_preserves_surrounding_text(tmp_path):
    root = make_repo(tmp_path, source_version="1.2.0", readme_version="0.9.0")
    assert urv.main(["update_readme_version.py"], root) == 0

    zh = (root / "README.md").read_text(encoding="utf-8")
    en = (root / "README.en.md").read_text(encoding="utf-8")
    assert "已发布：一些中文描述。" in zh
    assert "is released: some English description." in en
    # 许可声明里的 "is released" 没有 **vX.Y.Z** 前缀,必须原样保留
    assert "Lincoln is released under the [MIT License](LICENSE)." in en


def test_update_is_idempotent(tmp_path, capsys):
    root = make_repo(tmp_path, source_version="1.2.0", readme_version="0.9.0")
    assert urv.main(["update_readme_version.py"], root) == 0
    capsys.readouterr()
    assert urv.main(["update_readme_version.py"], root) == 0
    assert "nothing to do" in capsys.readouterr().out


def test_refuses_downgrade_by_default(tmp_path, capsys):
    root = make_repo(tmp_path, source_version="1.2.0", readme_version="1.3.0")
    assert urv.main(["update_readme_version.py"], root) == 1
    err = capsys.readouterr().err
    assert "newer than source" in err
    assert "v1.3.0" in err
    # 不得写入降级后的版本
    assert "v1.2.0" not in (root / "README.md").read_text(encoding="utf-8")


def test_allow_downgrade_rewrites_readmes(tmp_path):
    root = make_repo(tmp_path, source_version="1.2.0", readme_version="1.3.0")
    assert urv.main(["update_readme_version.py", "--allow-downgrade"], root) == 0
    assert "release-v1.2.0-blue" in (root / "README.md").read_text(encoding="utf-8")


def test_check_passes_when_in_sync(tmp_path):
    root = make_repo(tmp_path)
    assert urv.main(["update_readme_version.py", "--check"], root) == 0


def test_check_fails_on_drift_and_does_not_write(tmp_path, capsys):
    root = make_repo(tmp_path, source_version="1.2.0", readme_version="0.9.0")
    assert urv.main(["update_readme_version.py", "--check"], root) == 1

    err = capsys.readouterr().err
    assert "README.md" in err and "README.en.md" in err
    assert "v1.2.0" in err
    # --check 只报告,不写文件
    assert "0.9.0" in (root / "README.md").read_text(encoding="utf-8")
    assert "0.9.0" in (root / "README.en.md").read_text(encoding="utf-8")


def test_check_only_reports_drifted_file(tmp_path, capsys):
    root = make_repo(tmp_path)
    (root / "README.en.md").write_text(
        EN_README.format(version="0.9.0"), encoding="utf-8"
    )
    assert urv.main(["update_readme_version.py", "--check"], root) == 1
    err = capsys.readouterr().err
    assert "README.en.md" in err
    assert "  README.md:" not in err


def test_root_flag_overrides_default(tmp_path):
    make_repo(tmp_path)
    assert urv.main(["update_readme_version.py", "--check", "--root", str(tmp_path)]) == 0


def test_missing_version_source_exits(tmp_path):
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    (tmp_path / "README.en.md").write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit):
        urv.main(["update_readme_version.py"], tmp_path)


def test_malformed_version_source_exits(tmp_path):
    (tmp_path / ".version-bump.json").write_text("not json", encoding="utf-8")
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    (tmp_path / "README.en.md").write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit):
        urv.main(["update_readme_version.py"], tmp_path)


def test_invalid_version_in_source_exits(tmp_path):
    (tmp_path / ".version-bump.json").write_text(
        json.dumps({"version": "v1.2", "manifests": []}), encoding="utf-8"
    )
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    (tmp_path / "README.en.md").write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit):
        urv.main(["update_readme_version.py"], tmp_path)


def test_missing_readme_exits(tmp_path):
    root = make_repo(tmp_path)
    (root / "README.en.md").unlink()
    with pytest.raises(SystemExit):
        urv.main(["update_readme_version.py"], root)


def test_unknown_args_returns_usage_error(tmp_path):
    with pytest.raises(SystemExit):
        urv.main(["update_readme_version.py", "--bogus"], tmp_path)


def test_root_flag_without_path_returns_usage_error(tmp_path):
    with pytest.raises(SystemExit):
        urv.main(["update_readme_version.py", "--root"], tmp_path)
