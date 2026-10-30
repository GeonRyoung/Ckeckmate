from checkmate.catalog import load_catalog
from checkmate.evaluation import evaluate, load_cases
from checkmate.service import ExplanationService

REFUSALS = {"other-model", "other-warning", "off-is-normal", "no-profile", "epb-blink-unsupported"}


def test_eval_cases_reference_existing_evidence_of_their_own_warning():
    data, catalog = load_cases(), load_catalog()
    tags = {c.id: c.warningTags for c in catalog.chunks}
    assert data["profileId"] in {p.id for p in catalog.profiles}
    assert len({c["id"] for c in data["cases"]}) == len(data["cases"])
    assert REFUSALS == {c["id"] for c in data["cases"] if c.get("expectedStatus", "READY") != "READY"}
    for case in data["cases"]:
        if case.get("questionOnly"):
            assert case["expectedQuestionStatus"] == "NO_EVIDENCE" and "relevantChunks" not in case, case["id"]
        elif case["id"] not in REFUSALS:
            assert case["relevantChunks"] and case["mustInclude"], case["id"]
            assert all(case.get("type", "TPMS") in tags[c] for c in case["relevantChunks"]), case["id"]


def test_reviewed_overview_passes_every_case_and_refusals_hold_for_questions():
    data = load_cases()
    report = evaluate(ExplanationService(), data)
    assert report["WARNING_OVERVIEW"]["failures"] == []
    assert report["WARNING_OVERVIEW"]["passed"] == len([c for c in data["cases"] if not c.get("questionOnly")])
    assert not REFUSALS & {f["id"] for f in report["QUESTION"]["failures"]}
    assert report["baseline"]["ranker"] == "lexical-bigram-v1"


def test_forbidden_claim_is_detected():
    data = load_cases()
    data["forbidden"] = ["경고"]  # present in every READY overview
    assert evaluate(ExplanationService(), data)["WARNING_OVERVIEW"]["passed"] == len(REFUSALS)
