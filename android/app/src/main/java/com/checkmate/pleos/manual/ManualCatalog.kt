package com.checkmate.pleos.manual

/** A user-selected documentation scope, never an automatically detected vehicle identity. */
data class ManualProfile(
    val id: String,
    val model: String,
    val modelYear: Int,
    val powertrain: String,
    val market: String,
    val language: String,
    val projectCode: String,
    val documentRevision: String,
    val checkedOn: String,
    val source: ManualSource,
) {
    val label: String get() = "$modelYear $model · $powertrain · $market · $language"
}

data class ManualSource(
    val documentTitle: String,
    val section: String,
    val url: String,
    val contentSha256: String,
)

object ManualCatalog {
    val profiles = listOf(ManualProfile(
        id = "hyundai-ioniq5-2025-ev-kr-ko-r1.27",
        model = "현대 아이오닉 5",
        modelYear = 2025,
        powertrain = "전기차",
        market = "대한민국",
        language = "한국어",
        projectCode = "NE1",
        documentRevision = "1.27",
        checkedOn = "2026-10-26",
        source = ManualSource(
            documentTitle = "2025 아이오닉 5 디지털 취급 설명서",
            section = "타이어 공기압 경보 시스템 (TPMS)",
            url = "https://ownersmanual.hyundai.com/full_webhelp/NE1/2025/ko_KR/id23C5E0QD0YK.html",
            contentSha256 = "f921142b9e9ce9e8745b7546a4959a93ad5f1fd507e110e75cd91c9d95e8d360",
        ),
    ))

    // Unknown / removed profiles must not silently fall back to another model.
    fun find(id: String?): ManualProfile? = profiles.singleOrNull { it.id == id }
}
