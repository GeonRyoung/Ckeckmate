package com.checkmate.pleos.assistance

import ai.pleos.playground.tts.TextToSpeech
import ai.pleos.playground.tts.constant.ErrorType
import ai.pleos.playground.tts.constant.Mode
import ai.pleos.playground.tts.listener.EventListener
import ai.pleos.playground.tts.listener.OnInitializeListener
import android.os.Build
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.Collections
import java.util.Locale
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/** Opt-in engine probe; callbacks do not prove audible speaker output. */
@RunWith(AndroidJUnit4::class)
class PleosTtsProbeTest {
    private lateinit var tts: TextToSpeech
    @Test fun koreanOnDevicePlaybackCallbacks() {
        assumeTrue(InstrumentationRegistry.getArguments().getString("voiceProbe") == "true")
        assumeTrue(Build.HARDWARE == "ranchu")
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        val events = Collections.synchronizedList(mutableListOf<String>())
        val initialized = CountDownLatch(1)
        val finished = CountDownLatch(1)
        val listener = object : EventListener {
            override fun onReady() { events.add("ready") }
            override fun onStart() { events.add("start") }
            override fun onUpdatedRms(rms: Double) = Unit
            override fun onDone() { events.add("done"); finished.countDown() }
            override fun onStop() { events.add("stop") }
            override fun onError(errorType: ErrorType) {
                events.add("error:$errorType"); finished.countDown()
            }
        }
        try {
            instrumentation.runOnMainSync {
                tts = TextToSpeech(context.applicationContext, Mode.ON_DEVICE)
                tts.initialize(object : OnInitializeListener {
                    override fun onSuccess() { events.add("initialized"); initialized.countDown() }
                    override fun onFailure(errorType: ErrorType) {
                        events.add("initError:$errorType"); initialized.countDown()
                    }
                })
            }
            assertTrue("Initialization timeout: $events", initialized.await(20, TimeUnit.SECONDS))
            assertTrue("Initialization failed: $events", events.contains("initialized"))
            instrumentation.runOnMainSync {
                tts.addEventListener(listener)
                tts.setLocale(Locale.KOREA)
                tts.speak("체크메이트 음성 안내 시험입니다.")
            }
            assertTrue("Playback timeout: $events", finished.await(30, TimeUnit.SECONDS))
            assertTrue("Playback failed: $events", events.contains("start") && events.contains("done"))
        } finally {
            File(context.filesDir, "pleos-tts-probe.json").writeText(JSONObject()
                .put("sdk", "3.3.1").put("mode", "ON_DEVICE").put("locale", "ko-KR")
                .put("events", org.json.JSONArray(events.toList()))
                .put("physicalSpeakerVerified", false).toString(2))
            if (::tts.isInitialized) instrumentation.runOnMainSync {
                tts.stop()
                tts.removeEventListener(listener)
                tts.release()
            }
        }
    }
}
