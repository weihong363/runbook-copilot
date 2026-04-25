from pathlib import Path

from app.models.schemas import QueryRewrite, RetrievalFilters
from app.rag.ingestion import ingestKnowledge
from app.rag.retriever import HybridRetriever
from app.rag.vector_store import SQLiteVectorStore


def testHybridRetrieverFindsRelevantChunk(tmp_path: Path) -> None:
    knowledgeDir = tmp_path / "knowledge"
    knowledgeDir.mkdir()
    (knowledgeDir / "runbook.md").write_text(
        "# 支付服务 Runbook\nTags: payment\n\n## 数据库超时\n处理 DB_POOL_EXHAUSTED 和连接池耗尽。",
        encoding="utf-8",
    )
    store = SQLiteVectorStore(tmp_path / "db.sqlite3")
    ingestKnowledge(knowledgeDir, store, 64)

    results = HybridRetriever(store, 64).search("payment DB_POOL_EXHAUSTED", 3)

    assert results
    assert "DB_POOL_EXHAUSTED" in results[0]["content"]


def testHybridRetrieverBoostsExactServiceMatch(tmp_path: Path) -> None:
    knowledgeDir = tmp_path / "knowledge"
    knowledgeDir.mkdir()
    (knowledgeDir / "runbook-payment-service.md").write_text(
        "# payment-service Runbook\nTags: payment-service, postgres\n\n## 连接池耗尽\n处理 remaining connection slots are reserved。",
        encoding="utf-8",
    )
    (knowledgeDir / "runbook-order-service.md").write_text(
        "# order-service Runbook\nTags: order-service, postgres\n\n## 连接池耗尽\n处理 remaining connection slots are reserved。",
        encoding="utf-8",
    )
    store = SQLiteVectorStore(tmp_path / "db.sqlite3")
    ingestKnowledge(knowledgeDir, store, 64)

    results = HybridRetriever(store, 64).search("payment-service remaining connection slots are reserved", 3)

    assert results[0]["service"] == "payment-service"


def testHybridRetrieverBoostsDependencyAndErrorCode(tmp_path: Path) -> None:
    knowledgeDir = tmp_path / "knowledge"
    knowledgeDir.mkdir()
    (knowledgeDir / "runbook-checkout-api.md").write_text(
        "# checkout-api Runbook\nTags: checkout-api, redis\n\n## Redis 连接失败\n出现 redis connection refused 时检查缓存实例状态。",
        encoding="utf-8",
    )
    (knowledgeDir / "runbook-checkout-api-db.md").write_text(
        "# checkout-api 数据库 Runbook\nTags: checkout-api, postgres\n\n## 数据库超时\n出现 DB_POOL_EXHAUSTED 时检查连接池。",
        encoding="utf-8",
    )
    store = SQLiteVectorStore(tmp_path / "db.sqlite3")
    ingestKnowledge(knowledgeDir, store, 64)

    dependencyResults = HybridRetriever(store, 64).search("checkout-api redis connection refused", 3)
    errorCodeResults = HybridRetriever(store, 64).search("checkout-api DB_POOL_EXHAUSTED", 3)

    assert dependencyResults[0]["heading"] == "Redis 连接失败"
    assert errorCodeResults[0]["content"].find("DB_POOL_EXHAUSTED") >= 0


def testHybridRetrieverPrefersRunbookOverIncidentNoise(tmp_path: Path) -> None:
    knowledgeDir = tmp_path / "knowledge"
    knowledgeDir.mkdir()
    (knowledgeDir / "incident-payment-service.md").write_text(
        "# payment-service incident record\nTags: payment-service, postgres\n\n## 事故背景\n记录本次故障影响范围。",
        encoding="utf-8",
    )
    (knowledgeDir / "runbook-payment-service.md").write_text(
        "# payment-service Runbook\nTags: payment-service, postgres\n\n## 数据库连接耗尽\n处理 remaining connection slots are reserved 和活跃 session。",
        encoding="utf-8",
    )
    store = SQLiteVectorStore(tmp_path / "db.sqlite3")
    ingestKnowledge(knowledgeDir, store, 64)

    results = HybridRetriever(store, 64).search("payment-service remaining connection slots are reserved", 3)

    assert results[0]["doc_type"] == "runbook"


def testHybridRetrieverUsesStructuredFilters(tmp_path: Path) -> None:
    knowledgeDir = tmp_path / "knowledge"
    knowledgeDir.mkdir()
    (knowledgeDir / "runbook-order-service.md").write_text(
        "# order-service Runbook\nTags: order-service, redis\n\n## Redis 连接失败\n出现 connection refused 时检查 redis。",
        encoding="utf-8",
    )
    (knowledgeDir / "runbook-payment-service.md").write_text(
        "# payment-service Runbook\nTags: payment-service, redis\n\n## Redis 连接失败\n出现 connection refused 时检查 redis。",
        encoding="utf-8",
    )
    store = SQLiteVectorStore(tmp_path / "db.sqlite3")
    ingestKnowledge(knowledgeDir, store, 64)

    results = HybridRetriever(store, 64).search(
        QueryRewrite(
            keywordQuery="redis connection refused",
            semanticQuery="order-service redis connection refused after release",
            filters=RetrievalFilters(service="order-service", docTypes=["runbook"], dependencies=["redis"]),
        ),
        3,
    )

    assert results
    assert results[0]["service"] == "order-service"


def testHybridRetrieverDebugIncludesScoreBreakdownAndReasons(tmp_path: Path) -> None:
    knowledgeDir = tmp_path / "knowledge"
    knowledgeDir.mkdir()
    (knowledgeDir / "runbook-checkout-api.md").write_text(
        "# checkout-api Runbook\nTags: checkout-api, postgres\n\n## 数据库超时\n出现 DB_POOL_EXHAUSTED 时检查连接池。",
        encoding="utf-8",
    )
    store = SQLiteVectorStore(tmp_path / "db.sqlite3")
    ingestKnowledge(knowledgeDir, store, 64)

    searchResult = HybridRetriever(store, 64).searchWithDebug(
        QueryRewrite(
            keywordQuery="checkout-api DB_POOL_EXHAUSTED",
            semanticQuery="checkout-api database pool exhausted",
            filters=RetrievalFilters(
                service="checkout-api",
                docTypes=["runbook"],
                dependencies=["postgres"],
                errorCodes=["DB_POOL_EXHAUSTED"],
            ),
        ),
        3,
    )

    assert searchResult.results
    assert searchResult.debug.totalChunks >= searchResult.debug.filteredChunks
    assert searchResult.debug.candidates
    assert searchResult.debug.candidates[0].finalScore > 0
    assert any("error_code_match" in reason for reason in searchResult.debug.candidates[0].rerankReasons)
