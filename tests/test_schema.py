import pytest

from app.models.schemas import Citation, IncidentAnalyzeRequest, TroubleshootingResponse
from app.services.incident_analyzer import extractEntities, rewriteQuery, validateIncidentInput


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
