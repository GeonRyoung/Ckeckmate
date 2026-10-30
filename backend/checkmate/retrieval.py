"""Question rankers. They only order chunks that the caller already filtered by profile and warning."""
import math
import re
import threading
from collections import Counter
from typing import Protocol

import httpx

from .catalog import Chunk


class QuestionRanker(Protocol):
    name: str
    def rank(self, question: str, chunks: list[Chunk]) -> list[Chunk]: ...


def _bigrams(text: str) -> Counter:
    s = re.sub(r"\s+", "", text.lower())
    return Counter(s[i:i + 2] for i in range(len(s) - 1))


class LexicalRanker:
    """Character-bigram overlap. Kept as the baseline any other ranker must beat."""
    name = "lexical-bigram-v1"

    def rank(self, question: str, chunks: list[Chunk]) -> list[Chunk]:
        q = _bigrams(question)
        def score(chunk):
            c = _bigrams(chunk.sectionTitle + " " + chunk.text)
            # Normalised by chunk size so long chunks do not win by length alone.
            return sum(min(n, c[g]) for g, n in q.items()) / (sum(c.values()) ** 0.5 or 1)
        return sorted(chunks, key=lambda c: (-score(c), c.id))


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) or 1)


class OllamaEmbedder:
    """Calls Ollama /api/embed. Shared by the in-memory and the Qdrant rankers."""

    def __init__(self, model: str, base_url: str, transport=None):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.transport = transport

    def __call__(self, texts: list[str]) -> list[list[float]]:
        # The first call loads the model; on a CPU-only laptop that alone took over 30 seconds.
        with httpx.Client(timeout=httpx.Timeout(90, connect=3), transport=self.transport, trust_env=False) as client:
            response = client.post(self.base_url + "/api/embed", json={"model": self.model, "input": texts})
            response.raise_for_status()
            vectors = response.json()["embeddings"]
        if len(vectors) != len(texts) or any(not v for v in vectors):
            raise ValueError("Unexpected embedding response")
        return vectors


def embedding_text(chunk: Chunk) -> str:
    return chunk.sectionTitle + "\n" + chunk.text


class OllamaEmbeddingRanker:
    """Dense ranking in memory. Chunk vectors are cached by their reviewed text hash."""

    def __init__(self, model: str, base_url: str, transport=None):
        self.embed = OllamaEmbedder(model, base_url, transport)
        self.name = f"ollama-embed:{model}"
        self._cache: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def rank(self, question: str, chunks: list[Chunk]) -> list[Chunk]:
        with self._lock:
            missing = [c for c in chunks if c.textSha256 not in self._cache]
            if missing:
                for c, v in zip(missing, self.embed([embedding_text(c) for c in missing])):
                    self._cache[c.textSha256] = v
        q = self.embed([question])[0]
        return sorted(chunks, key=lambda c: (-_cosine(q, self._cache[c.textSha256]), c.id))
