package com.checkmate.pleos.summary

import java.time.ZoneId
import org.junit.Assert.*
import org.junit.Test

class SummaryPresenterTest {
    private class Pending(val window: SummaryWindow, val callback: (Result<ServiceSummary>) -> Unit) {
        fun succeed() = callback(Result.success(ServiceSummary(window, emptyList(), emptyList(), emptyList())))
    }
    private val pending = mutableListOf<Pending>()
    private var clock = 1_793_070_000_000L
    private val presenter = SummaryPresenter(
        load = { window, callback -> pending.add(Pending(window, callback)); Unit },
        changed = {}, now = { clock }, zone = { ZoneId.of("Asia/Seoul") },
    )

    @Test fun hiddenScreenCannotRequestOrChangePeriod() {
        presenter.refresh()
        presenter.select(SummaryPeriod.TODAY)
        assertTrue(pending.isEmpty())
        assertEquals(SummaryPeriod.SEVEN_DAYS, presenter.state.period)
    }

    @Test fun changingPeriodRejectsAnOlderResultEvenWhenItArrivesLast() {
        presenter.setActive(true)
        presenter.select(SummaryPeriod.TODAY)
        assertEquals(2, pending.size)
        assertTrue(pending[0].window.startInclusive < pending[1].window.startInclusive)
        pending[1].succeed()
        val current = presenter.state.body
        pending[0].succeed()
        assertEquals(current, presenter.state.body)
        assertFalse(presenter.state.loading)
        assertEquals(SummaryPeriod.TODAY, presenter.state.period)
    }

    @Test fun restrictionOrNavigationHidesContentAndDiscardsInflightQueries() {
        presenter.setActive(true)
        presenter.setActive(false)
        pending[0].succeed()
        assertEquals("", presenter.state.body)
        assertFalse(presenter.state.loading)
        presenter.setActive(true)
        assertEquals(2, pending.size)
        pending[1].succeed()
        assertTrue(presenter.state.body.isNotEmpty())
    }

    @Test fun repeatedRendersDoNotReloadAndExplicitRefreshAdvancesCutoff() {
        presenter.setActive(true)
        presenter.setActive(true)
        assertEquals(1, pending.size)
        pending[0].succeed()
        clock += 1_000
        presenter.refresh()
        assertEquals(2, pending.size)
        assertEquals(pending[0].window.endExclusive + 1_000, pending[1].window.endExclusive)
        assertEquals("", presenter.state.body)
    }

    @Test fun queryFailureClearsOldReportAndRetryCanRecover() {
        presenter.setActive(true)
        pending[0].succeed()
        presenter.refresh()
        pending[1].callback(Result.failure(IllegalStateException("storage unavailable")))
        assertTrue(presenter.state.failed)
        assertFalse(presenter.state.loading)
        assertEquals("", presenter.state.body)
        presenter.refresh()
        pending[2].succeed()
        assertFalse(presenter.state.failed)
        assertTrue(presenter.state.body.isNotEmpty())
    }
}
