"""Question rankers. They only order chunks that the caller already filtered by profile and warning."""
import math
import os
import re
import threading
from collections import Counter
from typing import Protocol

import httpx

from .catalog import Chunk

# bge-m3 cosine below which a question is treated as not covered by the selected warning's evidence.
# Provisional: on evals/ioniq5_2025.json (2026-10-30) off-topic top-1 scores reached 0.498 and the lowest
# in-scope one was 0.472, so 0.50 abstains on all 12 off-topic questions and on 1 of 34 valid ones.
DEFAULT_MIN_SCORE = 0.50


class QuestionRanker(Protocol):
    name: str
    # None: scores are not calibrated, so the service never abstains on them.
    min_score: float | None
    def rank_scored(self, question: str, chunks: list[Chunk]) -> list[tuple[Chunk, float]]: ...
    def rank(self, question: str, chunks: list[Chunk]) -> list[Chunk]: ...


class _RankMixin:
    def rank(self, question: str, chunks: list[Chunk]) -> list[Chunk]:
        return [c for c, _ in self.rank_scored(question, chunks)]


def _bigrams(text: str) -> Counter:
    s = re.sub(r"\s+", "", text.lower())
    return Counter(s[i:i + 2] for i in range(len(s) - 1))


class LexicalRanker(_RankMixin):
    """Character-bigram overlap. Kept as the baseline any other ranker must beat."""
    name = "lexical-bigram-v1"
    min_score = None

    def rank_scored(self, question: str, chunks: list[Chunk]) -> list[tuple[Chunk, float]]:
        q = _bigrams(question)
        def score(chunk):
            c = _bigrams(chunk.sectionTitle + " " + chunk.text)
            # Normalised by chunk size so long chunks do not win by length alone.
            return sum(min(n, c[g]) for g, n in q.items()) / (sum(c.values()) ** 0.5 or 1)
        return sorted(((c, score(c)) for c in chunks), key=lambda x: (-x[1], x[0].id))


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) or 1)


def configured_min_score() -> float:
    return float(os.getenv("CHECKMATE_MIN_SCORE", DEFAULT_MIN_SCORE))


class OllamaEmbedder:
    """Calls Ollama /api/embed. Shared by the in-memory and the Qdrant rankers."""

    def __init__(self, model: str, base_url: str, transport=None):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.transport = transport
        device = os.getenv("OLLAMA_EMBED_NUM_GPU")
        self.num_gpu = None if device is None else int(device)
        if self.num_gpu is not None and self.num_gpu < 0:
            raise ValueError("OLLAMA_EMBED_NUM_GPU must be non-negative (0 selects CPU)")

    def __call__(self, texts: list[str]) -> list[list[float]]:
        # The first call loads the model; on a CPU-only laptop that alone took over 30 seconds.
        with httpx.Client(timeout=httpx.Timeout(90, connect=3), transport=self.transport, trust_env=False) as client:
            payload = {"model": self.model, "input": texts}
            if self.num_gpu is not None:
                payload["options"] = {"num_gpu": self.num_gpu}
            response = client.post(self.base_url + "/api/embed", json=payload)
            response.raise_for_status()
            vectors = response.json()["embeddings"]
        if len(vectors) != len(texts) or any(not v for v in vectors):
            raise ValueError("Unexpected embedding response")
        return vectors


def embedding_text(chunk: Chunk) -> str:
    return chunk.sectionTitle + "\n" + chunk.text


class OllamaEmbeddingRanker(_RankMixin):
    """Dense ranking in memory. Chunk vectors are cached by their reviewed text hash."""

    def __init__(self, model: str, base_url: str, transport=None, min_score: float | None = DEFAULT_MIN_SCORE):
        self.embed = OllamaEmbedder(model, base_url, transport)
        self.name = f"ollama-embed:{model}"
        self.min_score = min_score
        self._cache: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def rank_scored(self, question: str, chunks: list[Chunk]) -> list[tuple[Chunk, float]]:
        with self._lock:
            missing = [c for c in chunks if c.textSha256 not in self._cache]
            if missing:
                for c, v in zip(missing, self.embed([embedding_text(c) for c in missing])):
                    self._cache[c.textSha256] = v
        q = self.embed([question])[0]
        return sorted(((c, _cosine(q, self._cache[c.textSha256])) for c in chunks), key=lambda x: (-x[1], x[0].id))
