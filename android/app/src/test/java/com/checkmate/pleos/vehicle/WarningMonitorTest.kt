package com.checkmate.pleos.vehicle

import org.junit.Assert.*
import org.junit.Test

class WarningMonitorTest {
    private val tpms = WarningReading("TPMS", "ON")

    @Test fun duplicateSnapshotsDoNotCreateEvents() {
        val monitor = WarningMonitor()
        repeat(3) { monitor.accept(listOf(tpms), it.toLong()) }
        assertEquals(1, monitor.events.size)
        assertEquals(0L, monitor.current.single().observedAt)
        assertEquals(2L, monitor.lastReceivedAt)
    }

    @Test fun removalAndReappearanceKeepThreeObservations() {
        val monitor = WarningMonitor()
        monitor.accept(listOf(tpms), 1)
        monitor.accept(emptyList(), 2)
        monitor.accept(listOf(tpms), 3)
        assertEquals(3, monitor.events.size)
        assertTrue(monitor.events.first().message.contains("재관측"))
        assertTrue(monitor.events[1].message.contains("해제 의미 미검증"))
    }

    @Test fun errorsDoNotClearWarningsAndResumeDoesNotInferMissingEvents() {
        val monitor = WarningMonitor()
        monitor.accept(listOf(tpms), 1)
        monitor.accept(null, 2)
        assertFalse(monitor.isCurrent)
        assertEquals(tpms, monitor.current.single().reading)
        monitor.accept(emptyList(), 3)
        assertTrue(monitor.isCurrent)
        assertEquals(2, monitor.events.size) // first observation + gap, no fabricated clear
    }

    @Test fun partialRemovalKeepsOtherWarningsAndTheirTime() {
        val monitor = WarningMonitor()
        val other = WarningReading("OTHER", "ON")
        monitor.accept(listOf(tpms, other), 1)
        monitor.accept(listOf(other), 2)
        assertEquals(other, monitor.current.single().reading)
        assertEquals(1L, monitor.current.single().observedAt)
        assertTrue(monitor.events.first().message.startsWith("TPMS"))
    }

    @Test fun stateChangesAndGapsHaveDifferentMeaning() {
        val monitor = WarningMonitor()
        monitor.accept(listOf(tpms), 1)
        monitor.accept(listOf(tpms.copy(state = "BLINK")), 2)
        assertTrue(monitor.events.first().message.contains("상태 변경"))
        monitor.unavailable("connection lost", 3)
        monitor.accept(listOf(tpms), 4)
        assertTrue(monitor.events.first().message.contains("관측 재개"))
        assertEquals(4L, monitor.current.single().observedAt)
    }

    @Test fun invalidDuplicateTypesAreNotAcceptedAsCurrentData() {
        val monitor = WarningMonitor()
        monitor.accept(listOf(tpms), 1)
        monitor.accept(listOf(tpms, tpms.copy(state = "OFF")), 2)
        assertFalse(monitor.isCurrent)
        assertEquals(1L, monitor.lastReceivedAt)
    }

    @Test fun historyIsBounded() {
        val monitor = WarningMonitor()
        repeat(100) { monitor.accept(listOf(tpms.copy(state = "$it")), it.toLong()) }
        assertEquals(50, monitor.events.size)
        assertEquals(99L, monitor.events.first().at)
    }
}
