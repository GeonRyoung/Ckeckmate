package com.checkmate.pleos

import android.os.Bundle
import android.graphics.Typeface
import android.text.SpannableString
import android.text.Spanned
import android.text.style.RelativeSizeSpan
import android.text.style.ForegroundColorSpan
import androidx.core.view.doOnLayout
import android.content.Intent
import android.content.ActivityNotFoundException
import android.net.Uri
import com.checkmate.pleos.manual.TpmsGuide
import android.widget.Button
import android.widget.TextView
import android.widget.LinearLayout
import android.view.View
import com.checkmate.pleos.manual.ManualCatalog
import com.checkmate.pleos.manual.ManualPreferences
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
    private enum class Screen { CURRENT, HISTORY, DETAIL, PROFILE }
    private var screen = Screen.CURRENT
    private val historyVisible get() = screen == Screen.HISTORY
    private var diagnosticsVisible = false
    private lateinit var manualPreferences: ManualPreferences
    private var selection: WarningSelection? = null
    private var renderedWarnings: List<com.checkmate.pleos.vehicle.ObservedWarning>? = null
    private data class WarningSelection(val type: String, val state: String?, val at: Long,
        val historical: Boolean, val message: String)

    private var historyOffset = 0
    private var historyRequest = 0
    private var historyDirty = false
    private var historyLoading = false
    private var historyTotal = 0
    private var historyCount = 0
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
            val margin = (24 * resources.displayMetrics.density).toInt()
            view.setPadding(bars.left + margin, bars.top + margin, bars.right + margin, bars.bottom + margin)
            insets
        }
        ViewCompat.requestApplyInsets(binding.root)
        binding.contentScroll.doOnLayout { scroll ->
            binding.content.layoutParams = binding.content.layoutParams.apply {
                width = minOf(scroll.width, dp(1080))
                (this as android.widget.FrameLayout.LayoutParams).gravity = android.view.Gravity.CENTER_HORIZONTAL
            }
        }
        repository = HistoryRepository.get(this)
        manualPreferences = ManualPreferences(this)
        savedInstanceState?.let { saved ->
            screen = runCatching { Screen.valueOf(saved.getString("screen").orEmpty()) }.getOrDefault(Screen.CURRENT)
            historyOffset = saved.getInt("historyOffset")
            diagnosticsVisible = saved.getBoolean("diagnostics")
            saved.getString("warningType")?.let { type ->
                selection = WarningSelection(type, saved.getString("warningState"), saved.getLong("warningAt"),
                    saved.getBoolean("historical"), saved.getString("warningMessage").orEmpty())
            }
            if (screen == Screen.DETAIL && selection == null) screen = Screen.CURRENT
        }
        ManualCatalog.profiles.forEach { profile ->
            binding.profileOptions.addView(actionButton(profile.label) {
                manualPreferences.select(profile.id)
                render()
            })
        }
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
        binding.showCurrent.setOnClickListener { navigate(Screen.CURRENT) }
        binding.showHistory.setOnClickListener {
            historyOffset = 0
            navigate(Screen.HISTORY)
            loadHistory()
        }
        binding.showProfile.setOnClickListener { navigate(Screen.PROFILE) }
        binding.detailChooseProfile.setOnClickListener { navigate(Screen.PROFILE) }
        binding.detailBack.setOnClickListener {
            navigate(if (selection?.historical == true) Screen.HISTORY else Screen.CURRENT)
            if (historyVisible) loadHistory()
        }
        binding.openSource.setOnClickListener {
            if (!detailsAllowed) return@setOnClickListener
            val item = selection ?: return@setOnClickListener
            val current = monitor.current.firstOrNull { it.reading.type == item.type }
            val rawState = if (!item.historical && current != null) current.reading.state else item.state
            val source = TpmsGuide.get(manualPreferences.selectedId, item.type, rawState).source ?: return@setOnClickListener
            try {
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(source.url)))
                binding.sourceOpenStatus.text = ""
            } catch (_: ActivityNotFoundException) {
                binding.sourceOpenStatus.text = "원문을 열 수 있는 앱이 없습니다. 위의 원문 주소로 확인해 주세요."
            } catch (_: SecurityException) {
                binding.sourceOpenStatus.text = "이 환경에서는 외부 원문을 열 수 없습니다. 위의 원문 주소로 확인해 주세요."
            }
        }
        binding.profileBack.setOnClickListener { navigate(Screen.DETAIL) }
        binding.clearProfile.setOnClickListener { manualPreferences.select(null); render() }
        binding.toggleDiagnostics.setOnClickListener {
            diagnosticsVisible = !diagnosticsVisible
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
        if (historyVisible) loadHistory()
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
        historyLoading = true
        historyCount = 0
        val requestedOffset = historyOffset
        val request = ++historyRequest
        binding.historyCards.removeAllViews()
        binding.historyEntries.text = getString(R.string.history_loading)
        binding.previousPage.isEnabled = false
        binding.nextPage.isEnabled = false
        repository.page(requestedOffset) { result ->
            if (isDestroyed || request != historyRequest) return@page
            historyLoading = false
            result.fold(onSuccess = { page ->
                historyTotal = page.total
                historyCount = page.events.size
                binding.historyEntries.text = if (page.events.isEmpty()) getString(R.string.history_empty) else ""
                page.events.forEach { event ->
                    if (event.warningType != null) {
                        binding.historyCards.addView(actionButton("${time(event.observedAt)}\n${event.message}  ›") {
                            selection = WarningSelection(event.warningType, event.rawState, event.observedAt, true, event.message)
                            navigate(Screen.DETAIL)
                        })
                    } else {
                        binding.historyCards.addView(TextView(this).apply {
                            text = "${time(event.observedAt)}\n${event.message}"
                            textSize = 18f
                            setTextColor(getColor(R.color.text_secondary))
                            setPadding(16, 20, 16, 20)
                        })
                    }
                }
                binding.historyPage.text = getString(R.string.history_page,
                    page.total, if (page.events.isEmpty()) 0 else requestedOffset + 1,
                    requestedOffset + page.events.size)
            }, onFailure = {
                binding.historyPage.text = getString(R.string.history_read_failed)
                binding.historyEntries.text = getString(R.string.history_read_failed)
            })
            render()
        }
    }

    private fun time(at: Long) = timeFormat.format(Instant.ofEpochMilli(at))

    private fun render() {
        binding.details.isVisible = detailsAllowed
        binding.restrictionNotice.isVisible = !detailsAllowed
        binding.retry.isEnabled = detailsAllowed
        binding.previousPage.isEnabled = detailsAllowed && !historyLoading && historyOffset > 0
        binding.nextPage.isEnabled = detailsAllowed && !historyLoading && historyCount > 0 &&
            historyOffset + historyCount < historyTotal
        binding.refreshHistory.isEnabled = detailsAllowed && !historyLoading
        binding.currentPanel.isVisible = screen == Screen.CURRENT
        binding.detailPanel.isVisible = screen == Screen.DETAIL
        binding.profilePanel.isVisible = screen == Screen.PROFILE
        binding.diagnosticsPanel.isVisible = diagnosticsVisible
        binding.toggleDiagnostics.text = if (diagnosticsVisible) "최근 관측 변화 접기" else "최근 관측 변화 펼치기"
        binding.historyPanel.isVisible = historyVisible
        binding.showCurrent.isSelected = screen == Screen.CURRENT || (screen == Screen.DETAIL && selection?.historical != true)
        binding.showHistory.isSelected = screen == Screen.HISTORY || (screen == Screen.DETAIL && selection?.historical == true)
        binding.showProfile.isSelected = screen == Screen.PROFILE
        binding.showCurrent.isEnabled = detailsAllowed && screen != Screen.CURRENT
        binding.showHistory.isEnabled = detailsAllowed && screen != Screen.HISTORY
        binding.showProfile.isEnabled = detailsAllowed && screen != Screen.PROFILE
        renderProfile()
        renderWarningCards()
        renderDetail()
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
            else -> "${monitor.current.size}개의 경고가 관측됐습니다. 경고를 눌러 상세를 확인하세요."
        }
        binding.eventLog.text = monitor.events.joinToString("\n\n") {
            "${time(it.at)} · ${it.message}"
        }.ifEmpty { getString(R.string.no_events) }
    }

    private fun navigate(target: Screen) {
        if (!detailsAllowed) return
        binding.sourceOpenStatus.text = ""
        screen = target
        render()
        binding.contentScroll.isFocusableInTouchMode = true
        binding.contentScroll.requestFocus()
        binding.contentScroll.post { binding.contentScroll.scrollTo(0, 0) }
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    private fun actionButton(label: String, action: () -> Unit) = Button(this).apply {
        id = View.generateViewId()
        text = SpannableString(label).apply {
            val split = label.indexOf('\n')
            if (split >= 0) {
                setSpan(RelativeSizeSpan(0.75f), split, length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                setSpan(ForegroundColorSpan(getColor(R.color.text_secondary)), split, length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
            }
        }
        backgroundTintList = null
        setBackgroundResource(R.drawable.button_background)
        setTextColor(getColor(R.color.text_primary))
        typeface = Typeface.create("sans-serif", Typeface.NORMAL)
        textSize = 24f
        setLineSpacing(dp(6).toFloat(), 1f)
        isAllCaps = false
        gravity = android.view.Gravity.START or android.view.Gravity.CENTER_VERTICAL
        minHeight = dp(88)
        setPadding(dp(24), dp(20), dp(24), dp(20))
        layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT).apply {
            bottomMargin = dp(16)
        }
        setOnClickListener { if (detailsAllowed) action() }
    }

    private fun renderWarningCards() {
        if (renderedWarnings == monitor.current) return
        renderedWarnings = monitor.current.toList()
        binding.warningCards.removeAllViews()
        monitor.current.forEach { warning ->
            binding.warningCards.addView(actionButton("${warning.reading.type} · ${warning.reading.state}  ›\n${time(warning.observedAt)} 관측") {
                selection = WarningSelection(warning.reading.type, warning.reading.state, warning.observedAt, false, "")
                navigate(Screen.DETAIL)
            })
        }
    }

    private fun renderProfile() {
        val profile = manualPreferences.selected
        val description = profile?.label ?: if (manualPreferences.selectedId == null)
            "매뉴얼 프로필 미선택" else "선택했던 매뉴얼을 사용할 수 없습니다. 다시 선택하세요."
        binding.profileBack.isVisible = selection != null
        binding.selectedProfile.text = description
        binding.detailProfile.text = description
        binding.profileSource.text = profile?.let {
            "${it.source.documentTitle}\n문서 버전 ${it.documentRevision} · 확인 ${it.checkedOn}\n${it.source.section}\n${it.source.url}"
        }.orEmpty()
        binding.clearProfile.isEnabled = detailsAllowed && manualPreferences.selectedId != null
    }

    private fun renderDetail() {
        val item = selection ?: return
        binding.detailTitle.text = "${item.type} 경고 상세"
        val current = monitor.current.firstOrNull { it.reading.type == item.type }
        binding.detailContext.text = when {
            item.historical -> "과거 관측 기록 · 현재 차량 상태가 아닙니다."
            !monitor.isCurrent -> "이전 수신 정보 · 현재 상태 확인 불가"
            current == null -> "현재 수신 목록에 없는 경고 · 선택 당시 관측값입니다."
            else -> "현재 수신 정보 · Pleos Vehicle SDK"
        }
        val state = if (!item.historical && current != null) current.reading.state else item.state
        val at = if (!item.historical && current != null) current.observedAt else item.at
        binding.detailFacts.text = "${item.type} · 기록 상태값 ${state ?: "없음"}\n관측 시각 ${time(at)}" +
            if (item.historical) "\n${item.message}\n출처: Pleos Vehicle SDK" else ""
        val guide = TpmsGuide.get(manualPreferences.selectedId, item.type, state)
        binding.guideTitle.text = guide.title
        binding.guideBody.text = guide.explanation
        binding.guideLimits.text = guide.observationLimit
        binding.guideCitation.text = guide.source?.let { source ->
            val profile = manualPreferences.selected!!
            "출처 · ${source.documentTitle}\n${source.section} — 저압 타이어 감지 / 타이어 공기압 경보 시스템 이상\n" +
                "문서 버전 ${profile.documentRevision} · 확인 ${profile.checkedOn}\n${source.url}"
        }.orEmpty()
        binding.sourceCard.isVisible = guide.source != null
        binding.limitsCard.isVisible = guide.source != null
        binding.guideCitation.isVisible = guide.source != null
        binding.openSource.isVisible = guide.source != null
        binding.openSource.isEnabled = detailsAllowed && guide.source != null
    }

    override fun onSaveInstanceState(outState: Bundle) {
        outState.putString("screen", screen.name)
        outState.putInt("historyOffset", historyOffset)
        outState.putBoolean("diagnostics", diagnosticsVisible)
        selection?.let {
            outState.putString("warningType", it.type)
            outState.putString("warningState", it.state)
            outState.putLong("warningAt", it.at)
            outState.putBoolean("historical", it.historical)
            outState.putString("warningMessage", it.message)
        }
        super.onSaveInstanceState(outState)
    }

    private fun warningText() = monitor.current.joinToString("\n\n") {
        "${it.reading.type} · ${it.reading.state}\n관측 시각 ${time(it.observedAt)}"
    }.ifEmpty { getString(R.string.no_warnings) }
}
