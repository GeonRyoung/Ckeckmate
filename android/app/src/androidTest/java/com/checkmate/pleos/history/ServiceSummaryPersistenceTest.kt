package com.checkmate.pleos.history

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.checkmate.pleos.summary.ServiceSummary
import com.checkmate.pleos.summary.SummaryWindow
import com.checkmate.pleos.vehicle.Observation
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ServiceSummaryPersistenceTest {
    private fun <T> await(operation: ((Result<T>) -> Unit) -> Unit): T {
        val done = CountDownLatch(1)
        var result: Result<T>? = null
        operation { result = it; done.countDown() }
        assertTrue("Database callback timed out", done.await(15, TimeUnit.SECONDS))
        return result!!.getOrThrow()
    }

    @Test fun summaryUsesTheWholePeriodWithoutChangingStoredHistory() {
        val context: Context = ApplicationProvider.getApplicationContext()
        val database = Room.inMemoryDatabaseBuilder(context, HistoryDatabase::class.java).build()
        val repository = HistoryRepository(database)
        try {
            await<List<String>> { repository.begin("session", 90, it) }
            fun save(at: Long, kind: String, type: String?, state: String?) {
                await<Unit> { repository.append("session", Observation(at, kind, kind, type, state), it) }
            }
            save(99, "FIRST_OBSERVED", "ABS", "ON")
            repeat(55) { save(100L + it, "STATE_CHANGED", "TPMS", if (it % 2 == 0) "ON" else "BLINK") }
            save(180, "REMOVED_FROM_LIST", "TPMS", "ON")
            save(181, "OBSERVATION_RESUMED", "TPMS", "BLINK")
            save(182, "OBSERVATION_GAP", null, null)
            save(183, "RECOVERY_GAP", null, null)
            save(200, "FIRST_OBSERVED", "ABS", "ON")
            val before = await<HistoryPage> { repository.page(0, it) }
            val summary = await<ServiceSummary> { repository.summary(SummaryWindow(100, 200), it) }
            assertEquals(59, summary.totalRecords)
            assertEquals(50, summary.recentRecords.size)
            assertEquals(183L, summary.recentRecords.first().at)
            val tpms = summary.warnings.single()
            assertEquals("TPMS", tpms.type)
            assertEquals(57, tpms.records)
            assertEquals(55, tpms.stateChanges)
            assertEquals(1, tpms.removals)
            assertEquals(1, tpms.resumptions)
            assertEquals(100L, tpms.firstRecordedAt)
            assertEquals(181L, tpms.lastRecordedAt)
            assertEquals(setOf("ON", "BLINK"), tpms.recordedStates!!.split(',').toSet())
            assertEquals(0, await<ServiceSummary> { repository.summary(SummaryWindow(190, 200), it) }.totalRecords)
            assertEquals(before, await<HistoryPage> { repository.page(0, it) })
            assertEquals(61, before.total)
        } finally {
            repository.closeForTest()
        }
    }
}
