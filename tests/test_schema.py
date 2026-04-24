import pytest

from app.models.schemas import Citation, IncidentAnalyzeRequest, TroubleshootingResponse
from app.services.incident_analyzer import buildGroundedAnswer, extractEntities, rewriteQuery, validateIncidentInput


def testTroubleshootingResponseSchemaIsValid() -> None:
    response = TroubleshootingResponse(
        summary="找到相关 runbook。",
        likelyCauses=["数据库连接池耗尽。"],
        steps=["检查连接池指标。"],
        citations=[
            Citation(
                chunkId="doc#1",
                title="示例",
                path="knowledge/example.md",
                heading="处理步骤",
                score=0.9,
                excerpt="检查连接池。",
            )
        ],
        nextAction="打开 runbook 继续排查。",
    )

    assert response.citations[0].score == 0.9


def testExtractEntitiesIgnoresPlainHttpToken() -> None:
    request = IncidentAnalyzeRequest(
        alertTitle="checkout-api HTTP 500 错误率升高",
        serviceName="checkout-api",
        logSnippet="HTTP 500 DB_POOL_EXHAUSTED RedisTimeout timeout acquiring connection",
        symptomDescription="latest deployment 后 5xx increased",
    )

    entities = extractEntities(request)

    assert "HTTP" not in entities.errorCodes
    assert "500" in entities.errorCodes
    assert "DB_POOL_EXHAUSTED" in entities.errorCodes
    assert "redis" in entities.dependencies
    assert "RedisTimeout" in entities.exceptionTypes
    assert "5xx_spike" in entities.symptomTags


def testRewriteQueryReturnsStructuredQueries() -> None:
    request = IncidentAnalyzeRequest(
        alertTitle="order-service redis connection refused",
        serviceName="order-service",
        logSnippet="RedisConnectionError connection refused",
        symptomDescription="release 后 latency 增加",
    )

    entities = extractEntities(request)
    rewrite = rewriteQuery(request, entities)

    assert rewrite.filters.service == "order-service"
    assert "runbook" in rewrite.filters.docTypes
    assert "redis" in rewrite.keywordQuery.lower()
    assert "latency" in rewrite.semanticQuery.lower()


def testValidateIncidentInputRejectsNoiseLog() -> None:
    request = IncidentAnalyzeRequest(
        alertTitle="test",
        serviceName="svc",
        logSnippet="!!! ???",
    )

    with pytest.raises(ValueError):
        validateIncidentInput(request)


def testBuildGroundedAnswerReturnsUncertainSummaryForWeakEvidence() -> None:
    request = IncidentAnalyzeRequest(
        alertTitle="order-service redis refused",
        serviceName="order-service",
        logSnippet="connection refused after deploy",
    )
    rewrite = rewriteQuery(request, extractEntities(request))
    results = [
        {
            "id": "doc#1",
            "title": "示例文档",
            "path": "knowledge/example.md",
            "heading": "背景说明",
            "heading_level": 1,
            "score": 0.18,
            "content": "# 背景说明\n这里只是相邻场景线索。",
        }
    ]

    answer = buildGroundedAnswer(request, rewrite, results)

    assert "证据还不足以直接下结论" in answer.summary
    assert "暂时不能确认根因" in answer.likelyCauses[0]
    assert "不要直接把它当作已确认根因" in answer.steps[2]


def testBuildGroundedAnswerUsesStableCitationExcerpt() -> None:
    request = IncidentAnalyzeRequest(
        alertTitle="checkout-api HTTP 500",
        serviceName="checkout-api",
        logSnippet="DB_POOL_EXHAUSTED timeout acquiring connection",
    )
    rewrite = rewriteQuery(request, extractEntities(request))
    results = [
        {
            "id": "doc#2",
            "title": "checkout-api Runbook",
            "path": "knowledge/runbook-checkout-api.md",
            "heading": "处理步骤",
            "heading_level": 2,
            "score": 0.62,
            "content": "## 处理步骤\n1. 检查连接池。\n2. 检查活跃连接。\n",
        }
    ]

    answer = buildGroundedAnswer(request, rewrite, results)

    assert answer.citations[0].excerpt.startswith("1. 检查连接池。")
    assert "## 处理步骤" not in answer.citations[0].excerpt
