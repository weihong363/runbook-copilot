import re

from app.models.schemas import (
    Citation,
    ExtractedEntities,
    IncidentAnalyzeRequest,
    QueryRewrite,
    RetrievalFilters,
    TroubleshootingResponse,
)
from app.rag.retriever import HybridRetriever
from app.rag.tokenizer import tokenize

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
ERROR_PATTERN = re.compile(r"\b(?:[A-Z][A-Z0-9_]{2,}|HTTP\s?[45]\d{2}|[45]\d{2})\b")
EXCEPTION_PATTERN = re.compile(r"\b[A-Z][A-Za-z0-9]+(?:Exception|Error|Timeout)\b")


class IncidentAnalyzer:
    def __init__(self, retriever: HybridRetriever, topK: int) -> None:
        if topK < 1:
            raise ValueError("topK 必须大于 0")
        self.retriever = retriever
        self.topK = topK

    def analyze(
        self,
        request: IncidentAnalyzeRequest,
    ) -> tuple[ExtractedEntities, QueryRewrite, TroubleshootingResponse]:
        validateIncidentInput(request)
        entities = extractEntities(request)
        rewrittenQuery = rewriteQuery(request, entities)
        results = self.retriever.search(rewrittenQuery, self.topK)
        answer = buildGroundedAnswer(request, results)
        return entities, rewrittenQuery, answer


def validateIncidentInput(request: IncidentAnalyzeRequest) -> None:
    tokens = tokenize(" ".join(filter(None, [request.alertTitle, request.serviceName, request.logSnippet])))
    signalTokens = [token for token in tokens if len(token) > 1 and token not in {"error", "alert", "warn"}]
    if len(signalTokens) < 3:
        raise ValueError("输入信息过少，请提供更具体的告警标题、服务名或日志片段。")
    if _looksLikeNoise(request.logSnippet):
        raise ValueError("日志片段缺少可识别信号，请提供包含错误码、异常名或依赖信息的日志。")


def extractEntities(request: IncidentAnalyzeRequest) -> ExtractedEntities:
    text = " ".join(
        value for value in [request.alertTitle, request.serviceName, request.logSnippet, request.symptomDescription] if value
    )
    errorCodes = sorted(set(ERROR_PATTERN.findall(text)) - {"HTTP", "HTTPS"})
    dependencies = _extractDependencies(text)
    exceptionTypes = sorted(set(EXCEPTION_PATTERN.findall(text)))
    symptomTags = _extractSymptomTags(text)
    keywords = _topKeywords(text, request.serviceName, ignored=set(dependencies))
    return ExtractedEntities(
        service=request.serviceName,
        dependencies=dependencies,
        exceptionTypes=exceptionTypes,
        errorCodes=errorCodes,
        keywords=keywords,
        symptomTags=symptomTags,
    )


def rewriteQuery(request: IncidentAnalyzeRequest, entities: ExtractedEntities) -> QueryRewrite:
    keywordParts = [
        request.serviceName,
        request.alertTitle,
        " ".join(entities.dependencies),
        " ".join(entities.exceptionTypes),
        " ".join(entities.errorCodes),
        " ".join(entities.keywords[:6]),
        " ".join(entities.symptomTags),
    ]
    semanticParts = [
        request.alertTitle,
        request.serviceName,
        request.symptomDescription or "",
        request.logSnippet[:500],
    ]
    return QueryRewrite(
        keywordQuery=" ".join(part for part in keywordParts if part.strip()),
        semanticQuery=" ".join(part for part in semanticParts if part.strip()),
        filters=RetrievalFilters(
            service=request.serviceName,
            docTypes=["runbook", "incident"],
            dependencies=entities.dependencies,
            errorCodes=entities.errorCodes,
        ),
    )


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


def _topKeywords(text: str, serviceName: str, ignored: set[str] | None = None) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_\-.]{2,}", text.lower())
    ignoredWords = {serviceName.lower(), "error", "failed", "exception", "alert", "http"}
    if ignored:
        ignoredWords.update(ignored)
    unique: list[str] = []
    for word in words:
        if word in ignoredWords or word in unique:
            continue
        unique.append(word)
    return unique[:8]


def _extractSymptomTags(text: str) -> list[str]:
    lowered = text.lower()
    tags = []
    for tag, patterns in {
        "5xx_spike": ["5xx", "http 500", "error spike"],
        "timeout": ["timeout", "timed out", "deadline exceeded"],
        "connection_refused": ["connection refused", "refused"],
        "latency": ["latency", "slow response", "slow query"],
        "post_deploy": ["deployment", "release", "rollout"],
        "resource_saturation": ["exhausted", "connection pool", "slots are reserved"],
    }.items():
        if any(pattern in lowered for pattern in patterns):
            tags.append(tag)
    return tags


def _extractDependencies(text: str) -> list[str]:
    lowered = text.lower()
    return [dependency for dependency in sorted(DEPENDENCY_TOKENS) if dependency in lowered]


def _looksLikeNoise(logSnippet: str) -> bool:
    tokens = tokenize(logSnippet)
    if len(tokens) < 2:
        return True
    alnumTokens = [token for token in tokens if re.search(r"[A-Za-z0-9\u4e00-\u9fff]", token)]
    return len(alnumTokens) < 2


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
