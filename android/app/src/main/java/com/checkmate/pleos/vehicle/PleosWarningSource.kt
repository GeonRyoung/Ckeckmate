package com.checkmate.pleos.vehicle

import ai.pleos.playground.vehicle.Vehicle
import ai.pleos.playground.vehicle.api.Safety
import ai.pleos.playground.vehicle.api.model.capability.AccessType
import ai.pleos.playground.vehicle.api.model.telltale.Telltales
import ai.pleos.playground.vehicle.listener.TelltaleInfoListener
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log

/** All callbacks are serialized on the main thread and scoped to one connection generation. */
class PleosWarningSource(
    private val context: Context,
    private val onReadings: (List<WarningReading>?) -> Unit,
    private val onError: (String) -> Unit,
) {
    private val main = Handler(Looper.getMainLooper())
    private var epoch = 0
    private var vehicle: Vehicle? = null
    private var safety: Safety? = null
    private var listener: TelltaleInfoListener? = null

    fun start() {
        if (vehicle != null) return
        val generation = ++epoch
        var liveCallbackReceived = false
        fun deliver(action: () -> Unit) {
            main.post { if (generation == epoch) action() }
        }
        fun failed(error: Exception) {
            Log.e(TAG, "Vehicle request failed", error)
            onError("${error.javaClass.simpleName}: ${error.message.orEmpty()}")
        }
        fun readings(value: Telltales?) = value?.telltales?.map {
            WarningReading(it.type.name, it.state.name)
        }
        try {
            val connection = Vehicle(context)
            vehicle = connection
            connection.initialize()
            val api = connection.getSafety()
            safety = api
            api.checkTelltalesCapabilities(
                onComplete = { capability -> deliver {
                    if (capability.accessType !in setOf(AccessType.READ, AccessType.READ_WRITE)) {
                        onError("이 환경은 경고 조회를 지원하지 않습니다")
                    } else {
                        try {
                            val subscription = object : TelltaleInfoListener {
                                override fun onTelltaleInfoUpdated(telltales: Telltales?) = deliver {
                                    liveCallbackReceived = true
                                    Log.d(TAG, "REALTIME: $telltales")
                                    onReadings(readings(telltales))
                                }
                                override fun onFailed(e: Exception) = deliver {
                                    liveCallbackReceived = true
                                    failed(e)
                                }
                            }
                            listener = subscription
                            api.registerTelltales(subscription)
                            api.getTelltalesInfo(
                                onComplete = { data -> deliver {
                                    if (!liveCallbackReceived) {
                                        Log.d(TAG, "INITIAL: $data")
                                        onReadings(readings(data))
                                    }
                                } },
                                onFailed = { error -> deliver {
                                    if (!liveCallbackReceived) failed(error)
                                } },
                            )
                        } catch (error: Exception) { failed(error) }
                    }
                } },
                onFailed = { error -> deliver { failed(error) } },
            )
        } catch (error: Exception) { failed(error) }
    }

    fun stop() {
        ++epoch // Ignore callbacks already queued by the previous connection.
        listener?.let { subscription ->
            try { safety?.unregisterTelltales(subscription) }
            catch (error: Exception) { Log.w(TAG, "Unregister failed", error) }
        }
        listener = null
        safety = null
        try { vehicle?.release() }
        catch (error: Exception) { Log.w(TAG, "Release failed", error) }
        vehicle = null
    }

    companion object { const val TAG = "CHECKMATE_VEHICLE" }
}
