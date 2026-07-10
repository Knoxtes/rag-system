"""
Admin Sync Routes - API endpoints for managed document synchronization

Provides REST API for:
- Triggering incremental sync
- Checking sync status
- Viewing sync history
- Managing tracked files
"""

from flask import Blueprint, request, jsonify
from admin_auth import require_admin
import threading
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Create blueprint
sync_bp = Blueprint('admin_sync', __name__, url_prefix='/admin/sync')

# Global state for background sync
_sync_state = {
    'running': False,
    'progress': 0,
    'message': 'Ready',
    'started_at': None,
    'stats': None,
    'error': None
}
_sync_lock = threading.Lock()


def _update_sync_state(**kwargs):
    """Thread-safe state update."""
    with _sync_lock:
        _sync_state.update(kwargs)


def _run_incremental_sync(dry_run: bool = False):
    """Background sync worker."""
    try:
        _update_sync_state(
            running=True,
            progress=0,
            message='Initializing...',
            started_at=datetime.utcnow().isoformat(),
            error=None
        )
        
        from incremental_indexer import IncrementalIndexer
        
        _update_sync_state(message='Connecting to Google Drive...', progress=10)
        
        indexer = IncrementalIndexer(dry_run=dry_run)
        
        _update_sync_state(message='Scanning folders...', progress=20)
        
        stats = indexer.run_full_sync()
        
        _update_sync_state(
            running=False,
            progress=100,
            message='Sync completed successfully',
            stats=stats
        )
        
        logger.info(f"Incremental sync completed: {stats}")
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        import traceback
        _update_sync_state(
            running=False,
            progress=0,
            message='Sync failed',
            error=str(e)
        )


@sync_bp.route('/status', methods=['GET'])
@require_admin
def get_sync_status():
    """Get current sync status."""
    with _sync_lock:
        status = dict(_sync_state)
    
    # Add tracker stats
    try:
        from file_tracker import FileTracker
        tracker = FileTracker()
        tracker_stats = tracker.get_stats()
        status['tracker'] = tracker_stats
    except Exception as e:
        status['tracker_error'] = str(e)
    
    return jsonify(status)


@sync_bp.route('/start', methods=['POST'])
@require_admin
def start_sync():
    """Start incremental sync."""
    data = request.get_json() or {}
    dry_run = data.get('dry_run', False)

    with _sync_lock:
        if _sync_state['running']:
            return jsonify({
                'success': False,
                'error': 'Sync already in progress'
            }), 409
        _sync_state['running'] = True

    thread = threading.Thread(
        target=_run_incremental_sync,
        args=(dry_run,),
        daemon=True
    )
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Sync started',
        'dry_run': dry_run
    })


@sync_bp.route('/history', methods=['GET'])
@require_admin
def get_sync_history():
    """Get sync history."""
    try:
        from file_tracker import FileTracker
        
        limit = request.args.get('limit', 10, type=int)
        
        tracker = FileTracker()
        history = tracker.get_sync_history(limit=limit)
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@sync_bp.route('/files', methods=['GET'])
@require_admin
def get_tracked_files():
    """Get list of tracked files."""
    try:
        from file_tracker import FileTracker
        
        folder_id = request.args.get('folder_id')
        limit = request.args.get('limit', 100, type=int)
        
        tracker = FileTracker()
        
        if folder_id:
            files = tracker.get_files_in_folder(folder_id)
        else:
            # Get summary stats instead of all files
            stats = tracker.get_stats()
            return jsonify({
                'success': True,
                'total_files': stats['total_files'],
                'total_chunks': stats['total_chunks'],
                'by_folder': stats['files_by_folder']
            })
        
        return jsonify({
            'success': True,
            'files': files[:limit]
        })
        
    except Exception as e:
        logger.error(f"Error getting files: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@sync_bp.route('/file/<file_id>', methods=['GET'])
@require_admin
def get_file_state(file_id: str):
    """Get state of a specific tracked file."""
    try:
        from file_tracker import FileTracker
        
        tracker = FileTracker()
        state = tracker.get_file_state(file_id)
        
        if state:
            return jsonify({
                'success': True,
                'file': state
            })
        else:
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting file state: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@sync_bp.route('/file/<file_id>/reindex', methods=['POST'])
@require_admin
def reindex_file(file_id: str):
    """Force reindex a specific file."""
    try:
        from file_tracker import FileTracker
        
        tracker = FileTracker()
        
        # Remove from tracker to force reindex on next sync
        tracker.remove_file(file_id)
        
        return jsonify({
            'success': True,
            'message': 'File marked for reindexing'
        })
        
    except Exception as e:
        logger.error(f"Error marking file for reindex: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@sync_bp.route('/schedule', methods=['GET'])
@require_admin
def get_schedule_info():
    """Get scheduled sync information."""
    try:
        from scheduler import get_last_run_info
        import os
        
        last_run = get_last_run_info()
        sync_time = os.getenv('SYNC_TIME', '00:00')
        interval_days = int(os.getenv('SYNC_INTERVAL_DAYS', '1'))

        return jsonify({
            'success': True,
            'scheduled_time': sync_time,
            'interval_days': interval_days,
            'timezone': 'UTC',
            'last_run': last_run
        })
        
    except Exception as e:
        logger.error(f"Error getting schedule info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
