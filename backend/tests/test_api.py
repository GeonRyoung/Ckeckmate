from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from checkmate.catalog import load_catalog
from checkmate.main import create_app
from checkmate.service import ExplanationService, retrieve

PROFILE = load_catalog().profiles[0].id


def payload(profile=PROFILE, type="TPMS", state="ON"):
    return {"requestId": str(uuid4()), "profileId": profile,
            "warning": {"type": type, "rawState": state}, "intent": "WARNING_OVERVIEW"}


def test_ready_links_each_section_to_actual_source_and_preserves_request():
    with TestClient(create_app()) as client:
        req = payload()
        response = client.post("/v1/explanations", json=req)
        assert response.status_code == 200
        data = response.json()
        assert data["requestId"] == req["requestId"]
        assert data["warning"] == req["warning"]
        assert data["mode"] == "REVIEWED_RETRIEVAL"
        assert len(data["sections"]) == 5
        assert data["sections"][0]["kind"] == "MEANING"
        ids = {c["id"] for c in data["citations"]}
        assert all(set(s["citationIds"]) <= ids for s in data["sections"])
        assert all(c["url"] == "https://ownersmanual.hyundai.com/full_pdf/NE1/2025/ko_KR" for c in data["citations"])
        assert [c["page"] for c in data["citations"]] == [493, 495, 495, 138, 496]
        assert data["versions"]["document"] == "2025-04-16"
        assert client.get("/health").json()["status"] == "ok"
        assert client.get("/v1/manual-profiles").json()["profiles"][0]["id"] == PROFILE


@pytest.mark.parametrize("profile,kind,state,expected", [
    (None, "TPMS", "ON", "PROFILE_REQUIRED"),
    ("wrong-year", "TPMS", "ON", "PROFILE_UNSUPPORTED"),
    (PROFILE, "ABS", "ON", "WARNING_UNSUPPORTED"),
    (PROFILE, "TPMS", "OFF", "STATE_UNSUPPORTED"),
])
def test_failures_never_contain_explanations(profile, kind, state, expected):
    with TestClient(create_app()) as client:
        result = client.post("/v1/explanations", json=payload(profile, kind, state)).json()
        assert result["status"] == expected
        assert result["sections"] == result["citations"] == []
        assert result["mode"] == "NONE"


def test_no_evidence_when_all_chunks_are_unapproved():
    catalog = load_catalog().model_copy(deep=True)
    for c in catalog.chunks: c.retrievalApproved = False
    with TestClient(create_app(ExplanationService(catalog))) as client:
        assert client.post("/v1/explanations", json=payload()).json()["status"] == "NO_EVIDENCE"


def test_retrieval_never_crosses_profile_boundary():
    catalog = load_catalog().model_copy(deep=True)
    for c in catalog.chunks: c.profileId = "another-car"
    assert retrieve(catalog, PROFILE, "TPMS") == []


def test_blink_does_not_change_evidence_into_a_diagnosis():
    with TestClient(create_app()) as client:
        on = client.post("/v1/explanations", json=payload()).json()
        blink = client.post("/v1/explanations", json=payload(state="BLINK")).json()
        assert on["sections"] == blink["sections"]
        assert on["limitations"] == blink["limitations"]


def test_epb_overview_uses_only_epb_evidence_and_its_own_limits():
    with TestClient(create_app()) as client:
        data = client.post("/v1/explanations", json=payload(type="ELECTRONIC_PARKING_BRAKE")).json()
        tpms = client.post("/v1/explanations", json=payload()).json()
    assert data["status"] == "READY"
    assert [c["id"] for c in data["citations"]][0] == "epb-10-overview"
    assert all(c["id"].startswith("epb-") for c in data["citations"]) and len(data["citations"]) == 5
    assert "약 3초" in data["limitations"][0] and data["limitations"] != tpms["limitations"]


def test_epb_blink_is_not_described_because_the_manual_only_describes_a_lit_lamp():
    with TestClient(create_app()) as client:
        data = client.post("/v1/explanations", json=payload(type="ELECTRONIC_PARKING_BRAKE", state="BLINK")).json()
    assert data["status"] == "STATE_UNSUPPORTED" and data["sections"] == []


def test_extra_fields_are_rejected_by_http_contract():
    with TestClient(create_app()) as client:
        assert client.post("/v1/explanations", json={**payload(), "vin": "private"}).status_code == 422
