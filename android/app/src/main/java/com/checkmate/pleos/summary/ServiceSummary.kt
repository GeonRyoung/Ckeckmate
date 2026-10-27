package com.checkmate.pleos.summary

import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

/** Calendar days in the device zone, with a fixed cutoff captured when a query starts. */
enum class SummaryPeriod(val days: Long) {
    TODAY(1), SEVEN_DAYS(7), THIRTY_DAYS(30);

    fun window(now: Long, zone: ZoneId): SummaryWindow {
        val today = Instant.ofEpochMilli(now).atZone(zone).toLocalDate()
        val start = today.minusDays(days - 1).atStartOfDay(zone).toInstant().toEpochMilli()
        return SummaryWindow(start, Math.addExact(now, 1))
    }
}

data class SummaryWindow(val startInclusive: Long, val endExclusive: Long) {
    init { require(startInclusive < endExclusive) }
}

/** Aggregates cover every matching DB row, independently of the limited detail list. */
data class WarningRollup(
    val type: String,
    val records: Int,
    val firstRecordedAt: Long,
    val lastRecordedAt: Long,
    val recordedStates: String?,
    val firstObservations: Int,
    val stateChanges: Int,
    val reobservations: Int,
    val resumptions: Int,
    val removals: Int,
)

data class SummaryEventCount(val kind: String, val records: Int)

data class SummaryRecord(
    val at: Long,
    val kind: String,
    val type: String?,
    val rawState: String?,
)

data class ServiceSummary(
    val window: SummaryWindow,
    val warnings: List<WarningRollup>,
    val eventCounts: List<SummaryEventCount>,
    val recentRecords: List<SummaryRecord>,
) {
    val totalRecords: Int get() = eventCounts.sumOf { it.records }
}

/** Deterministic rendering of saved facts. No inference about fault duration or recurrence. */
object ServiceSummaryFormatter {
    fun format(summary: ServiceSummary, zone: ZoneId): String {
        val formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss").withZone(zone)
        fun time(value: Long) = formatter.format(Instant.ofEpochMilli(value))
        val counts = summary.eventCounts.associate { it.kind to it.records }
        return buildString {
            appendLine("CHECKMATE · 정비 전달용 관측 요약")
            appendLine("조회 기간: ${time(summary.window.startInclusive)} ~ ${time(summary.window.endExclusive - 1)}")
            appendLine("시간대: ${zone.id}")
            appendLine("출처: 이 기기에 저장된 Pleos Vehicle SDK 관측 기록")
            appendLine("전체 변화 기록 ${summary.totalRecords}개 · 경고 종류 ${summary.warnings.size}개")
            appendLine()
            appendLine("선택 기간에 저장된 변화만 정리했습니다. 기간 이전부터 유지된 경고는 새 변화가 없으면 포함되지 않을 수 있습니다.")
            appendLine("기록 수는 고장 발생 횟수가 아닙니다. 첫·마지막 기록은 고장의 시작·종료 시각이 아닙니다.")
            appendLine()
            appendLine("관측 공백")
            appendLine("수신 중단 기록 ${counts["OBSERVATION_GAP"] ?: 0}개 · 이전 수신 구간 종료 시각 미확인 기록 ${counts["RECOVERY_GAP"] ?: 0}개")
            appendLine("공백 기록이 없어도 연속 수신을 보장하지 않습니다. 기록이 없는 시간의 차량 상태는 확인할 수 없습니다.")
            appendLine()
            appendLine("경고별 기록")
            if (summary.warnings.isEmpty()) {
                appendLine("선택 기간에 저장된 경고 변화 기록이 없습니다. 차량 정상 여부를 뜻하지 않습니다.")
            }
            summary.warnings.sortedBy { it.type }.forEach { warning ->
                appendLine("${warning.type} · 변화 기록 ${warning.records}개")
                val states = warning.recordedStates.orEmpty().split(',').filter { it.isNotBlank() }.distinct().sorted()
                appendLine("기록된 원시 상태: ${states.joinToString(", ").ifEmpty { "없음" }}")
                appendLine("기간 내 첫 기록: ${time(warning.firstRecordedAt)}")
                appendLine("기간 내 마지막 기록: ${time(warning.lastRecordedAt)}")
                appendLine("최초 관측 ${warning.firstObservations} · 상태 변경 ${warning.stateChanges} · 재관측 ${warning.reobservations}")
                appendLine("관측 재개 ${warning.resumptions} · 목록 제외 ${warning.removals}")
                val other = warning.records - warning.firstObservations - warning.stateChanges -
                    warning.reobservations - warning.resumptions - warning.removals
                if (other > 0) appendLine("기타 변화 기록 $other")
                appendLine()
            }
            appendLine("최근 변화 상세 · 최신순 ${summary.recentRecords.size}개 / 전체 ${summary.totalRecords}개")
            if (summary.totalRecords > summary.recentRecords.size) {
                appendLine("이전 ${summary.totalRecords - summary.recentRecords.size}개의 상세는 생략했습니다. 위 집계에는 전체 기록을 포함했습니다.")
            }
            summary.recentRecords.forEach { record ->
                val state = record.rawState?.let {
                    if (record.kind == "REMOVED_FROM_LIST") " · 제외 전 기록 상태 $it" else " · $it"
                }.orEmpty()
                val warning = record.type?.let { "$it$state · " }.orEmpty()
                appendLine("${time(record.at)} · $warning${eventLabel(record.kind)}")
            }
            appendLine()
            append("목록 제외는 경고 해제나 수리 완료를 뜻하지 않습니다. 이 요약은 관측 기록이며 원인·주행 가능 여부를 판정하지 않습니다.")
        }
    }

    private fun eventLabel(kind: String) = when (kind) {
        "FIRST_OBSERVED" -> "최초 관측"
        "STATE_CHANGED" -> "상태 변경"
        "REOBSERVED" -> "재관측"
        "OBSERVATION_RESUMED" -> "관측 재개 (공백 중 상태 미확인)"
        "REMOVED_FROM_LIST" -> "목록 제외 관측"
        "OBSERVATION_GAP" -> "수신 중단 · 관측 공백"
        "RECOVERY_GAP" -> "이전 수신 구간 종료 시각 미확인"
        else -> "기타 기록 ($kind)"
    }
}
