import json
import re

from app.rag.bm25 import BM25Index
from app.rag.embedding import embedText
from app.rag.vector_store import SQLiteVectorStore

DEPENDENCY_TOKENS = {
    "redis",
    "postgres",
    "postgresql",
    "mysql",
    "mongodb",
    "kafka",
    "rabbitmq",
    "elasticsearch",
    "clickhouse",
}
ERROR_CODE_PATTERN = re.compile(r"\b(?:[45]\d{2}|[a-z][a-z0-9_-]{2,})\b")


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
        normalizedQuery = _normalizeText(query)
        vectorResults = self.vectorStore.search(embedText(normalizedQuery, self.dimension), topK * 3)
        bm25Results = BM25Index(chunks).search(query, topK * 2)
        return self._merge(vectorResults, bm25Results, normalizedQuery, topK)

    def _merge(
        self,
        vectorResults: list[tuple[dict, float]],
        bm25Results: list[tuple[dict, float]],
        normalizedQuery: str,
        topK: int,
    ) -> list[dict]:
        scores: dict[str, dict] = {}
        for chunk, score in vectorResults:
            scores[chunk["id"]] = {"chunk": chunk, "score": 0.55 * score}
        maxBm25 = max((score for _, score in bm25Results), default=0.0) or 1.0
        for chunk, score in bm25Results:
            item = scores.setdefault(chunk["id"], {"chunk": chunk, "score": 0.0})
            item["score"] += 0.45 * (score / maxBm25)
        for item in scores.values():
            item["score"] += _rerankBoost(item["chunk"], normalizedQuery)
        ranked = sorted(scores.values(), key=lambda item: item["score"], reverse=True)
        return [
            {**item["chunk"], "score": round(float(item["score"]), 4)}
            for item in ranked[:topK]
            if item["score"] > 0
        ]


def _rerankBoost(chunk: dict, normalizedQuery: str) -> float:
    boost = 0.0
    queryTokens = set(_queryTokens(normalizedQuery))
    chunkTokens = set(_queryTokens(_chunkSearchText(chunk)))
    service = _normalizeText(str(chunk.get("service", "")))
    heading = _normalizeText(str(chunk.get("heading", "")))
    docType = _normalizeText(str(chunk.get("doc_type", "")))
    headingLevel = int(chunk.get("heading_level", 0) or 0)
    if service and service in normalizedQuery:
        boost += 0.22
    if heading and any(token in heading for token in queryTokens):
        boost += 0.08
    errorCodes = set(ERROR_CODE_PATTERN.findall(normalizedQuery))
    if errorCodes:
        matchedCodes = sum(1 for code in errorCodes if code.lower() in chunkTokens)
        boost += min(0.24, matchedCodes * 0.12)
    dependencyMatches = len(_dependencyTokens(normalizedQuery) & chunkTokens)
    boost += min(0.18, dependencyMatches * 0.09)
    if docType == "runbook":
        boost += 0.04
    if headingLevel >= 2:
        boost += 0.06
    if headingLevel == 1:
        boost -= 0.08
    return boost


def _chunkSearchText(chunk: dict) -> str:
    tags = chunk.get("tags", "[]")
    if isinstance(tags, str):
        try:
            parsedTags = json.loads(tags)
        except json.JSONDecodeError:
            parsedTags = [tags]
    else:
        parsedTags = tags
    return " ".join(
        [
            str(chunk.get("title", "")),
            str(chunk.get("doc_type", "")),
            str(chunk.get("service", "")),
            str(chunk.get("heading", "")),
            " ".join(str(tag) for tag in parsedTags),
            str(chunk.get("content", "")),
        ]
    )


def _dependencyTokens(text: str) -> set[str]:
    return {token for token in _queryTokens(text) if token in DEPENDENCY_TOKENS}


def _queryTokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_][a-z0-9_\-.]*", _normalizeText(text))


def _normalizeText(text: str) -> str:
    return text.lower()
