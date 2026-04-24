import json
import re

from app.models.schemas import QueryRewrite
from app.rag.bm25 import BM25Index
from app.rag.embedding import cosineSimilarity, embedText
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

    def search(self, query: str | QueryRewrite, topK: int) -> list[dict]:
        if topK < 1:
            raise ValueError("topK 必须大于 0")
        queryBundle = _ensureQueryRewrite(query)
        if not queryBundle.keywordQuery.strip() and not queryBundle.semanticQuery.strip():
            raise ValueError("query 不能为空")
        chunks = _applyFilters(self.vectorStore.allChunks(), queryBundle)
        if not chunks:
            return []
        vectorResults = _vectorSearch(chunks, queryBundle.semanticQuery, topK * 3, self.dimension)
        bm25Results = BM25Index(chunks).search(queryBundle.keywordQuery, topK * 2)
        return self._merge(vectorResults, bm25Results, queryBundle, topK)

    def _merge(
        self,
        vectorResults: list[tuple[dict, float]],
        bm25Results: list[tuple[dict, float]],
        queryBundle: QueryRewrite,
        topK: int,
    ) -> list[dict]:
        scores: dict[str, dict] = {}
        normalizedQuery = _normalizeText(f"{queryBundle.keywordQuery} {queryBundle.semanticQuery}")
        for chunk, score in vectorResults:
            scores[chunk["id"]] = {"chunk": chunk, "score": 0.55 * score}
        maxBm25 = max((score for _, score in bm25Results), default=0.0) or 1.0
        for chunk, score in bm25Results:
            item = scores.setdefault(chunk["id"], {"chunk": chunk, "score": 0.0})
            item["score"] += 0.45 * (score / maxBm25)
        for item in scores.values():
            item["score"] += _rerankBoost(item["chunk"], normalizedQuery, queryBundle)
        ranked = sorted(scores.values(), key=lambda item: item["score"], reverse=True)
        return [
            {**item["chunk"], "score": round(float(item["score"]), 4)}
            for item in ranked[:topK]
            if item["score"] > 0
        ]


def _ensureQueryRewrite(query: str | QueryRewrite) -> QueryRewrite:
    if isinstance(query, QueryRewrite):
        return query
    normalized = str(query).strip()
    return QueryRewrite(keywordQuery=normalized, semanticQuery=normalized, filters={})


def _applyFilters(chunks: list[dict], queryBundle: QueryRewrite) -> list[dict]:
    filtered = chunks
    service = _normalizeText(queryBundle.filters.service or "")
    if service:
        matching = [chunk for chunk in filtered if _normalizeText(str(chunk.get("service", ""))) == service]
        if matching:
            filtered = matching
    docTypes = {_normalizeText(docType) for docType in queryBundle.filters.docTypes}
    if docTypes:
        matching = [chunk for chunk in filtered if _normalizeText(str(chunk.get("doc_type", ""))) in docTypes]
        if matching:
            filtered = matching
    return filtered


def _vectorSearch(
    chunks: list[dict],
    semanticQuery: str,
    topK: int,
    dimension: int,
) -> list[tuple[dict, float]]:
    if not semanticQuery.strip():
        return []
    queryEmbedding = embedText(_normalizeText(semanticQuery), dimension)
    scored: list[tuple[dict, float]] = []
    for chunk in chunks:
        embedding = json.loads(chunk["embedding"])
        score = max(0.0, cosineSimilarity(queryEmbedding, embedding))
        scored.append((chunk, score))
    return sorted(scored, key=lambda item: item[1], reverse=True)[:topK]


def _rerankBoost(chunk: dict, normalizedQuery: str, queryBundle: QueryRewrite) -> float:
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
    matchedCodes = sum(1 for code in queryBundle.filters.errorCodes if code.lower() in chunkTokens)
    boost += min(0.24, matchedCodes * 0.12)
    matchedDependencies = sum(1 for dependency in queryBundle.filters.dependencies if dependency in chunkTokens)
    boost += min(0.18, matchedDependencies * 0.09)
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


def _queryTokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_][a-z0-9_\-.]*", _normalizeText(text))


def _normalizeText(text: str) -> str:
    return text.lower()
