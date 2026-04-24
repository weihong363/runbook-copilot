from pathlib import Path

from app.rag.chunking import MarkdownChunk, chunkMarkdown
from app.rag.embedding import embedText
from app.rag.vector_store import SQLiteVectorStore


def ingestKnowledge(knowledgeDir: Path, vectorStore: SQLiteVectorStore, dimension: int) -> tuple[int, int]:
    if not knowledgeDir.exists():
        raise FileNotFoundError(f"知识目录不存在: {knowledgeDir}")
    markdownPaths = sorted(knowledgeDir.rglob("*.md"))
    chunks: list[MarkdownChunk] = []
    for path in markdownPaths:
        markdown = path.read_text(encoding="utf-8")
        chunks.extend(chunkMarkdown(markdown, path))
    embeddings = {
        chunk.id: embedText(
            f"{chunk.metadata.title}\n{chunk.heading}\n{' '.join(chunk.metadata.tags)}\n{chunk.content}",
            dimension,
        )
        for chunk in chunks
    }
    vectorStore.replaceChunks(chunks, embeddings)
    return len(markdownPaths), len(chunks)
