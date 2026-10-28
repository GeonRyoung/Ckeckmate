"""Offline evaluation for the reviewed TPMS evidence.

Two separate measurements:
- response checks: the real service answer keeps required conditions, cites the right evidence,
  avoids forbidden claims and refuses out-of-scope requests (works for reviewed and ollama modes);
- question retrieval baseline: a simple character-bigram ranker over the same chunks. The API does
  not take free questions yet; this number is the bar a future embedding/LangGraph retriever must beat.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path
from uuid import uuid4

from .catalog import Catalog
from .contracts import ExplanationRequest

DEFAULT_CASES = Path(__file__).parents[1] / "evals/tpms_ioniq5_2025.json"


def load_cases(path: Path = DEFAULT_CASES) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_case(service, data: dict, case: dict) -> list[str]:
    """Returns failure reasons; an empty list means the case passed."""
    req = ExplanationRequest(requestId=uuid4(), profileId=case.get("profileId", data["profileId"]),
        warning={"type": case.get("type", "TPMS"), "rawState": case["state"]})
    res = service.explain(req)
    expected = case.get("expectedStatus", "READY")
    if res.status != expected:
        return [f"status {res.status} != {expected}"]
    if expected != "READY":
        return []
    text = " ".join(s.title + " " + s.text for s in res.sections)
    cited = {c.chunkId for c in res.citations}
    failures = [f"missing evidence {c}" for c in case["relevantChunks"] if c not in cited]
    failures += [f"missing one of {group}" for group in case["mustInclude"] if not any(p in text for p in group)]
    failures += [f"forbidden '{p}'" for p in data["forbidden"] if p in text]
    return failures


def _bigrams(text: str) -> Counter:
    s = re.sub(r"\s+", "", text.lower())
    return Counter(s[i:i + 2] for i in range(len(s) - 1))


def rank_by_question(catalog: Catalog, profile_id: str, question: str) -> list[str]:
    q = _bigrams(question)
    def score(chunk):
        c = _bigrams(chunk.sectionTitle + " " + chunk.text)
        # Overlap normalised by chunk size so long chunks do not win by length alone.
        return sum(min(n, c[g]) for g, n in q.items()) / (sum(c.values()) ** 0.5 or 1)
    chunks = [c for c in catalog.chunks if c.profileId == profile_id and c.retrievalApproved]
    return [c.id for c in sorted(chunks, key=lambda c: (-score(c), c.id))]


def evaluate(service, data: dict) -> dict:
    results, hits = [], {1: 0, 2: 0}
    ready = [c for c in data["cases"] if c.get("expectedStatus", "READY") == "READY"]
    for case in data["cases"]:
        results.append({"id": case["id"], "failures": check_case(service, data, case)})
    for case in ready:
        ranked = rank_by_question(service.catalog, data["profileId"], case["question"])
        for k in hits:
            hits[k] += bool(set(ranked[:k]) & set(case["relevantChunks"]))
    return {
        "evalVersion": data["evalVersion"], "mode": service.mode,
        "responsePassed": sum(not r["failures"] for r in results), "responseTotal": len(results),
        "failures": [r for r in results if r["failures"]],
        "questionRetrievalBaseline": {f"hit@{k}": round(v / len(ready), 3) for k, v in hits.items()},
    }


if __name__ == "__main__":
    from .generation import configured_service
    print(json.dumps(evaluate(configured_service(), load_cases()), ensure_ascii=False, indent=2))
    sys.exit(0)
