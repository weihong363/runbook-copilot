import json
from pathlib import Path
from uuid import uuid4

from app.core.database import connect, initializeDatabase
from app.models.schemas import IncidentAnalyzeRequest, IncidentAnalyzeResponse, IncidentEventRequest, IncidentRecord


def saveIncidentAnalysis(
    databasePath: Path,
    request: IncidentAnalyzeRequest,
    response: IncidentAnalyzeResponse,
    sourceType: str = "manual",
    sourceId: str | None = None,
    severity: str | None = None,
    labels: dict[str, str] | None = None,
) -> str:
    if not request.alertTitle.strip():
        raise ValueError("alertTitle 不能为空")
    incidentId = response.incidentId or f"inc_{uuid4().hex}"
    initializeDatabase(databasePath)
    with connect(databasePath) as connection:
        connection.execute(
            """
            INSERT INTO incidents (
                id, source_type, source_id, alert_title, service_name, log_snippet,
                symptom_description, severity, labels, analysis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                source_type = excluded.source_type,
                source_id = excluded.source_id,
                alert_title = excluded.alert_title,
                service_name = excluded.service_name,
                log_snippet = excluded.log_snippet,
                symptom_description = excluded.symptom_description,
                severity = excluded.severity,
                labels = excluded.labels,
                analysis = excluded.analysis,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                incidentId,
                sourceType,
                sourceId,
                request.alertTitle,
                request.serviceName,
                request.logSnippet,
                request.symptomDescription,
                severity,
                json.dumps(labels or {}, ensure_ascii=False),
                response.model_dump_json(),
            ),
        )
    return incidentId


def eventToAnalyzeRequest(event: IncidentEventRequest) -> IncidentAnalyzeRequest:
    return IncidentAnalyzeRequest(
        alertTitle=event.alertTitle,
        serviceName=event.serviceName,
        logSnippet=event.logSnippet,
        symptomDescription=event.symptomDescription,
        debug=event.debug,
    )


def listIncidents(databasePath: Path, limit: int = 20) -> list[IncidentRecord]:
    if limit < 1 or limit > 100:
        raise ValueError("limit 必须在 1 到 100 之间")
    initializeDatabase(databasePath)
    with connect(databasePath) as connection:
        rows = connection.execute(
            """
            SELECT * FROM incidents
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_rowToIncident(row) for row in rows]


def getIncident(databasePath: Path, incidentId: str) -> IncidentRecord | None:
    if not incidentId.strip():
        raise ValueError("incidentId 不能为空")
    initializeDatabase(databasePath)
    with connect(databasePath) as connection:
        row = connection.execute("SELECT * FROM incidents WHERE id = ?", (incidentId,)).fetchone()
    if row is None:
        return None
    return _rowToIncident(row)


def _rowToIncident(row) -> IncidentRecord:
    analysis = json.loads(row["analysis"])
    labels = json.loads(row["labels"] or "{}")
    return IncidentRecord(
        incidentId=row["id"],
        sourceType=row["source_type"],
        sourceId=row["source_id"],
        alertTitle=row["alert_title"],
        serviceName=row["service_name"],
        severity=row["severity"],
        status=row["status"],
        labels=labels,
        answer=analysis["answer"],
        createdAt=row["created_at"],
        updatedAt=row["updated_at"],
    )
