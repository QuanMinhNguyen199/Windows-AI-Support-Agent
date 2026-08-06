import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS pending_actions (
    id TEXT PRIMARY KEY,
    software_id TEXT NOT NULL,
    command_id TEXT NOT NULL,
    definition_json TEXT NOT NULL,
    display_command TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    warning TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    finished_at TEXT,
    result_json TEXT
    , action_kind TEXT NOT NULL DEFAULT 'software_install'
    , resource_id TEXT
    , stage TEXT NOT NULL DEFAULT 'awaiting_confirmation'
    , status_message TEXT NOT NULL DEFAULT 'Đang chờ xác nhận.'
);

CREATE INDEX IF NOT EXISTS idx_pending_actions_state_expiry
ON pending_actions(state, expires_at);

CREATE TABLE IF NOT EXISTS user_confirmations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(action_id) REFERENCES pending_actions(id)
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    intent TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_messages_session
ON messages(session_id, id);

CREATE TABLE IF NOT EXISTS app_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""
logger = logging.getLogger("winassist")


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._initialize_database()
        except sqlite3.DatabaseError as exc:
            logger.error(
                "database_recovered",
                extra={"exception_type": type(exc).__name__},
            )
            self._preserve_corrupt_database()
            self._initialize_database()

    def _initialize_database(self) -> None:
        check_connection = self.connect()
        try:
            integrity = check_connection.execute("PRAGMA quick_check").fetchone()[0]
            if integrity != "ok":
                raise sqlite3.DatabaseError(f"SQLite quick_check failed: {integrity}")
        finally:
            check_connection.close()
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(SCHEMA)
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(pending_actions)")
            }
            migrations = {
                "action_kind": (
                    "ALTER TABLE pending_actions ADD COLUMN action_kind TEXT "
                    "NOT NULL DEFAULT 'software_install'"
                ),
                "resource_id": (
                    "ALTER TABLE pending_actions ADD COLUMN resource_id TEXT"
                ),
                "stage": (
                    "ALTER TABLE pending_actions ADD COLUMN stage TEXT "
                    "NOT NULL DEFAULT 'awaiting_confirmation'"
                ),
                "status_message": (
                    "ALTER TABLE pending_actions ADD COLUMN status_message TEXT "
                    "NOT NULL DEFAULT 'Đang chờ xác nhận.'"
                ),
            }
            for column, statement in migrations.items():
                if column not in columns:
                    connection.execute(statement)
            connection.execute(
                """
                UPDATE pending_actions
                SET resource_id = software_id
                WHERE resource_id IS NULL OR resource_id = ''
                """
            )
            connection.execute(
                """
                INSERT INTO app_metadata(key, value) VALUES('schema_version', '1')
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """
            )

    def _preserve_corrupt_database(self) -> None:
        if not self.path.exists():
            return
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = self.path.with_name(f"{self.path.name}.corrupt-{timestamp}")
        counter = 1
        while backup.exists():
            backup = self.path.with_name(
                f"{self.path.name}.corrupt-{timestamp}-{counter}"
            )
            counter += 1
        self.path.replace(backup)
        for suffix in ("-wal", "-shm"):
            sidecar = Path(f"{self.path}{suffix}")
            if sidecar.exists():
                sidecar.replace(Path(f"{backup}{suffix}"))
