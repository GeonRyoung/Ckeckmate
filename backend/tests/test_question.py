from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from checkmate.catalog import load_catalog
from checkmate.main import create_app
from checkmate.retrieval import OllamaEmbeddingRanker
from checkmate.service import QUESTION_TOP_K, ExplanationService

PROFILE = load_catalog().profiles[0].id


def ask(question=None, intent="QUESTION", profile=PROFILE, type="TPMS"):
    body = {"requestId": str(uuid4()), "profileId": profile, "intent": intent,
            "warning": {"type": type, "rawState": "ON"}}
    return body | ({"question": question} if question is not None else {})


@pytest.mark.parametrize("body", [ask(None), ask("   "), ask("질문", intent="WARNING_OVERVIEW"), ask("가" * 301)])
def test_question_must_match_intent_and_length(body):
    with TestClient(create_app()) as client:
        assert client.post("/v1/explanations", json=body).status_code == 422


def test_question_returns_focused_cited_evidence():
    with TestClient(create_app()) as client:
        data = client.post("/v1/explanations", json=ask("예비 타이어로 바꿨더니 켜졌어요")).json()
    assert data["status"] == "READY"
    assert 1 <= len(data["sections"]) <= QUESTION_TOP_K
    assert all(c["url"].startswith("https://ownersmanual.hyundai.com/") for c in data["citations"])


def test_question_cannot_reach_other_profiles_or_warnings():
    with TestClient(create_app()) as client:
        assert client.post("/v1/explanations", json=ask("TPMS", profile="other-car")).json()["status"] == "PROFILE_UNSUPPORTED"
        assert client.post("/v1/explanations", json=ask("TPMS 공기압", type="ABS")).json()["status"] == "WARNING_UNSUPPORTED"


def fake_embedder(calls):
    # Vector = [mentions spare tire, anything else]; enough to check ordering and caching.
    def handler(request):
        texts = __import__("json").loads(request.content)["input"]
        calls.append(len(texts))
        return httpx.Response(200, json={"embeddings": [[1.0 if "예비 타이어" in t else 0.0, 0.1] for t in texts]})
    return httpx.MockTransport(handler)


def test_embedding_ranker_orders_by_similarity_and_caches_chunk_vectors():
    calls = []
    ranker = OllamaEmbeddingRanker("bge-m3", "http://ollama", transport=fake_embedder(calls))
    chunks = [c for c in load_catalog().chunks if "TPMS" in c.warningTags]
    assert ranker.rank("예비 타이어를 달았어요", chunks)[0].id == "tpms-50-other-causes"
    ranker.rank("예비 타이어", chunks)
    assert calls == [len(chunks), 1, 1]  # chunks embedded once, then only the question


def test_embedding_failure_is_unavailable_not_a_guess():
    def down(request): return httpx.Response(500)
    service = ExplanationService(ranker=OllamaEmbeddingRanker("bge-m3", "http://ollama", transport=httpx.MockTransport(down)))
    with TestClient(create_app(service)) as client:
        data = client.post("/v1/explanations", json=ask("체인 감았어요")).json()
    assert data["status"] == "TEMPORARILY_UNAVAILABLE"
    assert data["sections"] == data["citations"] == []
