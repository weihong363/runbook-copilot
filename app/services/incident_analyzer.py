import re

from app.models.schemas import Citation, ExtractedEntities, IncidentAnalyzeRequest, TroubleshootingResponse
from app.rag.retriever import HybridRetriever


ERROR_PATTERN = re.compile(r"\b(?:[A-Z][A-Z0-9_]{2,}|HTTP\s?[45]\d{2}|[45]\d{2})\b")


class IncidentAnalyzer:
    def __init__(self, retriever: HybridRetriever, topK: int) -> None:
        if topK < 1:
            raise ValueError("topK 必须大于 0")
        self.retriever = retriever
        self.topK = topK

    def analyze(self, request: IncidentAnalyzeRequest) -> tuple[ExtractedEntities, str, TroubleshootingResponse]:
        entities = extractEntities(request)
        rewrittenQuery = rewriteQuery(request, entities)
        results = self.retriever.search(rewrittenQuery, self.topK)
        answer = buildGroundedAnswer(request, results)
        return entities, rewrittenQuery, answer


def extractEntities(request: IncidentAnalyzeRequest) -> ExtractedEntities:
    text = " ".join(
        value for value in [request.alertTitle, request.serviceName, request.logSnippet, request.symptomDescription] if value
    )
    errorCodes = sorted(set(ERROR_PATTERN.findall(text)) - {"HTTP", "HTTPS"})
    keywords = _topKeywords(text, request.serviceName)
    return ExtractedEntities(service=request.serviceName, errorCodes=errorCodes, keywords=keywords)


def rewriteQuery(request: IncidentAnalyzeRequest, entities: ExtractedEntities) -> str:
    parts = [
        request.serviceName,
        request.alertTitle,
        " ".join(entities.errorCodes),
        " ".join(entities.keywords),
        request.symptomDescription or "",
        request.logSnippet[:800],
    ]
    return " ".join(part for part in parts if part.strip())


def buildGroundedAnswer(request: IncidentAnalyzeRequest, results: list[dict]) -> TroubleshootingResponse:
    citations = [_toCitation(result) for result in results]
    if not citations:
        return TroubleshootingResponse(
            summary=f"未在本地知识库中找到与 {request.serviceName} / {request.alertTitle} 明确相关的资料。",
            likelyCauses=["知识库缺少相关 runbook，或告警信息不足以命中已有文档。"],
            steps=[
                "补充更完整的错误日志、时间范围和受影响实例。",
                "确认知识库已执行 /api/knowledge/ingest。",
                "将本次排障结论沉淀为 markdown runbook 后重新入库。",
            ],
            citations=[],
            nextAction="先检查知识库是否已导入，并补充该服务的 runbook。",
        )
    top = citations[0]
    return TroubleshootingResponse(
        summary=f"最相关资料是《{top.title}》的“{top.heading}”，可作为本次排障起点。",
        likelyCauses=_likelyCauses(results),
        steps=_steps(results),
        citations=citations,
        nextAction=f"优先打开 {top.path}，按“{top.heading}”中的检查项验证。",
    )


def _topKeywords(text: str, serviceName: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_\-.]{2,}", text.lower())
    ignored = {serviceName.lower(), "error", "failed", "exception", "alert"}
    unique = []
    for word in words:
        if word in ignored or word in unique:
            continue
        unique.append(word)
    return unique[:8]


def _toCitation(result: dict) -> Citation:
    excerpt = result["content"].replace("\n", " ")[:260]
    return Citation(
        chunkId=result["id"],
        title=result["title"],
        path=result["path"],
        heading=result["heading"],
        score=float(result["score"]),
        excerpt=excerpt,
    )


def _likelyCauses(results: list[dict]) -> list[str]:
    causes = []
    for result in results[:3]:
        causes.append(f"可能与《{result['title']}》中“{result['heading']}”描述的场景相关。")
    return causes


def _steps(results: list[dict]) -> list[str]:
    steps = ["确认告警时间窗口、影响范围和最近发布记录。"]
    for result in results[:3]:
        steps.append(f"参考《{result['title']}》/{result['heading']}，执行其中的检查或回滚步骤。")
    steps.append("记录最终根因和修复动作，补充到对应 runbook。")
    return steps
