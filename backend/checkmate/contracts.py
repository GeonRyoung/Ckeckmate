from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Warning(Contract):
    type: str = Field(min_length=1, max_length=64, pattern=r"^[A-Z0-9_]+$")
    rawState: str = Field(min_length=1, max_length=32, pattern=r"^[A-Z0-9_]+$")


class ExplanationRequest(Contract):
    requestId: UUID
    profileId: str | None = Field(default=None, max_length=128)
    warning: Warning
    intent: Literal["WARNING_OVERVIEW"] = "WARNING_OVERVIEW"


class Status(StrEnum):
    READY = "READY"
    PROFILE_REQUIRED = "PROFILE_REQUIRED"
    PROFILE_UNSUPPORTED = "PROFILE_UNSUPPORTED"
    WARNING_UNSUPPORTED = "WARNING_UNSUPPORTED"
    STATE_UNSUPPORTED = "STATE_UNSUPPORTED"
    NO_EVIDENCE = "NO_EVIDENCE"
    TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"


class Section(Contract):
    kind: Literal["MEANING", "MANUAL_GUIDANCE"]
    title: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=1200)
    citationIds: list[str] = Field(min_length=1, max_length=8)


class Citation(Contract):
    id: str
    documentId: str
    chunkId: str
    documentTitle: str
    sectionTitle: str
    url: str
    page: int | None = Field(default=None, ge=1)
    contentKind: Literal["REVIEWED_SUMMARY", "LICENSED_ORIGINAL"]


class Versions(Contract):
    document: str | None = None
    index: str
    prompt: str | None = None
    model: str | None = None


class ExplanationResponse(Contract):
    requestId: UUID
    status: Status
    profileId: str | None
    warning: Warning
    mode: Literal["NONE", "REVIEWED_RETRIEVAL", "AI_GENERATED"] = "NONE"
    message: str = ""
    sections: list[Section] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    versions: Versions

    @model_validator(mode="after")
    def evidence_invariants(self):
        if self.status == Status.READY:
            if not self.sections or not self.citations or self.mode == "NONE":
                raise ValueError("Ready responses need sections, citations and an explicit mode")
            ids = [c.id for c in self.citations]
            if len(ids) != len(set(ids)):
                raise ValueError("Duplicate citations")
            if any(not set(s.citationIds) <= set(ids) for s in self.sections):
                raise ValueError("A section references unknown evidence")
        elif self.sections or self.citations or self.mode != "NONE":
            raise ValueError("Non-ready responses must not contain an explanation")
        return self
