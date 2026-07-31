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
        "--disable-interactivity",
    )
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
