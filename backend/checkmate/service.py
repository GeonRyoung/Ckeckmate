import httpx

from .catalog import Catalog, Chunk, load_catalog
from .contracts import Citation, ExplanationRequest, ExplanationResponse, Section, Status, Versions
from .retrieval import LexicalRanker, QuestionRanker

GENERAL_LIMITATION = "선택한 매뉴얼의 일반 설명이며 실제 연결 차량을 식별하거나 진단한 결과가 아닙니다."
# Per SDK warning type: states the manual actually describes, and what the raw state cannot tell.
WARNING_SCOPE = {
    "TPMS": ({"ON", "BLINK"}, [
        "SDK의 ON 또는 BLINK 값만으로 저압이나 시스템 고장을 확정할 수 없습니다. 깜빡임의 지속 시간과 이후 점등 패턴은 별도 확인이 필요합니다.",
        "타이어별 압력·위치, 정확한 원인, 주행 가능 여부, 수리 완료 여부는 확인하지 못했습니다.",
    ]),
    # The manual describes the EPB lamp as lit only; blinking belongs to the separate brake lamp.
    "ELECTRONIC_PARKING_BRAKE": ({"ON"}, [
        "SDK의 ON 값만으로 시동 직후 약 3초 점검 점등, 스위치 과다 조작, 실제 주차 브레이크 이상을 구분할 수 없습니다.",
        "주차 브레이크 체결 여부, 브레이크 경고등·ESC 경고등 동시 점등, 정확한 원인과 수리 완료 여부는 확인하지 못했습니다.",
    ]),
}


def limitations(warning_type: str) -> list[str]:
    return WARNING_SCOPE.get(warning_type, (set(), []))[1] + [GENERAL_LIMITATION]
MESSAGES = {
    Status.PROFILE_REQUIRED: "설명에 사용할 매뉴얼 프로필을 선택해 주세요.",
    Status.PROFILE_UNSUPPORTED: "서버가 해당 매뉴얼 프로필을 지원하지 않습니다.",
    Status.WARNING_UNSUPPORTED: "선택한 매뉴얼에서 이 경고의 설명을 지원하지 않습니다.",
    Status.STATE_UNSUPPORTED: "이 원시 상태값에 대한 설명은 지원하지 않습니다.",
    Status.NO_EVIDENCE: "선택한 범위에서 설명에 사용할 근거를 찾지 못했습니다.",
    Status.TEMPORARILY_UNAVAILABLE: "설명 서버를 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해 주세요.",
}


# Measured on evals/ioniq5_2025.json with bge-m3: TPMS hit@2 0.909, hit@3 1.0 (2026-10-28);
# TPMS+EPB hit@2 0.941 (2026-10-29).
QUESTION_TOP_K = 3


def candidates(catalog: Catalog, profile_id: str, warning_type: str) -> list[Chunk]:
    # Filter before ranking. A high score can never cross a profile or warning boundary.
    return [c for c in catalog.chunks if c.retrievalApproved
            and c.profileId == profile_id and warning_type in c.warningTags]


def retrieve(catalog: Catalog, profile_id: str, warning_type: str) -> list[Chunk]:
    terms = [warning_type.lower(), "공기압", "경고", "점검"]
    def score(chunk):
        text = (chunk.sectionTitle + " " + chunk.text).lower()
        return sum(term in text for term in terms)
    return sorted((c for c in candidates(catalog, profile_id, warning_type) if score(c) > 0),
                  key=lambda c: (-score(c), c.id))[:5]


class ExplanationService:
    mode = "reviewed"

    def __init__(self, catalog: Catalog | None = None, ranker: QuestionRanker | None = None):
        self.catalog = catalog if catalog is not None else load_catalog()
        self.ranker = ranker or LexicalRanker()

    def failure(self, req: ExplanationRequest, status: Status) -> ExplanationResponse:
        return ExplanationResponse(requestId=req.requestId, profileId=req.profileId, warning=req.warning,
            status=status, message=MESSAGES[status], limitations=limitations(req.warning.type),
            versions=Versions(index=self.catalog.indexVersion))

    def explain(self, req: ExplanationRequest) -> ExplanationResponse:
        if req.profileId is None:
            return self.failure(req, Status.PROFILE_REQUIRED)
        profile = next((p for p in self.catalog.profiles if p.id == req.profileId), None)
        if profile is None:
            return self.failure(req, Status.PROFILE_UNSUPPORTED)
        if req.warning.type not in profile.supportedWarnings:
            return self.failure(req, Status.WARNING_UNSUPPORTED)
        if req.warning.rawState not in WARNING_SCOPE.get(req.warning.type, (set(), []))[0]:
            return self.failure(req, Status.STATE_UNSUPPORTED)
        if req.intent == "QUESTION":
            pool = candidates(self.catalog, profile.id, req.warning.type)
            try:
                # Ranking order is kept: the most relevant reviewed evidence comes first.
                chunks = self.ranker.rank(req.question, pool)[:QUESTION_TOP_K] if pool else []
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                return self.failure(req, Status.TEMPORARILY_UNAVAILABLE)
        else:
            chunks = retrieve(self.catalog, profile.id, req.warning.type)
            # The first overview uses the same reviewed evidence for ON and BLINK, not a diagnosis.
            chunks.sort(key=lambda c: (c.kind != "MEANING", c.id))
        if not chunks:
            return self.failure(req, Status.NO_EVIDENCE)
        doc = next(d for d in self.catalog.documents if d.id == profile.documentId)
        return self.compose(req, chunks, doc.revision)

    def compose(self, req: ExplanationRequest, chunks: list[Chunk], revision: str) -> ExplanationResponse:
        docs = {d.id: d for d in self.catalog.documents}
        citations = [Citation(id=c.id, chunkId=c.id, documentId=c.documentId,
            documentTitle=docs[c.documentId].title, sectionTitle=c.sectionTitle,
            url=docs[c.documentId].url, page=c.page, contentKind=c.contentKind) for c in chunks]
        sections = [Section(kind=c.kind, title=c.sectionTitle, text=c.text, citationIds=[c.id]) for c in chunks]
        return ExplanationResponse(requestId=req.requestId, profileId=req.profileId, warning=req.warning,
            status=Status.READY, mode="REVIEWED_RETRIEVAL", sections=sections,
            citations=citations, limitations=limitations(req.warning.type),
            versions=Versions(document=revision, index=self.catalog.indexVersion))
