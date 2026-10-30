"""Offline evaluation for the reviewed TPMS evidence.

- response checks: the real service answer keeps required conditions, cites the right evidence,
  avoids forbidden claims and refuses out-of-scope requests. Run for the fixed overview and for
  QUESTION requests (reviewed and ollama generation modes alike);
- retrieval: hit@k of the configured question ranker against the lexical baseline, inside the
  same profile/warning filter the service uses.
"""
import json
import sys
from pathlib import Path
from uuid import uuid4

from .contracts import ExplanationRequest
from .retrieval import LexicalRanker
from .service import candidates

DEFAULT_CASES = Path(__file__).parents[1] / "evals/ioniq5_2025.json"


def load_cases(path: Path = DEFAULT_CASES) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_case(service, data: dict, case: dict, intent: str = "WARNING_OVERVIEW") -> list[str]:
    """Returns failure reasons; an empty list means the case passed."""
    req = ExplanationRequest(requestId=uuid4(), profileId=case.get("profileId", data["profileId"]),
        warning={"type": case.get("type", "TPMS"), "rawState": case["state"]}, intent=intent,
        question=case["question"] if intent == "QUESTION" else None)
    res = service.explain(req)
    expected = case.get("expectedStatus", "READY")
    if intent == "QUESTION" and "expectedQuestionStatus" in case:
        expected = case["expectedQuestionStatus"]
    if res.status != expected:
        return [f"status {res.status} != {expected}"]
    if expected != "READY":
        return []
    text = " ".join(s.title + " " + s.text for s in res.sections)
    cited = [c.chunkId for c in res.citations]
    if intent == "QUESTION":
        # A focused answer must include at least one right source, not every listed one.
        failures = [] if set(cited) & set(case["relevantChunks"]) else [f"no relevant evidence in {cited}"]
        groups = [g for g in case["mustInclude"]
                  if any(any(p in c.text for p in g) for c in service.catalog.chunks if c.id in cited)]
    else:
        failures = [f"missing evidence {c}" for c in case["relevantChunks"] if c not in cited]
        groups = case["mustInclude"]
    failures += [f"missing one of {g}" for g in groups if not any(p in text for p in g)]
    failures += [f"forbidden '{p}'" for p in data["forbidden"] if p in text]
    return failures


def answerable(case: dict) -> bool:
    return case.get("expectedStatus", "READY") == "READY" and not case.get("questionOnly")


def hit_rates(ranker, catalog, data: dict, ks=(1, 2)) -> dict:
    ready = [c for c in data["cases"] if answerable(c)]
    hits, misses = {k: 0 for k in ks}, []
    for case in ready:
        pool = candidates(catalog, data["profileId"], case.get("type", "TPMS"))
        ranked = [c.id for c in ranker.rank(case["question"], pool)]
        for k in ks:
            hits[k] += bool(set(ranked[:k]) & set(case["relevantChunks"]))
        if not set(ranked[:1]) & set(case["relevantChunks"]):
            misses.append({"id": case["id"], "top1": ranked[0], "expected": case["relevantChunks"]})
    return {"ranker": ranker.name, **{f"hit@{k}": round(v / len(ready), 3) for k, v in hits.items()},
            "top1Misses": misses}


def evaluate(service, data: dict) -> dict:
    report = {"evalVersion": data["evalVersion"], "mode": service.mode}
    for intent in ("WARNING_OVERVIEW", "QUESTION"):
        cases = [c for c in data["cases"] if intent == "QUESTION" or not c.get("questionOnly")]
        results = [{"id": c["id"], "failures": check_case(service, data, c, intent)} for c in cases]
        report[intent] = {"passed": sum(not r["failures"] for r in results), "total": len(results),
                          "failures": [r for r in results if r["failures"]]}
    failed = {f["id"] for f in report["QUESTION"]["failures"]}
    off = [c["id"] for c in data["cases"] if c.get("expectedQuestionStatus") == "NO_EVIDENCE"]
    report["abstention"] = {"minScore": getattr(service.ranker, "min_score", None),
        "offTopicAbstained": sum(i not in failed for i in off), "offTopicTotal": len(off),
        "validWronglyAbstained": [f["id"] for f in report["QUESTION"]["failures"]
                                  if any("NO_EVIDENCE" in x for x in f["failures"])]}
    report["retrieval"] = hit_rates(service.ranker, service.catalog, data)
    report["baseline"] = hit_rates(LexicalRanker(), service.catalog, data)
    return report


if __name__ == "__main__":
    from .generation import configured_service
    print(json.dumps(evaluate(configured_service(), load_cases()), ensure_ascii=False, indent=2))
    sys.exit(0)
