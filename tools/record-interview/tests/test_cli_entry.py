from importlib.metadata import entry_points


def test_lincoln_console_script_is_registered():
    eps = entry_points(group="console_scripts")
    lincoln = [ep for ep in eps if ep.name == "Lincoln"]
    assert len(lincoln) == 1
    assert lincoln[0].value == "record_interview.cli:main"
