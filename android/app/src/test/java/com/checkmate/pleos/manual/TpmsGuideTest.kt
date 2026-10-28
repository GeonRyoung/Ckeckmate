package com.checkmate.pleos.manual

import org.junit.Assert.*
import org.junit.Test

class TpmsGuideTest {
    private val profile = ManualCatalog.profiles.single()

    @Test fun missingAndUnavailableProfilesDoNotReturnEvidence() {
        val absent = TpmsGuide.get(null, "TPMS", "ON")
        val unknown = TpmsGuide.get("other-car", "TPMS", "ON")
        assertEquals(GuideStatus.PROFILE_REQUIRED, absent.status)
        assertEquals(GuideStatus.PROFILE_UNAVAILABLE, unknown.status)
        assertNull(absent.source)
        assertNull(unknown.source)
    }

    @Test fun unsupportedWarningCannotReuseTpmsExplanation() {
        val guide = TpmsGuide.get(profile.id, "ABS", "ON")
        assertEquals(GuideStatus.UNSUPPORTED_WARNING, guide.status)
        assertNull(guide.source)
    }

    @Test fun unknownAndMissingStatesDoNotAcquireAnInterpretation() {
        listOf(null, "OFF", "UNKNOWN").forEach { state ->
            val guide = TpmsGuide.get(profile.id, "TPMS", state)
            assertEquals(GuideStatus.UNSUPPORTED_STATE, guide.status)
            assertNull(guide.source)
        }
    }

    @Test fun onAndBlinkShareEvidenceButNeverClaimADiagnosisFromTheRawState() {
        val on = TpmsGuide.get(profile.id, "TPMS", "ON")
        val blink = TpmsGuide.get(profile.id, "TPMS", "BLINK")
        assertEquals(GuideStatus.READY, on.status)
        assertEquals(on.explanation, blink.explanation)
        assertEquals(profile.source, on.source)
        assertEquals(profile.source, blink.source)
        assertTrue(on.observationLimit.contains("ON 값만으로"))
        assertTrue(blink.observationLimit.contains("BLINK 값만으로"))
        assertTrue(blink.observationLimit.contains("확정할 수 없습니다"))
    }

    @Test fun offlineGuideKeepsLowPressureAndSystemFaultBranchesSeparate() {
        val text = TpmsGuide.get(profile.id, "TPMS", "ON").explanation
        assertTrue(text.contains("저압 타이어 감지"))
        assertTrue(text.contains("시스템 이상 표시"))
        assertTrue(text.contains("약 1분간 깜빡인 뒤 켜지는"))
        assertTrue(text.contains("저압이 해소되었다는 뜻은 아닙니다"))
        assertTrue(text.contains("감지하지 못합니다"))
    }
}
