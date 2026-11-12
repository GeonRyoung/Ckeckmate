package com.checkmate.pleos.ui

import android.content.Context
import android.graphics.drawable.Drawable
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.annotation.ColorRes
import androidx.annotation.DrawableRes
import androidx.annotation.StyleRes
import androidx.core.content.ContextCompat
import androidx.core.widget.TextViewCompat
import com.checkmate.pleos.R

/** Display labels for raw SDK values. Raw values stay visible where they are evidence. */
object WarningLabels {
    fun name(type: String?): String = when (type) {
        "TPMS" -> "타이어 공기압 경고"
        "ELECTRONIC_PARKING_BRAKE" -> "전자식 주차 브레이크 경고"
        "ABS" -> "ABS 경고"
        null -> "차량 관측"
        else -> "$type 경고"
    }

    fun state(raw: String?): String = when (raw) {
        "ON" -> "점등"
        "BLINK" -> "깜빡임"
        "OFF" -> "꺼짐"
        null -> "상태 없음"
        else -> raw
    }

    @DrawableRes
    fun icon(type: String?): Int = when (type) {
        "TPMS" -> R.drawable.ic_tpms
        "ELECTRONIC_PARKING_BRAKE" -> R.drawable.ic_epb
        else -> R.drawable.ic_warning
    }

    /** Severity wording follows the manual: TPMS blink means a system fault to inspect right away. */
    fun severity(type: String?, raw: String?): Severity = when {
        raw == "BLINK" -> Severity.URGENT
        raw == "ON" && (type == "TPMS" || type == "ELECTRONIC_PARKING_BRAKE") -> Severity.CAUTION
        raw == "ON" -> Severity.CAUTION
        else -> Severity.INFO
    }

    fun hint(type: String?, raw: String?): String = when {
        type == "TPMS" && raw == "BLINK" -> "TPMS 시스템 이상일 수 있습니다.\n안전한 곳에 정차한 뒤 점검을 받아 주세요."
        type == "TPMS" -> "속도를 줄이고 급조향을 피하세요.\n안전한 곳에 정차한 뒤 타이어 공기압을 점검해 주세요."
        type == "ELECTRONIC_PARKING_BRAKE" -> "시동 후 약 3초 뒤에도 켜져 있다면\n점검이 필요할 수 있습니다."
        else -> "이 경고는 아직 매뉴얼 안내를 제공하지 않습니다.\n관측 기록은 이력에 저장됩니다."
    }
}

enum class Severity(val label: String, @DrawableRes val chip: Int, @ColorRes val text: Int,
    @DrawableRes val card: Int, @ColorRes val icon: Int) {
    URGENT("즉시 점검", R.drawable.chip_red, R.color.red_text, R.drawable.card_danger, R.color.red_text),
    CAUTION("주의", R.drawable.chip_amber, R.color.amber_text, R.drawable.card_warning, R.color.amber_icon),
    INFO("정보", R.drawable.chip_neutral, R.color.text_secondary, R.drawable.card_background, R.color.text_secondary),
}

fun TextView.phraseBreaks() = apply {
    if (android.os.Build.VERSION.SDK_INT >= 33) {
        lineBreakWordStyle = android.graphics.text.LineBreakConfig.LINE_BREAK_WORD_STYLE_PHRASE
    }
}

fun Context.dp(value: Int) = (value * resources.displayMetrics.density).toInt()

fun Context.styledText(@StyleRes style: Int, value: CharSequence = "", size: Float? = null) = TextView(this).apply {
    TextViewCompat.setTextAppearance(this, style)
    text = value
    size?.let { setTextSize(TypedValue.COMPLEX_UNIT_SP, it) }
    phraseBreaks()
}

fun Context.chip(value: String, @DrawableRes background: Int, @ColorRes color: Int) = TextView(this).apply {
    text = value
    setBackgroundResource(background)
    setTextColor(ContextCompat.getColor(context, color))
    setTextSize(TypedValue.COMPLEX_UNIT_SP, 17f)
    typeface = resources.getFont(R.font.pretendard).let { android.graphics.Typeface.create(it, 600, false) }
    setPadding(dp(14), dp(6), dp(14), dp(6))
}

/** Plain or primary button matching Widget.Checkmate.Button(.Primary). */
fun Context.uiButton(label: String, primary: Boolean = false, @DrawableRes icon: Int? = null) = Button(this).apply {
    id = View.generateViewId()
    text = label
    isAllCaps = false
    stateListAnimator = null
    backgroundTintList = null
    setBackgroundResource(if (primary) R.drawable.button_primary else R.drawable.button_background)
    setTextColor(ContextCompat.getColorStateList(context, if (primary) R.color.button_primary_text else R.color.button_text))
    setTextSize(TypedValue.COMPLEX_UNIT_SP, 21f)
    typeface = android.graphics.Typeface.create(resources.getFont(R.font.pretendard), 600, false)
    minHeight = dp(72)
    minimumHeight = dp(72)
    setPadding(dp(24), dp(10), dp(24), dp(10))
    icon?.let { res ->
        val d: Drawable? = ContextCompat.getDrawable(context, res)?.mutate()
        d?.setTintList(ContextCompat.getColorStateList(context, if (primary) R.color.button_primary_text else R.color.button_text))
        setCompoundDrawablesRelativeWithIntrinsicBounds(d, null, null, null)
        compoundDrawablePadding = dp(12)
        // Keep the icon next to its label instead of pinned to the far edge.
        gravity = Gravity.START or Gravity.CENTER_VERTICAL
    }
    phraseBreaks()
}

/** Selectable row with a radio mark; text is exactly [label] so tests and a11y read it as-is. */
fun Context.optionRow(label: String) = Button(this).apply {
    id = View.generateViewId()
    text = label
    isAllCaps = false
    stateListAnimator = null
    backgroundTintList = null
    setBackgroundResource(R.drawable.option_background)
    setTextColor(ContextCompat.getColor(context, R.color.text_primary))
    setTextSize(TypedValue.COMPLEX_UNIT_SP, 21f)
    typeface = android.graphics.Typeface.create(resources.getFont(R.font.pretendard), 500, false)
    gravity = Gravity.START or Gravity.CENTER_VERTICAL
    minHeight = dp(80)
    minimumHeight = dp(80)
    setPadding(dp(24), dp(14), dp(24), dp(14))
    setCompoundDrawablesRelativeWithIntrinsicBounds(null, null, ContextCompat.getDrawable(context, R.drawable.radio_mark), null)
    compoundDrawablePadding = dp(16)
    layoutParams = LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(12) }
    phraseBreaks()
}

fun Context.card(@DrawableRes background: Int = R.drawable.card_background) = LinearLayout(this).apply {
    orientation = LinearLayout.VERTICAL
    setBackgroundResource(background)
    setPadding(dp(32), dp(32), dp(32), dp(32))
}

fun Context.divider() = View(this).apply {
    setBackgroundColor(ContextCompat.getColor(context, R.color.divider))
}

fun LinearLayout.LayoutParams.margins(top: Int = 0, bottom: Int = 0, start: Int = 0, end: Int = 0) = apply {
    topMargin = top; bottomMargin = bottom; marginStart = start; marginEnd = end
}
