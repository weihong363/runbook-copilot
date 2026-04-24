import hashlib
import math

from app.rag.tokenizer import tokenize


def embedText(text: str, dimension: int) -> list[float]:
    if dimension < 16:
        raise ValueError("dimension 至少为 16")
    vector = [0.0] * dimension
    for token in tokenize(text):
        index = _stableIndex(token, dimension)
        vector[index] += 1.0
    return _normalize(vector)


def cosineSimilarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("向量维度不一致")
    return sum(a * b for a, b in zip(left, right))


def _stableIndex(token: str, dimension: int) -> int:
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % dimension


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
