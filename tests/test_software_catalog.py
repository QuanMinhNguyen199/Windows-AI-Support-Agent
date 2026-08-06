import json

import pytest
from pydantic import ValidationError

from app.services.software_catalog import SoftwareCatalog, SoftwareCatalogError


def test_default_catalog_contains_general_and_developer_software() -> None:
    catalog = SoftwareCatalog()
    items = catalog.list()

    assert len(items) == 79
    assert catalog.catalog_version == "2026.08.2"
    assert {item.id for item in items} >= {
        "firefox", "7zip", "vscode", "python", "speedtest", "steam",
        "epic-games", "discord", "league-of-legends", "valorant",
        "telegram", "google-drive", "notion", "obs-studio", "canva",
        "docker-desktop", "dbeaver", "winscp", "wireshark", "github-cli",
        "cursor", "codex-cli", "antigravity-ide", "windsurf", "zed",
        "sublime-text", "visual-studio-community",
        "brave", "opera", "vivaldi", "librewolf",
        "zalo", "coc-coc", "unikey", "capcut", "figma", "foxit-reader",
        "anki", "zotero", "geogebra", "draw-io", "calibre", "microsoft-365",
    }
    assert catalog.get("FIREFOX").winget_id == "Mozilla.Firefox"
    assert catalog.get("steam").winget_id == "Valve.Steam"
    assert catalog.get("league-of-legends").category == "entertainment"
    assert catalog.get("league-of-legends").display_name == "League of Legends"
    assert catalog.get("valorant").display_name == "VALORANT"
    assert len(catalog.get("league-of-legends").verification_commands) == 1
    assert "RiotClientInstalls.json" in catalog.get("league-of-legends").verification_commands[0][-1]
    assert catalog.get("codex-cli").winget_id == "OpenAI.Codex"
    assert catalog.get("antigravity-ide").winget_id == "Google.AntigravityIDE"
    assert catalog.get("canva").advanced_group == "marketing"
    assert catalog.get("google-drive").advanced_group == "office"
    assert catalog.get("cursor").advanced_group is None
    assert all(item.description for item in items)
    assert catalog.get("winrar").description.startswith("Nén và giải nén")
    assert len(catalog.get("discord").verification_commands) == 1
    assert "Discord.exe" in catalog.get("discord").verification_commands[0][-1]
    assert catalog.get("brave").winget_id == "Brave.Brave"
    assert catalog.get("librewolf").category == "browsers"
    assert catalog.summary("adobe-reader").cleanup_available is True
    assert catalog.get("adobe-reader").cleanup_paths == (
        "%LOCALAPPDATA%\\Adobe\\Acrobat Reader\\Cache",
    )
    assert all(item.cleanup_available for item in items)
    assert items[0].display_rank == 1
    assert catalog.get("chrome").display_rank == 1
    assert catalog.get("canva").display_rank == 1
    assert catalog.get("anki").category == "student"
    assert catalog.get("microsoft-365").advanced_group == "office"
    assert "bản quyền" in catalog.get("microsoft-365").description


def test_unknown_software_is_rejected() -> None:
    with pytest.raises(SoftwareCatalogError):
        SoftwareCatalog().get("user-supplied-package")


def test_duplicate_package_id_is_rejected(tmp_path) -> None:
    entry = {
        "display_name": "Example",
        "description": "Ứng dụng dùng để kiểm tra catalog.",
        "publisher": "Example",
        "category": "utilities",
        "audience": "general",
        "winget_id": "Example.Package",
        "check_commands": [["where", "example"]],
        "provenance": "https://github.com/microsoft/winget-pkgs/example",
        "license_note": "Example license",
    }
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps({"catalog_version": "2026.08.1", "software": {"one": entry, "two": entry}}),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match="trùng"):
        SoftwareCatalog(path)


def test_cleanup_path_outside_appdata_is_rejected(tmp_path) -> None:
    entry = {
        "display_name": "Example",
        "description": "Ứng dụng dùng để kiểm tra catalog.",
        "publisher": "Example",
        "category": "utilities",
        "audience": "general",
        "winget_id": "Example.Package",
        "check_commands": [["where", "example"]],
        "cleanup_paths": ["C:\\Users"],
        "provenance": "https://github.com/microsoft/winget-pkgs/example",
        "license_note": "Example license",
    }
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({"catalog_version": "2026.08.1", "software": {"example": entry}}), encoding="utf-8")

    with pytest.raises(ValidationError, match="AppData"):
        SoftwareCatalog(path)
