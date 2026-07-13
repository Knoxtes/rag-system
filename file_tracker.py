"""
File Tracker - Persistent Document State Tracking

Tracks file states (hash, modification time, chunk count) to enable:
1. Incremental indexing - only process new/changed files
2. Efficient updates - replace only modified documents
3. Deletion detection - remove orphaned documents from vector store

Storage: SQLite database for reliability and performance
"""

import sqlite3
import os
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class FileTracker:
    """
    Tracks file states for incremental document indexing.
    Uses SQLite for persistent, reliable storage.
    """
    
    def __init__(self, db_path: str = "./file_tracker.db"):
        """Initialize the file tracker database."""
        self.db_path = db_path
        self._initialize_db()
        logger.info(f"FileTracker initialized: {db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _initialize_db(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Main file tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tracked_files (
                    file_id TEXT PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    mime_type TEXT,
                    folder_id TEXT,
                    folder_name TEXT,
                    modified_time TEXT,
                    content_hash TEXT,
                    file_size INTEGER,
                    chunk_count INTEGER DEFAULT 0,
                    indexed_at TEXT,
                    last_checked TEXT,
                    status TEXT DEFAULT 'indexed'
                )
            """)
            
            # Index for folder queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_folder_id 
                ON tracked_files(folder_id)
            """)
            
            # Index for status queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON tracked_files(status)
            """)
            
            # Index for last_checked (for expired entries)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_checked 
                ON tracked_files(last_checked)
            """)
            
            # Sync history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT DEFAULT 'running',
                    folders_scanned INTEGER DEFAULT 0,
                    files_checked INTEGER DEFAULT 0,
                    files_added INTEGER DEFAULT 0,
                    files_updated INTEGER DEFAULT 0,
                    files_deleted INTEGER DEFAULT 0,
                    files_skipped INTEGER DEFAULT 0,
                    errors TEXT,
                    duration_seconds REAL
                )
            """)
            
            logger.info("Database tables initialized")
    
    def get_file_state(self, file_id: str) -> Optional[Dict]:
        """Get the tracked state of a file."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tracked_files WHERE file_id = ?
            """, (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def check_file_needs_update(
        self, 
        file_id: str, 
        modified_time: str,
        content_hash: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Check if a file needs to be re-indexed.
        
        Returns:
            (needs_update: bool, reason: str)
            - True, "new" - file is not tracked
            - True, "modified" - file's modification time changed
            - True, "content_changed" - file's content hash changed
            - False, "up_to_date" - file is unchanged
        """
        state = self.get_file_state(file_id)

        if not state or state.get('status') == 'deleted':
            return True, "new"

        # Check modification time
        if state['modified_time'] != modified_time:
            return True, "modified"
        
        # Optionally check content hash if provided
        if content_hash and state['content_hash'] and state['content_hash'] != content_hash:
            return True, "content_changed"
        
        return False, "up_to_date"
    
    def update_file_state(
        self,
        file_id: str,
        file_name: str,
        mime_type: str,
        folder_id: str,
        folder_name: str,
        modified_time: str,
        chunk_count: int,
        content_hash: Optional[str] = None,
        file_size: Optional[int] = None
    ):
        """Update or insert file tracking state after successful indexing."""
        now = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tracked_files 
                (file_id, file_name, mime_type, folder_id, folder_name, 
                 modified_time, content_hash, file_size, chunk_count, 
                 indexed_at, last_checked, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'indexed')
                ON CONFLICT(file_id) DO UPDATE SET
                    file_name = excluded.file_name,
                    mime_type = excluded.mime_type,
                    folder_id = excluded.folder_id,
                    folder_name = excluded.folder_name,
                    modified_time = excluded.modified_time,
                    content_hash = excluded.content_hash,
                    file_size = excluded.file_size,
                    chunk_count = excluded.chunk_count,
                    indexed_at = excluded.indexed_at,
                    last_checked = excluded.last_checked,
                    status = 'indexed'
            """, (
                file_id, file_name, mime_type, folder_id, folder_name,
                modified_time, content_hash, file_size, chunk_count,
                now, now
            ))
    
    def mark_file_checked(self, file_id: str):
        """Mark a file as checked during sync (even if not re-indexed)."""
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tracked_files 
                SET last_checked = ?
                WHERE file_id = ?
            """, (now, file_id))
    
    def mark_file_deleted(self, file_id: str):
        """Mark a file as deleted (no longer exists in source)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tracked_files 
                SET status = 'deleted'
                WHERE file_id = ?
            """, (file_id,))
    
    def rename_folder(self, folder_id: str, new_name: str):
        """Update the display name recorded for all tracked files in a folder."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tracked_files SET folder_name = ? WHERE folder_id = ?
            """, (new_name, folder_id))

    def remove_file(self, file_id: str):
        """Completely remove a file from tracking."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM tracked_files WHERE file_id = ?
            """, (file_id,))
    
    def get_stale_files(self, cutoff_time: datetime) -> List[Dict]:
        """
        Get files that haven't been seen since cutoff_time.
        These files may have been deleted from the source.
        """
        cutoff_str = cutoff_time.isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tracked_files 
                WHERE last_checked < ? AND status = 'indexed'
            """, (cutoff_str,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_files_in_folder(self, folder_id: str) -> List[Dict]:
        """Get all tracked files in a folder."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tracked_files 
                WHERE folder_id = ? AND status = 'indexed'
            """, (folder_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_tracked_file_ids(self) -> set:
        """Get set of all tracked file IDs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_id FROM tracked_files WHERE status = 'indexed'
            """)
            return {row['file_id'] for row in cursor.fetchall()}
    
    def get_stats(self) -> Dict:
        """Get tracking statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total files
            cursor.execute("SELECT COUNT(*) as count FROM tracked_files WHERE status = 'indexed'")
            total_files = cursor.fetchone()['count']
            
            # Total chunks
            cursor.execute("SELECT SUM(chunk_count) as count FROM tracked_files WHERE status = 'indexed'")
            total_chunks = cursor.fetchone()['count'] or 0
            
            # Files by folder
            cursor.execute("""
                SELECT folder_name, COUNT(*) as count 
                FROM tracked_files 
                WHERE status = 'indexed'
                GROUP BY folder_id
                ORDER BY count DESC
            """)
            by_folder = {row['folder_name']: row['count'] for row in cursor.fetchall()}
            
            # Last sync
            cursor.execute("""
                SELECT * FROM sync_history 
                ORDER BY id DESC LIMIT 1
            """)
            last_sync = cursor.fetchone()
            
            return {
                'total_files': total_files,
                'total_chunks': total_chunks,
                'files_by_folder': by_folder,
                'last_sync': dict(last_sync) if last_sync else None
            }
    
    def start_sync_session(self) -> int:
        """Start a new sync session and return its ID."""
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_history (started_at, status)
                VALUES (?, 'running')
            """, (now,))
            return cursor.lastrowid
    
    _SYNC_HISTORY_COLUMNS = frozenset({
        'status', 'folders_scanned', 'files_checked', 'files_added',
        'files_updated', 'files_deleted', 'files_skipped', 'errors',
        'completed_at', 'duration_seconds'
    })

    def update_sync_session(
        self,
        session_id: int,
        **kwargs
    ):
        """Update sync session progress."""
        if not kwargs:
            return

        set_clauses = []
        values = []
        for key, value in kwargs.items():
            if key not in self._SYNC_HISTORY_COLUMNS:
                raise ValueError(f"Unknown sync_history column: {key}")
            set_clauses.append(f"{key} = ?")
            values.append(value)

        values.append(session_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE sync_history
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """, values)
    
    def complete_sync_session(
        self,
        session_id: int,
        status: str = 'completed',
        files_checked: int = 0,
        files_added: int = 0,
        files_updated: int = 0,
        files_deleted: int = 0,
        files_skipped: int = 0,
        folders_scanned: int = 0,
        errors: Optional[str] = None
    ):
        """Complete a sync session with final statistics."""
        now = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get start time for duration calculation
            cursor.execute("""
                SELECT started_at FROM sync_history WHERE id = ?
            """, (session_id,))
            row = cursor.fetchone()
            
            duration = None
            if row:
                started = datetime.fromisoformat(row['started_at'])
                duration = (datetime.utcnow() - started).total_seconds()
            
            cursor.execute("""
                UPDATE sync_history SET
                    completed_at = ?,
                    status = ?,
                    folders_scanned = ?,
                    files_checked = ?,
                    files_added = ?,
                    files_updated = ?,
                    files_deleted = ?,
                    files_skipped = ?,
                    errors = ?,
                    duration_seconds = ?
                WHERE id = ?
            """, (
                now, status, folders_scanned, files_checked,
                files_added, files_updated, files_deleted, files_skipped,
                errors, duration, session_id
            ))
    
    def get_sync_history(self, limit: int = 10) -> List[Dict]:
        """Get recent sync history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sync_history 
                ORDER BY id DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]


def compute_content_hash(text: str) -> str:
    """Compute hash of document content for change detection."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


if __name__ == "__main__":
    # Test the file tracker
    tracker = FileTracker("./test_tracker.db")
    
    # Test operations
    print("Stats:", tracker.get_stats())
    
    # Test file state operations
    needs_update, reason = tracker.check_file_needs_update(
        "test_file_1", 
        "2025-01-01T00:00:00Z"
    )
    print(f"File needs update: {needs_update} ({reason})")
    
    # Update file state
    tracker.update_file_state(
        file_id="test_file_1",
        file_name="test.pdf",
        mime_type="application/pdf",
        folder_id="folder_123",
        folder_name="Test Folder",
        modified_time="2025-01-01T00:00:00Z",
        chunk_count=5,
        content_hash="abc123"
    )
    
    # Check again
    needs_update, reason = tracker.check_file_needs_update(
        "test_file_1",
        "2025-01-01T00:00:00Z"
    )
    print(f"After update - needs update: {needs_update} ({reason})")
    
    print("Final stats:", tracker.get_stats())
    
    # Cleanup test
    os.remove("./test_tracker.db")
    print("Test completed successfully!")
