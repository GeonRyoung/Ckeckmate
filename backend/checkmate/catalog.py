import hashlib
from datetime import date
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, model_validator
from .contracts import Contract


class Profile(Contract):
    id: str
    model: str
    modelYear: int
    powertrain: str
    market: str
    language: str
    documentId: str
    supportedWarnings: list[str]


class Document(Contract):
    id: str
    profileId: str
    title: str
    revision: str
    url: str
    sourceSha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    checkedOn: date
    originalIngestionApproved: bool = False


class Chunk(Contract):
    id: str
    documentId: str
    profileId: str
    warningTags: list[str]
    sectionTitle: str
    kind: Literal["MEANING", "MANUAL_GUIDANCE"]
    text: str = Field(min_length=1, max_length=4000)
    textSha256: str
    contentKind: Literal["REVIEWED_SUMMARY", "LICENSED_ORIGINAL"]
    retrievalApproved: bool = False
    page: int | None = Field(default=None, ge=1)


class Catalog(Contract):
    indexVersion: str
    profiles: list[Profile]
    documents: list[Document]
    chunks: list[Chunk]

    @model_validator(mode="after")
    def validate_relations(self):
        for items in (self.profiles, self.documents, self.chunks):
            if len({x.id for x in items}) != len(items):
                raise ValueError("Duplicate data ID")
        profiles = {p.id: p for p in self.profiles}
        docs = {d.id: d for d in self.documents}
        for profile in self.profiles:
            if profile.documentId not in docs or docs[profile.documentId].profileId != profile.id:
                raise ValueError("Profile/document mismatch")
        for doc in self.documents:
            url = urlparse(doc.url)
            if doc.profileId not in profiles or url.scheme != "https" or url.hostname != "ownersmanual.hyundai.com":
                raise ValueError("Invalid document provenance")
        for chunk in self.chunks:
            doc = docs.get(chunk.documentId)
            if doc is None or chunk.profileId != doc.profileId:
                raise ValueError("Chunk/profile mismatch")
            if hashlib.sha256(chunk.text.encode()).hexdigest() != chunk.textSha256:
                raise ValueError("Chunk hash mismatch")
            if chunk.contentKind == "LICENSED_ORIGINAL" and chunk.retrievalApproved and not doc.originalIngestionApproved:
                raise ValueError("Original text not approved for ingestion")
        return self


def load_catalog(path: Path | None = None) -> Catalog:
    return Catalog.model_validate_json((path or Path(__file__).parent / "data/manuals.json").read_text(encoding="utf-8"))
