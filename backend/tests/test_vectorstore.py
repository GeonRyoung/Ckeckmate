from uuid import uuid4

from qdrant_client import QdrantClient, models

from checkmate.catalog import load_catalog
from checkmate.contracts import ExplanationRequest
from checkmate.service import ExplanationService, candidates
from checkmate.vectorstore import QdrantRanker, point_id


class FakeEmbed:
    """Keyword vectors: enough to check ordering, caching and filtering without Ollama."""
    model = "fake-embed"

    def __init__(self):
        self.calls = []

    def __call__(self, texts):
        self.calls.append(len(texts))
        return [[1.0 if "예비 타이어" in t else 0.0, 1.0 if "체인" in t else 0.0, 0.1] for t in texts]


def ranker():
    embed = FakeEmbed()
    r = QdrantRanker(embed, QdrantClient(":memory:"))
    r.bind(load_catalog())
    return r, embed


def tpms_pool(catalog):
    return candidates(catalog, catalog.profiles[0].id, "TPMS")


def test_sync_embeds_only_new_or_changed_chunks_and_removes_stale_points():
    r, embed = ranker()
    assert r.sync() == {"embedded": 10, "deleted": 0, "total": 10}
    assert r.sync()["embedded"] == 0
    catalog = load_catalog().model_copy(deep=True)
    catalog.chunks[0].textSha256 = "0" * 64  # simulates a re-reviewed summary
    catalog.chunks = catalog.chunks[:-1]
    r.bind(catalog)
    assert r.sync() == {"embedded": 1, "deleted": 1, "total": 9}


def test_rank_orders_by_similarity_and_keeps_the_whole_pool():
    r, _ = ranker()
    pool = tpms_pool(r.catalog)
    ranked = r.rank("예비 타이어를 달았어요", pool)
    assert ranked[0].id == "tpms-50-other-causes"
    assert sorted(c.id for c in ranked) == sorted(c.id for c in pool)


def test_index_entries_outside_the_pool_or_with_stale_text_are_never_returned_first():
    r, _ = ranker()
    r.sync()
    pool = tpms_pool(r.catalog)
    # A foreign point that matches the question perfectly, and a tampered hash on a pool chunk.
    r.client.upsert(r.collection, points=[models.PointStruct(id=str(uuid4()), vector=[1.0, 0.0, 0.1],
        payload={"chunkId": "other-car-spare", "profileId": "other-car", "warningTags": ["TPMS"],
                 "retrievalApproved": True, "textSha256": "x"})])
    r.client.set_payload(r.collection, payload={"textSha256": "tampered"}, points=[point_id("tpms-50-other-causes")])
    ranked = [c.id for c in r.rank("예비 타이어", pool)]
    assert "other-car-spare" not in ranked
    assert ranked[-1] == "tpms-50-other-causes" and len(ranked) == len(pool)


def test_index_failure_is_unavailable_not_a_guess():
    class Broken:
        def collection_exists(self, *a, **k): raise RuntimeError("locked by another process")
    r = QdrantRanker(FakeEmbed(), Broken())
    service = ExplanationService(ranker=r)
    req = ExplanationRequest(requestId=uuid4(), profileId=service.catalog.profiles[0].id,
        warning={"type": "TPMS", "rawState": "ON"}, intent="QUESTION", question="체인 감았어요")
    response = service.explain(req)
    assert response.status == "TEMPORARILY_UNAVAILABLE" and response.sections == []


def test_service_question_through_qdrant_cites_only_selected_warning():
    r, embed = ranker()
    service = ExplanationService(ranker=r)
    req = ExplanationRequest(requestId=uuid4(), profileId=service.catalog.profiles[0].id,
        warning={"type": "ELECTRONIC_PARKING_BRAKE", "rawState": "ON"}, intent="QUESTION", question="체인 감았어요")
    response = service.explain(req)
    assert response.status == "READY"
    assert all(c.chunkId.startswith("epb-") for c in response.citations)
    assert embed.calls[0] == 1 and embed.calls[1] == 10  # dimension probe, then the catalog once
