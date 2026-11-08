package com.checkmate.pleos.assistance

import com.checkmate.pleos.explanation.ExplanationJson
import com.checkmate.pleos.explanation.RemoteContext
import com.checkmate.pleos.manual.ManualCatalog
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.time.ZoneId

class AssistanceTest {
    private val profile = ManualCatalog.profiles.single()
    private val context = RemoteContext(profile.id, "TPMS", "ON", 123, false, true)

    @Test fun unsupportedProfilesWarningsAndStatesCannotOfferScenarios() {
        assertTrue(WarningScenarios.available(null, "TPMS", "ON").isEmpty())
        assertTrue(WarningScenarios.available("other-car", "TPMS", "ON").isEmpty())
        assertTrue(WarningScenarios.available(profile.id, "ABS", "ON").isEmpty())
        assertTrue(WarningScenarios.available(profile.id, "TPMS", "OFF").isEmpty())
        assertTrue(WarningScenarios.available(profile.id, "ELECTRONIC_PARKING_BRAKE", "BLINK").isEmpty())
    }

    @Test fun sixScenariosHaveDistinctIdsAndKeepWarningScopeInQuestionRequests() {
        val all = listOf("TPMS", "ELECTRONIC_PARKING_BRAKE").flatMap { type ->
            WarningScenarios.available(profile.id, type, "ON").also { assertEquals(3, it.size) }
        }
        assertEquals(6, all.map { it.id }.toSet().size)
        all.forEach { scenario ->
            val request = JSONObject(ExplanationJson.request("id", context.copy(type = scenario.warningType), scenario.question))
            assertEquals("QUESTION", request.getString("intent"))
            assertEquals(scenario.warningType, request.getJSONObject("warning").getString("type"))
            assertEquals(scenario.question, request.getString("question"))
            assertFalse(request.has("symptoms"))
            assertFalse(request.has("observedAt"))
        }
    }

    @Test fun questionValidationDoesNotSilentlyTurnBlankOrOversizeIntoOverview() {
        listOf("  ", "가".repeat(301)).forEach {
            assertTrue(runCatching { ExplanationJson.request("id", context, it) }.isFailure)
        }
        val json = JSONObject(ExplanationJson.request("id", context, "  무슨 뜻인가요?  "))
        assertEquals("무슨 뜻인가요?", json.getString("question"))
        assertEquals("WARNING_OVERVIEW", JSONObject(ExplanationJson.request("id", context)).getString("intent"))
    }

    @Test fun reportSeparatesUserClaimsFromObservationAndNeverClaimsDelivery() {
        val report = ServiceRequest.format(profile.label, context.copy(historical = true), "깜빡였어요",
            "타이어가 흔들려요", "공기압 조절", "관측 공백 1개", ZoneId.of("Asia/Seoul"))
        assertTrue(report.contains("과거 이력 (현재 상태 아님)"))
        assertTrue(report.contains("차량 센서로 확인하지 않은 내용"))
        assertTrue(report.contains("타이어가 흔들려요"))
        assertTrue(report.contains("관측 공백 1개"))
        assertTrue(report.contains("접수·예약·전송 완료를 의미하지 않습니다"))
        assertTrue(report.contains("진단 결과가 아닙니다"))
    }

    @Test fun missingHistoryCannotBecomeACompleteReportAndBlankSymptomsAreExplicit() {
        assertTrue(runCatching { ServiceRequest.format(profile.label, context, null, "", "", "") }.isFailure)
        val report = ServiceRequest.format(profile.label, context.copy(current = false), null, "", "", "기록 없음")
        assertTrue(report.contains("현재 상태 확인 불가"))
        assertTrue(report.contains("증상: 입력하지 않음"))
        assertTrue(report.contains("선택한 상황: 선택하지 않음"))
    }
}
