package com.checkmate.pleos.history

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import android.content.Context
import com.checkmate.pleos.vehicle.Observation
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

@RunWith(AndroidJUnit4::class)
class HistoryPersistenceTest {
    private val context: Context = ApplicationProvider.getApplicationContext()
    private fun <T> await(operation: ((Result<T>) -> Unit) -> Unit): T {
        val done = CountDownLatch(1)
        var result: Result<T>? = null
        operation { result = it; done.countDown() }
        assertTrue("Database callback timed out", done.await(15, TimeUnit.SECONDS))
        return result!!.getOrThrow()
    }

    @Test fun eventsSurviveReopenAndUnfinishedSessionsBecomeGaps() {
        val name = "history-test-${UUID.randomUUID()}.db"
        var database = Room.databaseBuilder(context, HistoryDatabase::class.java, name).build()
        var repository = HistoryRepository(database)
        try {
            await<List<String>> { repository.begin("first", 100, it) }
            val event = Observation(110, "TPMS ON", "FIRST_OBSERVED", "TPMS", "ON")
            await<Unit> { repository.append("first", event, it) }
            await<Unit> { repository.append("first", event, it) } // retry is idempotent
            await<Unit> { repository.received("first", 120, it) }
            assertEquals(1, await<HistoryPage> { repository.page(0, it) }.total)
            repository.closeForTest() // Simulate process loss without a session-end write.
            database = Room.databaseBuilder(context, HistoryDatabase::class.java, name).build()
            repository = HistoryRepository(database)
            val seen = await<List<String>> { repository.begin("second", 200, it) }
            assertEquals(listOf("TPMS"), seen)
            val page = await<HistoryPage> { repository.page(0, it) }
            assertEquals(2, page.total)
            assertEquals("RECOVERY_GAP", page.events.first().eventKind)
            assertEquals("ON", page.events.last().rawState)
            assertEquals("INTERRUPTED", database.history().session("first")!!.endReason)
            assertNull(database.history().session("first")!!.endedAt)
            assertEquals(120L, database.history().session("first")!!.lastReceivedAt)
            await<Unit> { repository.finish("second", 220, "SCREEN_STOPPED", it) }
            await<List<String>> { repository.begin("third", 300, it) }
            assertEquals(2, await<HistoryPage> { repository.page(0, it) }.total)
        } finally {
            repository.closeForTest()
            context.deleteDatabase(name)
        }
    }

    @Test fun paginationIsStableForEqualTimesAndWriteFailuresAreReported() {
        val database = Room.inMemoryDatabaseBuilder(context, HistoryDatabase::class.java).build()
        val repository = HistoryRepository(database)
        try {
            await<List<String>> { repository.begin("session", 1, it) }
            repeat(55) { index ->
                await<Unit> { repository.append("session",
                    Observation(10, "event $index", "STATE_CHANGED", "TPMS", "$index"), it) }
            }
            val first = await<HistoryPage> { repository.page(0, it) }
            val second = await<HistoryPage> { repository.page(50, it) }
            assertEquals(55, first.total)
            assertEquals(50, first.events.size)
            assertEquals(5, second.events.size)
            assertEquals("54", first.events.first().rawState)
            assertEquals("0", second.events.last().rawState)
            assertTrue(first.events.map { it.id }.intersect(second.events.map { it.id }.toSet()).isEmpty())
            val failure = runCatching { await<Unit> {
                repository.append("missing-session", Observation(20, "invalid"), it)
            } }
            assertTrue(failure.isFailure)
            assertEquals(55, await<HistoryPage> { repository.page(0, it) }.total)
        } finally { repository.closeForTest() }
    }
}
