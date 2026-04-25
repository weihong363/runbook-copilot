from fastapi import APIRouter, HTTPException

from app.core.config import getSettings
from app.models.schemas import IngestResponse
from app.rag.embedding_provider import createEmbeddingProvider
from app.rag.factory import createVectorStore
from app.rag.ingestion import ingestKnowledge

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/ingest", response_model=IngestResponse)
def ingest() -> IngestResponse:
    settings = getSettings()
    try:
        store = createVectorStore(settings)
        embeddingProvider = createEmbeddingProvider(
            settings.embeddingProvider,
            settings.vectorDimension,
            settings.embeddingModel,
        )
        stats = ingestKnowledge(settings.knowledgeDir, store, settings.vectorDimension, embeddingProvider)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return IngestResponse(**stats)
