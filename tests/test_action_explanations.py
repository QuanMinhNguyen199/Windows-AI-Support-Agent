from app.models.command import CommandResult
from app.services.action_explanations import explain_command_failure


def failed_result(*, stderr: str = "", exit_code: int | None = 1, timed_out: bool = False):
    return CommandResult(
        command_id="software.install.test",
        executable="winget",
        arguments=[],
        exit_code=exit_code,
        stdout="",
        stderr=stderr,
        duration_ms=100,
        timed_out=timed_out,
        success=False,
    )


def test_explains_missing_winget() -> None:
    summary, suggestions = explain_command_failure(
        failed_result(stderr="Executable was not found.", exit_code=None)
    )
    assert "winget" in summary
    assert suggestions


def test_explains_cancelled_installer() -> None:
    summary, _ = explain_command_failure(failed_result(stderr="0x800704c7"))
    assert "bị hủy" in summary


def test_explains_timeout() -> None:
    summary, _ = explain_command_failure(failed_result(timed_out=True))
    assert "nhiều thời gian" in summary


def test_success_has_no_failure_explanation() -> None:
    result = failed_result().model_copy(update={"success": True, "exit_code": 0})
    assert explain_command_failure(result) == (None, [])
