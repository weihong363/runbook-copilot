from fastapi.testclient import TestClient

from app.core.config import getSettings
from app.main import app


def testAnalyzeDebugFlagReturnsRetrievalDebug(monkeypatch, tmp_path) -> None:
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
    client.post("/api/knowledge/ingest")

    response = client.post(
        "/api/incidents/analyze",
        json={
            "alertTitle": "checkout-api HTTP 500",
            "serviceName": "checkout-api",
            "logSnippet": "DB_POOL_EXHAUSTED timeout acquiring connection",
            "debug": True,
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["debug"] is not None
    assert payload["debug"]["retrieval"]["candidates"]
    assert payload["debug"]["retrieval"]["candidates"][0]["rerankReasons"]
    getSettings.cache_clear()


def testAnalyzeWithoutDebugKeepsDebugFieldEmpty(monkeypatch, tmp_path) -> None:
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
    client.post("/api/knowledge/ingest")

    response = client.post(
        "/api/incidents/analyze",
        json={
            "alertTitle": "checkout-api HTTP 500",
            "serviceName": "checkout-api",
            "logSnippet": "DB_POOL_EXHAUSTED timeout acquiring connection",
        },
    )

    assert response.status_code == 200
    assert response.json()["debug"] is None
    getSettings.cache_clear()
