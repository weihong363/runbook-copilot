import pytest

from app.rag.embedding_provider import HashEmbeddingProvider, createEmbeddingProvider


def testHashEmbeddingProviderReturnsConfiguredDimension() -> None:
    provider = HashEmbeddingProvider(32)

    vector = provider.embed("checkout-api DB_POOL_EXHAUSTED")

    assert len(vector) == 32


def testCreateEmbeddingProviderRejectsUnknownProvider() -> None:
    with pytest.raises(ValueError):
        createEmbeddingProvider("unknown", 32, "unused")
