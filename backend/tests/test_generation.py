import json
from uuid import uuid4
import httpx
import pytest
from fastapi.testclient import TestClient
from checkmate.catalog import load_catalog
from checkmate.contracts import ExplanationRequest, Section
from checkmate.generation import GeneratedExplanation, GeneratingService, OllamaGenerator
from checkmate.main import create_app

PROFILE = load_catalog().profiles[0].id


def request():
    return ExplanationRequest(requestId=uuid4(), profileId=PROFILE, warning={"type": "TPMS", "rawState": "ON"})


class Stub:
    model = "test-model"
    def __init__(self, fault=None): self.fault = fault
    def generate(self, req, chunks):
        if self.fault == "timeout": raise httpx.ReadTimeout("private provider detail")
        sections = [Section(kind=c.kind, title=c.sectionTitle, text=c.text, citationIds=[c.id]) for c in chunks]
        if self.fault == "citation": sections[0].citationIds = ["imaginary-id"]
        if self.fault == "number": sections[0].text += " 99 psi로 조절하세요."
        if self.fault == "missing": sections.pop()
        return GeneratedExplanation(sections=sections)


def test_ai_mode_keeps_server_owned_provenance_and_limitations():
    response = GeneratingService(Stub()).explain(request())
    assert response.status == "READY"
    assert response.mode == "AI_GENERATED"
    assert response.versions.model == "test-model"
    assert response.limitations
    assert all(c.url.startswith("https://ownersmanual.hyundai.com/") for c in response.citations)


@pytest.mark.parametrize("fault", ["timeout", "citation", "number", "missing"])
def test_invalid_generation_is_not_shown(fault):
    with TestClient(create_app(GeneratingService(Stub(fault)))) as client:
        response = client.post("/v1/explanations", json=request().model_dump(mode="json"))
        assert response.status_code == 503
        assert response.json()["status"] == "TEMPORARILY_UNAVAILABLE"
        assert response.json()["sections"] == []
        assert "private provider detail" not in response.text


def test_ollama_request_and_response_contract():
    def handler(req):
        body = json.loads(req.content)
        assert body["stream"] is False
        assert "properties" in body["format"]
        assert body["model"] == "qwen2.5:7b"
        assert len(body["messages"]) == 2
        sent = {e["id"] for e in json.loads(body["messages"][1]["content"])["evidence"]}
        output = Stub().generate(request(), [c for c in load_catalog().chunks if c.id in sent])
        return httpx.Response(200, json={"model": body["model"], "done": True, "done_reason": "stop",
                                       "message": {"content": output.model_dump_json()}})
    service = GeneratingService(OllamaGenerator("qwen2.5:7b", "http://local-test", httpx.MockTransport(handler)))
    assert service.explain(request()).status == "READY"


@pytest.mark.parametrize("provider_data", [
    {"done": False},
    {"done": True, "done_reason": "length", "model": "qwen2.5:7b"},
    {"done": True, "done_reason": "stop", "model": "qwen2.5:7b", "message": {"content": "not-json"}},
])
def test_incomplete_or_malformed_model_output_is_rejected(provider_data):
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=provider_data))
    result = GeneratingService(OllamaGenerator("qwen2.5:7b", "http://local-test", transport)).explain(request())
    assert result.status == "TEMPORARILY_UNAVAILABLE"
