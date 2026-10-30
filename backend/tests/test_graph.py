from uuid import uuid4

import httpx

from checkmate.catalog import load_catalog
from checkmate.contracts import ExplanationRequest, Section
from checkmate.generation import GeneratedExplanation, GeneratingService
from checkmate.retrieval import OllamaEmbeddingRanker
from checkmate.service import ExplanationService

PROFILE = load_catalog().profiles[0].id


def request(type="TPMS", state="ON", profile=PROFILE, question=None):
    return ExplanationRequest(requestId=uuid4(), profileId=profile, warning={"type": type, "rawState": state},
        intent="QUESTION" if question else "WARNING_OVERVIEW", question=question)


def run(service, req):
    return service.graph.invoke({"req": req})


class FlakyGenerator:
    """Fails validation `failures` times (cites an unknown id), then answers correctly."""
    model = "stub"

    def __init__(self, failures):
        self.failures, self.calls = failures, 0

    def generate(self, req, chunks):
        self.calls += 1
        bad = self.calls <= self.failures
        return GeneratedExplanation(sections=[Section(kind=c.kind, title=c.sectionTitle, text=c.text,
            citationIds=["made-up"] if bad else [c.id]) for c in chunks])


def test_out_of_scope_requests_stop_before_retrieval():
    for req in [request(profile=None), request(profile="other-car"), request(type="ABS"),
                request(type="ELECTRONIC_PARKING_BRAKE", state="BLINK")]:
        state = run(ExplanationService(), req)
        assert state["trace"] == [f"check_scope:{state['response'].status}"]
        assert "chunks" not in state


def test_reviewed_path_and_question_path():
    overview = run(ExplanationService(), request())
    assert overview["trace"] == ["check_scope:ok", "retrieve:5", "grade:ok", "answer:REVIEWED_RETRIEVAL"]
    question = run(ExplanationService(), request(question="예비 타이어로 바꿨어요"))
    # The lexical baseline has uncalibrated scores, so it never abstains.
    assert question["trace"] == ["check_scope:ok", "retrieve:3", "grade:ok", "answer:REVIEWED_RETRIEVAL"]


def test_rejected_draft_is_retried_once_then_accepted():
    generator = FlakyGenerator(failures=1)
    state = run(GeneratingService(generator), request())
    assert state["trace"][-2:] == ["answer:rejected#1", "answer:AI_GENERATED"]
    assert state["response"].status == "READY" and generator.calls == 2


def test_repeated_rejection_becomes_unavailable_without_a_partial_answer():
    generator = FlakyGenerator(failures=5)
    state = run(GeneratingService(generator), request())
    assert generator.calls == 2
    assert state["response"].status == "TEMPORARILY_UNAVAILABLE" and state["response"].sections == []


def test_provider_timeout_is_not_retried():
    class Slow:
        model, calls = "stub", 0
        def generate(self, req, chunks):
            self.calls += 1
            raise httpx.ReadTimeout("slow")
    generator = Slow()
    state = run(GeneratingService(generator), request())
    assert generator.calls == 1 and state["trace"][-1] == "answer:unavailable"


def test_retrieval_failure_ends_before_answer():
    down = OllamaEmbeddingRanker("bge-m3", "http://ollama", transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    state = run(ExplanationService(ranker=down), request(question="체인 감았어요"))
    assert state["trace"] == ["check_scope:ok", "retrieve:unavailable"]
