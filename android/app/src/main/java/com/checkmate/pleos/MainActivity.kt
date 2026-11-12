package com.checkmate.pleos

import android.os.Bundle
import com.checkmate.pleos.explanation.ExplanationClient
import com.checkmate.pleos.explanation.RemoteContext
import com.checkmate.pleos.explanation.RemoteExplanation
import com.checkmate.pleos.explanation.RemoteRequestGate
import android.graphics.Typeface
import android.text.SpannableString
import android.text.Spanned
import android.text.style.RelativeSizeSpan
import android.text.style.ForegroundColorSpan
import androidx.core.view.doOnLayout
import android.content.Intent
import android.content.ActivityNotFoundException
import android.net.Uri
import com.checkmate.pleos.manual.GuideStatus
import com.checkmate.pleos.manual.ManualGuides
import com.checkmate.pleos.manual.TpmsSignalMapping
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
import com.checkmate.pleos.summary.ServiceSummaryPanel
import com.checkmate.pleos.summary.SummaryPeriod
import com.checkmate.pleos.ui.WarningLabels
import com.checkmate.pleos.ui.card
import com.checkmate.pleos.ui.chip
import com.checkmate.pleos.ui.margins
import com.checkmate.pleos.ui.optionRow
import com.checkmate.pleos.ui.styledText
import com.checkmate.pleos.ui.uiButton
import android.widget.ImageView
import android.content.res.ColorStateList
import java.util.UUID
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

class MainActivity : AppCompatActivity() {
    private lateinit var assistancePanel: com.checkmate.pleos.assistance.AssistancePanel
    private var foreground = false
    private var remoteQuestion: String? = null
    private val explanationClient = ExplanationClient(BuildConfig.EXPLANATION_BASE_URL)
    private val remoteGate = RemoteRequestGate()
    private var remoteContext: RemoteContext? = null
    private var remoteExplanation: RemoteExplanation? = null
    private var remoteLoading = false
    private var remoteMessage = ""
    private lateinit var binding: ActivityMainBinding
    private lateinit var repository: HistoryRepository
    private var sessionId: String? = null
    private var lifecycleEpoch = 0
    private var pendingWrites = 0
    private var storageError: String? = null
    private enum class Screen { CURRENT, HISTORY, DETAIL, PROFILE, SUMMARY }
    private lateinit var summaryPanel: ServiceSummaryPanel
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
    private val clockFormat = DateTimeFormatter.ofPattern("HH:mm").withZone(ZoneId.systemDefault())
    private val dayFormat = DateTimeFormatter.ofPattern("M월 d일").withZone(ZoneId.systemDefault())

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
        assistancePanel = com.checkmate.pleos.assistance.AssistancePanel(this, binding.assistancePanel, repository) {
            requestServerExplanation(it)
        }
        manualPreferences = ManualPreferences(this)
        val summaryPeriod = runCatching {
            SummaryPeriod.valueOf(savedInstanceState?.getString("summaryPeriod").orEmpty())
        }.getOrDefault(SummaryPeriod.SEVEN_DAYS)
        summaryPanel = ServiceSummaryPanel(binding.serviceSummary, repository, summaryPeriod) {
            navigate(Screen.HISTORY)
            loadHistory()
        }
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
            binding.profileOptions.addView(optionRow(profile.label).apply {
                tag = profile.id
                setOnClickListener { if (detailsAllowed) { manualPreferences.select(profile.id); render() } }
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
            if (!allowed) clearServerExplanation()
            detailsAllowed = allowed
            binding.uxStatus.text = if (allowed) "정차 중 · 상세 화면 사용 가능" else message
            render()
        }
        binding.showCurrent.setOnClickListener { navigate(Screen.CURRENT) }
        binding.showHistory.setOnClickListener {
            historyOffset = 0
            navigate(Screen.HISTORY)
            loadHistory()
        }
        binding.showProfile.setOnClickListener { navigate(Screen.PROFILE) }
        binding.showSummary.setOnClickListener { navigate(Screen.SUMMARY) }
        binding.showSummaryNav.setOnClickListener { navigate(Screen.SUMMARY) }
        binding.showDetail.setOnClickListener { if (selection != null) navigate(Screen.DETAIL) }
        binding.detailChooseProfile.setOnClickListener { navigate(Screen.PROFILE) }
        binding.detailBack.setOnClickListener {
            navigate(if (selection?.historical == true) Screen.HISTORY else Screen.CURRENT)
            if (historyVisible) loadHistory()
        }
        binding.requestServer.setOnClickListener { requestServerExplanation() }
        binding.useLocal.setOnClickListener { clearServerExplanation(); render() }
        binding.openSource.setOnClickListener {
            if (!detailsAllowed) return@setOnClickListener
            val item = selection ?: return@setOnClickListener
            val current = monitor.current.firstOrNull { it.reading.type == item.type }
            val rawState = if (!item.historical && current != null) current.reading.state else item.state
            val source = ManualGuides.get(manualPreferences.selectedId, item.type, rawState).source ?: return@setOnClickListener
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
        foreground = true
        monitor.waiting()
        uxSource.start()
        beginSession()
        render()
    }

    override fun onStop() {
        foreground = false
        detailsAllowed = false
        assistancePanel.suspend()
        summaryPanel.setActive(false)
        clearServerExplanation()
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
                page.events.forEachIndexed { index, event ->
                    binding.historyCards.addView(historyRow(event, index > 0))
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
    private fun clock(at: Long) = clockFormat.format(Instant.ofEpochMilli(at))
    private fun day(at: Long) = dayFormat.format(Instant.ofEpochMilli(at))
    private fun semibold() = android.graphics.Typeface.create(resources.getFont(R.font.pretendard), 600, false)

    private fun historyRow(event: com.checkmate.pleos.history.WarningEvent, divided: Boolean): View {
        val gap = event.eventKind.contains("GAP") || event.eventKind.contains("INTERRUPT")
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = android.view.Gravity.CENTER_VERTICAL
            setPadding(dp(20), dp(20), dp(20), dp(20))
            if (gap) setBackgroundResource(R.drawable.gap_box)
            else if (event.warningType != null) setBackgroundResource(R.drawable.button_text_background)
            layoutParams = LinearLayout.LayoutParams(-1, -2).margins(top = if (gap) dp(8) else 0, bottom = if (gap) dp(8) else 0)
        }
        row.addView(styledText(R.style.Text_Checkmate_Caption, clock(event.observedAt), 20f).apply {
            layoutParams = LinearLayout.LayoutParams(dp(92), -2)
        })
        row.addView(ImageView(this).apply {
            setImageResource(if (event.warningType != null) R.drawable.dot_ring else R.drawable.dot_ring_gray)
            layoutParams = LinearLayout.LayoutParams(dp(16), dp(16)).margins(end = dp(20))
        })
        val texts = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(0, -2, 1f)
        }
        val title = when {
            event.warningType != null -> WarningLabels.name(event.warningType)
            gap -> "관측 공백"
            else -> event.message.substringBefore(" · ")
        }
        texts.addView(styledText(R.style.Text_Checkmate_Body, title, 21f).apply { typeface = semibold() })
        texts.addView(styledText(R.style.Text_Checkmate_Caption, "${day(event.observedAt)} · ${event.message}", 16f))
        row.addView(texts)
        if (event.warningType != null) {
            val severity = WarningLabels.severity(event.warningType, event.rawState)
            row.addView(chip(WarningLabels.state(event.rawState), severity.chip, severity.text).apply {
                layoutParams = LinearLayout.LayoutParams(-2, -2).margins(start = dp(16))
            })
            row.contentDescription = "${time(event.observedAt)} ${event.message}"
            row.isClickable = true
            row.setOnClickListener {
                if (!detailsAllowed) return@setOnClickListener
                selection = WarningSelection(event.warningType, event.rawState, event.observedAt, true, event.message)
                navigate(Screen.DETAIL)
            }
        }
        if (!divided || gap) return row
        return LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            addView(View(context).apply {
                setBackgroundColor(getColor(R.color.divider))
                layoutParams = LinearLayout.LayoutParams(-1, dp(1)).margins(start = dp(20), end = dp(20))
            })
            addView(row)
        }
    }

    private fun render() {
        binding.details.isVisible = detailsAllowed
        binding.restrictionPanel.isVisible = !detailsAllowed
        binding.retry.isEnabled = detailsAllowed
        binding.previousPage.isEnabled = detailsAllowed && !historyLoading && historyOffset > 0
        binding.nextPage.isEnabled = detailsAllowed && !historyLoading && historyCount > 0 &&
            historyOffset + historyCount < historyTotal
        binding.refreshHistory.isEnabled = detailsAllowed && !historyLoading
        binding.currentPanel.isVisible = screen == Screen.CURRENT
        binding.detailPanel.isVisible = screen == Screen.DETAIL
        binding.profilePanel.isVisible = screen == Screen.PROFILE
        binding.diagnosticsPanel.isVisible = diagnosticsVisible
        binding.toggleDiagnostics.text = if (diagnosticsVisible) "간단히 보기" else "전체 변화 보기"
        binding.historyPanel.isVisible = historyVisible
        binding.serviceSummary.root.isVisible = screen == Screen.SUMMARY
        binding.showSummary.isEnabled = detailsAllowed
        summaryPanel.setActive(foreground && detailsAllowed && screen == Screen.SUMMARY)
        binding.showCurrent.isSelected = screen == Screen.CURRENT || (screen == Screen.DETAIL && selection?.historical != true)
        binding.showHistory.isSelected = screen == Screen.HISTORY || screen == Screen.SUMMARY || (screen == Screen.DETAIL && selection?.historical == true)
        binding.showProfile.isSelected = screen == Screen.PROFILE
        binding.showCurrent.isSelected = screen == Screen.CURRENT
        binding.showHistory.isSelected = screen == Screen.HISTORY
        binding.showDetail.isSelected = screen == Screen.DETAIL
        binding.showSummaryNav.isSelected = screen == Screen.SUMMARY
        binding.showCurrent.isEnabled = detailsAllowed && screen != Screen.CURRENT
        binding.showHistory.isEnabled = detailsAllowed && screen != Screen.HISTORY
        binding.showProfile.isEnabled = detailsAllowed && screen != Screen.PROFILE
        binding.showDetail.isEnabled = detailsAllowed && selection != null && screen != Screen.DETAIL
        binding.showSummaryNav.isEnabled = detailsAllowed && screen != Screen.SUMMARY
        val active = if (monitor.isCurrent) monitor.current.size else 0
        binding.currentBadge.isVisible = active > 0
        binding.currentBadge.text = active.toString()
        binding.restrictionDetail.text = if (active > 0) "정차 후 다시 확인할 수 있어요 · 현재 경고 ${active}개"
            else getString(R.string.ui_restriction_detail)
        binding.emptyCard.isVisible = monitor.current.isEmpty()
        binding.emptyTitle.text = if (monitor.isCurrent) getString(R.string.ui_empty_title) else "차량 상태를 확인하고 있습니다"
        binding.connectionDot.setImageResource(if (monitor.isCurrent) R.drawable.dot_live else R.drawable.dot_idle)
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
        binding.breadcrumb.text = "내 차량  /  " + (manualPreferences.selected?.let { vehicleName(it) } ?: "매뉴얼 미선택")
        binding.warningList.text = when {
            !monitor.isCurrent && monitor.lastReceivedAt == null -> getString(R.string.no_vehicle_data)
            !monitor.isCurrent -> getString(R.string.previous_data, warningText())
            monitor.current.isEmpty() -> getString(R.string.no_warnings)
            else -> "지금 확인이 필요한 신호가 ${monitor.current.size}개 있습니다."
        }
        renderRecentEvents()
    }

    private fun navigate(target: Screen) {
        if (!detailsAllowed) return
        clearServerExplanation()
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

    private var renderedEvents: Pair<List<com.checkmate.pleos.vehicle.Observation>, Boolean>? = null

    private fun vehicleName(profile: com.checkmate.pleos.manual.ManualProfile) =
        "${profile.modelYear} ${profile.model.removePrefix("현대 ")}"

    private fun renderRecentEvents() {
        val key = monitor.events to diagnosticsVisible
        if (renderedEvents == key) return
        renderedEvents = key
        binding.recentEvents.removeAllViews()
        val shown = if (diagnosticsVisible) monitor.events else monitor.events.take(4)
        if (shown.isEmpty()) {
            binding.recentEvents.addView(styledText(R.style.Text_Checkmate_Caption, getString(R.string.no_events)))
        }
        shown.forEachIndexed { index, event ->
            if (index > 0) binding.recentEvents.addView(View(this).apply {
                setBackgroundColor(getColor(R.color.divider))
                layoutParams = LinearLayout.LayoutParams(-1, dp(1))
            })
            binding.recentEvents.addView(LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                setPadding(0, dp(14), 0, dp(14))
                addView(styledText(R.style.Text_Checkmate_Caption, clock(event.at), 18f).apply {
                    layoutParams = LinearLayout.LayoutParams(dp(72), -2)
                })
                addView(styledText(R.style.Text_Checkmate_Body, eventLabel(event), 18f).apply {
                    layoutParams = LinearLayout.LayoutParams(0, -2, 1f)
                })
            })
        }
        binding.toggleDiagnostics.isVisible = monitor.events.size > 4 || diagnosticsVisible
    }

    private fun eventLabel(event: com.checkmate.pleos.vehicle.Observation): String {
        val type = event.warningType ?: return event.message
        return if (event.kind == "REMOVED_FROM_LIST") "${WarningLabels.name(type)} 목록 제외"
            else "${WarningLabels.name(type)} ${WarningLabels.state(event.rawState)}"
    }

    private fun renderWarningCards() {
        if (renderedWarnings == monitor.current) return
        renderedWarnings = monitor.current.toList()
        binding.warningCards.removeAllViews()
        monitor.current.forEachIndexed { index, warning ->
            binding.warningCards.addView(warningCard(warning).apply {
                layoutParams = LinearLayout.LayoutParams(-1, -2).margins(top = if (index > 0) dp(24) else 0)
            })
        }
    }

    private fun warningCard(warning: com.checkmate.pleos.vehicle.ObservedWarning): View {
        val type = warning.reading.type
        val state = warning.reading.state
        val severity = WarningLabels.severity(type, state)
        val open = {
            if (detailsAllowed) {
                selection = WarningSelection(type, state, warning.observedAt, false, "")
                navigate(Screen.DETAIL)
            }
        }
        return card(severity.card).apply {
            setPadding(dp(40), dp(36), dp(40), dp(36))
            addView(LinearLayout(context).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = android.view.Gravity.CENTER_VERTICAL
                addView(chip("●  " + WarningLabels.state(state), severity.chip, severity.text))
                addView(android.widget.Space(context), LinearLayout.LayoutParams(0, 1, 1f))
                addView(styledText(R.style.Text_Checkmate_Caption, "$type · $state  ·  ${severity.label}", 17f))
            })
            addView(ImageView(context).apply {
                setImageResource(WarningLabels.icon(type))
                imageTintList = ColorStateList.valueOf(getColor(severity.icon))
                layoutParams = LinearLayout.LayoutParams(dp(88), dp(88)).margins(top = dp(28))
            })
            addView(styledText(R.style.Text_Checkmate_Title, WarningLabels.name(type), 36f).apply {
                layoutParams = LinearLayout.LayoutParams(-2, -2).margins(top = dp(20))
            })
            addView(styledText(R.style.Text_Checkmate_Subtitle, WarningLabels.hint(type, state), 22f).apply {
                layoutParams = LinearLayout.LayoutParams(-2, -2).margins(top = dp(12))
            })
            addView(View(context).apply {
                setBackgroundColor(getColor(R.color.divider))
                layoutParams = LinearLayout.LayoutParams(-1, dp(1)).margins(top = dp(28), bottom = dp(24))
            })
            addView(LinearLayout(context).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = android.view.Gravity.CENTER_VERTICAL
                addView(styledText(R.style.Text_Checkmate_Caption, "최초 관측 시각", 18f))
                addView(styledText(R.style.Text_Checkmate_CardTitle, clock(warning.observedAt), 28f).apply {
                    layoutParams = LinearLayout.LayoutParams(-2, -2).margins(start = dp(20))
                })
            })
            addView(LinearLayout(context).apply {
                orientation = LinearLayout.HORIZONTAL
                layoutParams = LinearLayout.LayoutParams(-1, -2).margins(top = dp(28))
                addView(uiButton("원인과 대처 보기", primary = true, icon = R.drawable.ic_arrow_forward).apply {
                    tag = "open:$type"
                    contentDescription = "${WarningLabels.name(type)} 원인과 대처 보기"
                    setOnClickListener { open() }
                })
                addView(uiButton("상황별 도움받기").apply {
                    tag = "help:$type"
                    layoutParams = LinearLayout.LayoutParams(-2, -2).margins(start = dp(16))
                    setOnClickListener { open() }
                })
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
        for (i in 0 until binding.profileOptions.childCount) {
            val option = binding.profileOptions.getChildAt(i)
            option.isSelected = option.tag == manualPreferences.selectedId
        }
        binding.selectedProfile.text = if (profile != null) "현재 선택 · ${profile.label}" else description
        binding.sidebarVehicle.text = profile?.let { vehicleName(it) } ?: getString(R.string.ui_vehicle_none)
        binding.sidebarProfile.text = profile?.let { "${it.powertrain} · ${it.language} 매뉴얼 기준" } ?: getString(R.string.ui_vehicle_hint)
        if (profile == null) binding.profileSource.text = getString(R.string.ui_profile_source_empty)
    }

    private fun renderDetail() {
        val item = selection ?: run {
            assistancePanel.update(null, false, false, false)
            return
        }
        binding.detailTitle.text = WarningLabels.name(item.type)
        val current = monitor.current.firstOrNull { it.reading.type == item.type }
        binding.detailContext.text = when {
            item.historical -> "과거 관측 기록 · 현재 차량 상태가 아닙니다."
            !monitor.isCurrent -> "이전 수신 정보 · 현재 상태 확인 불가"
            current == null -> "현재 수신 목록에 없는 경고 · 선택 당시 관측값입니다."
            else -> "현재 수신 정보 · Pleos Vehicle SDK"
        }
        val state = if (!item.historical && current != null) current.reading.state else item.state
        val at = if (!item.historical && current != null) current.observedAt else item.at
        val severity = WarningLabels.severity(item.type, state)
        binding.detailIcon.setImageResource(WarningLabels.icon(item.type))
        binding.detailIcon.imageTintList = ColorStateList.valueOf(getColor(severity.icon))
        binding.detailStateChip.text = WarningLabels.state(state)
        binding.detailStateChip.setBackgroundResource(severity.chip)
        binding.detailStateChip.setTextColor(getColor(severity.text))
        binding.detailSeverityChip.text = "심각도 · ${severity.label}"
        binding.detailFacts.text = "${item.type} · 기록 상태값 ${state ?: "없음"}\n관측 시각 ${time(at)}" +
            if (item.historical) "\n${item.message}\n출처: Pleos Vehicle SDK" else ""
        val profile = manualPreferences.selected
        val context = profile?.let { RemoteContext(it.id, item.type, state.orEmpty(), at,
            item.historical, item.historical || (monitor.isCurrent && current != null)) }
        if (context != remoteContext) {
            clearServerExplanation()
            remoteContext = context
        }
        val guide = ManualGuides.get(manualPreferences.selectedId, item.type, state)
        // Order matching is defined only for TPMS (blink-then-on); other warnings show none.
        val pattern = if (guide.status == GuideStatus.READY && item.type == "TPMS") "관측 순서 대조\n" + TpmsSignalMapping.describe(state,
            !item.historical && monitor.isCurrent && current != null, monitor.events).text + "\n\n" else ""
        binding.guideTitle.text = guide.title
        binding.guideBody.text = guide.explanation
        binding.guideLimits.text = pattern + guide.observationLimit
        binding.guideCitation.text = guide.source?.let { source ->
            val profile = manualPreferences.selected!!
            "출처 · ${source.documentTitle}\n${source.section}\n" +
                "문서 버전 ${profile.documentRevision} · 확인 ${profile.checkedOn}\n${source.url}"
        }.orEmpty()
        binding.sourceCard.isVisible = guide.source != null
        binding.limitsCard.isVisible = guide.source != null
        binding.guideCitation.isVisible = guide.source != null
        binding.openSource.isVisible = guide.source != null
        binding.openSource.isEnabled = detailsAllowed && guide.source != null
        val canRequest = guide.source != null && BuildConfig.EXPLANATION_BASE_URL.isNotEmpty()
        assistancePanel.update(context, foreground && detailsAllowed && screen == Screen.DETAIL, canRequest, remoteLoading)
        assistancePanel.showAnswer(remoteQuestion?.let { question ->
            "질문: $question\n\n" + when {
                remoteLoading -> "답변을 기다리고 있습니다."
                remoteExplanation?.status == "READY" -> remoteExplanation!!.let { "${it.body}\n\n${it.limits}\n\n${it.citations}" }
                else -> "$remoteMessage\n질문에 대한 답변을 제공하지 못했습니다. 아래의 전체 매뉴얼 안내를 참고하세요."
            }
        }.orEmpty())
        binding.serverNotice.isVisible = canRequest
        binding.requestServer.isVisible = canRequest
        binding.requestServer.isEnabled = detailsAllowed && !remoteLoading && canRequest
        binding.requestServer.text = if (remoteMessage.isEmpty()) "서버 설명 요청" else "서버 설명 다시 요청"
        binding.useLocal.isVisible = remoteLoading || remoteExplanation != null
        binding.useLocal.isEnabled = detailsAllowed
        binding.serverStatus.text = when {
            remoteLoading -> "설명을 요청하고 있습니다. 첫 요청은 모델 준비로 시간이 걸릴 수 있습니다."
            remoteMessage.isNotEmpty() -> remoteMessage
            else -> ""
        }
        remoteExplanation?.takeIf { it.status == "READY" && remoteQuestion == null }?.let { remote ->
            binding.guideTitle.text = if (remote.mode == "AI_GENERATED") "AI 설명 · 서버" else "검토 요약 검색 · 서버"
            binding.guideBody.text = remote.body
            // Keep the local observation boundary even if a future server omits a specific warning.
            binding.guideLimits.text = pattern + guide.observationLimit + "\n\n" + remote.limits
            binding.guideCitation.text = remote.citations
        }
    }

    private fun clearServerExplanation() {
        if (::assistancePanel.isInitialized) assistancePanel.stopVoice()
        remoteGate.invalidate()
        explanationClient.cancel()
        remoteContext = null
        remoteExplanation = null
        remoteLoading = false
        remoteMessage = ""
        remoteQuestion = null
    }

    private fun requestServerExplanation(question: String? = null) {
        if (!foreground || !detailsAllowed || screen != Screen.DETAIL || remoteLoading) return
        val profile = manualPreferences.selected ?: return
        val context = remoteContext ?: return
        if (BuildConfig.EXPLANATION_BASE_URL.isEmpty()) return
        val ticket = remoteGate.begin()
        val requestId = UUID.randomUUID().toString()
        remoteLoading = true
        remoteExplanation = null
        remoteMessage = ""
        remoteQuestion = question
        render()
        explanationClient.request(requestId, context, profile, question) { result ->
            if (isDestroyed || !remoteGate.accepts(ticket) || !detailsAllowed ||
                screen != Screen.DETAIL || remoteContext != context) return@request
            remoteLoading = false
            val response = result.getOrNull()
            remoteExplanation = response?.takeIf { it.status == "READY" }
            remoteMessage = when (response?.status) {
                "READY" -> "서버 설명을 받았습니다. 문장에 표시된 번호로 근거를 확인하세요."
                "PROFILE_REQUIRED", "PROFILE_UNSUPPORTED" -> "서버가 선택한 매뉴얼을 지원하지 않습니다. 로컬 요약을 표시합니다."
                "WARNING_UNSUPPORTED", "STATE_UNSUPPORTED" -> "서버가 이 경고·상태를 지원하지 않습니다. 로컬 요약을 표시합니다."
                "NO_EVIDENCE" -> "서버에서 근거를 찾지 못했습니다. 검토된 로컬 요약을 표시합니다."
                else -> "서버 설명을 받지 못했습니다. 로컬 요약을 표시합니다. 잠시 후 다시 요청해 주세요."
            }
            render()
        }
    }

    override fun onDestroy() {
        assistancePanel.close()
        summaryPanel.setActive(false)
        remoteGate.invalidate()
        explanationClient.close()
        super.onDestroy()
    }

    override fun onSaveInstanceState(outState: Bundle) {
        outState.putString("screen", screen.name)
        outState.putString("summaryPeriod", summaryPanel.period.name)
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
