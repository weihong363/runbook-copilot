from app.core.config import Settings
from app.llm.answer_generator import AnswerGenerator, createAnswerGenerator
from app.rag.embedding_provider import EmbeddingProvider, createEmbeddingProvider
from app.rag.retriever import HybridRetriever
from app.rag.vector_store import SQLiteVectorStore, VectorStore


def createVectorStore(settings: Settings) -> VectorStore:
    backend = settings.vectorStoreBackend.strip().lower()
    if backend == "sqlite":
        return SQLiteVectorStore(settings.databasePath)
    raise ValueError(f"不支持的 vector store backend: {settings.vectorStoreBackend}")


def createRetriever(settings: Settings) -> HybridRetriever:
    embeddingProvider = createEmbeddingProvider(
        settings.embeddingProvider,
        settings.vectorDimension,
        settings.embeddingModel,
    )
    return HybridRetriever(createVectorStore(settings), embeddingProvider)


def createAnswerGeneratorFromSettings(settings: Settings) -> AnswerGenerator:
    return createAnswerGenerator(settings.answerGenerator, settings.openaiModel, settings.answerPromptVersion)
