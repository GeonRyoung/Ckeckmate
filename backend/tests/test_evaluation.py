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


def test_reviewed_overview_passes_every_case_and_reports_both_rankers():
    report = evaluate(ExplanationService(), load_cases())
    assert report["WARNING_OVERVIEW"]["failures"] == []
    assert report["WARNING_OVERVIEW"]["passed"] == 26
    # Refusals hold for free questions too, whatever the ranker returns.
    refusals = {"other-model", "other-warning", "off-is-normal", "no-profile"}
    assert not refusals & {f["id"] for f in report["QUESTION"]["failures"]}
    assert report["baseline"]["ranker"] == "lexical-bigram-v1"
    assert report["baseline"]["hit@1"] == 0.5


def test_forbidden_claim_is_detected():
    data = load_cases()
    data["forbidden"] = ["공기압"]  # present in every READY overview
    assert evaluate(ExplanationService(), data)["WARNING_OVERVIEW"]["passed"] == 4
