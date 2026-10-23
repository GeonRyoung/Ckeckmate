package com.checkmate.pleos.vehicle

import android.car.Car
import android.car.drivingstate.CarUxRestrictions
import android.car.drivingstate.CarUxRestrictionsManager
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log

class UxRestrictionSource(
    private val context: Context,
    private val onChanged: (Boolean, String) -> Unit,
) {
    private var car: Car? = null
    private var manager: CarUxRestrictionsManager? = null
    private var epoch = 0

    fun start() {
        if (car != null) return
        val generation = ++epoch
        onChanged(false, "사용 제한 상태 확인 중")
        try {
            car = Car.createCar(context, Handler(Looper.getMainLooper()), Car.CAR_WAIT_TIMEOUT_DO_NOT_WAIT) { connection, ready ->
                if (generation != epoch) return@createCar
                if (!ready) {
                    manager = null
                    onChanged(false, "사용 제한 상태 확인 불가")
                } else {
                    try {
                        manager?.unregisterListener()
                        val service = connection.getCarManager(Car.CAR_UX_RESTRICTION_SERVICE) as CarUxRestrictionsManager
                        manager = service
                        service.registerListener { restrictions ->
                            if (generation == epoch) publish(restrictions)
                        }
                        publish(service.currentCarUxRestrictions)
                    } catch (error: Exception) {
                        Log.w("CHECKMATE_UX", "UX restrictions unavailable", error)
                        onChanged(false, "사용 제한 상태 확인 불가")
                    }
                }
            }
        } catch (error: Exception) {
            Log.w("CHECKMATE_UX", "Car service unavailable", error)
            onChanged(false, "차량 UX 서비스 연결 불가")
        }
    }

    private fun publish(value: CarUxRestrictions?) {
        val allowed = value != null && !value.isRequiresDistractionOptimization &&
            value.activeRestrictions == CarUxRestrictions.UX_RESTRICTIONS_BASELINE
        onChanged(allowed, if (allowed) "상세 화면 사용 가능" else "상세 화면 사용 제한")
    }

    fun stop() {
        ++epoch
        try { manager?.unregisterListener() }
        catch (error: Exception) { Log.w("CHECKMATE_UX", "Unregister failed", error) }
        manager = null
        car?.disconnect()
        car = null
        onChanged(false, "사용 제한 상태 미확인")
    }
}
