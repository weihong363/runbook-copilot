import re

from app.models.schemas import Citation, IncidentAnalyzeRequest, QueryRewrite, TroubleshootingResponse


def buildGroundedAnswer(
    request: IncidentAnalyzeRequest,
    rewrittenQuery: QueryRewrite,
    results: list[dict],
) -> TroubleshootingResponse:
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
    evidence = assessEvidence(results)
    top = citations[0]
    return TroubleshootingResponse(
        summary=_buildSummary(request, top, evidence),
        likelyCauses=_likelyCauses(results, evidence),
        steps=_steps(results, evidence),
        citations=_visibleCitations(citations, evidence),
        nextAction=_nextAction(top, evidence),
    )


def assessEvidence(results: list[dict]) -> dict[str, object]:
    if not results:
        return {"strength": "none", "strongResults": [], "weakResults": []}
    strongResults = [result for result in results if _isStrongEvidence(result)]
    weakResults = [result for result in results if not _isStrongEvidence(result)]
    strength = "strong" if strongResults else "weak"
    return {
        "strength": strength,
        "strongResults": strongResults,
        "weakResults": weakResults,
    }


def toCitation(result: dict) -> Citation:
    return _toCitation(result)


def _toCitation(result: dict) -> Citation:
    excerpt = _stableExcerpt(result["content"])
    return Citation(
        chunkId=result["id"],
        title=result["title"],
        path=result["path"],
        heading=result["heading"],
        score=float(result["score"]),
        excerpt=excerpt,
    )


def _likelyCauses(results: list[dict], evidence: dict[str, object]) -> list[str]:
    strongResults = evidence["strongResults"]
    weakResults = evidence["weakResults"]
    if not strongResults:
        return [
            "当前仅命中弱相关资料，暂时不能确认根因。",
            *[
                f"《{result['title']}》/“{result['heading']}”可能提供相邻场景线索，但需要先核对服务名、错误码和依赖是否一致。"
                for result in weakResults[:2]
            ],
        ]
    causes = []
    for result in strongResults[:3]:
        causes.append(f"《{result['title']}》/“{result['heading']}”提供了与当前信号相符的排障证据。")
    return causes


def _steps(results: list[dict], evidence: dict[str, object]) -> list[str]:
    strongResults = evidence["strongResults"]
    steps = ["先确认告警时间窗口、影响范围和最近发布记录。"]
    if not strongResults:
        steps.append("当前召回结果证据较弱，先核对服务名、依赖和错误码是否与引用文档一致。")
        for result in results[:2]:
            steps.append(f"将《{result['title']}》/{result['heading']} 作为线索阅读，不要直接把它当作已确认根因。")
        steps.append("补充更完整日志后再次检索，或补充该服务的 runbook。")
        return steps
    for result in strongResults[:3]:
        steps.append(f"优先执行《{result['title']}》/{result['heading']} 中记录的检查或缓解步骤。")
    steps.append("记录最终根因和修复动作，补充到对应 runbook。")
    return steps


def _buildSummary(request: IncidentAnalyzeRequest, top: Citation, evidence: dict[str, object]) -> str:
    if evidence["strength"] == "weak":
        return (
            f"当前只找到与 {request.serviceName} / {request.alertTitle} 部分相关的资料，"
            f"《{top.title}》的“{top.heading}”可作为初步线索，但证据还不足以直接下结论。"
        )
    return f"最相关资料是《{top.title}》的“{top.heading}”，可作为本次排障起点。"


def _nextAction(top: Citation, evidence: dict[str, object]) -> str:
    if evidence["strength"] == "weak":
        return f"先核对 {top.path} 中“{top.heading}”是否与当前服务、错误码和依赖一致，再决定是否沿该方向排查。"
    return f"优先打开 {top.path}，按“{top.heading}”中的检查项验证。"


def _visibleCitations(citations: list[Citation], evidence: dict[str, object]) -> list[Citation]:
    if evidence["strength"] == "weak":
        return citations[:3]
    return citations[:5]


def _isStrongEvidence(result: dict) -> bool:
    score = float(result.get("score", 0.0))
    headingLevel = int(result.get("heading_level", 0) or 0)
    return score >= 0.35 and headingLevel >= 2


def _stableExcerpt(content: str) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if lines and lines[0].startswith("#"):
        lines = lines[1:]
    excerpt = " ".join(lines)
    excerpt = re.sub(r"\s+", " ", excerpt)
    return excerpt[:220]
