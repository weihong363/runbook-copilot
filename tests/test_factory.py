import pytest

from app.core.config import Settings
from app.llm.answer_generator import TemplateAnswerGenerator
from app.rag.factory import createAnswerGeneratorFromSettings, createRetriever, createVectorStore
from app.rag.vector_store import SQLiteVectorStore


def testCreateVectorStoreUsesSqliteBackend(tmp_path) -> None:
    settings = Settings(databasePath=tmp_path / "store.sqlite3")

    store = createVectorStore(settings)

    assert isinstance(store, SQLiteVectorStore)


def testCreateVectorStoreRejectsUnknownBackend(tmp_path) -> None:
    settings = Settings(databasePath=tmp_path / "store.sqlite3", vectorStoreBackend="unknown")

    with pytest.raises(ValueError):
        createVectorStore(settings)


def testCreateRetrieverKeepsDefaultHashProvider(tmp_path) -> None:
    settings = Settings(databasePath=tmp_path / "store.sqlite3")

    retriever = createRetriever(settings)

    assert retriever.embeddingProvider.name == "hash"


def testCreateAnswerGeneratorUsesConfiguredPromptVersion(tmp_path) -> None:
    settings = Settings(databasePath=tmp_path / "store.sqlite3", answerPromptVersion="grounded-v1")

    generator = createAnswerGeneratorFromSettings(settings)

    assert isinstance(generator, TemplateAnswerGenerator)
    assert generator.promptVersion == "grounded-v1"
