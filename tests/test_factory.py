import pytest

from app.core.config import Settings
from app.rag.factory import createRetriever, createVectorStore
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
