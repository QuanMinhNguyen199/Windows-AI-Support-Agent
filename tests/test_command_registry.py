import pytest

from app.core.command_registry import CommandRegistry, CommandRegistryError
from app.models.command import RiskLevel
from app.services.software_catalog import SoftwareCatalog
from app.services.software_service import registry_from_catalog


def test_unknown_command_id_is_rejected() -> None:
    registry = CommandRegistry()

    with pytest.raises(CommandRegistryError):
        registry.get("network.user_supplied_command")


def test_invalid_gateway_is_rejected() -> None:
    registry = CommandRegistry()

    with pytest.raises(CommandRegistryError):
        registry.ping_gateway("1.1.1.1 & whoami")


def test_valid_gateway_becomes_fixed_ping_definition() -> None:
    definition = CommandRegistry().ping_gateway("192.168.1.1")

    assert definition.id == "network.ping_gateway"
    assert definition.arguments == ("192.168.1.1", "-n", "10")


def test_software_install_definition_is_low_risk_and_exact() -> None:
    registry = registry_from_catalog(SoftwareCatalog())

    definition = registry.software_install("firefox")

    assert definition.risk_level is RiskLevel.LOW_RISK
    assert definition.arguments == (
        "install",
        "--id",
        "Mozilla.Firefox",
        "--exact",
        "--source",
        "winget",
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--disable-interactivity",
    )
    assert definition.timeout_seconds == 600
    registry.assert_registered(definition)


def test_firefox_uses_executable_verification_and_native_uninstaller() -> None:
    registry = registry_from_catalog(SoftwareCatalog())

    verifications = registry.software_verifications("firefox")
    uninstall = registry.software_uninstall("firefox")

    assert len(verifications) == 1
    assert verifications[0].executable == "powershell"
    assert "firefox.exe" in verifications[0].display_command
    assert uninstall.executable == "powershell"
    assert "uninstall\\helper.exe" in uninstall.display_command
    assert uninstall.risk_level is RiskLevel.LOW_RISK


def test_windows_update_install_is_registered_and_requires_confirmation() -> None:
    registry = CommandRegistry()

    definition = registry.get("windows.install_updates")

    assert definition.executable == "powershell"
    assert definition.risk_level is RiskLevel.LOW_RISK
    assert definition.timeout_seconds == 3600
    assert "Microsoft.Update.Session" not in definition.display_command
    assert "-WindowStyle Hidden" in definition.display_command
    registry.assert_registered(definition)


def test_cleanup_commands_are_fixed_and_require_confirmation_for_deletion() -> None:
    registry = CommandRegistry()

    scan = registry.cleanup_scan("user_temp")
    cleanup = registry.cleanup_selected(("thumbnail_cache", "user_temp"))

    assert scan.risk_level is RiskLevel.READ_ONLY
    assert cleanup.risk_level is RiskLevel.LOW_RISK
    assert "Downloads" not in cleanup.display_command
    assert "Documents" not in cleanup.display_command
    assert "bytes=$totalBytes}|ConvertTo-Json" in scan.arguments[-1]
    registry.assert_registered(scan)
    registry.assert_registered(cleanup)


def test_unknown_cleanup_category_is_rejected() -> None:
    registry = CommandRegistry()

    with pytest.raises(CommandRegistryError):
        registry.cleanup_selected(("downloads",))


def test_adobe_reader_purge_only_uses_reviewed_user_data_targets() -> None:
    registry = registry_from_catalog(SoftwareCatalog())

    definition = registry.software_purge("adobe-reader")

    assert definition.risk_level is RiskLevel.LOW_RISK
    assert "%LOCALAPPDATA%\\Adobe\\Acrobat Reader\\Cache" in definition.display_command
    assert "Documents" not in definition.display_command
    assert "Downloads" not in definition.display_command
    registry.assert_registered(definition)


def test_every_catalog_app_has_safe_purge_command() -> None:
    catalog = SoftwareCatalog()
    registry = registry_from_catalog(catalog)

    for item in catalog.list():
        definition = registry.software_purge(item.id)
        assert definition.risk_level is RiskLevel.LOW_RISK
        registry.assert_registered(definition)
