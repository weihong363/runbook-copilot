from collections import Counter
import math

from app.rag.tokenizer import tokenize


class BM25Index:
    def __init__(self, documents: list[dict]) -> None:
        if documents is None:
            raise ValueError("documents 不能为 None")
        self.documents = documents
        self.tokens = [tokenize(_searchText(document)) for document in documents]
        self.avgLength = self._averageLength()
        self.docFrequency = self._documentFrequency()

    def search(self, query: str, topK: int) -> list[tuple[dict, float]]:
        if topK < 1:
            raise ValueError("topK 必须大于 0")
        queryTokens = tokenize(query)
        scored = [
            (document, self._score(queryTokens, index))
            for index, document in enumerate(self.documents)
        ]
        return sorted(scored, key=lambda item: item[1], reverse=True)[:topK]

    def _score(self, queryTokens: list[str], index: int) -> float:
        frequencies = Counter(self.tokens[index])
        documentLength = max(1, len(self.tokens[index]))
        score = 0.0
        for token in queryTokens:
            if frequencies[token] == 0:
                continue
            idf = self._idf(token)
            numerator = frequencies[token] * 2.5
            denominator = frequencies[token] + 1.5 * (0.25 + 0.75 * documentLength / self.avgLength)
            score += idf * numerator / denominator
        return max(0.0, score)

    def _idf(self, token: str) -> float:
        total = max(1, len(self.documents))
        frequency = self.docFrequency.get(token, 0)
        return math.log(1 + (total - frequency + 0.5) / (frequency + 0.5))

    def _averageLength(self) -> float:
        if not self.tokens:
            return 1.0
        return sum(len(tokens) for tokens in self.tokens) / len(self.tokens) or 1.0

    def _documentFrequency(self) -> dict[str, int]:
        frequency: dict[str, int] = {}
        for tokens in self.tokens:
            for token in set(tokens):
                frequency[token] = frequency.get(token, 0) + 1
        return frequency


def _searchText(document: dict) -> str:
    return " ".join(
        [
            str(document.get("title", "")),
            str(document.get("heading", "")),
            str(document.get("tags", "")),
            str(document.get("content", "")),
        ]
    )
