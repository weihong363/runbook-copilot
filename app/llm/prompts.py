import json

from app.models.schemas import IncidentAnalyzeRequest, QueryRewrite
from app.llm.grounded_answer import toCitation

PROMPT_VERSIONS = {
    "grounded-v1": {
        "developer": (
            "你是面向工程事故排障的 Runbook Copilot。"
            "只能基于给定 citations 生成答案。"
            "不要编造未在 citations 中出现的根因、命令或系统状态。"
            "如果证据不足，必须明确说明不确定。"
            "输出必须符合 JSON schema。"
        )
    }
}


def buildAnswerPrompt(request: IncidentAnalyzeRequest, rewrittenQuery: QueryRewrite, results: list[dict]) -> str:
    citations = [toCitation(result).model_dump() for result in results[:5]]
    payload = {
        "incident": {
            "alertTitle": request.alertTitle,
            "serviceName": request.serviceName,
            "logSnippet": request.logSnippet,
            "symptomDescription": request.symptomDescription,
        },
        "rewrittenQuery": rewrittenQuery.model_dump(),
        "citations": citations,
        "rules": [
            "summary 必须是基于 citations 的简短判断。",
            "likelyCauses 只能引用 citations 中支持的可能原因。",
            "steps 必须是排障动作，不要输出泛泛建议。",
            "citations 必须原样使用输入 citations 的 chunkId/title/path/heading/score/excerpt。",
            "nextAction 必须指出下一步最应该核对的文档或信息。",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def getPromptDeveloperMessage(promptVersion: str) -> str:
    if promptVersion not in PROMPT_VERSIONS:
        raise ValueError(f"未知 prompt version: {promptVersion}")
    return PROMPT_VERSIONS[promptVersion]["developer"]
