package com.checkmate.pleos.assistance

import com.checkmate.pleos.manual.GuideStatus
import com.checkmate.pleos.manual.ManualGuides

/** Explicit user-selected situations. Never inferred from a single SDK raw state. */
data class WarningScenario(
    val id: String,
    val warningType: String,
    val title: String,
    val check: String,
    val guidance: String,
    val question: String,
    val pages: String,
)

object WarningScenarios {
    private val scenarios = listOf(
        WarningScenario("tpms-first", "TPMS", "공기압 경고가 처음 켜졌어요",
            "계속 켜져 있나요, 깜빡인 뒤 켜졌나요? 차체가 불안하거나 타이어 손상이 보이는지도 확인해 주세요.",
            "저압 경고등이 켜진 경우 매뉴얼은 속도를 낮추고 급격한 조향을 피하며, 현대 직영 하이테크센터나 블루핸즈에서 타이어 상태를 점검한 뒤 공기압을 조절하도록 안내합니다. 주행 중 차체가 불안하면 가속 페달에서 발을 떼고 안전한 장소로 천천히 이동한 뒤 점검하도록 안내합니다. 앱의 상태값만으로 저압이나 주행 가능 여부를 확정할 수 없습니다.",
            "타이어 공기압 경고가 처음 켜졌는데 어떻게 대처해야 하나요?", "495–496"),
        WarningScenario("tpms-blink", "TPMS", "깜빡인 뒤 계속 켜져 있어요",
            "깜빡임 뒤 점등을 직접 보셨나요? 대략 얼마나 깜빡였는지 증상에 적어 주세요. 앱이 지속 시간을 확인한 것은 아닙니다.",
            "매뉴얼은 TPMS 경고등이 깜빡인 뒤 켜지면 시스템 이상으로 보고 즉시 점검받도록 안내합니다. 공기를 보충한 뒤에도 약 1분간 깜빡인 뒤 켜지는 경우도 점검 대상입니다. 저압 표시가 사라져도 저압이 해소되었다는 뜻은 아닙니다. 실제 원인은 정비 점검이 필요합니다.",
            "경고등이 깜빡이다가 계속 켜져 있어요", "138, 495"),
        WarningScenario("tpms-again", "TPMS", "공기압 조절 후 다시 켜졌어요",
            "조절한 시점과 이후 기온 변화, 깜빡임 여부를 증상에 적어 주세요. 실제 타이어 공기압은 앱에서 확인하지 못합니다.",
            "매뉴얼에 따르면 적정 공기압으로 조절한 뒤에도 기온이 낮아지면 공기압이 줄어 경고등이 켜질 수 있습니다. 이 설명만으로 현재 차량이 정상이라고 판단하지 않습니다. 공기압은 주행 종료 후 3시간 이후 또는 주행 시작 후 1.6 km 이내에 조절합니다. 깜빡인 뒤 켜지면 즉시 점검받도록 안내합니다.",
            "공기압을 조절했는데 경고등이 다시 켜졌어요", "138, 495"),
        WarningScenario("epb-first", "ELECTRONIC_PARKING_BRAKE", "EPB 경고가 켜졌어요",
            "시동 직후 잠깐 켜졌나요, 약 3초 뒤에도 남아 있나요? 브레이크 경고등이나 ESC 경고등도 보이는지 적어 주세요.",
            "매뉴얼은 EPB 경고등이 시동 시 켜지고 약 3초 후 꺼지는 점검 점등을 설명합니다. 3초 후에도 꺼지지 않거나 주행 중 켜지면 현대 직영 하이테크센터나 블루핸즈에서 점검받도록 안내합니다. EPB 경고등과 주차 브레이크 체결 표시등은 다릅니다. 앱의 ON 값만으로 두 상황을 구분하지 못합니다.",
            "EPB 경고등이 계속 켜져 있어요", "138, 331, 333"),
        WarningScenario("epb-stuck", "ELECTRONIC_PARKING_BRAKE", "주차 브레이크가 풀리지 않아요",
            "해제를 시도했는데도 풀리지 않나요? 함께 보이는 경고와 시도한 조치를 적어 주세요. 앱이 실제 체결 여부를 확인하지는 못합니다.",
            "주차 브레이크를 체결한 채 주행하지 마십시오. 매뉴얼은 정상적으로 해제되지 않으면 견인 후 점검하도록 안내합니다. 비상 상황이 아니면 주행 중 EPB 스위치를 조작하지 않습니다. 여기서는 고장을 확정하거나 차량 제어를 수행하지 않습니다.",
            "전자식 주차 브레이크가 정상적으로 해제되지 않아요", "331–333"),
        WarningScenario("epb-remains", "ELECTRONIC_PARKING_BRAKE", "재시동 후에도 경고가 남아요",
            "정차 후 재시동했는데도 경고가 남았나요? 스위치 조작 여부와 재시동 뒤의 상태를 적어 주세요.",
            "매뉴얼은 EPB 스위치를 빠르게 반복 조작하거나 당긴 채 두어 경고가 켜질 수도 있다고 설명합니다. 시동을 끄고 잠시 기다린 후 다시 걸어 경고등과 작동을 확인하고, 계속 켜져 있으면 점검받도록 안내합니다. 정상적으로 해제되지 않으면 견인 후 점검합니다. 재시동 후 꺼졌다는 사실만으로 수리 완료를 판단하지 않습니다.",
            "시동을 다시 걸어도 EPB 경고등이 계속 켜져 있어요", "331–333"),
    )

    fun available(profileId: String?, warningType: String, state: String?): List<WarningScenario> =
        if (ManualGuides.get(profileId, warningType, state).status == GuideStatus.READY)
            scenarios.filter { it.warningType == warningType } else emptyList()
}
