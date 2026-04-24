from pathlib import Path

from app.rag.chunking import chunkMarkdown
from app.rag.ingestion import ingestKnowledge
from app.rag.vector_store import SQLiteVectorStore


def testChunkMarkdownSplitsByHeading() -> None:
    markdown = "# 标题\nTags: api\n\n## 场景\n内容 A\n\n## 步骤\n内容 B"
    chunks = chunkMarkdown(markdown, Path("knowledge/test-runbook.md"))

    assert len(chunks) == 3
    assert chunks[0].metadata.title == "标题"
    assert chunks[1].heading == "场景"
    assert chunks[1].headingLevel == 2
    assert chunks[2].content.endswith("内容 B")


def testIngestKnowledgeReturnsDocTypeStats(tmp_path: Path) -> None:
    knowledgeDir = tmp_path / "knowledge"
    knowledgeDir.mkdir()
    (knowledgeDir / "runbook-payment-service.md").write_text(
        "# payment-service Runbook\nTags: payment-service, postgres\n\n## 处理步骤\n检查连接池。",
        encoding="utf-8",
    )
    store = SQLiteVectorStore(tmp_path / "db.sqlite3")

    stats = ingestKnowledge(knowledgeDir, store, 64)

    assert stats["indexedDocuments"] == 1
    assert stats["indexedChunks"] >= 1
    assert stats["indexedByDocType"] == {"runbook": 1}
