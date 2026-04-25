from pathlib import Path
from typing import TypedDict

from app.rag.embedding_provider import EmbeddingProvider, HashEmbeddingProvider
from app.rag.chunking import MarkdownChunk, chunkMarkdown
from app.rag.vector_store import VectorStore


class IngestStats(TypedDict):
    indexedDocuments: int
    indexedChunks: int
    indexedByDocType: dict[str, int]
    emptySectionsMerged: int
    indexedFiles: list[str]


def ingestKnowledge(
    knowledgeDir: Path,
    vectorStore: VectorStore,
    dimension: int,
    embeddingProvider: EmbeddingProvider | None = None,
) -> IngestStats:
    if not knowledgeDir.exists():
        raise FileNotFoundError(f"知识目录不存在: {knowledgeDir}")
    provider = embeddingProvider or HashEmbeddingProvider(dimension)
    markdownPaths = sorted(knowledgeDir.rglob("*.md"))
    chunks: list[MarkdownChunk] = []
    docTypeCounts: dict[str, int] = {}
    for path in markdownPaths:
        markdown = path.read_text(encoding="utf-8")
        documentChunks = chunkMarkdown(markdown, path)
        chunks.extend(documentChunks)
        if documentChunks:
            docType = documentChunks[0].metadata.docType
            docTypeCounts[docType] = docTypeCounts.get(docType, 0) + 1
    embeddings = {
        chunk.id: provider.embed(
            (
                f"{chunk.metadata.title}\n{chunk.metadata.docType}\n{chunk.metadata.service}\n"
                f"{chunk.heading}\n{' '.join(chunk.metadata.tags)}\n{chunk.content}"
            )
        )
        for chunk in chunks
    }
    vectorStore.replaceChunks(chunks, embeddings)
    mergedSections = sum(1 for chunk in chunks if "补充小节" in chunk.content)
    return {
        "indexedDocuments": len(markdownPaths),
        "indexedChunks": len(chunks),
        "indexedByDocType": docTypeCounts,
        "emptySectionsMerged": mergedSections,
        "indexedFiles": [str(path) for path in markdownPaths],
    }
