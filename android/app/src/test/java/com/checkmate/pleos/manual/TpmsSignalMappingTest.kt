package com.checkmate.pleos.manual

import com.checkmate.pleos.vehicle.WarningMonitor
import com.checkmate.pleos.vehicle.WarningReading
import org.junit.Assert.*
import org.junit.Test

class TpmsSignalMappingTest {
    private fun tpms(state: String) = listOf(WarningReading("TPMS", state))
    private fun describe(monitor: WarningMonitor, current: Boolean = true) =
        TpmsSignalMapping.describe(monitor.current.single().reading.state, current, monitor.events)

    @Test fun continuousBlinkThenOnMatchesSystemFaultOrderWithoutDiagnosing() {
        val m = WarningMonitor()
        m.accept(emptyList(), 0)
        m.accept(tpms("BLINK"), 1_000)
        m.accept(tpms("BLINK"), 30_000)
        m.accept(tpms("ON"), 61_000)
        val note = describe(m)
        assertEquals(TpmsPattern.BLINK_THEN_ON, note.pattern)
        assertEquals(60_000L, note.blinkObservedMs)
        assertTrue(note.text.contains("약 60초"))
        assertTrue(note.text.contains("같은 순서"))
        assertFalse(note.text.contains("고장입니다"))
    }

    @Test fun blinkAlreadyPresentAtStartGivesOnlyALowerBound() {
        val m = WarningMonitor()
        m.accept(tpms("BLINK"), 0)
        m.accept(tpms("ON"), 20_000)
        val note = describe(m)
        assertEquals(TpmsPattern.BLINK_THEN_ON, note.pattern)
        assertTrue(note.text.contains("최소 20초"))
    }

    @Test fun onFromAContinuousRunWithoutBlinkKeepsStartupCheckAndMissedBlinkOpen() {
        val m = WarningMonitor()
        m.accept(emptyList(), 0)
        m.accept(tpms("ON"), 5_000)
        val note = describe(m)
        assertEquals(TpmsPattern.ON_WITHOUT_OBSERVED_BLINK, note.pattern)
        assertTrue(note.text.contains("약 3초"))
        assertTrue(note.text.contains("배제할 수 없습니다"))
    }

    @Test fun onAtObservationStartOrAfterAGapCannotBeSeparated() {
        val first = WarningMonitor().apply { accept(tpms("ON"), 0) }
        assertEquals(TpmsPattern.ON_PRIOR_UNKNOWN, describe(first).pattern)

        val gap = WarningMonitor()
        gap.accept(tpms("BLINK"), 0)
        gap.unavailable("연결 끊김", 10_000)
        gap.accept(tpms("ON"), 70_000)
        // The BLINK before the gap must not be joined to the ON after it.
        assertEquals(TpmsPattern.ON_PRIOR_UNKNOWN, describe(gap).pattern)
    }

    @Test fun blinkRemovedThenOnIsNotTreatedAsBlinkThenOn() {
        val m = WarningMonitor()
        m.accept(tpms("BLINK"), 0)
        m.accept(emptyList(), 10_000)
        m.accept(tpms("ON"), 20_000)
        assertEquals(TpmsPattern.ON_WITHOUT_OBSERVED_BLINK, describe(m).pattern)
    }

    @Test fun blinkIsNeverCalledLowPressureAndHistoryIsNotEvaluated() {
        val m = WarningMonitor().apply { accept(tpms("BLINK"), 0) }
        val blink = describe(m)
        assertEquals(TpmsPattern.BLINK_ONGOING, blink.pattern)
        assertTrue(blink.text.contains("아직 관측되지 않았습니다"))
        assertEquals(TpmsPattern.NOT_EVALUATED, describe(m, current = false).pattern)
        assertEquals(TpmsPattern.NOT_EVALUATED, TpmsSignalMapping.describe("OFF", true, m.events).pattern)
    }
}
