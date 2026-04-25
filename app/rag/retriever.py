from dataclasses import dataclass
import json
import re

from app.models.schemas import QueryRewrite, RetrievalDebug, RetrievalDebugItem
from app.rag.bm25 import BM25Index
from app.rag.embedding import cosineSimilarity
from app.rag.embedding_provider import EmbeddingProvider, HashEmbeddingProvider
from app.rag.vector_store import VectorStore

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


@dataclass(frozen=True)
class SearchResult:
    results: list[dict]
    debug: RetrievalDebug


@dataclass(frozen=True)
class FilterResult:
    chunks: list[dict]
    stages: list[str]


class HybridRetriever:
    def __init__(self, vectorStore: VectorStore, dimensionOrProvider: int | EmbeddingProvider) -> None:
        self.vectorStore = vectorStore
        if isinstance(dimensionOrProvider, int):
            self.embeddingProvider = HashEmbeddingProvider(dimensionOrProvider)
        else:
            self.embeddingProvider = dimensionOrProvider

    def search(self, query: str | QueryRewrite, topK: int) -> list[dict]:
        return self.searchWithDebug(query, topK).results

    def searchWithDebug(self, query: str | QueryRewrite, topK: int) -> SearchResult:
        if topK < 1:
            raise ValueError("topK 必须大于 0")
        queryBundle = _ensureQueryRewrite(query)
        if not queryBundle.keywordQuery.strip() and not queryBundle.semanticQuery.strip():
            raise ValueError("query 不能为空")
        allChunks = self.vectorStore.allChunks()
        filterResult = _applyStageFilters(allChunks, queryBundle)
        chunks = filterResult.chunks
        if not chunks:
            return SearchResult(
                results=[],
                debug=RetrievalDebug(
                    totalChunks=len(allChunks),
                    filteredChunks=0,
                    appliedFilters=queryBundle.filters,
                    stages=filterResult.stages,
                    candidates=[],
                ),
            )
        vectorResults = _vectorSearch(chunks, queryBundle.semanticQuery, topK * 4, self.embeddingProvider)
        bm25Results = BM25Index(chunks).search(queryBundle.keywordQuery, topK * 4)
        return self._merge(
            vectorResults,
            bm25Results,
            queryBundle,
            topK,
            len(allChunks),
            len(chunks),
            filterResult.stages,
        )

    def _merge(
        self,
        vectorResults: list[tuple[dict, float]],
        bm25Results: list[tuple[dict, float]],
        queryBundle: QueryRewrite,
        topK: int,
        totalChunks: int,
        filteredChunks: int,
        stages: list[str],
    ) -> SearchResult:
        scores: dict[str, dict] = {}
        normalizedQuery = _normalizeText(f"{queryBundle.keywordQuery} {queryBundle.semanticQuery}")
        for chunk, score in vectorResults:
            scores[chunk["id"]] = {
                "chunk": chunk,
                "vectorScore": score,
                "bm25Score": 0.0,
                "bm25Normalized": 0.0,
            }
        maxBm25 = max((score for _, score in bm25Results), default=0.0) or 1.0
        for chunk, score in bm25Results:
            item = scores.setdefault(
                chunk["id"],
                {"chunk": chunk, "vectorScore": 0.0, "bm25Score": 0.0, "bm25Normalized": 0.0},
            )
            item["bm25Score"] = score
            item["bm25Normalized"] = score / maxBm25
        for item in scores.values():
            boost, reasons = _rerankBreakdown(item["chunk"], normalizedQuery, queryBundle)
            item["rerankBoost"] = boost
            item["rerankReasons"] = reasons
            item["score"] = (0.55 * item["vectorScore"]) + (0.45 * item["bm25Normalized"]) + boost
        ranked = sorted(scores.values(), key=lambda item: item["score"], reverse=True)
        results = [
            {**item["chunk"], "score": round(float(item["score"]), 4)}
            for item in ranked[:topK]
            if item["score"] > 0
        ]
        debugItems = [_toDebugItem(item) for item in ranked[: max(topK, 5)] if item["score"] > 0]
        return SearchResult(
            results=results,
            debug=RetrievalDebug(
                totalChunks=totalChunks,
                filteredChunks=filteredChunks,
                appliedFilters=queryBundle.filters,
                stages=stages,
                candidates=debugItems,
            ),
        )


def _ensureQueryRewrite(query: str | QueryRewrite) -> QueryRewrite:
    if isinstance(query, QueryRewrite):
        return query
    normalized = str(query).strip()
    return QueryRewrite(keywordQuery=normalized, semanticQuery=normalized, filters={})


def _applyFilters(chunks: list[dict], queryBundle: QueryRewrite) -> list[dict]:
    return _applyStageFilters(chunks, queryBundle).chunks


def _applyStageFilters(chunks: list[dict], queryBundle: QueryRewrite) -> FilterResult:
    filtered = chunks
    stages = [f"start:{len(chunks)}"]
    service = _normalizeText(queryBundle.filters.service or "")
    if service:
        matching = [chunk for chunk in filtered if _normalizeText(str(chunk.get("service", ""))) == service]
        if matching:
            filtered = matching
            stages.append(f"service_exact:{service}:{len(filtered)}")
        else:
            stages.append(f"service_exact:{service}:fallback")
    docTypes = {_normalizeText(docType) for docType in queryBundle.filters.docTypes}
    if docTypes:
        matching = [chunk for chunk in filtered if _normalizeText(str(chunk.get("doc_type", ""))) in docTypes]
        if matching:
            filtered = matching
            stages.append(f"doc_type:{','.join(sorted(docTypes))}:{len(filtered)}")
        else:
            stages.append(f"doc_type:{','.join(sorted(docTypes))}:fallback")
    return FilterResult(chunks=filtered, stages=stages)


def _vectorSearch(
    chunks: list[dict],
    semanticQuery: str,
    topK: int,
    embeddingProvider: EmbeddingProvider,
) -> list[tuple[dict, float]]:
    if not semanticQuery.strip():
        return []
    queryEmbedding = embeddingProvider.embed(_normalizeText(semanticQuery))
    scored: list[tuple[dict, float]] = []
    for chunk in chunks:
        embedding = json.loads(chunk["embedding"])
        score = max(0.0, cosineSimilarity(queryEmbedding, embedding))
        scored.append((chunk, score))
    return sorted(scored, key=lambda item: item[1], reverse=True)[:topK]


def _rerankBoost(chunk: dict, normalizedQuery: str, queryBundle: QueryRewrite) -> float:
    boost, _ = _rerankBreakdown(chunk, normalizedQuery, queryBundle)
    return boost


def _rerankBreakdown(chunk: dict, normalizedQuery: str, queryBundle: QueryRewrite) -> tuple[float, list[str]]:
    boost = 0.0
    reasons: list[str] = []
    queryTokens = set(_queryTokens(normalizedQuery))
    chunkTokens = set(_queryTokens(_chunkSearchText(chunk)))
    chunkText = _normalizeText(_chunkSearchText(chunk))
    service = _normalizeText(str(chunk.get("service", "")))
    heading = _normalizeText(str(chunk.get("heading", "")))
    docType = _normalizeText(str(chunk.get("doc_type", "")))
    headingLevel = int(chunk.get("heading_level", 0) or 0)
    if service and service in normalizedQuery:
        boost += 0.25
        reasons.append("service_match:+0.25")
    if heading and any(token in heading for token in queryTokens):
        boost += 0.08
        reasons.append("heading_token_match:+0.08")
    if heading and heading in normalizedQuery:
        boost += 0.05
        reasons.append("heading_phrase_match:+0.05")
    matchedCodes = sum(1 for code in queryBundle.filters.errorCodes if code.lower() in chunkTokens)
    codeBoost = min(0.28, matchedCodes * 0.14)
    if codeBoost:
        boost += codeBoost
        reasons.append(f"error_code_match:+{codeBoost:.2f}")
    matchedDependencies = sum(1 for dependency in queryBundle.filters.dependencies if dependency in chunkTokens)
    dependencyBoost = min(0.2, matchedDependencies * 0.10)
    if dependencyBoost:
        boost += dependencyBoost
        reasons.append(f"dependency_match:+{dependencyBoost:.2f}")
    tagMatches = _tagMatches(chunk, queryTokens)
    tagBoost = min(0.12, len(tagMatches) * 0.04)
    if tagBoost:
        boost += tagBoost
        reasons.append(f"tag_match:{','.join(tagMatches)}:+{tagBoost:.2f}")
    phraseMatches = _phraseMatches(normalizedQuery, chunkText)
    phraseBoost = min(0.1, len(phraseMatches) * 0.05)
    if phraseBoost:
        boost += phraseBoost
        reasons.append(f"phrase_match:+{phraseBoost:.2f}")
    requestedDocTypes = {_normalizeText(docType) for docType in queryBundle.filters.docTypes}
    if requestedDocTypes and docType in requestedDocTypes:
        boost += 0.06
        reasons.append(f"requested_doc_type:{docType}:+0.06")
    if docType == "runbook":
        boost += 0.03
        reasons.append("runbook_doc:+0.03")
    if headingLevel >= 2:
        boost += 0.06
        reasons.append("section_chunk:+0.06")
    if headingLevel == 1:
        boost -= 0.1
        reasons.append("title_chunk:-0.10")
    return boost, reasons


def _tagMatches(chunk: dict, queryTokens: set[str]) -> list[str]:
    tags = _parseTags(chunk.get("tags", "[]"))
    return sorted(tag for tag in tags if tag in queryTokens)


def _phraseMatches(normalizedQuery: str, chunkText: str) -> list[str]:
    tokens = _queryTokens(normalizedQuery)
    phrases: list[str] = []
    for size in [4, 3, 2]:
        for index in range(0, max(0, len(tokens) - size + 1)):
            phrase = " ".join(tokens[index : index + size])
            if len(phrase) < 8 or phrase in phrases:
                continue
            if phrase in chunkText:
                phrases.append(phrase)
    return phrases[:3]


def _toDebugItem(item: dict) -> RetrievalDebugItem:
    chunk = item["chunk"]
    return RetrievalDebugItem(
        chunkId=str(chunk["id"]),
        title=str(chunk["title"]),
        path=str(chunk["path"]),
        heading=str(chunk["heading"]),
        docType=str(chunk["doc_type"]),
        service=str(chunk.get("service", "")),
        vectorScore=round(float(item["vectorScore"]), 4),
        bm25Score=round(float(item["bm25Score"]), 4),
        bm25Normalized=round(float(item["bm25Normalized"]), 4),
        rerankBoost=round(float(item["rerankBoost"]), 4),
        finalScore=round(float(item["score"]), 4),
        rerankReasons=list(item["rerankReasons"]),
    )


def _chunkSearchText(chunk: dict) -> str:
    parsedTags = _parseTags(chunk.get("tags", "[]"))
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


def _parseTags(tags: object) -> list[str]:
    if isinstance(tags, str):
        try:
            parsed = json.loads(tags)
        except json.JSONDecodeError:
            parsed = [tags]
    else:
        parsed = tags
    return [_normalizeText(str(tag)) for tag in parsed]


def _queryTokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_][a-z0-9_\-.]*", _normalizeText(text))


def _normalizeText(text: str) -> str:
    return text.lower()
