package com.checkmate.pleos.history

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log
import androidx.room.Room
import com.checkmate.pleos.vehicle.Observation
import com.checkmate.pleos.summary.ServiceSummary
import com.checkmate.pleos.summary.SummaryWindow
import java.util.UUID
import java.util.concurrent.Executors

/** One process-wide queue preserves ordering across Activity recreation and reconnects. */
class HistoryRepository internal constructor(private val database: HistoryDatabase) {
    private val queue = Executors.newSingleThreadExecutor()
    private val main = Handler(Looper.getMainLooper())

    fun begin(id: String, at: Long, callback: (Result<List<String>>) -> Unit) = submit(callback) {
        val dao = database.history()
        var seen = emptyList<String>()
        database.runInTransaction {
            val interrupted = dao.openSessions()
            dao.markInterrupted() // endedAt remains null: actual termination time is unknown.
            dao.insertSession(ObservationSession(id, at))
            if (interrupted.isNotEmpty()) {
                dao.insertEvent(WarningEvent(eventKey = UUID.randomUUID().toString(), sessionId = id,
                    warningType = null, rawState = null, eventKind = "RECOVERY_GAP", observedAt = at,
                    message = "이전 수신 구간의 종료 기록 없음 · 종료 시각과 공백 중 차량 상태 미확인"))
            }
            seen = dao.seenTypes()
        }
        seen
    }

    fun append(sessionId: String, observation: Observation, callback: (Result<Unit>) -> Unit) = submit(callback) {
        database.history().insertEvent(WarningEvent(
            eventKey = observation.id, sessionId = sessionId, warningType = observation.warningType,
            rawState = observation.rawState, eventKind = observation.kind,
            observedAt = observation.at, message = observation.message))
        Unit
    }

    fun received(sessionId: String, at: Long, callback: (Result<Unit>) -> Unit) = submit(callback) {
        database.history().received(sessionId, at)
    }

    fun finish(sessionId: String, at: Long, reason: String, callback: (Result<Unit>) -> Unit) = submit(callback) {
        database.history().finish(sessionId, at, reason)
    }

    fun page(offset: Int, callback: (Result<HistoryPage>) -> Unit) = submit(callback) {
        var page = HistoryPage(emptyList(), 0)
        database.runInTransaction {
            val dao = database.history()
            page = HistoryPage(dao.page(PAGE_SIZE, offset), dao.count())
        }
        page
    }

    fun summary(window: SummaryWindow, callback: (Result<ServiceSummary>) -> Unit) = submit(callback) {
        // One transaction keeps totals, rollups and the detail sample on the same snapshot.
        database.runInTransaction(java.util.concurrent.Callable {
            val dao = database.history()
            ServiceSummary(window,
                dao.summaryWarnings(window.startInclusive, window.endExclusive),
                dao.summaryCounts(window.startInclusive, window.endExclusive),
                dao.summaryRecent(window.startInclusive, window.endExclusive, PAGE_SIZE))
        })
    }

    private fun <T> submit(callback: (Result<T>) -> Unit, block: () -> T) {
        queue.execute {
            val result = runCatching(block)
            result.exceptionOrNull()?.let { Log.e("CHECKMATE_DB", "History operation failed", it) }
            main.post { callback(result) }
        }
    }

    internal fun closeForTest() {
        queue.shutdown()
        check(queue.awaitTermination(10, java.util.concurrent.TimeUnit.SECONDS))
        database.close()
    }

    companion object {
        const val PAGE_SIZE = 50
        @Volatile private var instance: HistoryRepository? = null
        fun get(context: Context): HistoryRepository = instance ?: synchronized(this) {
            instance ?: HistoryRepository(Room.databaseBuilder(context.applicationContext,
                HistoryDatabase::class.java, "checkmate-history.db").build()).also { instance = it }
        }
    }
}

data class HistoryPage(val events: List<WarningEvent>, val total: Int)
