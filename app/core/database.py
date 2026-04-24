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
                tags TEXT NOT NULL,
                heading TEXT NOT NULL,
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
