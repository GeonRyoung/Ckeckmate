package com.checkmate.pleos.vehicle

data class WarningReading(val type: String, val state: String)
data class ObservedWarning(val reading: WarningReading, val observedAt: Long)
data class Observation(val at: Long, val message: String)

/** Single-threaded, in-memory observations. Absence is not a repair/clear verdict. */
class WarningMonitor {
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
        if (continuous) record(at, "관측 공백 시작 · $reason")
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
            (old.keys - incoming.keys).forEach { record(at, "$it · 목록 제외 관측 (해제 의미 미검증)") }
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
                record(at, "${reading.type} · ${reading.state} · $kind")
            }
            seen.add(reading.type)
            ObservedWarning(reading, if (same) previous!!.observedAt else at)
        }
        lastReceivedAt = at
        continuous = true
        isCurrent = true
        status = "유효한 차량 데이터 수신"
    }

    private fun record(at: Long, message: String) {
        history.addFirst(Observation(at, message))
        while (history.size > 50) history.removeLast()
    }
}
