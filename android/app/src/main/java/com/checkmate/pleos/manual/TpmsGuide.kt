package com.checkmate.pleos.manual

enum class GuideStatus { READY, PROFILE_REQUIRED, PROFILE_UNAVAILABLE, UNSUPPORTED_WARNING, UNSUPPORTED_STATE }

data class ManualGuide(
    val status: GuideStatus,
    val title: String,
    val explanation: String,
    val observationLimit: String,
    val source: ManualSource? = null,
)

/** Reviewed local paraphrase; no network call and no generated vehicle diagnosis. */
object TpmsGuide {
    fun get(profileId: String?, warningType: String, rawState: String?): ManualGuide {
        if (profileId == null) return unavailable(GuideStatus.PROFILE_REQUIRED,
            "설명 기준을 선택해 주세요", "매뉴얼 설정에서 차량·연식·판매 지역을 확인하고 프로필을 선택하세요.")
        val profile = ManualCatalog.find(profileId) ?: return unavailable(GuideStatus.PROFILE_UNAVAILABLE,
            "선택한 매뉴얼을 사용할 수 없습니다", "등록된 프로필을 다시 선택해 주세요. 다른 차종의 설명으로 대체하지 않습니다.")
        if (warningType != "TPMS") return unavailable(GuideStatus.UNSUPPORTED_WARNING,
            "이 경고의 매뉴얼 설명은 준비되지 않았습니다", "현재는 선택한 프로필의 TPMS 설명만 제공합니다. 관측 기록은 그대로 확인할 수 있습니다.")
        if (rawState !in setOf("ON", "BLINK")) return unavailable(GuideStatus.UNSUPPORTED_STATE,
            "이 상태값에 대한 설명은 제공하지 않습니다", "수신한 원시 상태와 관측 시각만 표시합니다.")
        return ManualGuide(
            status = GuideStatus.READY,
            title = "매뉴얼 요약 · 오프라인",
            explanation = """
                TPMS는 타이어의 압력 상태를 감시해 낮은 공기압을 알리는 장치입니다.

                저압 타이어 감지
                매뉴얼은 저압 경고가 켜지면 감속하고 급격한 방향 전환을 피하며, 현대 하이테크센터 또는 블루핸즈에서 타이어 점검과 공기압 조정을 받도록 안내합니다.

                시스템 이상 표시
                매뉴얼에서 TPMS 경고가 깜빡인 뒤 계속 켜지는 패턴은 시스템 이상 안내에 해당합니다. 이 경우 즉시 현대 하이테크센터 또는 블루핸즈에서 점검하도록 안내합니다.
            """.trimIndent(),
            observationLimit = """
                앱이 받은 ${rawState} 값만으로 저압 또는 시스템 고장을 확정할 수 없습니다. 깜빡임의 지속 시간과 이후 점등 패턴도 이 값 하나로 판단하지 않습니다.
                타이어별 압력·위치, 정확한 원인, 주행 가능 여부와 수리 완료 여부는 확인하지 못했습니다. 위 내용은 선택한 차량 매뉴얼의 일반 설명이며 실제 차량의 진단 결과가 아닙니다.
            """.trimIndent(),
            source = profile.source,
        )
    }

    private fun unavailable(status: GuideStatus, title: String, explanation: String) =
        ManualGuide(status, title, explanation, "관측 정보와 매뉴얼 설명은 별도로 표시됩니다.")
}
