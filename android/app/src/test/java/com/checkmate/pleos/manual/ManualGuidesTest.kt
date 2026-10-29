package com.checkmate.pleos.manual

import org.junit.Assert.*
import org.junit.Test

class ManualGuidesTest {
    private val profile = ManualCatalog.profiles.single()
    private val epb = "ELECTRONIC_PARKING_BRAKE"

    @Test fun missingAndUnavailableProfilesDoNotReturnEvidence() {
        val absent = ManualGuides.get(null, "TPMS", "ON")
        val unknown = ManualGuides.get("other-car", epb, "ON")
        assertEquals(GuideStatus.PROFILE_REQUIRED, absent.status)
        assertEquals(GuideStatus.PROFILE_UNAVAILABLE, unknown.status)
        assertNull(absent.source)
        assertNull(unknown.source)
    }

    @Test fun unsupportedWarningCannotReuseAnotherWarningsExplanation() {
        listOf("ABS", "PARKING_BRAKE").forEach { type ->
            val guide = ManualGuides.get(profile.id, type, "ON")
            assertEquals(GuideStatus.UNSUPPORTED_WARNING, guide.status)
            assertNull(guide.source)
        }
    }

    @Test fun unknownAndMissingStatesDoNotAcquireAnInterpretation() {
        listOf(null, "OFF", "UNKNOWN").forEach { state ->
            val guide = ManualGuides.get(profile.id, "TPMS", state)
            assertEquals(GuideStatus.UNSUPPORTED_STATE, guide.status)
            assertNull(guide.source)
        }
    }

    @Test fun epbBlinkIsNotDescribedBecauseTheManualOnlyDescribesALitLamp() {
        assertEquals(GuideStatus.UNSUPPORTED_STATE, ManualGuides.get(profile.id, epb, "BLINK").status)
        assertEquals(GuideStatus.READY, ManualGuides.get(profile.id, epb, "ON").status)
    }

    @Test fun onAndBlinkShareEvidenceButNeverClaimADiagnosisFromTheRawState() {
        val on = ManualGuides.get(profile.id, "TPMS", "ON")
        val blink = ManualGuides.get(profile.id, "TPMS", "BLINK")
        assertEquals(GuideStatus.READY, on.status)
        assertEquals(on.explanation, blink.explanation)
        assertEquals(profile.source.url, on.source?.url)
        assertEquals(profile.source.contentSha256, blink.source?.contentSha256)
        assertTrue(on.observationLimit.contains("ON 값만으로"))
        assertTrue(blink.observationLimit.contains("BLINK 값만으로"))
        assertTrue(blink.observationLimit.contains("확정할 수 없습니다"))
    }

    @Test fun eachGuideCitesItsOwnSectionOfTheSameDocument() {
        val tpms = ManualGuides.get(profile.id, "TPMS", "ON").source!!
        val parking = ManualGuides.get(profile.id, epb, "ON").source!!
        assertEquals(tpms.url, parking.url)
        assertTrue(tpms.section.contains("493–496"))
        assertTrue(parking.section.contains("331–333"))
    }

    @Test fun offlineGuideKeepsLowPressureAndSystemFaultBranchesSeparate() {
        val text = ManualGuides.get(profile.id, "TPMS", "ON").explanation
        assertTrue(text.contains("저압 타이어 감지"))
        assertTrue(text.contains("시스템 이상 표시"))
        assertTrue(text.contains("약 1분간 깜빡인 뒤 켜지는"))
        assertTrue(text.contains("저압이 해소되었다는 뜻은 아닙니다"))
        assertTrue(text.contains("감지하지 못합니다"))
    }

    @Test fun epbGuideKeepsStartupCheckRecoveryAndEmergencyLimits() {
        val guide = ManualGuides.get(profile.id, epb, "ON")
        assertTrue(guide.explanation.contains("약 3초 후 꺼집니다"))
        assertTrue(guide.explanation.contains("시동을 끄고 잠시 기다린 후"))
        assertTrue(guide.explanation.contains("견인 후 점검"))
        assertTrue(guide.explanation.contains("비상 상황이 아니면"))
        assertTrue(guide.observationLimit.contains("구분할 수 없습니다"))
    }
}
