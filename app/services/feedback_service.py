from pathlib import Path

from app.core.database import connect, initializeDatabase
from app.models.schemas import FeedbackItem, FeedbackRequest, FeedbackSummary


def saveFeedback(databasePath: Path, feedback: FeedbackRequest) -> int:
    initializeDatabase(databasePath)
    with connect(databasePath) as connection:
        cursor = connection.execute(
            "INSERT INTO feedback (incident_id, rating, useful, reason, comment) VALUES (?, ?, ?, ?, ?)",
            (feedback.incidentId, feedback.rating, _boolToInt(feedback.useful), feedback.reason, feedback.comment),
        )
        return int(cursor.lastrowid)


def listFeedback(databasePath: Path, incidentId: str | None = None, limit: int = 50) -> list[FeedbackItem]:
    if limit < 1 or limit > 100:
        raise ValueError("limit 必须在 1 到 100 之间")
    initializeDatabase(databasePath)
    query = "SELECT * FROM feedback"
    params: tuple[object, ...] = ()
    if incidentId:
        query += " WHERE incident_id = ?"
        params = (incidentId,)
    query += " ORDER BY created_at DESC LIMIT ?"
    with connect(databasePath) as connection:
        rows = connection.execute(query, (*params, limit)).fetchall()
    return [_rowToFeedback(row) for row in rows]


def summarizeFeedback(databasePath: Path, incidentId: str | None = None) -> FeedbackSummary:
    items = listFeedback(databasePath, incidentId=incidentId, limit=100)
    ratings = [item.rating for item in items]
    average = round(sum(ratings) / len(ratings), 2) if ratings else None
    return FeedbackSummary(
        total=len(items),
        averageRating=average,
        usefulCount=sum(1 for item in items if item.useful is True),
        notUsefulCount=sum(1 for item in items if item.useful is False),
    )


def _rowToFeedback(row) -> FeedbackItem:
    return FeedbackItem(
        feedbackId=row["id"],
        incidentId=row["incident_id"],
        rating=row["rating"],
        useful=_intToBool(row["useful"]),
        reason=row["reason"],
        comment=row["comment"],
        createdAt=row["created_at"],
    )


def _boolToInt(value: bool | None) -> int | None:
    if value is None:
        return None
    return 1 if value else 0


def _intToBool(value: int | None) -> bool | None:
    if value is None:
        return None
    return bool(value)
