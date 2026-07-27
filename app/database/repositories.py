import sqlite3
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.core.redaction import redact_text
from app.database.db import Database
from app.models.actions import ActionState, PendingAction, PendingActionRecord
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
        software_id: str,
        definition: CommandDefinition,
        warning: str,
        ttl: timedelta = timedelta(minutes=5),
        now: datetime | None = None,
    ) -> PendingActionRecord:
        created_at = now or utc_now()
        expires_at = created_at + ttl
        action_id = str(uuid4())
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO pending_actions (
                    id, software_id, command_id, definition_json,
                    display_command, risk_level, warning, state,
                    created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    action_id,
                    software_id,
                    definition.id,
                    definition.model_dump_json(),
                    definition.display_command,
                    definition.risk_level.value,
                    warning,
                    ActionState.PENDING.value,
                    created_at.isoformat(),
                    expires_at.isoformat(),
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
                    "UPDATE pending_actions SET state = ?, finished_at = ? WHERE id = ?",
                    (ActionState.EXPIRED.value, current_time.isoformat(), action_id),
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
                SET state = ?
                WHERE id = ? AND state = ?
                """,
                (ActionState.EXECUTING.value, action_id, ActionState.PENDING.value),
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
                "UPDATE pending_actions SET state = ?, finished_at = ? WHERE id = ?",
                (ActionState.CANCELLED.value, current_time.isoformat(), action_id),
            )
            connection.execute(
                "INSERT INTO user_confirmations(action_id, decision, created_at) VALUES (?, ?, ?)",
                (action_id, "cancelled", current_time.isoformat()),
            )
            connection.commit()
        return self.get(action_id)

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
                SET state = ?, finished_at = ?, result_json = ?
                WHERE id = ? AND state = ?
                """,
                (
                    state.value,
                    finished_at.isoformat(),
                    result.model_dump_json(),
                    action_id,
                    ActionState.EXECUTING.value,
                ),
            )
            if updated.rowcount != 1:
                raise ActionStateError("Pending action không ở trạng thái executing.")
        return self.get(action_id)

    @staticmethod
    def public(record: PendingActionRecord) -> PendingAction:
        return PendingAction.model_validate(
            record.model_dump(exclude={"software_id", "definition", "created_at"})
        )

    @staticmethod
    def _record(row: sqlite3.Row) -> PendingActionRecord:
        return PendingActionRecord(
            id=row["id"],
            software_id=row["software_id"],
            command_id=row["command_id"],
            definition=CommandDefinition.model_validate_json(row["definition_json"]),
            display_command=row["display_command"],
            risk_level=row["risk_level"],
            warning=row["warning"],
            state=row["state"],
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
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
