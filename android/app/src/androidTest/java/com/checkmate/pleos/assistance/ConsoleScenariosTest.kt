package com.checkmate.pleos.assistance

import android.graphics.Bitmap
import android.os.Build
import android.os.Bundle
import android.os.SystemClock
import android.view.View
import android.view.ViewGroup
import android.view.inspector.WindowInspector
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.checkmate.pleos.MainActivity
import com.checkmate.pleos.R
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

/** Opt-in E2E. All warning/UX signals enter through the real emulator console and Vehicle SDK.
 * No monitor mutation, permission override or mocked network responses.
 * Reflection only reads the released voice handle after lifecycle cancellation.
 * Run only with scripts/verify_three_scenarios.py on the named verification AVD.
 */
@RunWith(AndroidJUnit4::class)
class ConsoleScenariosTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val evidence get() = File(instrumentation.targetContext.filesDir, "console-scenarios").apply { mkdirs() }

    @Before fun requireIsolatedEmulator() {
        assumeTrue("Opt-in console E2E only", InstrumentationRegistry.getArguments().getString("verificationAvd") == "Checkmate_Verification_Empty_API_34")
        assertEquals("ranchu", Build.HARDWARE)
        assertTrue(Build.VERSION.SDK_INT >= 29)
    }

    private fun console(path: String): JSONObject {
        val connection = URL("http://127.0.0.1:8088$path").openConnection() as HttpURLConnection
        try {
            connection.requestMethod = "PUT"
            connection.connectTimeout = 5000
            connection.readTimeout = 10000
            assertEquals("Console rejected $path", 200, connection.responseCode)
            return JSONObject(connection.inputStream.bufferedReader().use { it.readText() })
        } finally { connection.disconnect() }
    }

    private fun signal(type: String, state: String) = console("/vehicle/telltales/simulator?type=$type&state=$state&color=Yellow")
    private fun views(view: View): List<View> = listOf(view) +
        if (view is ViewGroup) (0 until view.childCount).flatMap { views(view.getChildAt(it)) } else emptyList()
    private fun text(view: View) = views(view).filterIsInstance<TextView>().joinToString("\n") { it.text.toString() }

    private fun awaitUi(scenario: ActivityScenario<MainActivity>, description: String, seconds: Int = 20,
                        check: (MainActivity) -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + seconds * 1000
        var okay = false
        while (SystemClock.elapsedRealtime() < deadline) {
            scenario.onActivity { okay = check(it) }
            if (okay) return
            SystemClock.sleep(100)
        }
        var diagnostic = ""
        scenario.onActivity { diagnostic = text(it.window.decorView) }
        File(evidence, "failure.txt").writeText("$description\n$diagnostic")
        fail("Timed out: $description; see console-scenarios/failure.txt")
    }

    // Read-only lifecycle assertion; vehicle state still enters through the real SDK.
    private fun assertVoiceReleased(activity: MainActivity) {
        val panel = MainActivity::class.java.getDeclaredField("assistancePanel").apply { isAccessible = true }.get(activity)
        val voice = AssistancePanel::class.java.getDeclaredField("voice").apply { isAccessible = true }.get(panel)
        assertNull(VoiceController::class.java.getDeclaredField("tts").apply { isAccessible = true }.get(voice))
    }

    private fun voiceStopFinished(activity: MainActivity): Boolean {
        val panel = MainActivity::class.java.getDeclaredField("assistancePanel").apply { isAccessible = true }.get(activity)
        val voice = AssistancePanel::class.java.getDeclaredField("voice").apply { isAccessible = true }.get(panel)
        return VoiceController::class.java.getDeclaredField("pendingTtsStops").apply { isAccessible = true }.getInt(voice) == 0
    }

    private fun screenshot(name: String) {
        instrumentation.waitForIdleSync()
        SystemClock.sleep(350) // Let the just-requested layout/dialog frame reach the compositor.
        instrumentation.uiAutomation.takeScreenshot().let { bitmap ->
            File(evidence, "$name.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
        }
    }

    private fun runCase(id: String, type: String, consoleType: String, title: String, blink: Boolean,
                        expectedAnswer: List<String>) {
        val result = JSONObject().put("id", id).put("source", "Pleos Virtual Console -> Vehicle SDK")
            .put("runId", InstrumentationRegistry.getArguments().getString("verificationRunId"))
            .put("generation", "reviewed (no Qwen)").put("passed", false)
        val started = SystemClock.elapsedRealtime()
        try {
            console("/vehicle/controls?speed=0&accelerator=0&brake=0&steering=0")
            console("/vehicle/gear?gear=Park")
            signal("TPMS", "Off")
            signal("ElectronicParkingBrake", "Off")
            ActivityScenario.launch(MainActivity::class.java).use { scenario ->
                awaitUi(scenario, "real parked UX permission and initial SDK read") {
                    it.findViewById<View>(R.id.details).isShown &&
                        it.findViewById<TextView>(R.id.connection_status).text.contains("유효한 차량 데이터 수신")
                }
                scenario.onActivity { it.findViewById<Button>(R.id.show_profile).performClick() }
                scenario.onActivity { activity ->
                    val options = activity.findViewById<LinearLayout>(R.id.profile_options)
                    (options.getChildAt(0) as Button).performClick()
                    activity.findViewById<Button>(R.id.show_current).performClick()
                }
                if (blink) {
                    signal(consoleType, "Blink")
                    awaitUi(scenario, "SDK BLINK") { text(it.findViewById(R.id.warning_cards)).contains("$type · BLINK") }
                    SystemClock.sleep(1200)
                }
                signal(consoleType, "On")
                awaitUi(scenario, "SDK ON") { text(it.findViewById(R.id.warning_cards)).contains("$type · ON") }
                if (type == "ELECTRONIC_PARKING_BRAKE") SystemClock.sleep(3500)
                scenario.onActivity { activity ->
                    views(activity.findViewById(R.id.warning_cards)).filterIsInstance<Button>()
                        .single { it.text.startsWith("$type · ON") }.performClick()
                }
                awaitUi(scenario, "scenario panel") { it.findViewById<View>(R.id.assistance_panel).isShown }
                scenario.onActivity { activity ->
                    val root = activity.findViewById<LinearLayout>(R.id.assistance_panel)
                    assertTrue(activity.findViewById<TextView>(R.id.detail_context).text.contains("현재 수신 정보"))
                    if (blink) assertTrue(activity.findViewById<TextView>(R.id.guide_limits).text.contains("BLINK 뒤 ON"))
                    views(root).filterIsInstance<Button>().single { it.text == title }.performClick()
                    val symptom = "검증 시나리오 $id: $title"
                    views(root).filterIsInstance<EditText>()[1].setText(symptom)
                    views(root).filterIsInstance<EditText>()[2].setText("정차 후 화면 안내 확인. 정비소 점검 전.")
                    result.put("observedFacts", activity.findViewById<TextView>(R.id.detail_facts).text.toString())
                    result.put("pattern", activity.findViewById<TextView>(R.id.guide_limits).text.toString())
                    assertTrue(text(root).contains("대처 안내"))
                    if (type == "ELECTRONIC_PARKING_BRAKE") assertTrue(text(root).contains("약 3초"))
                    activity.findViewById<ScrollView>(R.id.content_scroll).scrollTo(0, root.top)
                }
                screenshot("$id-guidance")
                val requestAt = SystemClock.elapsedRealtime()
                scenario.onActivity { activity ->
                    val root = activity.findViewById<LinearLayout>(R.id.assistance_panel)
                    val send = views(root).filterIsInstance<Button>().single { it.text == "질문 보내기" }
                    assertTrue("Live question server must be configured", send.isEnabled)
                    send.performClick()
                }
                awaitUi(scenario, "live server answer", 100) {
                    it.findViewById<TextView>(R.id.server_status).text.contains("서버 설명을 받았습니다")
                }
                result.put("questionElapsedMs", SystemClock.elapsedRealtime() - requestAt)
                scenario.onActivity { activity ->
                    val root = activity.findViewById<LinearLayout>(R.id.assistance_panel)
                    val answer = views(root).filterIsInstance<TextView>().single { it !is EditText && it.text.startsWith("질문:") }
                    val answerText = answer.text.toString()
                    expectedAnswer.forEach { assertTrue("Missing required guidance: $it", answerText.contains(it)) }
                    assertTrue(answerText.contains("ownersmanual.hyundai.com"))
                    assertTrue(answerText.contains("PDF"))
                    assertFalse(answerText.contains("주행해도 됩니다"))
                    // Full local warning guidance remains available separately from focused retrieval.
                    assertTrue(activity.findViewById<TextView>(R.id.guide_title).text.contains("오프라인"))
                    result.put("answer", answerText)
                    activity.findViewById<ScrollView>(R.id.content_scroll).scrollTo(0, root.top + answer.top)
                }
                screenshot("$id-answer")
                if (id == "tpms-first") {
                    android.util.Log.i("CheckmateVoice", "verification start ${result.getString("runId")}")
                    fun clickVoice(label: String) = scenario.onActivity { activity ->
                        views(activity.findViewById(R.id.assistance_panel)).filterIsInstance<Button>()
                            .single { it.text == label }.performClick()
                    }
                    clickVoice("질문 답변 읽어주기")
                    awaitUi(scenario, "official TTS answer starts", 40) {
                        text(it.findViewById(R.id.assistance_panel)).contains("안내를 읽고 있습니다")
                    }
                    result.put("answerTtsStarted", true)
                    clickVoice("음성 중지")
                    awaitUi(scenario, "answer stop IPC acknowledgment") { voiceStopFinished(it) }
                    clickVoice("상황 안내 읽어주기")
                    awaitUi(scenario, "official TTS guidance completes", 90) {
                        text(it.findViewById(R.id.assistance_panel)).contains("음성 안내를 마쳤습니다")
                    }
                    result.put("guidanceTtsCompleted", true)
                    scenario.onActivity { activity ->
                        val buttons = views(activity.findViewById(R.id.assistance_panel)).filterIsInstance<Button>()
                        buttons.single { it.text == "상황 안내 읽어주기" }.performClick()
                        buttons.single { it.text == "음성 중지" }.performClick()
                    }
                    SystemClock.sleep(1500)
                    scenario.onActivity {
                        assertTrue(text(it.findViewById(R.id.assistance_panel)).contains("음성을 중지했습니다"))
                        assertVoiceReleased(it)
                    }
                    clickVoice("상황 안내 읽어주기")
                    awaitUi(scenario, "TTS restarts after cancellation", 40) {
                        text(it.findViewById(R.id.assistance_panel)).contains("안내를 읽고 있습니다")
                    }
                    scenario.moveToState(androidx.lifecycle.Lifecycle.State.CREATED)
                    scenario.onActivity { assertVoiceReleased(it) }
                    awaitUi(scenario, "background stop IPC acknowledgment") { voiceStopFinished(it) }
                    scenario.moveToState(androidx.lifecycle.Lifecycle.State.RESUMED)
                    result.put("backgroundReleasedTts", true)
                    awaitUi(scenario, "foreground SDK reacquisition") {
                        it.findViewById<TextView>(R.id.connection_status).text.contains("유효한 차량 데이터 수신") &&
                            views(it.findViewById(R.id.assistance_panel)).filterIsInstance<Button>()
                                .any { button -> button.text == "정비 요청서 미리보기" && button.isEnabled }
                    }
                    // Resuming reacquires vehicle context and deliberately clears prior drafts/answer.
                    scenario.onActivity { activity ->
                        val root = activity.findViewById<LinearLayout>(R.id.assistance_panel)
                        views(root).filterIsInstance<Button>().single { it.text == title }.performClick()
                        views(root).filterIsInstance<EditText>()[1].setText("검증 시나리오 $id: $title")
                    }
                    clickVoice("상황 안내 읽어주기")
                    awaitUi(scenario, "TTS active before driving restriction", 40) {
                        text(it.findViewById(R.id.assistance_panel)).contains("안내를 읽고 있습니다")
                    }
                }
                scenario.onActivity { activity ->
                    views(activity.findViewById(R.id.assistance_panel)).filterIsInstance<Button>()
                        .single { it.text == "정비 요청서 미리보기" }.performClick()
                }
                var reportText = ""
                awaitUi(scenario, "report preview from real Room history") { _ ->
                    val dialog = WindowInspector.getGlobalWindowViews().firstOrNull { root ->
                        views(root).filterIsInstance<Button>().any { it.text == "공유 앱 선택" }
                    }
                    if (dialog != null) reportText = text(dialog)
                    dialog != null
                }
                assertTrue(reportText.contains("검증 시나리오 $id"))
                assertTrue(reportText.contains("경고: $type · 원시 상태: ON"))
                assertTrue(reportText.contains("전송 완료를 의미하지 않습니다"))
                assertTrue(reportText.contains("최근 7일"))
                assertTrue(reportText.contains("사용자 설명"))
                result.put("report", reportText)
                screenshot("$id-report")
                // No external share intent is sent. Verify the actual UX restriction closes the preview.
                console("/vehicle/gear?gear=Drive")
                console("/vehicle/controls?speed=30&accelerator=0&brake=0&steering=0")
                awaitUi(scenario, "actual driving restriction") { activity ->
                    !activity.findViewById<View>(R.id.details).isShown &&
                        WindowInspector.getGlobalWindowViews().none { root ->
                            views(root).filterIsInstance<Button>().any { it.text == "공유 앱 선택" }
                        }
                }
                result.put("restrictionClosedReport", true)
                if (id == "tpms-first") {
                    scenario.onActivity { assertVoiceReleased(it) }
                    awaitUi(scenario, "driving stop IPC acknowledgment") { voiceStopFinished(it) }
                    result.put("drivingReleasedTts", true)
                }
                console("/vehicle/controls?speed=0&accelerator=0&brake=0&steering=0")
                console("/vehicle/gear?gear=Park")
                awaitUi(scenario, "parked recovery") { it.findViewById<View>(R.id.details).isShown }
                result.put("passed", true)
            }
        } finally {
            result.put("totalElapsedMs", SystemClock.elapsedRealtime() - started)
            File(evidence, "$id.json").writeText(result.toString(2))
            instrumentation.sendStatus(0, Bundle().apply { putString("scenario", result.toString()) })
            console("/vehicle/controls?speed=0&accelerator=0&brake=0&steering=0")
            console("/vehicle/gear?gear=Park")
            signal("TPMS", "Off")
            signal("ElectronicParkingBrake", "Off")
        }
    }

    @Test fun tpmsFirstOn() = runCase("tpms-first", "TPMS", "TPMS", "공기압 경고가 처음 켜졌어요", false,
        listOf("속도를 낮추", "급격한 조향"))
    @Test fun tpmsBlinkThenOn() = runCase("tpms-blink", "TPMS", "TPMS", "깜빡인 뒤 계속 켜져 있어요", true,
        listOf("타이어 공기압 경보 시스템 이상", "즉시", "점검"))
    @Test fun epbRemainsOn() = runCase("epb-first", "ELECTRONIC_PARKING_BRAKE", "ElectronicParkingBrake", "EPB 경고가 켜졌어요", false,
        listOf("주차 브레이크 이상이 발생한 경우", "계속 켜진", "점검"))
}
