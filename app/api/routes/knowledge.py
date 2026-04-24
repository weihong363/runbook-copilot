from fastapi import APIRouter, HTTPException

from app.core.config import getSettings
from app.models.schemas import IngestResponse
from app.rag.ingestion import ingestKnowledge
from app.rag.vector_store import SQLiteVectorStore

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/ingest", response_model=IngestResponse)
def ingest() -> IngestResponse:
    settings = getSettings()
    try:
        store = SQLiteVectorStore(settings.databasePath)
        stats = ingestKnowledge(settings.knowledgeDir, store, settings.vectorDimension)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return IngestResponse(**stats)
