from app.database.db import Database


def test_database_preserves_corrupt_file_and_recovers(tmp_path) -> None:
    path = tmp_path / "winassist.db"
    path.write_bytes(b"not a sqlite database")

    database = Database(path)
    database.initialize()

    backups = list(tmp_path.glob("winassist.db.corrupt-*") )
    assert len(backups) == 1
    assert backups[0].read_bytes() == b"not a sqlite database"
    with database.connect() as connection:
        assert connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        assert connection.execute(
            "SELECT value FROM app_metadata WHERE key = 'schema_version'"
        ).fetchone()[0] == "1"
