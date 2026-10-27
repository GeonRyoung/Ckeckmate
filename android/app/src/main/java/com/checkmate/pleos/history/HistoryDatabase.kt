package com.checkmate.pleos.history

import androidx.room.*
import com.checkmate.pleos.summary.SummaryEventCount
import com.checkmate.pleos.summary.SummaryRecord
import com.checkmate.pleos.summary.WarningRollup

@Entity(tableName = "observation_sessions")
data class ObservationSession(
    @PrimaryKey val id: String,
    val startedAt: Long,
    val lastReceivedAt: Long? = null,
    val endedAt: Long? = null,
    val endReason: String? = null,
)

@Entity(
    tableName = "warning_events",
    foreignKeys = [ForeignKey(entity = ObservationSession::class,
        parentColumns = ["id"], childColumns = ["sessionId"], onDelete = ForeignKey.CASCADE)],
    indices = [Index("sessionId"), Index(value = ["eventKey"], unique = true), Index("observedAt")],
)
data class WarningEvent(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val eventKey: String,
    val sessionId: String,
    val warningType: String?,
    val rawState: String?,
    val eventKind: String,
    val observedAt: Long,
    val message: String,
    val source: String = "PLEOS_VEHICLE_SDK",
)

@Dao
interface HistoryDao {
    @Insert fun insertSession(session: ObservationSession)
    @Insert(onConflict = OnConflictStrategy.IGNORE) fun insertEvent(event: WarningEvent): Long
    @Query("SELECT * FROM observation_sessions WHERE endReason IS NULL")
    fun openSessions(): List<ObservationSession>
    @Query("UPDATE observation_sessions SET endReason = 'INTERRUPTED' WHERE endReason IS NULL")
    fun markInterrupted()
    @Query("UPDATE observation_sessions SET lastReceivedAt = :at WHERE id = :id")
    fun received(id: String, at: Long)
    @Query("UPDATE observation_sessions SET endedAt = :at, endReason = :reason WHERE id = :id")
    fun finish(id: String, at: Long, reason: String)
    @Query("SELECT DISTINCT warningType FROM warning_events WHERE warningType IS NOT NULL")
    fun seenTypes(): List<String>
    @Query("SELECT * FROM warning_events ORDER BY observedAt DESC, id DESC LIMIT :limit OFFSET :offset")
    fun page(limit: Int, offset: Int): List<WarningEvent>
    @Query("SELECT COUNT(*) FROM warning_events") fun count(): Int
    @Query("SELECT * FROM observation_sessions WHERE id = :id") fun session(id: String): ObservationSession?

    @Query("""
        SELECT warningType AS type, COUNT(*) AS records,
            MIN(observedAt) AS firstRecordedAt, MAX(observedAt) AS lastRecordedAt,
            GROUP_CONCAT(DISTINCT rawState) AS recordedStates,
            SUM(CASE WHEN eventKind = 'FIRST_OBSERVED' THEN 1 ELSE 0 END) AS firstObservations,
            SUM(CASE WHEN eventKind = 'STATE_CHANGED' THEN 1 ELSE 0 END) AS stateChanges,
            SUM(CASE WHEN eventKind = 'REOBSERVED' THEN 1 ELSE 0 END) AS reobservations,
            SUM(CASE WHEN eventKind = 'OBSERVATION_RESUMED' THEN 1 ELSE 0 END) AS resumptions,
            SUM(CASE WHEN eventKind = 'REMOVED_FROM_LIST' THEN 1 ELSE 0 END) AS removals
        FROM warning_events
        WHERE observedAt >= :start AND observedAt < :end AND warningType IS NOT NULL
        GROUP BY warningType ORDER BY warningType
    """)
    fun summaryWarnings(start: Long, end: Long): List<WarningRollup>

    @Query("""
        SELECT eventKind AS kind, COUNT(*) AS records FROM warning_events
        WHERE observedAt >= :start AND observedAt < :end GROUP BY eventKind ORDER BY eventKind
    """)
    fun summaryCounts(start: Long, end: Long): List<SummaryEventCount>

    @Query("""
        SELECT observedAt AS at, eventKind AS kind, warningType AS type, rawState
        FROM warning_events WHERE observedAt >= :start AND observedAt < :end
        ORDER BY observedAt DESC, id DESC LIMIT :limit
    """)
    fun summaryRecent(start: Long, end: Long, limit: Int): List<SummaryRecord>
}

@Database(entities = [ObservationSession::class, WarningEvent::class], version = 1, exportSchema = true)
abstract class HistoryDatabase : RoomDatabase() {
    abstract fun history(): HistoryDao
}
