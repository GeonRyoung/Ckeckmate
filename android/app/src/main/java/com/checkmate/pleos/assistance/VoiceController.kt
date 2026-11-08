package com.checkmate.pleos.assistance

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import ai.pleos.playground.tts.TextToSpeech
import ai.pleos.playground.tts.constant.Mode
import ai.pleos.playground.tts.constant.ErrorType
import ai.pleos.playground.tts.listener.EventListener
import ai.pleos.playground.tts.listener.OnInitializeListener
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import java.util.Locale

/** Button-driven speech only. Cancellation invalidates permission and recognition callbacks. */
class VoiceController(
    private val activity: AppCompatActivity,
    private val allowed: () -> Boolean,
    private val message: (String) -> Unit,
) {
    private var generation = 0L
    private var recognizer: SpeechRecognizer? = null
    private var pendingPermission: (() -> Unit)? = null
    private var tts: TextToSpeech? = null
    private var ttsListener: EventListener? = null
    private var ttsInitialized = false
    private var pendingTtsStops = 0
    private var closed = false
    private val permission = activity.registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        val action = pendingPermission
        pendingPermission = null
        if (granted && allowed()) action?.invoke()
        else if (action != null && allowed()) message("마이크 권한이 없어 음성 입력을 사용할 수 없습니다. 글로 입력해 주세요.")
    }

    fun listen(onText: (String) -> Unit) {
        if (!allowed()) return
        stop()
        val exportedRecognizer = activity.packageManager.queryIntentServices(
            Intent("android.speech.RecognitionService"), 0
        ).any { it.serviceInfo?.let { info -> info.exported && info.enabled } == true }
        if (!SpeechRecognizer.isRecognitionAvailable(activity) || !exportedRecognizer) {
            message("이 기기에 앱이 사용할 수 있는 음성 인식 서비스가 없습니다. 글로 입력해 주세요.")
            return
        }
        val ticket = generation
        val start = {
            if (ticket == generation && allowed()) startListening(ticket, onText)
        }
        if (ContextCompat.checkSelfPermission(activity, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) start()
        else {
            pendingPermission = start
            permission.launch(Manifest.permission.RECORD_AUDIO)
        }
    }

    private fun startListening(ticket: Long, onText: (String) -> Unit) {
        try {
            val listener = SpeechRecognizer.createSpeechRecognizer(activity)
            recognizer = listener
            listener.setRecognitionListener(object : RecognitionListener {
                private fun valid() = !closed && ticket == generation && allowed()
                override fun onReadyForSpeech(params: Bundle?) { if (valid()) message("말씀해 주세요. 인식 후 문장을 확인하고 질문 보내기를 누르세요.") }
                override fun onBeginningOfSpeech() = Unit
                override fun onRmsChanged(rmsdB: Float) = Unit
                override fun onBufferReceived(buffer: ByteArray?) = Unit
                override fun onEndOfSpeech() { if (valid()) message("말씀하신 내용을 확인하고 있습니다.") }
                override fun onError(error: Int) {
                    if (valid()) {
                        message("음성을 인식하지 못했습니다. 다시 누르거나 글로 입력해 주세요. (오류 $error)")
                        stop()
                    }
                }
                override fun onResults(results: Bundle?) {
                    if (!valid()) return
                    val text = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()?.trim()
                    stop()
                    if (text.isNullOrBlank()) message("인식된 문장이 없습니다. 다시 시도해 주세요.")
                    else onText(text)
                }
                override fun onPartialResults(partialResults: Bundle?) = Unit
                override fun onEvent(eventType: Int, params: Bundle?) = Unit
            })
            listener.startListening(Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                .putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                .putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ko-KR")
                .putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1))
            message("음성 입력을 준비하고 있습니다.")
        } catch (_: RuntimeException) {
            stop()
            message("이 환경에서 음성 입력을 시작할 수 없습니다. 글로 입력해 주세요.")
        }
    }

    fun speak(text: String) {
        if (closed || !allowed()) return
        stop()
        if (pendingTtsStops > 0) {
            message("이전 음성을 중지하고 있습니다. 잠시 후 읽기 버튼을 다시 눌러 주세요.")
            return
        }
        if (text.isBlank()) return
        // Application limit: never truncate safety instructions or their conditions.
        if (text.length > 4000) {
            message("안내가 길어 읽을 수 없습니다. 상황별 짧은 안내를 선택해 주세요.")
            return
        }
        val ticket = generation
        fun valid() = !closed && ticket == generation && allowed()
        fun update(action: () -> Unit) = activity.runOnUiThread { if (valid()) action() }
        try {
            val engine = TextToSpeech(activity.applicationContext, Mode.ON_DEVICE)
            tts = engine
            val listener = object : EventListener {
                override fun onReady() = Unit
                override fun onUpdatedRms(rms: Double) = Unit
                override fun onStart() { update { message("안내를 읽고 있습니다. 음성 중지 버튼으로 멈출 수 있습니다.") } }
                override fun onDone() { update { message("음성 안내를 마쳤습니다."); stop(completed = true) } }
                override fun onStop() { update { message("음성을 중지했습니다.") } }
                override fun onError(errorType: ErrorType) {
                    update { message("음성 안내를 재생하지 못했습니다. 화면 안내를 확인해 주세요. ($errorType)"); stop() }
                }
            }
            ttsListener = listener
            message("한국어 음성 안내를 준비하고 있습니다.")
            engine.initialize(object : OnInitializeListener {
                override fun onSuccess() {
                    update {
                        try {
                            ttsInitialized = true
                            engine.addEventListener(listener)
                            engine.setLocale(Locale.KOREA)
                            engine.speak(text)
                        } catch (_: RuntimeException) {
                            message("음성 재생을 시작하지 못했습니다. 화면 안내를 확인해 주세요.")
                            stop()
                        }
                    }
                }
                override fun onFailure(errorType: ErrorType) {
                    update { message("음성 서비스를 사용할 수 없습니다. 화면 안내를 확인해 주세요. ($errorType)"); stop() }
                }
            })
        } catch (_: RuntimeException) {
            message("음성 서비스를 사용할 수 없습니다. 화면 안내를 확인해 주세요.")
            stop()
        }
    }

    fun stop(completed: Boolean = false) {
        generation++
        pendingPermission = null
        recognizer?.let { it.cancel(); it.destroy() }
        recognizer = null
        val engine = tts
        val listener = ttsListener
        val initialized = ttsInitialized
        tts = null
        ttsListener = null
        ttsInitialized = false
        if (engine != null) {
            try { if (listener != null) engine.removeEventListener(listener) } catch (_: RuntimeException) { }
            if (!initialized || completed) {
                try { engine.release() } catch (_: RuntimeException) { }
                return
            }
            // stop() dispatches asynchronously. Immediate release() can cancel its IPC.
            val handler = android.os.Handler(android.os.Looper.getMainLooper())
            pendingTtsStops++
            var released = false
            lateinit var cleanup: EventListener
            lateinit var timeout: Runnable
            fun release() {
                if (released) return
                released = true
                pendingTtsStops--
                handler.removeCallbacks(timeout)
                try { engine.removeEventListener(cleanup) } catch (_: RuntimeException) { }
                try { engine.release() } catch (_: RuntimeException) { }
            }
            cleanup = object : EventListener {
                override fun onReady() = Unit
                override fun onStart() = Unit
                override fun onUpdatedRms(rms: Double) = Unit
                override fun onDone() = Unit // Only the stop acknowledgment confirms cancellation.
                override fun onStop() { handler.post {
                    android.util.Log.i("CheckmateVoice", "TTS stop acknowledged")
                    release()
                } }
                override fun onError(errorType: ErrorType) { handler.post { release() } }
            }
            timeout = Runnable {
                android.util.Log.w("CheckmateVoice", "TTS stop acknowledgment timed out")
                release()
            }
            handler.postDelayed(timeout, 5000)
            try { engine.addEventListener(cleanup); engine.stop() }
            catch (_: RuntimeException) { release() }
        }
    }

    fun close() {
        closed = true
        stop()
    }
}
