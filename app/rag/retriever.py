from app.rag.bm25 import BM25Index
from app.rag.embedding import embedText
from app.rag.vector_store import SQLiteVectorStore


class HybridRetriever:
    def __init__(self, vectorStore: SQLiteVectorStore, dimension: int) -> None:
        if dimension < 16:
            raise ValueError("dimension 至少为 16")
        self.vectorStore = vectorStore
        self.dimension = dimension

    def search(self, query: str, topK: int) -> list[dict]:
        if not query.strip():
            raise ValueError("query 不能为空")
        chunks = self.vectorStore.allChunks()
        if not chunks:
            return []
        vectorResults = self.vectorStore.search(embedText(query, self.dimension), topK * 2)
        bm25Results = BM25Index(chunks).search(query, topK * 2)
        return self._merge(vectorResults, bm25Results, topK)

    def _merge(
        self,
        vectorResults: list[tuple[dict, float]],
        bm25Results: list[tuple[dict, float]],
        topK: int,
    ) -> list[dict]:
        scores: dict[str, dict] = {}
        for chunk, score in vectorResults:
            scores[chunk["id"]] = {"chunk": chunk, "score": 0.6 * score}
        maxBm25 = max((score for _, score in bm25Results), default=0.0) or 1.0
        for chunk, score in bm25Results:
            item = scores.setdefault(chunk["id"], {"chunk": chunk, "score": 0.0})
            item["score"] += 0.4 * (score / maxBm25)
        ranked = sorted(scores.values(), key=lambda item: item["score"], reverse=True)
        return [
            {**item["chunk"], "score": round(float(item["score"]), 4)}
            for item in ranked[:topK]
            if item["score"] > 0
        ]
