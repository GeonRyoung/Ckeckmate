import pytest
from pydantic import ValidationError
from checkmate.catalog import Catalog, load_catalog


def test_seed_contains_reviewed_summaries_not_original_copies():
    catalog = load_catalog()
    assert len(catalog.chunks) == 5
    assert all(c.contentKind == "REVIEWED_SUMMARY" for c in catalog.chunks)
    assert all(c.page is not None for c in catalog.chunks)
    assert not catalog.documents[0].originalIngestionApproved


def test_low_pressure_and_system_fault_conditions_stay_separate():
    texts = {c.id: c.text for c in load_catalog().chunks}
    assert "속도를 낮추고 급격한 조향을 피하며" in texts["tpms-20-low-pressure"]
    assert "3시간 이후 또는 주행 시작 후 1.6 km 이내" in texts["tpms-20-low-pressure"]
    assert "깜빡인 뒤 켜진다" in texts["tpms-30-system-alert"]
    assert "위치 표시가 사라" in texts["tpms-30-system-alert"]
    assert "약 1분간 깜빡인 뒤 켜지면" in texts["tpms-40-cluster-check"]
    assert "감지하지 못하므로" in texts["tpms-50-other-causes"]


@pytest.mark.parametrize("mutation", ["hash", "profile", "original", "duplicate"])
def test_bad_provenance_is_rejected(mutation):
    data = load_catalog().model_dump(mode="json")
    chunk = data["chunks"][0]
    if mutation == "hash": chunk["text"] += "changed"
    if mutation == "profile": chunk["profileId"] = "another-car"
    if mutation == "original": chunk["contentKind"] = "LICENSED_ORIGINAL"
    if mutation == "duplicate": data["chunks"].append(chunk.copy())
    with pytest.raises(ValidationError): Catalog.model_validate(data)
