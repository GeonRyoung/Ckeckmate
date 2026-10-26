package com.checkmate.pleos.manual

import android.content.Context

class ManualPreferences(context: Context) {
    private val preferences = context.applicationContext.getSharedPreferences("manual-profile", Context.MODE_PRIVATE)
    val selectedId: String? get() = preferences.getString("profileId", null)
    val selected: ManualProfile? get() = ManualCatalog.find(selectedId)

    fun select(id: String?) {
        require(id == null || ManualCatalog.find(id) != null) { "Unknown manual profile" }
        preferences.edit().apply {
            if (id == null) remove("profileId") else putString("profileId", id)
        }.apply()
    }
}
