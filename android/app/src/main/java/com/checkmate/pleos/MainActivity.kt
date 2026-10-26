package com.checkmate.pleos

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.isVisible
import com.checkmate.pleos.databinding.ActivityMainBinding
import com.checkmate.pleos.vehicle.PleosWarningSource
import com.checkmate.pleos.vehicle.UxRestrictionSource
import com.checkmate.pleos.vehicle.WarningMonitor
import com.checkmate.pleos.history.HistoryRepository
import java.util.UUID
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private lateinit var repository: HistoryRepository
    private var sessionId: String? = null
    private var lifecycleEpoch = 0
    private var pendingWrites = 0
    private var storageError: String? = null
    private var historyVisible = false
    private var historyOffset = 0
    private var historyRequest = 0
    private var historyDirty = false
    private val monitor = WarningMonitor { observation ->
        sessionId?.let { id ->
            historyDirty = true
            pendingWrites++
            repository.append(id, observation, ::stored)
        }
    }
    private lateinit var source: PleosWarningSource
    private lateinit var uxSource: UxRestrictionSource
    private var detailsAllowed = false
    private val timeFormat = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss").withZone(ZoneId.systemDefault())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        ViewCompat.setOnApplyWindowInsetsListener(binding.root) { view, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            insets
        }
        ViewCompat.requestApplyInsets(binding.root)
        repository = HistoryRepository.get(this)
        source = PleosWarningSource(this,
            onReadings = {
                val at = System.currentTimeMillis()
                monitor.accept(it, at)
                if (monitor.isCurrent) sessionId?.let { id ->
                    pendingWrites++
                    repository.received(id, at, ::stored)
                }
                render()
            },
            onError = { monitor.unavailable(it, System.currentTimeMillis()); render() },
        )
        uxSource = UxRestrictionSource(this) { allowed, message ->
            detailsAllowed = allowed
            binding.uxStatus.text = message
            render()
        }
        binding.showHistory.setOnClickListener {
            historyVisible = !historyVisible
            historyOffset = 0
            if (historyVisible) loadHistory()
            render()
        }
        binding.previousPage.setOnClickListener {
            historyOffset = (historyOffset - HistoryRepository.PAGE_SIZE).coerceAtLeast(0)
            loadHistory()
        }
        binding.nextPage.setOnClickListener {
            historyOffset += HistoryRepository.PAGE_SIZE
            loadHistory()
        }
        binding.refreshHistory.setOnClickListener {
            historyOffset = 0
            loadHistory()
        }
        binding.retry.setOnClickListener {
            source.stop()
            monitor.unavailable("다시 연결", System.currentTimeMillis())
            monitor.waiting()
            render()
            finishSession("RECONNECT")
            beginSession()
        }
        render()
    }

    override fun onStart() {
        super.onStart()
        monitor.waiting()
        uxSource.start()
        beginSession()
        render()
    }

    override fun onStop() {
        source.stop()
        uxSource.stop()
        monitor.unavailable("화면 수신 중단", System.currentTimeMillis())
        finishSession("SCREEN_STOPPED")
        super.onStop()
    }

    private fun beginSession() {
        val epoch = ++lifecycleEpoch
        val id = UUID.randomUUID().toString()
        sessionId = id
        historyDirty = true
        pendingWrites++
        repository.begin(id, System.currentTimeMillis()) { result ->
            stored(result.map { Unit })
            if (isDestroyed || epoch != lifecycleEpoch) return@begin
            result.getOrNull()?.let(monitor::restoreSeen)
            source.start() // Local observation still works if storage failed; error stays visible.
        }
    }

    private fun finishSession(reason: String) {
        ++lifecycleEpoch
        sessionId?.let { id ->
            pendingWrites++
            repository.finish(id, System.currentTimeMillis(), reason, ::stored)
        }
        sessionId = null
    }

    private fun stored(result: Result<Unit>) {
        pendingWrites--
        if (isDestroyed) return
        result.exceptionOrNull()?.let { storageError = it.javaClass.simpleName }
        render()
        if (historyVisible && historyDirty && result.isSuccess && pendingWrites == 0) {
            historyOffset = 0
            loadHistory()
        }
    }

    private fun loadHistory() {
        historyDirty = false
        val request = ++historyRequest
        binding.historyEntries.text = getString(R.string.history_loading)
        binding.previousPage.isEnabled = false
        binding.nextPage.isEnabled = false
        repository.page(historyOffset) { result ->
            if (isDestroyed || request != historyRequest) return@page
            result.fold(onSuccess = { page ->
                binding.historyEntries.text = page.events.joinToString("\n\n") {
                    "${time(it.observedAt)} · ${it.message}\n출처: ${it.source}"
                }.ifEmpty { getString(R.string.history_empty) }
                binding.historyPage.text = getString(R.string.history_page,
                    page.total, if (page.total == 0) 0 else historyOffset + 1,
                    historyOffset + page.events.size)
                binding.previousPage.isEnabled = detailsAllowed && historyOffset > 0
                binding.nextPage.isEnabled = detailsAllowed && historyOffset + page.events.size < page.total
            }, onFailure = {
                binding.historyPage.text = getString(R.string.history_read_failed)
                binding.historyEntries.text = getString(R.string.history_read_failed)
            })
        }
    }

    private fun time(at: Long) = timeFormat.format(Instant.ofEpochMilli(at))

    private fun render() {
        binding.details.isVisible = detailsAllowed
        binding.restrictionNotice.isVisible = !detailsAllowed
        binding.retry.isEnabled = detailsAllowed
        binding.currentPanel.isVisible = !historyVisible
        binding.historyPanel.isVisible = historyVisible
        binding.showHistory.text = getString(if (historyVisible) R.string.show_current else R.string.show_history)
        binding.storageStatus.text = when {
            storageError != null -> getString(R.string.storage_failed, storageError)
            pendingWrites > 0 -> getString(R.string.storage_pending)
            else -> getString(R.string.storage_ready)
        }
        binding.connectionStatus.text = monitor.status
        binding.lastReceived.text = monitor.lastReceivedAt?.let {
            getString(R.string.last_received, time(it))
        } ?: getString(R.string.no_received_time)
        binding.warningList.text = when {
            !monitor.isCurrent && monitor.lastReceivedAt == null -> getString(R.string.no_vehicle_data)
            !monitor.isCurrent -> getString(R.string.previous_data, warningText())
            monitor.current.isEmpty() -> getString(R.string.no_warnings)
            else -> warningText()
        }
        binding.eventLog.text = monitor.events.joinToString("\n\n") {
            "${time(it.at)} · ${it.message}"
        }.ifEmpty { getString(R.string.no_events) }
    }

    private fun warningText() = monitor.current.joinToString("\n\n") {
        "${it.reading.type} · ${it.reading.state}\n관측 시각 ${time(it.observedAt)}"
    }.ifEmpty { getString(R.string.no_warnings) }
}
