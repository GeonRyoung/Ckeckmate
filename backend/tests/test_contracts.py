from uuid import uuid4

import pytest
from pydantic import ValidationError
from checkmate.contracts import ExplanationRequest, ExplanationResponse, Versions


def request(**changes):
    return dict(requestId=str(uuid4()), profileId=None,
                warning={"type": "TPMS", "rawState": "ON"}, **changes)


def test_request_rejects_unnecessary_personal_fields_and_free_questions():
    for extra in ({"location": "Seoul"}, {"history": []}, {"question": "왜?"}):
        with pytest.raises(ValidationError):
            ExplanationRequest.model_validate(request(**extra))


def test_missing_profile_can_be_reported_as_business_status():
    assert ExplanationRequest.model_validate(request()).profileId is None


def test_ready_without_evidence_is_invalid():
    with pytest.raises(ValidationError):
        ExplanationResponse(**request(), status="READY", versions=Versions(index="test"))


def test_unsupported_intent_is_rejected():
    with pytest.raises(ValidationError):
        ExplanationRequest.model_validate(request(intent="FREE_CHAT"))
