package com.checkmate.pleos.summary

import java.time.Instant
import java.time.ZoneId
import org.junit.Assert.*
import org.junit.Test

class ServiceSummaryTest {
    private val korea = ZoneId.of("Asia/Seoul")
    private fun epoch(text: String) = Instant.parse(text).toEpochMilli()

    @Test fun calendarPeriodsIncludeTodayAndStopAtTheQueryTime() {
        val now = epoch("2026-10-27T03:00:00Z")
        assertEquals(epoch("2026-10-26T15:00:00Z"), SummaryPeriod.TODAY.window(now, korea).startInclusive)
        assertEquals(epoch("2026-10-20T15:00:00Z"), SummaryPeriod.SEVEN_DAYS.window(now, korea).startInclusive)
        assertEquals(epoch("2026-09-27T15:00:00Z"), SummaryPeriod.THIRTY_DAYS.window(now, korea).startInclusive)
        assertEquals(now + 1, SummaryPeriod.TODAY.window(now, korea).endExclusive)
    }

    @Test fun midnightAndDaylightSavingUseLocalCalendarBoundaries() {
        val midnight = epoch("2026-10-26T15:00:00Z")
        assertEquals(SummaryWindow(midnight, midnight + 1), SummaryPeriod.TODAY.window(midnight, korea))
        val newYork = ZoneId.of("America/New_York")
        val now = epoch("2026-03-08T16:00:00Z")
        assertEquals(epoch("2026-03-08T05:00:00Z"), SummaryPeriod.TODAY.window(now, newYork).startInclusive)
        assertEquals(epoch("2026-03-02T05:00:00Z"), SummaryPeriod.SEVEN_DAYS.window(now, newYork).startInclusive)
    }

    @Test fun invalidOrEmptyWindowsAreRejected() {
        assertTrue(runCatching { SummaryWindow(2, 1) }.isFailure)
        assertTrue(runCatching { SummaryWindow(1, 1) }.isFailure)
    }

    @Test fun emptyHistoryDoesNotClaimAHealthyVehicleOrContinuousObservation() {
        val text = ServiceSummaryFormatter.format(ServiceSummary(SummaryWindow(1, 2), emptyList(), emptyList(), emptyList()), korea)
        assertTrue(text.contains("전체 변화 기록 0개"))
        assertTrue(text.contains("차량 정상 여부를 뜻하지 않습니다"))
        assertTrue(text.contains("공백 기록이 없어도 연속 수신을 보장하지 않습니다"))
        assertTrue(text.contains("기간 이전부터 유지된 경고"))
    }

    @Test fun gapsRemainVisibleWhenThereAreNoWarningRecords() {
        val summary = ServiceSummary(SummaryWindow(1, 4), emptyList(),
            listOf(SummaryEventCount("OBSERVATION_GAP", 1), SummaryEventCount("RECOVERY_GAP", 1)),
            listOf(SummaryRecord(3, "RECOVERY_GAP", null, null), SummaryRecord(2, "OBSERVATION_GAP", null, null)))
        val text = ServiceSummaryFormatter.format(summary, korea)
        assertTrue(text.contains("전체 변화 기록 2개 · 경고 종류 0개"))
        assertTrue(text.contains("수신 중단 기록 1개 · 이전 수신 구간 종료 시각 미확인 기록 1개"))
    }

    @Test fun removalStateIsClearlyAnEarlierReadingAndResumeIsNotAFaultCount() {
        val summary = ServiceSummary(SummaryWindow(1, 4),
            listOf(WarningRollup("TPMS", 2, 2, 3, "ON,BLINK", 0, 0, 0, 1, 1)),
            listOf(SummaryEventCount("REMOVED_FROM_LIST", 1), SummaryEventCount("OBSERVATION_RESUMED", 1)),
            listOf(SummaryRecord(3, "REMOVED_FROM_LIST", "TPMS", "ON"),
                SummaryRecord(2, "OBSERVATION_RESUMED", "TPMS", "BLINK")))
        val text = ServiceSummaryFormatter.format(summary, korea)
        assertTrue(text.contains("TPMS · 제외 전 기록 상태 ON · 목록 제외 관측"))
        assertTrue(text.contains("관측 재개 1 · 목록 제외 1"))
        assertTrue(text.contains("기록 수는 고장 발생 횟수가 아닙니다"))
        assertFalse(text.contains("고장 2회"))
    }

    @Test fun totalsStayIndependentOfTheLimitedDetailSample() {
        val summary = ServiceSummary(SummaryWindow(1, 100),
            listOf(WarningRollup("TPMS", 70, 1, 70, "ON", 1, 69, 0, 0, 0)),
            listOf(SummaryEventCount("FIRST_OBSERVED", 1), SummaryEventCount("STATE_CHANGED", 69)),
            listOf(SummaryRecord(70, "STATE_CHANGED", "TPMS", "ON")))
        val text = ServiceSummaryFormatter.format(summary, korea)
        assertTrue(text.contains("TPMS · 변화 기록 70개"))
        assertTrue(text.contains("최신순 1개 / 전체 70개"))
        assertTrue(text.contains("이전 69개의 상세는 생략했습니다"))
        assertTrue(text.contains("Asia/Seoul"))
    }
}
