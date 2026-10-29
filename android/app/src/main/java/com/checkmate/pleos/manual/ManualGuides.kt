package com.checkmate.pleos.manual

enum class GuideStatus { READY, PROFILE_REQUIRED, PROFILE_UNAVAILABLE, UNSUPPORTED_WARNING, UNSUPPORTED_STATE }

data class ManualGuide(
    val status: GuideStatus,
    val title: String,
    val explanation: String,
    val observationLimit: String,
    val source: ManualSource? = null,
)

/** Reviewed local paraphrase per SDK warning type; no network call and no generated vehicle diagnosis. */
object ManualGuides {
    private class Content(val states: Set<String>, val section: String, val explanation: String,
        val limit: (String) -> String)

    private val contents = mapOf(
        "TPMS" to Content(setOf("ON", "BLINK"), "타이어 공기압 경보 시스템 (TPMS) · PDF 138, 493–496쪽", """
            TPMS는 휠에 장착된 센서로 타이어 공기압을 감시해 낮은 공기압을 알리는 장치입니다. 매뉴얼은 저압 타이어 경고등이 켜지는 저압 감지와, TPMS 경고등이 깜빡인 뒤 켜지는 시스템 이상을 구분합니다.

            저압 타이어 감지
            매뉴얼은 저압 경고등이 켜지면 속도를 낮추고 급격한 조향을 피하며, 현대 직영 하이테크센터나 블루핸즈에서 타이어 상태를 점검한 뒤 공기압을 조절하도록 안내합니다. 공기압은 주행 종료 후 3시간 이후 또는 주행 시작 후 1.6 km 이내에 조절합니다. 기온이 낮아지면 적정 공기압으로 맞춘 뒤에도 경고등이 켜질 수 있습니다.

            시스템 이상 표시
            매뉴얼은 TPMS 경고등이 깜빡인 뒤 켜지면 시스템 이상으로 보고 즉시 점검받도록 안내합니다. 공기를 보충한 뒤에도 약 1분간 깜빡인 뒤 켜지는 경우도 점검 대상입니다. 저압 표시 중 고장이 나면 위치 표시가 사라지지만, 저압이 해소되었다는 뜻은 아닙니다.

            주의
            못이나 도로 파편으로 인한 갑작스러운 타이어 손상은 TPMS가 감지하지 못합니다. 주행 중 차체가 불안하면 가속 페달에서 발을 떼고 안전한 장소로 천천히 이동한 뒤 점검하도록 안내합니다.
        """.trimIndent()) { state -> """
            앱이 받은 $state 값만으로 저압 또는 시스템 고장을 확정할 수 없습니다. 깜빡임의 지속 시간과 이후 점등 패턴도 이 값 하나로 판단하지 않습니다.
            타이어별 압력·위치, 정확한 원인, 주행 가능 여부와 수리 완료 여부는 확인하지 못했습니다. 위 내용은 선택한 차량 매뉴얼의 일반 설명이며 실제 차량의 진단 결과가 아닙니다.
        """.trimIndent() },
        // The manual only describes this lamp as lit; a blinking brake lamp is a different lamp.
        "ELECTRONIC_PARKING_BRAKE" to Content(setOf("ON"), "전자식 주차 브레이크 (EPB) · PDF 138, 331–333쪽", """
            EPB 경고등은 전자식 주차 브레이크 이상을 알립니다. 주차 브레이크 체결 여부를 알리는 브레이크 경고등과는 다른 경고등입니다.

            시동 점검과 이상 점등
            정상 상태에서는 시동을 걸 때 켜지고 약 3초 후 꺼집니다. 3초 후에도 꺼지지 않거나 주행 중 켜지면 현대 직영 하이테크센터나 블루핸즈에서 점검받도록 안내합니다.

            경고등이 켜졌을 때
            EPB 스위치를 빠르게 반복 조작하거나 당긴 채로 두어도 켜질 수 있습니다. 시동을 끄고 잠시 기다린 후 다시 걸어 경고등이 꺼지고 정상 작동하는지 확인하고, 계속 켜져 있으면 점검받도록 안내합니다. 브레이크 경고등이 함께 깜빡이면 스위치를 한 번 눌렀다가 당긴 후 원래 위치에서 다시 당겨 봅니다. 정상적으로 해제되지 않으면 견인 후 점검하도록 안내합니다. ESC 고장 시 함께 켜질 수도 있습니다.

            주의
            주차 브레이크를 체결한 채 주행하지 마십시오. 비상 상황이 아니면 주행 중 EPB 스위치를 조작하지 않습니다. 브레이크에 문제가 생긴 비상시에만 스위치를 당긴 채 유지해 제동하며, 놓으면 중단되고 제동 거리는 길어질 수 있습니다.
        """.trimIndent()) { state -> """
            앱이 받은 $state 값만으로 시동 직후 약 3초 점검 점등, 스위치 과다 조작, 실제 주차 브레이크 이상을 구분할 수 없습니다.
            주차 브레이크 체결 여부, 브레이크 경고등·ESC 경고등의 동시 점등, 정확한 원인과 수리 완료 여부는 확인하지 못했습니다. 위 내용은 선택한 차량 매뉴얼의 일반 설명이며 실제 차량의 진단 결과가 아닙니다.
        """.trimIndent() },
    )

    val supportedWarnings: Set<String> get() = contents.keys

    fun get(profileId: String?, warningType: String, rawState: String?): ManualGuide {
        if (profileId == null) return unavailable(GuideStatus.PROFILE_REQUIRED,
            "설명 기준을 선택해 주세요", "매뉴얼 설정에서 차량·연식·판매 지역을 확인하고 프로필을 선택하세요.")
        val profile = ManualCatalog.find(profileId) ?: return unavailable(GuideStatus.PROFILE_UNAVAILABLE,
            "선택한 매뉴얼을 사용할 수 없습니다", "등록된 프로필을 다시 선택해 주세요. 다른 차종의 설명으로 대체하지 않습니다.")
        val content = contents[warningType] ?: return unavailable(GuideStatus.UNSUPPORTED_WARNING,
            "이 경고의 매뉴얼 설명은 준비되지 않았습니다",
            "현재는 선택한 프로필의 TPMS·전자식 주차 브레이크 설명만 제공합니다. 관측 기록은 그대로 확인할 수 있습니다.")
        if (rawState == null || rawState !in content.states) return unavailable(GuideStatus.UNSUPPORTED_STATE,
            "이 상태값에 대한 설명은 제공하지 않습니다", "수신한 원시 상태와 관측 시각만 표시합니다.")
        return ManualGuide(
            status = GuideStatus.READY,
            title = "매뉴얼 요약 · 오프라인",
            explanation = content.explanation,
            observationLimit = content.limit(rawState),
            source = profile.source.copy(section = content.section),
        )
    }

    private fun unavailable(status: GuideStatus, title: String, explanation: String) =
        ManualGuide(status, title, explanation, "관측 정보와 매뉴얼 설명은 별도로 표시됩니다.")
}
