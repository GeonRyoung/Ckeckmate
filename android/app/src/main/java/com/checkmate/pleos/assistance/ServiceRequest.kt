package com.checkmate.pleos.assistance

import com.checkmate.pleos.explanation.RemoteContext
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

object ServiceRequest {
    fun format(profileLabel: String, context: RemoteContext, scenario: String?, symptoms: String,
               actions: String, history: String, zone: ZoneId = ZoneId.systemDefault()): String {
        require(symptoms.length <= 1000 && actions.length <= 1000)
        require(history.isNotBlank())
        val at = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss z").withZone(zone)
            .format(Instant.ofEpochMilli(context.observedAt))
        return """
            CHECKMATE · 정비 진단 요청 자료
            정비소의 진단 결과가 아닙니다. 접수·예약·전송 완료를 의미하지 않습니다.

            사용자 선택 매뉴얼 프로필: $profileLabel
            실제 차량의 차종·연식은 정비소에서 확인해 주세요.

            [차량 관측 기록]
            경고: ${context.type} · 원시 상태: ${context.rawState}
            관측 시각: $at
            기록 구분: ${if (context.historical) "과거 이력 (현재 상태 아님)" else if (context.current) "요청서 작성 시 선택한 최근 관측" else "이전 수신 정보 (현재 상태 확인 불가)"}

            [사용자 설명 · 차량 센서로 확인하지 않은 내용]
            선택한 상황: ${scenario ?: "선택하지 않음"}
            증상: ${symptoms.trim().ifEmpty { "입력하지 않음" }}
            시도한 조치: ${actions.trim().ifEmpty { "입력하지 않음" }}

            [점검 요청]
            위 경고와 사용자 설명을 참고해 원인 및 필요한 조치를 점검해 주세요.

            [최근 7일 전체 경고 관측 요약 · 선택 경고 외 항목 포함 가능]
        """.trimIndent() + "\n" + history
    }
}
