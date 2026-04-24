import json
from pathlib import Path

from app.core.database import connect, initializeDatabase
from app.rag.chunking import MarkdownChunk
from app.rag.embedding import cosineSimilarity


class SQLiteVectorStore:
    def __init__(self, databasePath: Path) -> None:
        if not databasePath:
            raise ValueError("databasePath 不能为空")
        self.databasePath = databasePath
        initializeDatabase(databasePath)

    def replaceChunks(self, chunks: list[MarkdownChunk], embeddings: dict[str, list[float]]) -> None:
        if any(chunk.id not in embeddings for chunk in chunks):
            raise ValueError("每个 chunk 都必须有 embedding")
        with connect(self.databasePath) as connection:
            connection.execute("DELETE FROM chunks")
            connection.executemany(
                """
                INSERT INTO chunks (
                    id, document_id, title, path, doc_type, tags, heading, content, embedding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.id,
                        chunk.documentId,
                        chunk.metadata.title,
                        chunk.metadata.path,
                        chunk.metadata.docType,
                        json.dumps(chunk.metadata.tags, ensure_ascii=False),
                        chunk.heading,
                        chunk.content,
                        json.dumps(embeddings[chunk.id]),
                    )
                    for chunk in chunks
                ],
            )

    def allChunks(self) -> list[dict]:
        with connect(self.databasePath) as connection:
            rows = connection.execute("SELECT * FROM chunks").fetchall()
        return [dict(row) for row in rows]

    def search(self, queryEmbedding: list[float], topK: int) -> list[tuple[dict, float]]:
        if topK < 1:
            raise ValueError("topK 必须大于 0")
        scored: list[tuple[dict, float]] = []
        for chunk in self.allChunks():
            embedding = json.loads(chunk["embedding"])
            scored.append((chunk, max(0.0, cosineSimilarity(queryEmbedding, embedding))))
        return sorted(scored, key=lambda item: item[1], reverse=True)[:topK]
