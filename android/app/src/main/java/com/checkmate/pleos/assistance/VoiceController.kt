package com.checkmate.pleos.assistance

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
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
    private var ttsReady = false
    private var closed = false
    private val permission = activity.registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        val action = pendingPermission
        pendingPermission = null
        if (granted && allowed()) action?.invoke()
        else if (action != null && allowed()) message("마이크 권한이 없어 음성 입력을 사용할 수 없습니다. 글로 입력해 주세요.")
    }

    init {
        tts = TextToSpeech(activity.applicationContext) { status ->
            activity.runOnUiThread {
                if (!closed) {
                    val result = if (status == TextToSpeech.SUCCESS) tts?.setLanguage(Locale.KOREAN) else null
                    ttsReady = result != null && result >= TextToSpeech.LANG_AVAILABLE
                }
            }
        }
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
        if (!allowed()) return
        stop()
        if (!ttsReady) {
            message("한국어 음성 읽기 엔진이 없거나 준비되지 않았습니다. 화면 안내를 확인해 주세요.")
            return
        }
        // Do not truncate safety guidance or its conditions at the engine input limit.
        if (text.length > TextToSpeech.getMaxSpeechInputLength()) {
            message("안내가 길어 읽을 수 없습니다. 상황별 짧은 안내를 선택해 주세요.")
            return
        }
        if (tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "checkmate-$generation") == TextToSpeech.ERROR)
            message("음성 재생을 시작하지 못했습니다. 화면 안내를 확인해 주세요.")
        else message("안내를 읽습니다. 중지 버튼으로 멈출 수 있습니다.")
    }

    fun stop() {
        generation++
        pendingPermission = null
        recognizer?.let { it.cancel(); it.destroy() }
        recognizer = null
        tts?.stop()
    }

    fun close() {
        closed = true
        stop()
        tts?.shutdown()
        tts = null
    }
}
