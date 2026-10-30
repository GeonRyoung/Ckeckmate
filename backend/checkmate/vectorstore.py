"""Qdrant vector index for the reviewed chunks.

manuals.json stays the source of truth: Qdrant holds only vectors and filter metadata
(profile, warning tags, approval, text hash). Text shown to drivers always comes from the catalog,
so a stale or tampered index can reorder evidence but never change it or pull in another profile's.
"""
import re
import threading
import uuid

from qdrant_client import QdrantClient, models

from .catalog import Catalog, Chunk
from .retrieval import DEFAULT_MIN_SCORE, OllamaEmbedder, _RankMixin, embedding_text


class RetrievalUnavailable(ValueError):
    """The vector index could not be read or updated."""


def point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "checkmate-chunk:" + chunk_id))


class QdrantRanker(_RankMixin):
    def __init__(self, embed: OllamaEmbedder, client: QdrantClient, collection_prefix: str = "manual_chunks",
                 min_score: float | None = DEFAULT_MIN_SCORE):
        self.min_score = min_score
        self.embed = embed
        self.client = client
        # One collection per embedding model: vectors of different models are never mixed.
        self.collection = f"{collection_prefix}__{re.sub(r'[^a-zA-Z0-9]+', '_', embed.model)}"
        self.name = f"qdrant:{self.collection}"
        self.catalog: Catalog | None = None
        self._synced = False
        self._lock = threading.Lock()

    @staticmethod
    def _db(call, *args, **kwargs):
        # qdrant-client raises several unrelated exception types; the service sees one.
        try:
            return call(*args, **kwargs)
        except Exception as error:
            raise RetrievalUnavailable(f"Vector index error: {type(error).__name__}") from error

    def bind(self, catalog: Catalog):
        self.catalog = catalog
        self._synced = False

    def sync(self) -> dict:
        """Embeds new or changed chunks and deletes points no longer in the catalog."""
        if self.catalog is None:
            raise RetrievalUnavailable("Ranker is not bound to a catalog")
        wanted = {point_id(c.id): c for c in self.catalog.chunks}
        if not self._db(self.client.collection_exists, self.collection):
            size = len(self.embed(["dimension probe"])[0])
            self._db(self.client.create_collection, self.collection,
                vectors_config=models.VectorParams(size=size, distance=models.Distance.COSINE))
        stored, offset = {}, None
        while True:
            points, offset = self._db(self.client.scroll, self.collection, limit=256, offset=offset,
                with_payload=["textSha256"], with_vectors=False)
            stored.update({str(p.id): p.payload.get("textSha256") for p in points})
            if offset is None:
                break
        changed = [c for pid, c in wanted.items() if stored.get(pid) != c.textSha256]
        stale = [pid for pid in stored if pid not in wanted]
        if changed:
            vectors = self.embed([embedding_text(c) for c in changed])
            self._db(self.client.upsert, self.collection, points=[models.PointStruct(id=point_id(c.id), vector=v,
                payload={"chunkId": c.id, "profileId": c.profileId, "documentId": c.documentId,
                         "warningTags": c.warningTags, "retrievalApproved": c.retrievalApproved,
                         "textSha256": c.textSha256}) for c, v in zip(changed, vectors)])
        if stale:
            self._db(self.client.delete, self.collection, points_selector=models.PointIdsList(points=stale))
        self._synced = True
        return {"embedded": len(changed), "deleted": len(stale), "total": len(wanted)}

    def rank_scored(self, question: str, chunks: list[Chunk]) -> list[tuple[Chunk, float]]:
        if not chunks:
            return []
        with self._lock:
            if not self._synced:
                self.sync()
        query = self.embed([question])[0]
        profiles = {c.profileId for c in chunks}
        tags = sorted({t for c in chunks for t in c.warningTags})
        # The index repeats the service's filter; the pool check below is the final boundary.
        query_filter = models.Filter(must=[
            models.FieldCondition(key="chunkId", match=models.MatchAny(any=[c.id for c in chunks])),
            models.FieldCondition(key="profileId", match=models.MatchAny(any=sorted(profiles))),
            models.FieldCondition(key="warningTags", match=models.MatchAny(any=tags)),
            models.FieldCondition(key="retrievalApproved", match=models.MatchValue(value=True)),
        ])
        hits = self._db(self.client.query_points, self.collection, query=query, query_filter=query_filter,
            limit=len(chunks), with_payload=["chunkId", "textSha256"]).points
        pool = {c.id: c for c in chunks}
        ranked = [(pool[h.payload["chunkId"]], h.score) for h in hits
                  if h.payload.get("chunkId") in pool and h.payload.get("textSha256") == pool[h.payload["chunkId"]].textSha256]
        seen = {c.id for c, _ in ranked}
        # Chunks the index did not return (e.g. hash mismatch) stay last with no score rather than disappearing.
        return ranked + [(c, -1.0) for c in sorted(chunks, key=lambda c: c.id) if c.id not in seen]
