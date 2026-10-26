import pytest
from pydantic import ValidationError
from checkmate.catalog import Catalog, load_catalog


def test_seed_contains_reviewed_summaries_not_original_copies():
    catalog = load_catalog()
    assert len(catalog.chunks) == 3
    assert all(c.contentKind == "REVIEWED_SUMMARY" for c in catalog.chunks)
    assert not catalog.documents[0].originalIngestionApproved


@pytest.mark.parametrize("mutation", ["hash", "profile", "original", "duplicate"])
def test_bad_provenance_is_rejected(mutation):
    data = load_catalog().model_dump(mode="json")
    chunk = data["chunks"][0]
    if mutation == "hash": chunk["text"] += "changed"
    if mutation == "profile": chunk["profileId"] = "another-car"
    if mutation == "original": chunk["contentKind"] = "LICENSED_ORIGINAL"
    if mutation == "duplicate": data["chunks"].append(chunk.copy())
    with pytest.raises(ValidationError): Catalog.model_validate(data)
