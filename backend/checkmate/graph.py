"""LangGraph flow for one explanation request.

check_scope -> retrieve -> answer (-> answer again once if the generated draft is rejected) -> END.
Each node only calls ExplanationService hooks, so retrieval/generation stay swappable and every
guard (profile/warning filter, state scope, citation/number validation) is the existing code.
"""
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from .catalog import Chunk, Profile
from .contracts import ExplanationRequest, ExplanationResponse, Status

MAX_ANSWER_ATTEMPTS = 2


class AnswerRejected(ValueError):
    """A generated draft failed validation; another attempt may pass."""


class ExplanationState(TypedDict, total=False):
    req: ExplanationRequest
    profile: Profile
    chunks: list[Chunk]
    attempts: int
    response: ExplanationResponse
    trace: Annotated[list[str], operator.add]


def build_graph(service):
    def check_scope(state):
        profile, status = service.check_scope(state["req"])
        if status is not None:
            return {"response": service.failure(state["req"], status), "trace": [f"check_scope:{status}"]}
        return {"profile": profile, "trace": ["check_scope:ok"]}

    def retrieve(state):
        try:
            chunks = service.find_evidence(state["req"], state["profile"])
        except service.retrieval_errors:
            return {"response": service.failure(state["req"], Status.TEMPORARILY_UNAVAILABLE),
                    "trace": ["retrieve:unavailable"]}
        if not chunks:
            return {"response": service.failure(state["req"], Status.NO_EVIDENCE), "trace": ["retrieve:empty"]}
        return {"chunks": chunks, "trace": [f"retrieve:{len(chunks)}"]}

    def answer(state):
        attempts = state.get("attempts", 0) + 1
        try:
            response = service.answer(state["req"], state["profile"], state["chunks"])
        except AnswerRejected:
            if attempts < MAX_ANSWER_ATTEMPTS:
                return {"attempts": attempts, "trace": [f"answer:rejected#{attempts}"]}
            return {"attempts": attempts, "response": service.failure(state["req"], Status.TEMPORARILY_UNAVAILABLE),
                    "trace": [f"answer:rejected#{attempts}"]}
        except service.answer_errors:
            # Timeouts and provider errors are not retried; a retry would only double the wait.
            return {"attempts": attempts, "response": service.failure(state["req"], Status.TEMPORARILY_UNAVAILABLE),
                    "trace": ["answer:unavailable"]}
        return {"attempts": attempts, "response": response, "trace": [f"answer:{response.mode}"]}

    def done_or(next_node):
        return lambda state: END if "response" in state else next_node

    graph = StateGraph(ExplanationState)
    graph.add_node("check_scope", check_scope)
    graph.add_node("retrieve", retrieve)
    graph.add_node("answer", answer)
    graph.add_edge(START, "check_scope")
    graph.add_conditional_edges("check_scope", done_or("retrieve"), ["retrieve", END])
    graph.add_conditional_edges("retrieve", done_or("answer"), ["answer", END])
    graph.add_conditional_edges("answer", done_or("answer"), ["answer", END])
    return graph.compile()
