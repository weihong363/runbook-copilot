from pathlib import Path

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
