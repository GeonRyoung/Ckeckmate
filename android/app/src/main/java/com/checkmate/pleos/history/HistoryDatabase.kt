package com.checkmate.pleos.history

import androidx.room.*

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
}

@Database(entities = [ObservationSession::class, WarningEvent::class], version = 1, exportSchema = true)
abstract class HistoryDatabase : RoomDatabase() {
    abstract fun history(): HistoryDao
}
