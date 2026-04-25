import json

from app.core.config import getSettings
from app.evaluation.evaluate import evaluate


def testEvaluateReturnsStructuredMetrics(tmp_path, monkeypatch) -> None:
    knowledgeDir = tmp_path / "knowledge"
    knowledgeDir.mkdir()
    (knowledgeDir / "runbook-order-service-redis.md").write_text(
        "# order-service Redis 连接失败 Runbook\n"
        "tags: order-service, redis\n\n"
        "## 处理步骤\n"
        "出现 redis connection refused 时检查 redis 实例状态和网络连通性。\n",
        encoding="utf-8",
    )
    (knowledgeDir / "runbook-checkout-api.md").write_text(
        "# checkout-api 5xx 排障 Runbook\n"
        "tags: checkout-api, database\n\n"
        "## 处理步骤\n"
        "出现 DB_POOL_EXHAUSTED 时检查数据库连接池。\n",
        encoding="utf-8",
    )
    datasetPath = tmp_path / "dataset.jsonl"
    datasetPath.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "name": "order-redis",
                        "input": {
                            "alertTitle": "order-service redis connection refused",
                            "serviceName": "order-service",
                            "logSnippet": "RedisConnectionError connection refused",
                            "symptomDescription": "发布后错误率上升",
                        },
                        "expectedCitationPath": "knowledge/runbook-order-service-redis.md",
                        "expectedKeywords": ["order-service", "redis", "connection refused"],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "name": "checkout-db",
                        "input": {
                            "alertTitle": "checkout-api HTTP 500",
                            "serviceName": "checkout-api",
                            "logSnippet": "DB_POOL_EXHAUSTED timeout acquiring connection",
                        },
                        "expectedCitationPath": "knowledge/runbook-checkout-api.md",
                        "expectedKeywords": ["checkout-api", "db_pool_exhausted"],
                    },
                    ensure_ascii=False,
                ),
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KNOWLEDGE_DIR", str(knowledgeDir))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "eval.sqlite3"))
    getSettings.cache_clear()

    report = evaluate(datasetPath)

    assert report["summary"]["totalCases"] == 2
    assert report["summary"]["hitAt3"] == 1.0
    assert report["summary"]["hitAt5"] == 1.0
    assert report["summary"]["citationRelevance"] == 1.0
    assert report["summary"]["schemaValidity"] == 1.0
    assert report["summary"]["keywordCoverage"] >= 0.8
    assert report["summary"]["answerUsefulness"] == 1.0
    assert len(report["cases"]) == 2
    assert report["cases"][0]["actualCitationPaths"]
    assert report["cases"][0]["answerUseful"] is True
    getSettings.cache_clear()
