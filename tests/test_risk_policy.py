import pytest

from app.core.risk_policy import RiskPolicy, RiskPolicyError
from app.models.command import CommandDefinition, RiskLevel


def definition(risk: RiskLevel, *, requires_admin: bool = False) -> CommandDefinition:
    return CommandDefinition(
        id="test.command",
        executable="ipconfig",
        arguments=(),
        risk_level=risk,
        requires_admin=requires_admin,
        timeout_seconds=1,
        description="Test command.",
    )


def test_read_only_can_run_without_confirmation() -> None:
    RiskPolicy().assert_can_run(definition(RiskLevel.READ_ONLY))


def test_low_risk_requires_confirmation() -> None:
    with pytest.raises(RiskPolicyError):
        RiskPolicy().assert_can_run(definition(RiskLevel.LOW_RISK))

    RiskPolicy().assert_can_run(definition(RiskLevel.LOW_RISK), confirmed=True)


def test_high_risk_is_always_blocked() -> None:
    with pytest.raises(RiskPolicyError):
        RiskPolicy().assert_can_run(definition(RiskLevel.HIGH_RISK), confirmed=True)


def test_admin_command_is_blocked() -> None:
    with pytest.raises(RiskPolicyError):
        RiskPolicy().assert_can_run(
            definition(RiskLevel.READ_ONLY, requires_admin=True)
        )
