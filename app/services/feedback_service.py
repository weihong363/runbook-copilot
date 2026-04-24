from pathlib import Path

from app.core.database import connect, initializeDatabase
from app.models.schemas import FeedbackRequest


def saveFeedback(databasePath: Path, feedback: FeedbackRequest) -> int:
    initializeDatabase(databasePath)
    with connect(databasePath) as connection:
        cursor = connection.execute(
            "INSERT INTO feedback (incident_id, rating, comment) VALUES (?, ?, ?)",
            (feedback.incidentId, feedback.rating, feedback.comment),
        )
        return int(cursor.lastrowid)
