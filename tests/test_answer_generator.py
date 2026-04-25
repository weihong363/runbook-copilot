import pytest

from app.llm.answer_generator import TemplateAnswerGenerator, _enforceCitationBinding, createAnswerGenerator
from app.llm.prompts import buildAnswerPrompt, getPromptDeveloperMessage
from app.models.schemas import Citation, IncidentAnalyzeRequest, TroubleshootingResponse
from app.services.incident_analyzer import extractEntities, rewriteQuery


def testTemplateAnswerGeneratorReturnsDebugMetadata() -> None:
    request = _request()
    rewrite = rewriteQuery(request, extractEntities(request))

    result = TemplateAnswerGenerator("grounded-v1").generate(request, rewrite, [_result("doc#1")])

    assert result.debug.provider == "template"
    assert result.debug.promptVersion == "grounded-v1"
    assert result.debug.usedLlm is False
    assert result.answer.citations[0].chunkId == "doc#1"


def testCreateAnswerGeneratorRejectsUnknownProvider() -> None:
    with pytest.raises(ValueError):
        createAnswerGenerator("unknown", "gpt-5.2", "grounded-v1")


def testPromptVersionMustBeKnown() -> None:
    with pytest.raises(ValueError):
        getPromptDeveloperMessage("missing-version")


def testBuildAnswerPromptIncludesCitationPayload() -> None:
    request = _request()
    rewrite = rewriteQuery(request, extractEntities(request))

    prompt = buildAnswerPrompt(request, rewrite, [_result("doc#1")])

    assert "checkout-api" in prompt
    assert "doc#1" in prompt
    assert "citations" in prompt


def testCitationBindingKeepsOnlyRetrievedChunks() -> None:
    answer = TroubleshootingResponse(
        summary="找到相关 runbook。",
        likelyCauses=["数据库连接池耗尽。"],
        steps=["检查连接池指标。"],
        citations=[
            Citation(
                chunkId="fake",
                title="伪造文档",
                path="knowledge/fake.md",
                heading="处理步骤",
                score=0.99,
                excerpt="不应保留。",
            )
        ],
        nextAction="打开 runbook 继续排查。",
    )

    bounded = _enforceCitationBinding(answer, [_result("doc#1"), _result("doc#2")])

    assert [citation.chunkId for citation in bounded.citations] == ["doc#1", "doc#2"]
    assert bounded.citations[0].path == "knowledge/runbook-checkout-api.md"


def _request() -> IncidentAnalyzeRequest:
    return IncidentAnalyzeRequest(
        alertTitle="checkout-api HTTP 500",
        serviceName="checkout-api",
        logSnippet="DB_POOL_EXHAUSTED timeout acquiring connection",
    )


def _result(chunkId: str) -> dict:
    return {
        "id": chunkId,
        "title": "checkout-api Runbook",
        "path": "knowledge/runbook-checkout-api.md",
        "heading": "处理步骤",
        "heading_level": 2,
        "score": 0.72,
        "content": "## 处理步骤\n出现 DB_POOL_EXHAUSTED 时检查连接池。",
    }
