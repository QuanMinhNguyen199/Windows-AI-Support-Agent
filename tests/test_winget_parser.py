from app.parsers.winget_parser import extract_version, winget_reports_installed


def test_parse_installed_winget_package() -> None:
    output = """
Name                 Id                         Version Source
----------------------------------------------------------------
Mozilla Firefox      Mozilla.Firefox            128.0   winget
"""

    assert winget_reports_installed(output, "Mozilla.Firefox") is True
    assert extract_version(output, "Mozilla.Firefox") == "128.0"


def test_parse_missing_winget_package() -> None:
    output = "No installed package found matching input criteria."

    assert winget_reports_installed(output, "Mozilla.Firefox") is False
