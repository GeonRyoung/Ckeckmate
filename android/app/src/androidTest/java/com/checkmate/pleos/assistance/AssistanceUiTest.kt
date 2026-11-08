package com.checkmate.pleos.assistance

import android.graphics.Bitmap
import android.view.View
import android.view.ViewGroup
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
import com.checkmate.pleos.manual.ManualCatalog
import com.checkmate.pleos.manual.ManualPreferences
import com.checkmate.pleos.vehicle.WarningMonitor
import com.checkmate.pleos.vehicle.WarningReading
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

/** Synthetic UI integration: not proof of Vehicle SDK delivery, microphone, or real driving restrictions. */
@RunWith(AndroidJUnit4::class)
class AssistanceUiTest {
    private fun views(view: View): List<View> = listOf(view) +
        if (view is ViewGroup) (0 until view.childCount).flatMap { views(view.getChildAt(it)) } else emptyList()

    private fun render(activity: MainActivity) {
        MainActivity::class.java.getDeclaredMethod("render").apply { isAccessible = true }.invoke(activity)
    }

    private fun allow(activity: MainActivity, allowed: Boolean) {
        MainActivity::class.java.getDeclaredField("detailsAllowed").apply { isAccessible = true }.setBoolean(activity, allowed)
    }

    @Test fun sixSituationsRenderAndRestrictionClearsSensitiveDrafts() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            scenario.onActivity { activity ->
                ManualPreferences(activity).select(ManualCatalog.profiles.single().id)
                allow(activity, true)
                val monitor = MainActivity::class.java.getDeclaredField("monitor").apply { isAccessible = true }.get(activity) as WarningMonitor
                monitor.accept(listOf(WarningReading("TPMS", "ON"), WarningReading("ELECTRONIC_PARKING_BRAKE", "ON")), System.currentTimeMillis())
                render(activity)
                fun openWarning(type: String) {
                    activity.findViewById<Button>(R.id.show_current).performClick()
                    val cards = activity.findViewById<LinearLayout>(R.id.warning_cards)
                    views(cards).filterIsInstance<Button>().single { it.text.startsWith("$type ·") }.performClick()
                }
                listOf("TPMS", "ELECTRONIC_PARKING_BRAKE").forEach { type ->
                    openWarning(type)
                    val root = activity.findViewById<LinearLayout>(R.id.assistance_panel)
                    assertEquals(View.VISIBLE, root.visibility)
                    val choices = WarningScenarios.available(ManualCatalog.profiles.single().id, type, "ON")
                    choices.forEach { choice ->
                        views(root).filterIsInstance<Button>().single { it.text == choice.title }.performClick()
                        assertTrue(views(root).filterIsInstance<TextView>().any { it.text.contains(choice.guidance) })
                        assertEquals(choice.question, views(root).filterIsInstance<EditText>().first().text.toString())
                    }
                }
                val root = activity.findViewById<LinearLayout>(R.id.assistance_panel)
                views(root).filterIsInstance<EditText>()[1].setText("UI 검증용 증상")
                allow(activity, false)
                render(activity)
                assertEquals(View.GONE, activity.findViewById<View>(R.id.details).visibility)
                assertTrue(views(root).filterIsInstance<EditText>().all { it.text.isEmpty() })
                allow(activity, true)
                render(activity)
                openWarning("TPMS")
                views(root).filterIsInstance<Button>().single { it.text == "공기압 경고가 처음 켜졌어요" }.performClick()
                activity.findViewById<ScrollView>(R.id.content_scroll).scrollTo(0, root.top)
            }
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()
            val screenshot = InstrumentationRegistry.getInstrumentation().uiAutomation.takeScreenshot()
            val file = File(InstrumentationRegistry.getInstrumentation().targetContext.filesDir, "assistance-ui.png")
            file.outputStream().use { screenshot.compress(Bitmap.CompressFormat.PNG, 100, it) }
            InstrumentationRegistry.getInstrumentation().sendStatus(0, android.os.Bundle().apply { putString("screenshot", file.absolutePath) })
            scenario.onActivity { activity ->
                val root = activity.findViewById<LinearLayout>(R.id.assistance_panel)
                views(root).filterIsInstance<EditText>()[1].setText("요청서 검증용 증상")
                views(root).filterIsInstance<Button>().single { it.text == "정비 요청서 미리보기" }.performClick()
            }
            var dialog: androidx.appcompat.app.AlertDialog? = null
            for (attempt in 0 until 50) {
                scenario.onActivity { activity ->
                    val panel = MainActivity::class.java.getDeclaredField("assistancePanel").apply { isAccessible = true }.get(activity)
                    dialog = AssistancePanel::class.java.getDeclaredField("preview").apply { isAccessible = true }.get(panel) as? androidx.appcompat.app.AlertDialog
                }
                if (dialog != null) break
                android.os.SystemClock.sleep(100)
            }
            assertNotNull("Report preview should open after history loads", dialog)
            scenario.onActivity { activity ->
                val contents = views(dialog!!.window!!.decorView).filterIsInstance<TextView>().joinToString("\n") { it.text }
                assertTrue(contents.contains("요청서 검증용 증상"))
                assertTrue(contents.contains("전송 완료를 의미하지 않습니다"))
                assertEquals("공유 앱 선택", dialog!!.getButton(android.content.DialogInterface.BUTTON_POSITIVE).text)
                // Restriction must close the preview before a user can initiate sharing.
                allow(activity, false)
                render(activity)
                assertFalse(dialog!!.isShowing)
            }
        }
    }
}
