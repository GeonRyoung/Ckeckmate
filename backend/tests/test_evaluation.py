from checkmate.catalog import load_catalog
from checkmate.evaluation import evaluate, load_cases
from checkmate.service import ExplanationService


def test_eval_cases_reference_existing_evidence_and_known_profile():
    data, catalog = load_cases(), load_catalog()
    ids = {c.id for c in catalog.chunks}
    assert data["profileId"] in {p.id for p in catalog.profiles}
    assert len({c["id"] for c in data["cases"]}) == len(data["cases"])
    for case in data["cases"]:
        if case.get("expectedStatus", "READY") == "READY":
            assert case["relevantChunks"] and set(case["relevantChunks"]) <= ids, case["id"]
            assert case["mustInclude"], case["id"]


def test_reviewed_mode_passes_every_case():
    report = evaluate(ExplanationService(), load_cases())
    assert report["failures"] == []
    assert report["responsePassed"] == report["responseTotal"] == 26


def test_forbidden_claim_is_detected():
    data = load_cases()
    data["forbidden"] = ["공기압"]  # present in every READY answer
    report = evaluate(ExplanationService(), data)
    assert report["responsePassed"] == 4  # only the four refusal cases
