import pytest

from app.core.command_registry import CommandRegistry, CommandRegistryError


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
