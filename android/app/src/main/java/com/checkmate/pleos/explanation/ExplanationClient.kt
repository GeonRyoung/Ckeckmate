package com.checkmate.pleos.explanation

import android.os.Handler
import android.os.Looper
import com.checkmate.pleos.manual.ManualProfile
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors
import java.util.concurrent.Future
import java.util.concurrent.atomic.AtomicReference
import java.util.concurrent.atomic.AtomicBoolean

class ExplanationClient(private val baseUrl: String) {
    private val executor = Executors.newFixedThreadPool(2)
    private val main = Handler(Looper.getMainLooper())
    private class Call {
        val cancelled = AtomicBoolean(false)
        val connection = AtomicReference<HttpURLConnection?>()
    }
    private var activeCall: Call? = null
    private var task: Future<*>? = null

    fun request(id: String, context: RemoteContext, profile: ManualProfile, callback: (Result<RemoteExplanation>) -> Unit) {
        cancel()
        val call = Call()
        activeCall = call
        task = executor.submit {
            val result = runCatching {
                val profiles = JSONObject(exchange(call, "/v1/manual-profiles", null)).getJSONArray("profiles")
                val supported = (0 until profiles.length()).any { profiles.getJSONObject(it).getString("id") == profile.id }
                if (!supported) RemoteExplanation("PROFILE_UNSUPPORTED")
                else ExplanationJson.parse(exchange(call, "/v1/explanations", ExplanationJson.request(id, context)), id, context, profile)
            }
            if (!call.cancelled.get()) main.post { callback(result) }
        }
    }

    private fun exchange(call: Call, path: String, body: String?): String {
        check(!call.cancelled.get() && !Thread.currentThread().isInterrupted)
        val conn = URL(baseUrl.trimEnd('/') + path).openConnection() as HttpURLConnection
        call.connection.set(conn)
        try {
            check(!call.cancelled.get())
            conn.connectTimeout = 5000
            conn.readTimeout = 70000
            conn.instanceFollowRedirects = false
            conn.setRequestProperty("Accept", "application/json")
            if (body != null) {
                conn.requestMethod = "POST"
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                conn.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
            }
            val status = conn.responseCode
            require(status == 200 || (body != null && status == 503)) { "Explanation request failed" }
            val stream = if (status == 200) conn.inputStream else conn.errorStream
            val bytes = stream.use { it.readBytesLimited(64 * 1024) }
            return bytes.toString(Charsets.UTF_8)
        } finally {
            call.connection.compareAndSet(conn, null)
            conn.disconnect()
        }
    }

    private fun java.io.InputStream.readBytesLimited(limit: Int): ByteArray {
        val output = java.io.ByteArrayOutputStream()
        val buffer = ByteArray(4096)
        while (true) {
            val count = read(buffer)
            if (count < 0) break
            require(output.size() + count <= limit) { "Response too large" }
            output.write(buffer, 0, count)
        }
        return output.toByteArray()
    }

    fun cancel() {
        task?.cancel(true)
        activeCall?.let { call ->
            call.cancelled.set(true)
            call.connection.getAndSet(null)?.disconnect()
        }
        activeCall = null
        task = null
    }

    fun close() { cancel(); executor.shutdownNow() }
}
