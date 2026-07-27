from app.models.command import CommandDefinition, RiskLevel


class RiskPolicyError(ValueError):
    """Raised when a command is not allowed to execute automatically."""


class RiskPolicy:
    def assert_can_run(self, definition: CommandDefinition, *, confirmed: bool = False) -> None:
        if definition.risk_level is RiskLevel.HIGH_RISK:
            raise RiskPolicyError("Lệnh HIGH_RISK không được tự chạy trong MVP.")
        if definition.requires_admin:
            raise RiskPolicyError("Ứng dụng không tự chạy lệnh yêu cầu Administrator.")
        if definition.risk_level is RiskLevel.LOW_RISK and not confirmed:
            raise RiskPolicyError("Lệnh LOW_RISK cần được người dùng xác nhận.")
