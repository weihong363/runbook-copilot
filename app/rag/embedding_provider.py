from typing import Protocol

from app.rag.embedding import embedText


class EmbeddingProvider(Protocol):
    name: str
    dimension: int

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class HashEmbeddingProvider:
    name = "hash"

    def __init__(self, dimension: int) -> None:
        if dimension < 16:
            raise ValueError("dimension 至少为 16")
        self.dimension = dimension

    def embed(self, text: str) -> list[float]:
        return embedText(text, self.dimension)


class SentenceTransformersEmbeddingProvider:
    name = "sentence-transformers"

    def __init__(self, modelName: str) -> None:
        if not modelName.strip():
            raise ValueError("modelName 不能为空")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError(
                "未安装 sentence-transformers，无法使用 EMBEDDING_PROVIDER=sentence-transformers。"
            ) from error
        self.modelName = modelName
        self.model = SentenceTransformer(modelName)
        self.dimension = int(self.model.get_sentence_embedding_dimension())

    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(text, normalize_embeddings=True)
        return [float(value) for value in vector.tolist()]


def createEmbeddingProvider(provider: str, dimension: int, modelName: str) -> EmbeddingProvider:
    normalized = provider.strip().lower()
    if normalized == "hash":
        return HashEmbeddingProvider(dimension)
    if normalized in {"sentence-transformers", "sentence_transformers"}:
        return SentenceTransformersEmbeddingProvider(modelName)
    raise ValueError(f"不支持的 embedding provider: {provider}")
