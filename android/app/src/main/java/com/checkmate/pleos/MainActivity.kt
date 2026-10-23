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
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private val monitor = WarningMonitor()
    private lateinit var source: PleosWarningSource
    private lateinit var uxSource: UxRestrictionSource
    private var detailsAllowed = false
    private val timeFormat = DateTimeFormatter.ofPattern("MM-dd HH:mm:ss").withZone(ZoneId.systemDefault())

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
        source = PleosWarningSource(this,
            onReadings = { monitor.accept(it, System.currentTimeMillis()); render() },
            onError = { monitor.unavailable(it, System.currentTimeMillis()); render() },
        )
        uxSource = UxRestrictionSource(this) { allowed, message ->
            detailsAllowed = allowed
            binding.uxStatus.text = message
            render()
        }
        binding.retry.setOnClickListener {
            source.stop()
            monitor.unavailable("다시 연결", System.currentTimeMillis())
            monitor.waiting()
            render()
            source.start()
        }
        render()
    }

    override fun onStart() {
        super.onStart()
        monitor.waiting()
        uxSource.start()
        source.start()
        render()
    }

    override fun onStop() {
        source.stop()
        uxSource.stop()
        monitor.unavailable("화면 수신 중단", System.currentTimeMillis())
        super.onStop()
    }

    private fun time(at: Long) = timeFormat.format(Instant.ofEpochMilli(at))

    private fun render() {
        binding.details.isVisible = detailsAllowed
        binding.restrictionNotice.isVisible = !detailsAllowed
        binding.retry.isEnabled = detailsAllowed
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
