from fastapi import APIRouter, HTTPException

from app.core.config import getSettings
from app.models.schemas import IncidentAnalyzeRequest, IncidentAnalyzeResponse
from app.rag.factory import createRetriever
from app.services.incident_analyzer import IncidentAnalyzer

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("/analyze", response_model=IncidentAnalyzeResponse)
def analyzeIncident(request: IncidentAnalyzeRequest) -> IncidentAnalyzeResponse:
    settings = getSettings()
    try:
        retriever = createRetriever(settings)
        analyzer = IncidentAnalyzer(retriever, settings.topK)
        if request.debug:
            entities, rewrittenQuery, answer, debug = analyzer.analyzeWithDebug(request)
            return IncidentAnalyzeResponse(
                entities=entities,
                rewrittenQuery=rewrittenQuery,
                answer=answer,
                debug=debug,
            )
        entities, rewrittenQuery, answer = analyzer.analyze(request)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return IncidentAnalyzeResponse(entities=entities, rewrittenQuery=rewrittenQuery, answer=answer)
