package com.checkmate.pleos.assistance

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.text.InputFilter
import android.text.InputType
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import com.checkmate.pleos.R
import com.checkmate.pleos.explanation.RemoteContext
import com.checkmate.pleos.history.HistoryRepository
import com.checkmate.pleos.manual.ManualCatalog
import com.checkmate.pleos.summary.ServiceSummaryFormatter
import com.checkmate.pleos.summary.SummaryPeriod
import java.time.ZoneId

/** No simulated vehicle events. Scenarios describe what the user reports about a real selection. */
class AssistancePanel(
    private val activity: AppCompatActivity,
    private val root: LinearLayout,
    private val repository: HistoryRepository,
    private val ask: (String) -> Unit,
) {
    private var context: RemoteContext? = null
    private var active = false
    private var generation = 0L
    private var selected: WarningScenario? = null
    private var reportLoading = false
    private var preview: AlertDialog? = null
    private val scenarioButtons = LinearLayout(activity).apply { orientation = LinearLayout.VERTICAL }
    private val guidance = label("")
    private val question = input("이 경고에 대해 질문하세요 (300자)", 300)
    private val symptoms = input("직접 겪은 증상과 발생 상황 (1000자)", 1000)
    private val actions = input("이미 시도한 조치와 이후 상태 (1000자)", 1000)
    private val status = label("")
    private val answer = label("")
    private val send = button("질문 보내기") {
        val text = question.text.toString().trim()
        if (text.isEmpty()) status.text = "질문을 입력해 주세요."
        else { voice.stop(); ask(text) }
    }
    private val report = button("정비 요청서 미리보기") { prepareReport() }
    private val voice = VoiceController(activity, { active }, { status.text = it })

    init {
        root.addView(label("상황별 도움받기", 26f))
        root.addView(label("직접 확인한 상황을 선택하세요. 선택한 문장은 차량 센서로 확인된 사실과 구분합니다."))
        root.addView(scenarioButtons)
        root.addView(guidance)
        root.addView(button("상황 안내 읽어주기") {
            selected?.let { voice.speak("선택한 상황에 대한 매뉴얼 안내입니다. ${it.guidance} 확인 질문입니다. ${it.check}") }
                ?: run { status.text = "먼저 상황을 선택해 주세요." }
        })
        root.addView(label("추가 질문", 24f))
        root.addView(question)
        root.addView(label("질문은 선택한 매뉴얼·경고 상태와 함께 설명 서버로 전송됩니다. 이름·연락처·차량번호는 입력하지 마세요."))
        root.addView(button("음성으로 질문 입력") { listenInto(question, 300) })
        root.addView(send)
        root.addView(answer)
        root.addView(button("질문 답변 읽어주기") {
            if (answer.text.isNotBlank()) voice.speak(answer.text.toString())
            else status.text = "먼저 질문을 보내 답변을 받아 주세요."
        })
        root.addView(label("질문 답변은 아래의 전체 매뉴얼 안내를 대신하지 않습니다."))
        root.addView(label("정비소에 전달할 내용", 24f))
        root.addView(symptoms)
        root.addView(button("음성으로 증상 입력") { listenInto(symptoms, 1000) })
        root.addView(actions)
        root.addView(label("증상·조치는 이 화면에서만 보관합니다. 경고·프로필·화면이 바뀌면 지워집니다. 음성 인식 서비스는 오디오를 서버에서 처리할 수 있습니다."))
        root.addView(report)
        root.addView(button("현대 공식 정비소 찾기") {
            open(Intent(Intent.ACTION_VIEW, Uri.parse("https://www.hyundai.com/kr/ko/service-membership/service-network/service-reservation-search")))
        })
        root.addView(label("정비소 찾기는 공식 웹사이트를 엽니다. 요청서를 자동 접수하지 않습니다. 미리보기에서 내용을 확인하고, 수신처가 안내한 방법으로 공유하세요."))
        root.addView(button("음성 중지") { voice.stop(); status.text = "음성을 중지했습니다." })
        root.addView(status)
    }

    private fun listenInto(target: EditText, limit: Int) {
        voice.listen { text ->
            if (text.length > limit) status.text = "인식한 문장이 ${limit}자를 넘었습니다. 짧게 다시 말씀해 주세요."
            else { target.setText(text); status.text = "인식한 문장을 확인하고 필요하면 수정해 주세요. 아직 전송하지 않았습니다." }
        }
    }

    fun update(next: RemoteContext?, enabled: Boolean, serverAvailable: Boolean, loading: Boolean) {
        val choices = next?.let { WarningScenarios.available(it.profileId, it.type, it.rawState) }.orEmpty()
        if (context != next) {
            reset()
            context = next
            scenarioButtons.removeAllViews()
            choices.forEach { scenario ->
                scenarioButtons.addView(button(scenario.title) {
                    voice.stop()
                    selected = scenario
                    guidance.text = "선택한 상황: ${scenario.title}\n\n확인할 내용\n${scenario.check}\n\n대처 안내\n${scenario.guidance}\n\n출처: 2025 아이오닉 5 취급설명서 · PDF ${scenario.pages}쪽"
                    question.setText(scenario.question)
                    status.text = "선택한 상황의 안내입니다. 추가 질문은 내용을 확인한 뒤 보내세요."
                })
            }
        }
        if (active && !enabled) reset()
        active = enabled && choices.isNotEmpty()
        root.isVisible = choices.isNotEmpty()
        send.isEnabled = active && serverAvailable && !loading
        send.text = if (!serverAvailable) "질문 서버가 설정되지 않았습니다" else if (loading) "질문 응답을 기다리는 중" else "질문 보내기"
        report.isEnabled = active && !reportLoading
    }

    private fun prepareReport() {
        val snapshot = context ?: return
        val profile = ManualCatalog.find(snapshot.profileId) ?: return
        val ticket = ++generation
        val situation = selected?.title
        val symptomText = symptoms.text.toString()
        val actionText = actions.text.toString()
        val zone = ZoneId.systemDefault()
        reportLoading = true
        report.isEnabled = false
        status.text = "최근 7일 관측 이력을 읽고 있습니다."
        repository.summary(SummaryPeriod.SEVEN_DAYS.window(System.currentTimeMillis(), zone)) { result ->
            if (!active || generation != ticket || context != snapshot) return@summary
            reportLoading = false
            report.isEnabled = true
            result.fold(onSuccess = { summary ->
                val body = ServiceRequest.format(profile.label, snapshot, situation, symptomText, actionText,
                    ServiceSummaryFormatter.format(summary, zone), zone)
                val text = label(body, 22f).apply { setPadding(24, 24, 24, 24); setTextIsSelectable(true) }
                val scroll = ScrollView(activity).apply {
                    setBackgroundColor(activity.getColor(R.color.surface))
                    addView(text)
                }
                preview = AlertDialog.Builder(activity, R.style.ThemeOverlay_Checkmate_Dialog).setTitle("정비 요청서 확인 · 아직 전송하지 않음")
                    .setView(scroll).setNegativeButton("닫기", null)
                    .setPositiveButton("공유 앱 선택") { _, _ ->
                        if (active && context == snapshot && generation == ticket) {
                            open(Intent.createChooser(Intent(Intent.ACTION_SEND).apply {
                                type = "text/plain"
                                putExtra(Intent.EXTRA_SUBJECT, "CHECKMATE 정비 진단 요청")
                                putExtra(Intent.EXTRA_TEXT, body)
                            }, "수신처와 내용을 확인한 뒤 전송하세요"))
                        }
                    }.show()
                status.text = "공유 앱을 열어도 정비소의 접수·전송 완료를 확인할 수는 없습니다."
            }, onFailure = { status.text = "이력을 읽지 못해 요청서를 만들지 않았습니다. 다시 시도해 주세요." })
        }
    }

    fun showAnswer(text: String) { answer.text = text }
    fun stopVoice() = voice.stop()

    fun suspend() {
        active = false
        generation++
        reportLoading = false
        voice.stop()
        preview?.dismiss()
        preview = null
    }

    private fun reset() {
        suspend()
        selected = null
        question.text.clear()
        symptoms.text.clear()
        actions.text.clear()
        guidance.text = ""
        status.text = ""
    }

    fun close() { suspend(); voice.close() }

    private fun open(intent: Intent) {
        if (!active) return
        voice.stop()
        try { activity.startActivity(intent) }
        catch (_: ActivityNotFoundException) { status.text = "이 작업을 처리할 앱이 없습니다. 미리보기의 내용을 직접 확인해 주세요." }
        catch (_: SecurityException) { status.text = "이 환경에서는 외부 앱을 열 수 없습니다." }
    }

    private fun label(value: String, size: Float = 18f) = TextView(activity).apply {
        text = value; textSize = size
        setTextColor(activity.getColor(R.color.text_primary))
        setPadding(0, 12, 0, 12)
    }

    private fun input(hintText: String, limit: Int) = EditText(activity).apply {
        hint = hintText; textSize = 20f
        contentDescription = hintText
        setTextColor(activity.getColor(R.color.text_primary))
        setHintTextColor(activity.getColor(R.color.text_secondary))
        inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE or InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS
        filters = arrayOf(InputFilter.LengthFilter(limit))
        minLines = 2; maxLines = 5
        // Drafts are deliberately not persisted in the activity saved-state bundle.
        isSaveEnabled = false
        layoutParams = LinearLayout.LayoutParams(-1, -2)
    }

    private fun button(title: String, action: () -> Unit) = Button(activity).apply {
        text = title; textSize = 20f; isAllCaps = false
        minHeight = (64 * resources.displayMetrics.density).toInt()
        setTextColor(activity.getColor(R.color.button_text))
        backgroundTintList = null
        setBackgroundResource(R.drawable.button_background)
        layoutParams = LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = 12 }
        setOnClickListener { if (active) action() }
    }
}
