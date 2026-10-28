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
        // Official PDF revision date; the profile id is kept so saved selections stay valid.
        documentRevision = "2025-04-16",
        checkedOn = "2026-10-28",
        source = ManualSource(
            documentTitle = "2025 아이오닉 5 취급설명서",
            section = "타이어 공기압 경보 시스템 (TPMS) · PDF 138, 493–496쪽",
            url = "https://ownersmanual.hyundai.com/full_pdf/NE1/2025/ko_KR",
            contentSha256 = "7c92b1e3b1326d6811340e664111897fc66f23b6ae96788e2d76e6f99eb30725",
        ),
    ))

    // Unknown / removed profiles must not silently fall back to another model.
    fun find(id: String?): ManualProfile? = profiles.singleOrNull { it.id == id }
}
