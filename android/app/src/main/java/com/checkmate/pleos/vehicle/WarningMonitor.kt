package com.checkmate.pleos.vehicle

data class WarningReading(val type: String, val state: String)
data class ObservedWarning(val reading: WarningReading, val observedAt: Long)
data class Observation(
    val at: Long, val message: String,
    val kind: String = "OBSERVATION", val warningType: String? = null, val rawState: String? = null,
    val id: String = java.util.UUID.randomUUID().toString(),
    // False for the first batch after start or a gap: the previous state was not observed. Not persisted.
    val afterContinuousReading: Boolean = false,
)

/** Single-threaded, in-memory observations. Absence is not a repair/clear verdict. */
class WarningMonitor(private val onObservation: (Observation) -> Unit = {}) {
    fun restoreSeen(types: List<String>) { seen.addAll(types) }
    var status = "차량 데이터 수신 대기"
        private set
    var current: List<ObservedWarning> = emptyList()
        private set
    var lastReceivedAt: Long? = null
        private set
    var isCurrent = false
        private set
    val events: List<Observation> get() = history.toList()
    private val history = ArrayDeque<Observation>()
    private val seen = mutableSetOf<String>()
    private var continuous = false

    fun waiting() {
        status = "차량 데이터 수신 대기"
        isCurrent = false
    }

    fun unavailable(reason: String, at: Long) {
        if (continuous) record(at, "관측 공백 시작 · $reason", "OBSERVATION_GAP")
        continuous = false
        isCurrent = false
        status = "상태 확인 불가 · $reason"
    }

    fun accept(readings: List<WarningReading>?, at: Long) {
        if (readings == null) {
            unavailable("유효한 데이터 없음", at)
            return
        }
        if (readings.map { it.type }.distinct().size != readings.size) {
            unavailable("중복된 경고 종류 수신", at)
            return
        }
        val old = current.associateBy { it.reading.type }
        val incoming = readings.associateBy { it.type }
        if (continuous) {
            (old.keys - incoming.keys).forEach { record(at, "$it · 목록 제외 관측 (해제 의미 미검증)", "REMOVED_FROM_LIST", it, old[it]?.reading?.state) }
        }
        current = readings.sortedBy { it.type }.map { reading ->
            val previous = old[reading.type]
            val same = continuous && previous?.reading == reading
            if (!same) {
                val kind = when {
                    !continuous && reading.type in seen -> "관측 재개 (공백 중 상태 미확인)"
                    continuous && previous != null -> "상태 변경"
                    reading.type in seen -> "재관측"
                    else -> "최초 관측"
                }
                val eventKind = when {
                    !continuous && reading.type in seen -> "OBSERVATION_RESUMED"
                    continuous && previous != null -> "STATE_CHANGED"
                    reading.type in seen -> "REOBSERVED"
                    else -> "FIRST_OBSERVED"
                }
                record(at, "${reading.type} · ${reading.state} · $kind", eventKind, reading.type, reading.state)
            }
            seen.add(reading.type)
            ObservedWarning(reading, if (same) previous!!.observedAt else at)
        }
        lastReceivedAt = at
        continuous = true
        isCurrent = true
        status = "유효한 차량 데이터 수신"
    }

    private fun record(at: Long, message: String, kind: String, type: String? = null, state: String? = null) {
        val observation = Observation(at, message, kind, type, state, afterContinuousReading = continuous)
        history.addFirst(observation)
        onObservation(observation)
        while (history.size > 50) history.removeLast()
    }
}
