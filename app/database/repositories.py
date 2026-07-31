import sqlite3
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.core.redaction import redact_text
from app.database.db import Database
from app.models.actions import (
    ActionKind,
    ActionStage,
    ActionState,
    PendingAction,
    PendingActionRecord,
)
from app.models.command import CommandDefinition, CommandResult


class ActionNotFoundError(LookupError):
    pass


class ActionExpiredError(ValueError):
    pass


class ActionStateError(ValueError):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


class PendingActionRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        *,
        resource_id: str | None = None,
        software_id: str | None = None,
        kind: ActionKind = ActionKind.SOFTWARE_INSTALL,
        definition: CommandDefinition,
        warning: str,
        ttl: timedelta = timedelta(minutes=5),
        now: datetime | None = None,
    ) -> PendingActionRecord:
        resolved_resource_id = resource_id or software_id
        if not resolved_resource_id:
            raise ValueError("Action phải có resource_id.")
        active = self.find_active(kind=kind, resource_id=resolved_resource_id)
        if active is not None:
            return active
        created_at = now or utc_now()
        expires_at = created_at + ttl
        action_id = str(uuid4())
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO pending_actions (
                    id, software_id, command_id, definition_json,
                    display_command, risk_level, warning, state,
                    created_at, expires_at, action_kind, resource_id,
                    stage, status_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    action_id,
                    resolved_resource_id,
                    definition.id,
                    definition.model_dump_json(),
                    definition.display_command,
                    definition.risk_level.value,
                    warning,
                    ActionState.PENDING.value,
                    created_at.isoformat(),
                    expires_at.isoformat(),
                    kind.value,
                    resolved_resource_id,
                    ActionStage.AWAITING_CONFIRMATION.value,
                    "Đang chờ bạn xác nhận.",
                ),
            )
        return self.get(action_id)

    def get(self, action_id: str) -> PendingActionRecord:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM pending_actions WHERE id = ?", (action_id,)
            ).fetchone()
        if row is None:
            raise ActionNotFoundError("Không tìm thấy pending action.")
        return self._record(row)

    def list_recent(self, limit: int = 30) -> list[PendingActionRecord]:
        safe_limit = max(1, min(limit, 100))
        with self.database.connect() as connection:
            self._expire_pending(connection)
            rows = connection.execute(
                "SELECT * FROM pending_actions ORDER BY created_at DESC LIMIT ?",
                (safe_limit,),
            ).fetchall()
        return [self._record(row) for row in rows]

    def find_active(
        self, *, kind: ActionKind, resource_id: str
    ) -> PendingActionRecord | None:
        with self.database.connect() as connection:
            self._expire_pending(connection)
            row = connection.execute(
                """
                SELECT * FROM pending_actions
                WHERE action_kind = ? AND resource_id = ?
                  AND state IN (?, ?, ?)
                ORDER BY created_at DESC LIMIT 1
                """,
                (
                    kind.value,
                    resource_id,
                    ActionState.PENDING.value,
                    ActionState.EXECUTING.value,
                    ActionState.CANCELLING.value,
                ),
            ).fetchone()
        return self._record(row) if row is not None else None

    def claim_for_confirmation(
        self, action_id: str, *, now: datetime | None = None
    ) -> PendingActionRecord:
        current_time = now or utc_now()
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM pending_actions WHERE id = ?", (action_id,)
            ).fetchone()
            if row is None:
                raise ActionNotFoundError("Không tìm thấy pending action.")
            state = ActionState(row["state"])
            expires_at = datetime.fromisoformat(row["expires_at"])
            if state is ActionState.PENDING and expires_at <= current_time:
                connection.execute(
                    """
                    UPDATE pending_actions
                    SET state = ?, stage = ?, status_message = ?, finished_at = ?
                    WHERE id = ?
                    """,
                    (
                        ActionState.EXPIRED.value,
                        ActionStage.EXPIRED.value,
                        "Yêu cầu đã hết hạn.",
                        current_time.isoformat(),
                        action_id,
                    ),
                )
                connection.execute(
                    "INSERT INTO user_confirmations(action_id, decision, created_at) VALUES (?, ?, ?)",
                    (action_id, "expired", current_time.isoformat()),
                )
                connection.commit()
                raise ActionExpiredError("Pending action đã hết hạn.")
            if state is not ActionState.PENDING:
                raise ActionStateError(
                    f"Pending action không thể xác nhận ở trạng thái {state.value}."
                )
            updated = connection.execute(
                """
                UPDATE pending_actions
                SET state = ?, stage = ?, status_message = ?
                WHERE id = ? AND state = ?
                """,
                (
                    ActionState.EXECUTING.value,
                    ActionStage.PREPARING.value,
                    "Đang chuẩn bị thực thi lệnh.",
                    action_id,
                    ActionState.PENDING.value,
                ),
            )
            if updated.rowcount != 1:
                raise ActionStateError("Pending action đã được xử lý bởi request khác.")
            connection.execute(
                "INSERT INTO user_confirmations(action_id, decision, created_at) VALUES (?, ?, ?)",
                (action_id, "confirmed", current_time.isoformat()),
            )
            connection.commit()
        return self.get(action_id)

    def cancel(
        self, action_id: str, *, now: datetime | None = None
    ) -> PendingActionRecord:
        current_time = now or utc_now()
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM pending_actions WHERE id = ?", (action_id,)
            ).fetchone()
            if row is None:
                raise ActionNotFoundError("Không tìm thấy pending action.")
            state = ActionState(row["state"])
            expires_at = datetime.fromisoformat(row["expires_at"])
            if state is ActionState.PENDING and expires_at <= current_time:
                connection.execute(
                    "UPDATE pending_actions SET state = ?, finished_at = ? WHERE id = ?",
                    (ActionState.EXPIRED.value, current_time.isoformat(), action_id),
                )
                connection.commit()
                raise ActionExpiredError("Pending action đã hết hạn.")
            if state is not ActionState.PENDING:
                raise ActionStateError(
                    f"Pending action không thể hủy ở trạng thái {state.value}."
                )
            connection.execute(
                """
                UPDATE pending_actions
                SET state = ?, stage = ?, status_message = ?, finished_at = ?
                WHERE id = ?
                """,
                (
                    ActionState.CANCELLED.value,
                    ActionStage.CANCELLED.value,
                    "Yêu cầu đã được hủy.",
                    current_time.isoformat(),
                    action_id,
                ),
            )
            connection.execute(
                "INSERT INTO user_confirmations(action_id, decision, created_at) VALUES (?, ?, ?)",
                (action_id, "cancelled", current_time.isoformat()),
            )
            connection.commit()
        return self.get(action_id)

    def request_execution_cancel(
        self, action_id: str, *, now: datetime | None = None
    ) -> PendingActionRecord:
        requested_at = now or utc_now()
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT state FROM pending_actions WHERE id = ?", (action_id,)
            ).fetchone()
            if row is None:
                raise ActionNotFoundError("Không tìm thấy pending action.")
            state = ActionState(row["state"])
            if state is ActionState.CANCELLING:
                connection.commit()
                return self.get(action_id)
            if state is not ActionState.EXECUTING:
                raise ActionStateError(
                    f"Action không thể dừng ở trạng thái {state.value}."
                )
            connection.execute(
                """
                UPDATE pending_actions
                SET state = ?, stage = ?, status_message = ?
                WHERE id = ? AND state = ?
                """,
                (
                    ActionState.CANCELLING.value,
                    ActionStage.CANCELLING.value,
                    "Đang dừng installer theo yêu cầu của bạn.",
                    action_id,
                    ActionState.EXECUTING.value,
                ),
            )
            connection.execute(
                """
                INSERT INTO user_confirmations(action_id, decision, created_at)
                VALUES (?, ?, ?)
                """,
                (action_id, "cancel_requested", requested_at.isoformat()),
            )
            connection.commit()
        return self.get(action_id)

    def finish_execution_cancel(
        self, action_id: str, *, now: datetime | None = None
    ) -> PendingActionRecord:
        finished_at = now or utc_now()
        with self.database.connect() as connection:
            updated = connection.execute(
                """
                UPDATE pending_actions
                SET state = ?, stage = ?, status_message = ?, finished_at = ?
                WHERE id = ? AND state = ?
                """,
                (
                    ActionState.CANCELLED.value,
                    ActionStage.CANCELLED.value,
                    "Installer đã được dừng; trạng thái phần mềm sẽ được quét lại.",
                    finished_at.isoformat(),
                    action_id,
                    ActionState.CANCELLING.value,
                ),
            )
            if updated.rowcount != 1:
                raise ActionStateError("Action không ở trạng thái cancelling.")
        return self.get(action_id)

    def set_running(self, action_id: str, message: str) -> PendingActionRecord:
        return self._set_execution_stage(action_id, ActionStage.RUNNING, message)

    def set_verifying(self, action_id: str, message: str) -> PendingActionRecord:
        return self._set_execution_stage(action_id, ActionStage.VERIFYING, message)

    def finish(
        self,
        action_id: str,
        result: CommandResult,
        *,
        now: datetime | None = None,
    ) -> PendingActionRecord:
        finished_at = now or utc_now()
        state = ActionState.COMPLETED if result.success else ActionState.FAILED
        with self.database.connect() as connection:
            updated = connection.execute(
                """
                UPDATE pending_actions
                SET state = ?, stage = ?, status_message = ?,
                    finished_at = ?, result_json = ?
                WHERE id = ? AND state = ?
                """,
                (
                    state.value,
                    (
                        ActionStage.COMPLETED.value
                        if result.success
                        else ActionStage.FAILED.value
                    ),
                    (
                        "Thao tác đã hoàn tất."
                        if result.success
                        else "Thao tác không hoàn tất thành công."
                    ),
                    finished_at.isoformat(),
                    result.model_dump_json(),
                    action_id,
                    ActionState.EXECUTING.value,
                ),
            )
            if updated.rowcount != 1:
                raise ActionStateError("Pending action không ở trạng thái executing.")
        return self.get(action_id)

    def recover_interrupted(self, *, now: datetime | None = None) -> int:
        recovered_at = now or utc_now()
        with self.database.connect() as connection:
            updated = connection.execute(
                """
                UPDATE pending_actions
                SET state = ?, stage = ?, status_message = ?, finished_at = ?
                WHERE state IN (?, ?)
                """,
                (
                    ActionState.FAILED.value,
                    ActionStage.FAILED.value,
                    "Ứng dụng đã khởi động lại khi thao tác đang chạy.",
                    recovered_at.isoformat(),
                    ActionState.EXECUTING.value,
                    ActionState.CANCELLING.value,
                ),
            )
        return updated.rowcount

    @staticmethod
    def public(record: PendingActionRecord) -> PendingAction:
        return PendingAction.model_validate(
            record.model_dump(exclude={"definition", "result"})
        )

    def _set_execution_stage(
        self, action_id: str, stage: ActionStage, message: str
    ) -> PendingActionRecord:
        with self.database.connect() as connection:
            updated = connection.execute(
                """
                UPDATE pending_actions SET stage = ?, status_message = ?
                WHERE id = ? AND state = ?
                """,
                (stage.value, message, action_id, ActionState.EXECUTING.value),
            )
            if updated.rowcount != 1:
                raise ActionStateError("Action không ở trạng thái executing.")
        return self.get(action_id)

    @staticmethod
    def _expire_pending(connection: sqlite3.Connection) -> None:
        now = utc_now().isoformat()
        connection.execute(
            """
            UPDATE pending_actions
            SET state = ?, stage = ?, status_message = ?, finished_at = ?
            WHERE state = ? AND expires_at <= ?
            """,
            (
                ActionState.EXPIRED.value,
                ActionStage.EXPIRED.value,
                "Yêu cầu đã hết hạn.",
                now,
                ActionState.PENDING.value,
                now,
            ),
        )

    @staticmethod
    def _record(row: sqlite3.Row) -> PendingActionRecord:
        return PendingActionRecord(
            id=row["id"],
            kind=row["action_kind"],
            resource_id=row["resource_id"] or row["software_id"],
            command_id=row["command_id"],
            definition=CommandDefinition.model_validate_json(row["definition_json"]),
            display_command=row["display_command"],
            risk_level=row["risk_level"],
            warning=row["warning"],
            state=row["state"],
            stage=row["stage"],
            status_message=row["status_message"],
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            result=(
                CommandResult.model_validate_json(row["result_json"])
                if row["result_json"]
                else None
            ),
        )


class ChatRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get_or_create_session(self, session_id: str | None = None) -> str:
        candidate = session_id or str(uuid4())
        try:
            normalized = str(UUID(candidate))
        except ValueError:
            normalized = str(uuid4())
        now = utc_now().isoformat()
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO chat_sessions(id, created_at, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET updated_at = excluded.updated_at
                """,
                (normalized, now, now),
            )
        return normalized

    def add_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        intent: str | None = None,
    ) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("Chat role không hợp lệ.")
        now = utc_now().isoformat()
        safe_content = redact_text(content)[:4000]
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO messages(session_id, role, content, intent, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, role, safe_content, intent, now),
            )
            connection.execute(
                "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )
