import sqlite3
from pathlib import Path


def connect(databasePath: Path) -> sqlite3.Connection:
    if not databasePath:
        raise ValueError("databasePath 不能为空")
    databasePath.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(databasePath)
    connection.row_factory = sqlite3.Row
    return connection


def initializeDatabase(databasePath: Path) -> None:
    with connect(databasePath) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                title TEXT NOT NULL,
                path TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                service TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL,
                heading TEXT NOT NULL,
                heading_level INTEGER NOT NULL DEFAULT 0,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        _ensureColumn(connection, "chunks", "service", "TEXT NOT NULL DEFAULT ''")
        _ensureColumn(connection, "chunks", "heading_level", "INTEGER NOT NULL DEFAULT 0")


def _ensureColumn(connection: sqlite3.Connection, table: str, name: str, definition: str) -> None:
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if name not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
