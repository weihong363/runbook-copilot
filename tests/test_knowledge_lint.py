from pathlib import Path

from app.rag.knowledge_lint import lintKnowledgeDocument


def testLintKnowledgeDocumentPassesForWellFormedRunbook(tmp_path: Path) -> None:
    path = tmp_path / "runbook-order-service.md"
    path.write_text(
        "# order-service Redis 连接失败 Runbook\n"
        "tags: order-service, redis, cache\n\n"
        "## 适用场景\n"
        "出现 redis connection refused。\n\n"
        "## 快速判断\n"
        "检查 redis 实例状态。\n\n"
        "## 处理步骤\n"
        "检查网络连通性。\n",
        encoding="utf-8",
    )

    issues = lintKnowledgeDocument(path)

    assert issues == []


def testLintKnowledgeDocumentFindsMissingTagsAndH2(tmp_path: Path) -> None:
    path = tmp_path / "note.md"
    path.write_text(
        "# 临时说明\n"
        "这是一份没有 tags 和二级标题的文档。\n",
        encoding="utf-8",
    )

    issues = lintKnowledgeDocument(path)

    messages = [issue.message for issue in issues]
    assert any("缺少 `tags:` 行" in message for message in messages)
    assert any("无法识别文档类型" in message for message in messages)
