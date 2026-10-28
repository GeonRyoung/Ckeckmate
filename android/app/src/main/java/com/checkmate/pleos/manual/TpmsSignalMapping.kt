package com.checkmate.pleos.manual

import com.checkmate.pleos.vehicle.Observation

enum class TpmsPattern { NOT_EVALUATED, BLINK_ONGOING, BLINK_THEN_ON, ON_WITHOUT_OBSERVED_BLINK, ON_PRIOR_UNKNOWN }

data class TpmsPatternNote(val pattern: TpmsPattern, val text: String, val blinkObservedMs: Long? = null)

/**
 * Compares the SDK state order the app actually saw with the 2025 IONIQ 5 manual branches
 * (PDF 138·495). It names which manual description the order matches; it never diagnoses.
 */
object TpmsSignalMapping {
    private const val TYPE = "TPMS"
    private val stateEvents = setOf("FIRST_OBSERVED", "REOBSERVED", "STATE_CHANGED", "OBSERVATION_RESUMED")

    /** [events] is newest first, as kept by WarningMonitor. Only the current reading is evaluated. */
    fun describe(state: String?, current: Boolean, events: List<Observation>): TpmsPatternNote {
        if (!current || state !in setOf("ON", "BLINK")) return TpmsPatternNote(TpmsPattern.NOT_EVALUATED,
            "과거 기록이나 현재 상태를 확인할 수 없는 경우에는 관측 순서를 매뉴얼과 대조하지 않습니다.")
        // Stop at the latest gap: states before it belong to a different, unconnected observation run.
        val run = events.takeWhile { it.kind != "OBSERVATION_GAP" }
            .filter { it.warningType == TYPE && (it.kind in stateEvents || it.kind == "REMOVED_FROM_LIST") }
        val latest = run.firstOrNull()?.takeIf { it.kind in stateEvents }
        if (state == "BLINK") return TpmsPatternNote(TpmsPattern.BLINK_ONGOING, BLINK_TEXT)
        if (latest == null || latest.rawState != "ON" || !latest.afterContinuousReading) {
            return TpmsPatternNote(TpmsPattern.ON_PRIOR_UNKNOWN,
                "앱이 관측을 시작했을 때 이미 ON이었습니다. 그 전에 깜빡였는지는 알 수 없어 " +
                    "저압 점등과 깜빡인 뒤 켜짐(시스템 이상)을 구분할 수 없습니다.")
        }
        val previous = run.getOrNull(1)
        if (previous != null && previous.kind in stateEvents && previous.rawState == "BLINK") {
            val blinkMs = latest.at - previous.at
            val bound = if (previous.afterContinuousReading) "약" else "최소"
            return TpmsPatternNote(TpmsPattern.BLINK_THEN_ON,
                "끊김 없는 관측에서 BLINK 뒤 ON으로 바뀌었습니다(BLINK 관측 $bound ${blinkMs / 1000}초). " +
                    "매뉴얼의 시스템 이상 설명(깜빡인 뒤 켜짐, 경고등 표에서는 약 1분)과 같은 순서입니다. " +
                    "시간은 앱의 수신 간격으로 잰 값이라 실제 깜빡임 시간과 다를 수 있습니다.", blinkMs)
        }
        return TpmsPatternNote(TpmsPattern.ON_WITHOUT_OBSERVED_BLINK,
            "끊김 없는 관측에서 BLINK 없이 ON이 됐습니다. 매뉴얼은 저압 감지를 '켜짐'으로 설명합니다. " +
                "다만 시동 직후 약 3초 점검 점등이거나, 앱이 수신하지 못한 짧은 깜빡임 뒤일 가능성은 배제할 수 없습니다.")
    }

    private const val BLINK_TEXT = "BLINK가 관측됐습니다. 매뉴얼에서 깜빡임은 시스템 이상 설명(깜빡인 뒤 켜짐)에 나오며, " +
        "저압 감지는 '켜짐'으로 설명합니다. 깜빡임 뒤 켜지는지는 아직 관측되지 않았습니다."
}
