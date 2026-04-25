import json
from dataclasses import dataclass
from typing import Protocol

from app.llm.grounded_answer import buildGroundedAnswer, toCitation
from app.llm.prompts import buildAnswerPrompt, getPromptDeveloperMessage
from app.models.schemas import AnswerGenerationDebug, IncidentAnalyzeRequest, QueryRewrite, TroubleshootingResponse


@dataclass(frozen=True)
class AnswerGenerationResult:
    answer: TroubleshootingResponse
    debug: AnswerGenerationDebug


class AnswerGenerator(Protocol):
    def generate(
        self,
        request: IncidentAnalyzeRequest,
        rewrittenQuery: QueryRewrite,
        results: list[dict],
    ) -> AnswerGenerationResult:
        raise NotImplementedError


class TemplateAnswerGenerator:
    def __init__(self, promptVersion: str = "template-v1") -> None:
        self.promptVersion = promptVersion

    def generate(
        self,
        request: IncidentAnalyzeRequest,
        rewrittenQuery: QueryRewrite,
        results: list[dict],
    ) -> AnswerGenerationResult:
        return AnswerGenerationResult(
            answer=buildGroundedAnswer(request, rewrittenQuery, results),
            debug=AnswerGenerationDebug(
                provider="template",
                promptVersion=self.promptVersion,
                usedLlm=False,
                warnings=[],
            ),
        )


class OpenAIAnswerGenerator:
    def __init__(self, model: str, promptVersion: str) -> None:
        if not model.strip():
            raise ValueError("model 不能为空")
        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError("未安装 openai，无法使用 ANSWER_GENERATOR=openai。") from error
        self.client = OpenAI()
        self.model = model
        self.promptVersion = promptVersion

    def generate(
        self,
        request: IncidentAnalyzeRequest,
        rewrittenQuery: QueryRewrite,
        results: list[dict],
    ) -> AnswerGenerationResult:
        if not results:
            return TemplateAnswerGenerator(self.promptVersion).generate(request, rewrittenQuery, results)
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": getPromptDeveloperMessage(self.promptVersion),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": buildAnswerPrompt(request, rewrittenQuery, results),
                        }
                    ],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "troubleshooting_response",
                    "strict": True,
                    "schema": _responseSchema(),
                }
            },
        )
        answer = TroubleshootingResponse.model_validate(json.loads(response.output_text))
        return AnswerGenerationResult(
            answer=_enforceCitationBinding(answer, results),
            debug=AnswerGenerationDebug(
                provider="openai",
                promptVersion=self.promptVersion,
                usedLlm=True,
                warnings=[],
            ),
        )


def createAnswerGenerator(provider: str, model: str, promptVersion: str) -> AnswerGenerator:
    normalized = provider.strip().lower()
    if normalized == "template":
        return TemplateAnswerGenerator(promptVersion)
    if normalized == "openai":
        return OpenAIAnswerGenerator(model, promptVersion)
    raise ValueError(f"不支持的 answer generator: {provider}")


def _enforceCitationBinding(answer: TroubleshootingResponse, results: list[dict]) -> TroubleshootingResponse:
    allowed = {str(result["id"]): toCitation(result) for result in results[:5]}
    boundedCitations = [allowed[citation.chunkId] for citation in answer.citations if citation.chunkId in allowed]
    if not boundedCitations:
        boundedCitations = list(allowed.values())[:3]
    return TroubleshootingResponse(
        summary=answer.summary,
        likelyCauses=answer.likelyCauses,
        steps=answer.steps,
        citations=boundedCitations,
        nextAction=answer.nextAction,
    )


def _responseSchema() -> dict:
    citationSchema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "chunkId": {"type": "string"},
            "title": {"type": "string"},
            "path": {"type": "string"},
            "heading": {"type": "string"},
            "score": {"type": "number"},
            "excerpt": {"type": "string"},
        },
        "required": ["chunkId", "title", "path", "heading", "score", "excerpt"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "likelyCauses": {"type": "array", "items": {"type": "string"}},
            "steps": {"type": "array", "items": {"type": "string"}},
            "citations": {"type": "array", "items": citationSchema},
            "nextAction": {"type": "string"},
        },
        "required": ["summary", "likelyCauses", "steps", "citations", "nextAction"],
    }
