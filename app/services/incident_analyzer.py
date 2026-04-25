import re

from app.llm.answer_generator import AnswerGenerator, TemplateAnswerGenerator
from app.models.schemas import ExtractedEntities, IncidentAnalyzeDebug, IncidentAnalyzeRequest, QueryRewrite, RetrievalFilters, TroubleshootingResponse
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
    def __init__(self, retriever: HybridRetriever, topK: int, answerGenerator: AnswerGenerator | None = None) -> None:
        if topK < 1:
            raise ValueError("topK 必须大于 0")
        self.retriever = retriever
        self.topK = topK
        self.answerGenerator = answerGenerator or TemplateAnswerGenerator()

    def analyze(
        self,
        request: IncidentAnalyzeRequest,
    ) -> tuple[ExtractedEntities, QueryRewrite, TroubleshootingResponse]:
        validateIncidentInput(request)
        entities = extractEntities(request)
        rewrittenQuery = rewriteQuery(request, entities)
        results = self.retriever.search(rewrittenQuery, self.topK)
        answer = self.answerGenerator.generate(request, rewrittenQuery, results).answer
        return entities, rewrittenQuery, answer

    def analyzeWithDebug(
        self,
        request: IncidentAnalyzeRequest,
    ) -> tuple[ExtractedEntities, QueryRewrite, TroubleshootingResponse, IncidentAnalyzeDebug]:
        validateIncidentInput(request)
        entities = extractEntities(request)
        rewrittenQuery = rewriteQuery(request, entities)
        searchResult = self.retriever.searchWithDebug(rewrittenQuery, self.topK)
        answerResult = self.answerGenerator.generate(request, rewrittenQuery, searchResult.results)
        answer = answerResult.answer
        debug = IncidentAnalyzeDebug(
            entities=entities,
            rewrittenQuery=rewrittenQuery,
            retrieval=searchResult.debug,
            answerGeneration=answerResult.debug,
        )
        return entities, rewrittenQuery, answer, debug


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
