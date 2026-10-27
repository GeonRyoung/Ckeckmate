package com.checkmate.pleos.summary

import androidx.core.view.isVisible
import com.checkmate.pleos.R
import com.checkmate.pleos.databinding.PanelServiceSummaryBinding
import com.checkmate.pleos.history.HistoryRepository

class ServiceSummaryPanel(
    private val binding: PanelServiceSummaryBinding,
    repository: HistoryRepository,
    initialPeriod: SummaryPeriod,
    onBack: () -> Unit,
) {
    private val presenter = SummaryPresenter(initialPeriod,
        load = { window, callback -> repository.summary(window, callback); Unit },
        changed = ::render,
    )
    val period: SummaryPeriod get() = presenter.state.period

    init {
        binding.summaryBack.setOnClickListener { if (presenter.state.active) onBack() }
        binding.summaryToday.setOnClickListener { presenter.select(SummaryPeriod.TODAY) }
        binding.summaryWeek.setOnClickListener { presenter.select(SummaryPeriod.SEVEN_DAYS) }
        binding.summaryMonth.setOnClickListener { presenter.select(SummaryPeriod.THIRTY_DAYS) }
        binding.summaryRefresh.setOnClickListener { presenter.refresh() }
        render(presenter.state)
    }

    fun setActive(active: Boolean) = presenter.setActive(active)

    private fun render(state: SummaryViewState) {
        binding.summaryBack.isEnabled = state.active
        binding.summaryRefresh.isEnabled = state.active && !state.loading
        val buttons = listOf(
            binding.summaryToday to SummaryPeriod.TODAY,
            binding.summaryWeek to SummaryPeriod.SEVEN_DAYS,
            binding.summaryMonth to SummaryPeriod.THIRTY_DAYS,
        )
        buttons.forEach { (button, period) ->
            button.isSelected = state.period == period
            button.isEnabled = state.active && state.period != period
        }
        binding.summaryStatus.setText(when {
            state.loading -> R.string.summary_loading
            state.failed -> R.string.summary_failed
            state.body.isNotEmpty() -> R.string.summary_ready
            else -> R.string.summary_waiting
        })
        binding.summaryBody.text = state.body
        binding.summaryBody.isVisible = state.active && state.body.isNotEmpty()
    }
}
