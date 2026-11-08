package com.checkmate.pleos.explanation

import com.checkmate.pleos.manual.ManualProfile
import org.json.JSONObject

data class RemoteContext(val profileId: String, val type: String, val rawState: String,
    val observedAt: Long, val historical: Boolean, val current: Boolean)

/** Main-thread request generation. Any screen/profile/observation change invalidates older results. */
class RemoteRequestGate {
    private var generation = 0L
    fun begin(): Long = ++generation
    fun invalidate() { generation++ }
    fun accepts(ticket: Long): Boolean = ticket == generation
}

data class RemoteExplanation(val status: String, val mode: String = "NONE", val body: String = "",
    val limits: String = "", val citations: String = "")

object ExplanationJson {
    private val statuses = setOf("READY", "PROFILE_REQUIRED", "PROFILE_UNSUPPORTED", "WARNING_UNSUPPORTED",
        "STATE_UNSUPPORTED", "NO_EVIDENCE", "TEMPORARILY_UNAVAILABLE")

    fun request(id: String, context: RemoteContext, question: String? = null): String {
        val cleaned = question?.trim()
        require(cleaned == null || cleaned.length in 1..300) { "Question must be 1 to 300 characters" }
        return JSONObject()
            .put("requestId", id).put("profileId", context.profileId)
            .put("intent", if (cleaned == null) "WARNING_OVERVIEW" else "QUESTION")
            .put("warning", JSONObject().put("type", context.type).put("rawState", context.rawState))
            .apply { if (cleaned != null) put("question", cleaned) }.toString()
    }

    fun parse(raw: String, id: String, context: RemoteContext, profile: ManualProfile): RemoteExplanation {
        val root = JSONObject(raw)
        require(root.getString("requestId") == id && root.getString("profileId") == context.profileId)
        val warning = root.getJSONObject("warning")
        require(warning.getString("type") == context.type && warning.getString("rawState") == context.rawState)
        val status = root.getString("status")
        require(status in statuses)
        val sections = root.getJSONArray("sections")
        val citations = root.getJSONArray("citations")
        if (status != "READY") {
            require(sections.length() == 0 && citations.length() == 0 && root.getString("mode") == "NONE")
            return RemoteExplanation(status)
        }
        val mode = root.getString("mode")
        require(mode in setOf("REVIEWED_RETRIEVAL", "AI_GENERATED"))
        require(root.getJSONObject("versions").getString("document") == profile.documentRevision)
        require(sections.length() in 1..5 && citations.length() in 1..8)
        val numbers = mutableMapOf<String, Int>()
        val citationText = (0 until citations.length()).map { i ->
            val c = citations.getJSONObject(i)
            val sourceId = c.getString("id")
            require(sourceId.isNotBlank() && sourceId !in numbers)
            numbers[sourceId] = i + 1
            require(c.getString("url") == profile.source.url)
            require(c.getString("contentKind") in setOf("REVIEWED_SUMMARY", "LICENSED_ORIGINAL"))
            val page = if (c.isNull("page")) "" else " · PDF ${c.getInt("page").also { require(it >= 1) }}쪽"
            "[${i + 1}] ${c.getString("documentTitle")} · ${c.getString("sectionTitle")}$page"
        }.joinToString("\n\n") + "\n\n문서 버전 ${profile.documentRevision}\n${profile.source.url}"
        val body = (0 until sections.length()).map { i ->
            val s = sections.getJSONObject(i)
            val title = s.getString("title")
            val text = s.getString("text")
            require(title.isNotBlank() && title.length <= 100 && text.isNotBlank() && text.length <= 1200)
            require(s.getString("kind") in setOf("MEANING", "MANUAL_GUIDANCE"))
            val refs = s.getJSONArray("citationIds")
            require(refs.length() in 1..8)
            val labels = (0 until refs.length()).map { j ->
                val number = numbers[refs.getString(j)] ?: error("Unknown citation")
                "[$number]"
            }.joinToString(" ")
            "$title $labels\n$text"
        }.joinToString("\n\n")
        val limits = root.getJSONArray("limitations")
        require(limits.length() in 1..8)
        val limitationText = (0 until limits.length()).map { limits.getString(it) }.onEach {
            require(it.isNotBlank() && it.length <= 1200)
        }.joinToString("\n\n")
        return RemoteExplanation(status, mode, body, limitationText, citationText)
    }
}
