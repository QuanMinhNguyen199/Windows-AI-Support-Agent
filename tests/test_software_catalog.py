import json

import pytest
from pydantic import ValidationError

from app.services.software_catalog import SoftwareCatalog, SoftwareCatalogError


def test_default_catalog_contains_general_and_developer_software() -> None:
    catalog = SoftwareCatalog()
    items = catalog.list()

    assert len(items) == 9
    assert {item.id for item in items} >= {"firefox", "7zip", "vscode", "python"}
    assert catalog.get("FIREFOX").winget_id == "Mozilla.Firefox"


def test_unknown_software_is_rejected() -> None:
    with pytest.raises(SoftwareCatalogError):
        SoftwareCatalog().get("user-supplied-package")


def test_duplicate_package_id_is_rejected(tmp_path) -> None:
    entry = {
        "display_name": "Example",
        "publisher": "Example",
        "category": "utilities",
        "winget_id": "Example.Package",
        "check_commands": [["where", "example"]],
        "provenance": "https://github.com/microsoft/winget-pkgs/example",
        "license_note": "Example license",
    }
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps({"software": {"one": entry, "two": entry}}),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match="trùng"):
        SoftwareCatalog(path)
