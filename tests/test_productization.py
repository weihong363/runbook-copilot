from fastapi.testclient import TestClient

from app.core.config import getSettings
from app.main import app


def testIncidentAnalyzePersistsRecordAndFeedbackSummary(monkeypatch, tmp_path) -> None:
    client = _clientWithKnowledge(monkeypatch, tmp_path)

    analyzeResponse = client.post(
        "/api/incidents/analyze",
        json={
            "alertTitle": "checkout-api HTTP 500",
            "serviceName": "checkout-api",
            "logSnippet": "DB_POOL_EXHAUSTED timeout acquiring connection",
        },
    )

    assert analyzeResponse.status_code == 200
    incidentId = analyzeResponse.json()["incidentId"]
    assert incidentId.startswith("inc_")

    detailResponse = client.get(f"/api/incidents/{incidentId}")
    assert detailResponse.status_code == 200
    assert detailResponse.json()["serviceName"] == "checkout-api"

    feedbackResponse = client.post(
        "/api/feedback",
        json={"incidentId": incidentId, "rating": 4, "useful": True, "reason": "hit", "comment": "命中文档正确"},
    )
    assert feedbackResponse.status_code == 200

    summaryResponse = client.get(f"/api/feedback/summary?incidentId={incidentId}")
    assert summaryResponse.status_code == 200
    assert summaryResponse.json()["total"] == 1
    assert summaryResponse.json()["averageRating"] == 4.0
    assert summaryResponse.json()["usefulCount"] == 1

    getSettings.cache_clear()


def testIncidentEventEndpointStoresSourceMetadata(monkeypatch, tmp_path) -> None:
    client = _clientWithKnowledge(monkeypatch, tmp_path)

    response = client.post(
        "/api/incidents/events",
        json={
            "sourceType": "grafana-webhook",
            "sourceId": "alert-123",
            "alertTitle": "checkout-api HTTP 500",
            "serviceName": "checkout-api",
            "logSnippet": "DB_POOL_EXHAUSTED timeout acquiring connection",
            "severity": "critical",
            "labels": {"team": "checkout"},
        },
    )

    assert response.status_code == 200
    incidentId = response.json()["incidentId"]

    listResponse = client.get("/api/incidents?limit=5")
    assert listResponse.status_code == 200
    incident = listResponse.json()["incidents"][0]
    assert incident["incidentId"] == incidentId
    assert incident["sourceType"] == "grafana-webhook"
    assert incident["sourceId"] == "alert-123"
    assert incident["labels"]["team"] == "checkout"

    getSettings.cache_clear()


def testDebugPageIsAvailable(monkeypatch, tmp_path) -> None:
    _clientWithKnowledge(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/debug")

    assert response.status_code == 200
    assert "Runbook Copilot Debug" in response.text
    getSettings.cache_clear()


def testGrafanaWebhookMapsAlertsToIncidentEvents(monkeypatch, tmp_path) -> None:
    client = _clientWithKnowledge(monkeypatch, tmp_path)

    response = client.post(
        "/api/incidents/integrations/grafana",
        json={
            "receiver": "runbook-copilot",
            "status": "firing",
            "groupKey": "group-1",
            "commonLabels": {"service": "checkout-api", "severity": "critical"},
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "DBPoolExhausted", "service": "checkout-api"},
                    "annotations": {
                        "summary": "checkout-api HTTP 500",
                        "description": "DB_POOL_EXHAUSTED timeout acquiring connection",
                    },
                    "fingerprint": "alert-1",
                },
                {
                    "status": "resolved",
                    "labels": {"alertname": "OldAlert", "service": "checkout-api"},
                    "annotations": {"description": "old resolved alert"},
                    "fingerprint": "alert-2",
                },
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert len(payload["incidentIds"]) == 1
    assert payload["skippedResolved"] == 1

    incident = client.get(f"/api/incidents/{payload['incidentIds'][0]}").json()
    assert incident["sourceType"] == "grafana-webhook"
    assert incident["sourceId"] == "alert-1"
    assert incident["labels"]["alertname"] == "DBPoolExhausted"
    getSettings.cache_clear()


def _clientWithKnowledge(monkeypatch, tmp_path) -> TestClient:
    knowledgeDir = tmp_path / "knowledge"
    knowledgeDir.mkdir()
    (knowledgeDir / "runbook-checkout-api.md").write_text(
        "# checkout-api Runbook\n"
        "tags: checkout-api, postgres\n\n"
        "## 数据库超时\n"
        "出现 DB_POOL_EXHAUSTED 时检查连接池。\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("KNOWLEDGE_DIR", str(knowledgeDir))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "api.sqlite3"))
    getSettings.cache_clear()
    client = TestClient(app)
    ingestResponse = client.post("/api/knowledge/ingest")
    assert ingestResponse.status_code == 200
    return client
