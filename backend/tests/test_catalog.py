import pytest
from pydantic import ValidationError
from checkmate.catalog import Catalog, load_catalog


def test_seed_contains_reviewed_summaries_not_original_copies():
    catalog = load_catalog()
    assert len(catalog.chunks) == 10
    assert catalog.profiles[0].supportedWarnings == ["TPMS", "ELECTRONIC_PARKING_BRAKE"]
    assert all(len(c.warningTags) == 1 for c in catalog.chunks)  # no evidence shared across warnings
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


def test_epb_conditions_keep_startup_check_recovery_and_emergency_limits_separate():
    texts = {c.id: c.text for c in load_catalog().chunks}
    assert "약 3초 후 꺼집니다" in texts["epb-20-cluster-check"]
    assert "시동을 끄고 잠시 기다린 후" in texts["epb-30-lamp-on"]
    assert "견인한 후 점검" in texts["epb-40-not-engaged"]
    assert "당기고 있는 동안만 작동" in texts["epb-50-emergency-braking"]
    assert "비상 상황이 아니라면" in texts["epb-50-emergency-braking"]


@pytest.mark.parametrize("mutation", ["hash", "profile", "original", "duplicate"])
def test_bad_provenance_is_rejected(mutation):
    data = load_catalog().model_dump(mode="json")
    chunk = data["chunks"][0]
    if mutation == "hash": chunk["text"] += "changed"
    if mutation == "profile": chunk["profileId"] = "another-car"
    if mutation == "original": chunk["contentKind"] = "LICENSED_ORIGINAL"
    if mutation == "duplicate": data["chunks"].append(chunk.copy())
    with pytest.raises(ValidationError): Catalog.model_validate(data)
