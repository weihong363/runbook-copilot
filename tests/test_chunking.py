from pathlib import Path

from app.rag.chunking import chunkMarkdown


def testChunkMarkdownSplitsByHeading() -> None:
    markdown = "# 标题\nTags: api\n\n## 场景\n内容 A\n\n## 步骤\n内容 B"
    chunks = chunkMarkdown(markdown, Path("knowledge/test-runbook.md"))

    assert len(chunks) == 3
    assert chunks[0].metadata.title == "标题"
    assert chunks[1].heading == "场景"
    assert chunks[2].content.endswith("内容 B")
