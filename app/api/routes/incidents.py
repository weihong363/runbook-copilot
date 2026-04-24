from fastapi import APIRouter, HTTPException

from app.core.config import getSettings
from app.models.schemas import IncidentAnalyzeRequest, IncidentAnalyzeResponse
from app.rag.retriever import HybridRetriever
from app.rag.vector_store import SQLiteVectorStore
from app.services.incident_analyzer import IncidentAnalyzer

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("/analyze", response_model=IncidentAnalyzeResponse)
def analyzeIncident(request: IncidentAnalyzeRequest) -> IncidentAnalyzeResponse:
    settings = getSettings()
    try:
        store = SQLiteVectorStore(settings.databasePath)
        retriever = HybridRetriever(store, settings.vectorDimension)
        entities, rewrittenQuery, answer = IncidentAnalyzer(retriever, settings.topK).analyze(request)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return IncidentAnalyzeResponse(entities=entities, rewrittenQuery=rewrittenQuery, answer=answer)
