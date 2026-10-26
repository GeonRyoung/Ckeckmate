package com.checkmate.pleos.explanation

import com.checkmate.pleos.manual.ManualCatalog
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class ExplanationJsonTest {
    private val profile = ManualCatalog.profiles.single()
    private val context = RemoteContext(profile.id, "TPMS", "ON", 123, false, true)
    private val id = "d8adcf02-303c-40fd-9f3c-306f1c60fc4b"
    private fun response() = JSONObject("""{
        "requestId":"$id", "profileId":"${profile.id}",
        "warning":{"type":"TPMS","rawState":"ON"},"status":"READY","mode":"AI_GENERATED",
        "sections":[{"kind":"MEANING","title":"의미","text":"매뉴얼 설명","citationIds":["a"]}],
        "limitations":["원인을 확정할 수 없습니다."],
        "citations":[{"id":"a","documentTitle":"매뉴얼","sectionTitle":"TPMS","url":"${profile.source.url}","contentKind":"REVIEWED_SUMMARY"}],
        "versions":{"document":"1.27"}
    }""")

    @Test fun requestOnlyContainsAllowedFields() {
        val json = JSONObject(ExplanationJson.request(id, context))
        assertEquals(setOf("requestId", "profileId", "warning", "intent"), json.keys().asSequence().toSet())
        assertFalse(json.has("observedAt"))
    }

    @Test fun validEvidenceRendersCitationNumbers() {
        val result = ExplanationJson.parse(response().toString(), id, context, profile)
        assertTrue(result.body.contains("[1]"))
        assertTrue(result.citations.contains(profile.source.url))
    }

    @Test fun mismatchedRequestProfileStateVersionAndSourceAreRejected() {
        val mutations: List<(JSONObject) -> Unit> = listOf(
            { it.put("requestId", "old-request") },
            { it.put("profileId", "wrong-car") },
            { it.getJSONObject("warning").put("rawState", "BLINK") },
            { it.getJSONObject("versions").put("document", "another-version") },
            { it.getJSONArray("citations").getJSONObject(0).put("url", "https://example.com/fake") },
            { it.getJSONArray("sections").getJSONObject(0).getJSONArray("citationIds").put(0, "fake") },
        )
        mutations.forEach { mutate ->
            val json = response(); mutate(json)
            assertTrue(runCatching { ExplanationJson.parse(json.toString(), id, context, profile) }.isFailure)
        }
    }

    @Test fun lateResponsesAreInvalidatedByNavigationOrANewerRequest() {
        val gate = RemoteRequestGate()
        val first = gate.begin()
        gate.invalidate()
        assertFalse(gate.accepts(first))
        val second = gate.begin()
        val third = gate.begin()
        assertFalse(gate.accepts(second))
        assertTrue(gate.accepts(third))
    }
}
