import json
from pathlib import Path
from typing import Any, TypedDict

from app.core.config import getSettings
from app.models.schemas import IncidentAnalyzeRequest, TroubleshootingResponse
from app.rag.ingestion import ingestKnowledge
from app.rag.retriever import HybridRetriever
from app.rag.vector_store import SQLiteVectorStore
from app.services.incident_analyzer import IncidentAnalyzer


class EvaluationCase(TypedDict):
    name: str
    hitAt3: bool
    hitAt5: bool
    citationRelevant: bool
    schemaValid: bool
    keywordCoverage: float
    expectedCitationPath: str
    actualCitationPaths: list[str]
    rewrittenKeywordQuery: str
    rewrittenSemanticQuery: str


class EvaluationSummary(TypedDict):
    datasetPath: str
    totalCases: int
    hitAt3: float
    hitAt5: float
    citationRelevance: float
    schemaValidity: float
    keywordCoverage: float


class EvaluationReport(TypedDict):
    summary: EvaluationSummary
    cases: list[EvaluationCase]


def evaluate(datasetPath: Path) -> EvaluationReport:
    if not datasetPath.exists():
        raise FileNotFoundError(f"评测集不存在: {datasetPath}")
    settings = getSettings()
    store = SQLiteVectorStore(settings.databasePath)
    ingestKnowledge(settings.knowledgeDir, store, settings.vectorDimension)
    analyzer = IncidentAnalyzer(HybridRetriever(store, settings.vectorDimension), settings.topK)
    cases = [_evaluateCase(json.loads(line), analyzer) for line in _datasetLines(datasetPath)]
    return {
        "summary": _buildSummary(datasetPath, cases),
        "cases": cases,
    }


def _evaluateCase(item: dict[str, Any], analyzer: IncidentAnalyzer) -> EvaluationCase:
    request = IncidentAnalyzeRequest(**item["input"])
    _, rewrittenQuery, answer = analyzer.analyze(request)
    TroubleshootingResponse.model_validate(answer.model_dump())
    expectedPath = item["expectedCitationPath"]
    actualPaths = [citation.path for citation in answer.citations]
    expectedKeywords = [keyword.lower() for keyword in item.get("expectedKeywords", [])]
    keywordQuery = rewrittenQuery.keywordQuery.lower()
    return {
        "name": item.get("name", "case"),
        "hitAt3": _pathHit(expectedPath, actualPaths[:3]),
        "hitAt5": _pathHit(expectedPath, actualPaths[:5]),
        "citationRelevant": _pathHit(expectedPath, actualPaths[:1]),
        "schemaValid": True,
        "keywordCoverage": _keywordCoverage(expectedKeywords, keywordQuery),
        "expectedCitationPath": expectedPath,
        "actualCitationPaths": actualPaths,
        "rewrittenKeywordQuery": rewrittenQuery.keywordQuery,
        "rewrittenSemanticQuery": rewrittenQuery.semanticQuery,
    }


def _buildSummary(datasetPath: Path, cases: list[EvaluationCase]) -> EvaluationSummary:
    total = max(1, len(cases))
    return {
        "datasetPath": str(datasetPath),
        "totalCases": len(cases),
        "hitAt3": round(sum(1 for case in cases if case["hitAt3"]) / total, 4),
        "hitAt5": round(sum(1 for case in cases if case["hitAt5"]) / total, 4),
        "citationRelevance": round(sum(1 for case in cases if case["citationRelevant"]) / total, 4),
        "schemaValidity": round(sum(1 for case in cases if case["schemaValid"]) / total, 4),
        "keywordCoverage": round(sum(case["keywordCoverage"] for case in cases) / total, 4),
    }


def _datasetLines(datasetPath: Path) -> list[str]:
    return [line for line in datasetPath.read_text(encoding="utf-8").splitlines() if line.strip()]


def _pathHit(expectedPath: str, actualPaths: list[str]) -> bool:
    return any(path.endswith(expectedPath) for path in actualPaths)


def _keywordCoverage(expectedKeywords: list[str], keywordQuery: str) -> float:
    if not expectedKeywords:
        return 1.0
    hits = sum(1 for keyword in expectedKeywords if keyword in keywordQuery)
    return round(hits / len(expectedKeywords), 4)


if __name__ == "__main__":
    report = evaluate(Path("app/evaluation/sample_dataset.jsonl"))
    print(json.dumps(report, ensure_ascii=False, indent=2))
