import json
from pathlib import Path

from app.core.config import getSettings
from app.models.schemas import IncidentAnalyzeRequest
from app.rag.retriever import HybridRetriever
from app.rag.vector_store import SQLiteVectorStore
from app.services.incident_analyzer import IncidentAnalyzer


def evaluate(datasetPath: Path) -> list[dict]:
    if not datasetPath.exists():
        raise FileNotFoundError(f"评测集不存在: {datasetPath}")
    settings = getSettings()
    analyzer = IncidentAnalyzer(HybridRetriever(SQLiteVectorStore(settings.databasePath), settings.vectorDimension), settings.topK)
    results = []
    for line in datasetPath.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        request = IncidentAnalyzeRequest(**item["input"])
        _, _, answer = analyzer.analyze(request)
        expected = item.get("expectedCitationPath")
        hit = any(citation.path.endswith(expected) for citation in answer.citations) if expected else False
        results.append({"name": item.get("name", "case"), "hit": hit, "citations": [c.path for c in answer.citations]})
    return results


if __name__ == "__main__":
    for result in evaluate(Path("app/evaluation/sample_dataset.jsonl")):
        print(json.dumps(result, ensure_ascii=False))
