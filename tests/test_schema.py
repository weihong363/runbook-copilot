from app.models.schemas import Citation, TroubleshootingResponse
from app.models.schemas import IncidentAnalyzeRequest
from app.services.incident_analyzer import extractEntities


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
        logSnippet="HTTP 500 DB_POOL_EXHAUSTED timeout acquiring connection",
    )

    entities = extractEntities(request)

    assert "HTTP" not in entities.errorCodes
    assert "500" in entities.errorCodes
    assert "DB_POOL_EXHAUSTED" in entities.errorCodes
