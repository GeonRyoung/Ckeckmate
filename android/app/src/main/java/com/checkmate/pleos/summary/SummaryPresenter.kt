package com.checkmate.pleos.summary

import java.time.ZoneId

data class SummaryViewState(
    val period: SummaryPeriod,
    val active: Boolean = false,
    val loading: Boolean = false,
    val body: String = "",
    val failed: Boolean = false,
)

/** Main-thread state; late queries cannot replace a new period or a hidden screen. */
class SummaryPresenter(
    initialPeriod: SummaryPeriod = SummaryPeriod.SEVEN_DAYS,
    private val load: (SummaryWindow, (Result<ServiceSummary>) -> Unit) -> Unit,
    private val changed: (SummaryViewState) -> Unit,
    private val now: () -> Long = System::currentTimeMillis,
    private val zone: () -> ZoneId = ZoneId::systemDefault,
) {
    var state = SummaryViewState(initialPeriod)
        private set
    private var generation = 0L

    fun setActive(active: Boolean) {
        if (state.active == active) return
        generation++
        state = state.copy(active = active, loading = false, body = "", failed = false)
        changed(state)
        if (active) refresh()
    }

    fun select(period: SummaryPeriod) {
        if (!state.active || state.period == period) return
        state = state.copy(period = period)
        refresh()
    }

    fun refresh() {
        if (!state.active) return
        val ticket = ++generation
        val displayZone = zone()
        val window = state.period.window(now(), displayZone)
        state = state.copy(loading = true, body = "", failed = false)
        changed(state)
        load(window) { result ->
            if (!state.active || ticket != generation) return@load
            state = result.fold(
                onSuccess = { state.copy(loading = false, body = ServiceSummaryFormatter.format(it, displayZone), failed = false) },
                onFailure = { state.copy(loading = false, body = "", failed = true) },
            )
            changed(state)
        }
    }
}
