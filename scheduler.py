#!/usr/bin/env python3
"""
Scheduled Document Digestion Service

Runs incremental document indexing on a schedule (default: midnight daily).

Features:
1. Configurable schedule (cron-style or simple time)
2. Runs as background service or standalone
3. Email/webhook notifications for sync results
4. Graceful shutdown handling
5. Detailed logging

Usage:
    # Run as standalone scheduler daemon
    python scheduler.py
    
    # Run once immediately (for cron/Task Scheduler integration)
    python scheduler.py --once
    
    # Run with custom schedule
    python scheduler.py --time 02:30
    
    # Test mode (run now, then exit)
    python scheduler.py --test

For Plesk/cPanel Cron Integration:
    Add to crontab: 0 0 * * * cd /path/to/rag-system && python scheduler.py --once
"""

import os
import sys
import time
import signal
import logging
import argparse
import json
from datetime import datetime, timedelta
from threading import Thread, Event
from typing import Optional, Callable
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment (SYNC_TIME, SYNC_INTERVAL_DAYS, SYNC_WEBHOOK_URL)
try:
    from dotenv import load_dotenv
    _env_prod = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.production')
    load_dotenv(_env_prod if os.path.exists(_env_prod) else None)
except ImportError:
    pass

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'scheduler.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('scheduler')


class ScheduledIndexer:
    """
    Scheduled document indexing service.
    
    Runs incremental sync at configured times, handling:
    - Time-based scheduling
    - Graceful shutdown
    - Error recovery
    - Result notifications
    """
    
    def __init__(
        self,
        run_time: str = "00:00",
        timezone: str = "UTC",
        dry_run: bool = False,
        notification_webhook: Optional[str] = None,
        interval_days: int = 1
    ):
        """
        Initialize the scheduler.

        Args:
            run_time: Time to run sync in HH:MM format (24-hour)
            timezone: Timezone for scheduling (currently UTC-based)
            dry_run: If True, preview changes without making them
            notification_webhook: Optional webhook URL for notifications
            interval_days: Run sync every N days (e.g., 3 = every third day)
        """
        self.run_time = run_time
        self.timezone = timezone
        self.dry_run = dry_run
        self.notification_webhook = notification_webhook
        self.interval_days = max(1, int(interval_days))

        self._stop_event = Event()
        self._running = False

        # Parse run time
        self.run_hour, self.run_minute = map(int, run_time.split(':'))

        logger.info(f"Scheduler initialized: run_time={run_time}, "
                    f"interval_days={self.interval_days}, dry_run={dry_run}")

    def _last_run_timestamp(self) -> Optional[datetime]:
        """Timestamp of the last recorded run, if any."""
        info = get_last_run_info()
        if info and info.get('timestamp'):
            try:
                return datetime.fromisoformat(info['timestamp'])
            except ValueError:
                pass
        return None

    def _get_next_run_time(self) -> datetime:
        """Calculate the next scheduled run time (interval_days after the last run)."""
        now = datetime.utcnow()

        last_run = self._last_run_timestamp()
        if last_run:
            target = last_run.replace(
                hour=self.run_hour,
                minute=self.run_minute,
                second=0,
                microsecond=0
            ) + timedelta(days=self.interval_days)
            if target > now:
                return target
            # Overdue — run at the next occurrence of run_time

        target = now.replace(
            hour=self.run_hour,
            minute=self.run_minute,
            second=0,
            microsecond=0
        )
        if now >= target:
            target += timedelta(days=1)

        return target

    def is_due(self) -> bool:
        """True if at least interval_days have passed since the last run.

        Used by --once so a daily cron entry can drive an every-N-days
        schedule: runs that come up too early are skipped.
        """
        last_run = self._last_run_timestamp()
        if last_run is None:
            return True
        # 1-hour slack so a cron firing a few minutes early still counts
        elapsed = datetime.utcnow() - last_run
        return elapsed >= timedelta(days=self.interval_days) - timedelta(hours=1)
    
    def _seconds_until_next_run(self) -> float:
        """Calculate seconds until next scheduled run."""
        next_run = self._get_next_run_time()
        now = datetime.utcnow()
        return (next_run - now).total_seconds()
    
    def _run_sync(self) -> dict:
        """Execute the incremental sync."""
        logger.info("=" * 60)
        logger.info("Starting scheduled incremental sync")
        logger.info("=" * 60)
        
        try:
            from incremental_indexer import IncrementalIndexer
            
            indexer = IncrementalIndexer(dry_run=self.dry_run)
            stats = indexer.run_full_sync()
            
            logger.info("Scheduled sync completed successfully")
            return {
                'status': 'success',
                'stats': stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Scheduled sync failed: {e}")
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _send_notification(self, result: dict):
        """Send notification about sync result (if configured)."""
        if not self.notification_webhook:
            return
        
        try:
            import requests
            
            # Prepare notification payload
            payload = {
                'service': 'RAG Document Indexer',
                'event': 'scheduled_sync_complete',
                'status': result['status'],
                'timestamp': result['timestamp']
            }
            
            if result['status'] == 'success':
                stats = result['stats']
                payload['summary'] = (
                    f"Added: {stats.get('files_added', 0)}, "
                    f"Updated: {stats.get('files_updated', 0)}, "
                    f"Skipped: {stats.get('files_skipped', 0)}, "
                    f"Deleted: {stats.get('files_deleted', 0)}"
                )
            else:
                payload['error'] = result.get('error', 'Unknown error')
            
            response = requests.post(
                self.notification_webhook,
                json=payload,
                timeout=30
            )
            
            if 200 <= response.status_code < 300:
                logger.info("Notification sent successfully")
            else:
                logger.warning(f"Notification failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def _save_last_run(self, result: dict):
        """Save last run information to file."""
        try:
            last_run_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'last_scheduled_run.json'
            )
            
            with open(last_run_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save last run info: {e}")
    
    def run_once(self, force: bool = False) -> dict:
        """
        Run sync once immediately (for cron/Task Scheduler integration).

        With interval_days > 1, skips the run if the last one was too recent —
        so a daily cron entry yields an every-N-days schedule. Pass force=True
        to run regardless.
        """
        if not force and not self.is_due():
            last_run = self._last_run_timestamp()
            logger.info(f"Skipping sync: last run {last_run} is within "
                        f"the {self.interval_days}-day interval")
            return {
                'status': 'skipped',
                'reason': f'Last run within {self.interval_days}-day interval',
                'timestamp': datetime.utcnow().isoformat()
            }

        logger.info("Running one-time sync...")

        result = self._run_sync()
        self._save_last_run(result)
        self._send_notification(result)

        return result
    
    def run_daemon(self):
        """
        Run as a daemon, executing sync at scheduled times.
        
        Runs indefinitely until stopped with SIGTERM/SIGINT.
        """
        logger.info("Starting scheduler daemon")
        logger.info(f"Scheduled sync time: {self.run_time} UTC")
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        
        self._running = True
        
        while self._running and not self._stop_event.is_set():
            try:
                # Calculate time until next run
                seconds = self._seconds_until_next_run()
                next_run = self._get_next_run_time()
                
                logger.info(f"Next sync scheduled at: {next_run.isoformat()} UTC "
                           f"({seconds/3600:.1f} hours)")
                
                # Wait until next run or stop signal
                # Check every minute to remain responsive
                while seconds > 0 and not self._stop_event.is_set():
                    wait_time = min(60, seconds)
                    self._stop_event.wait(timeout=wait_time)
                    seconds = self._seconds_until_next_run()
                
                if self._stop_event.is_set():
                    break
                
                # Run the sync
                result = self._run_sync()
                self._save_last_run(result)
                self._send_notification(result)
                
                # Small delay to ensure we don't run immediately again
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                logger.error(traceback.format_exc())
                # Wait before retrying
                time.sleep(300)
        
        logger.info("Scheduler daemon stopped")
    
    def _handle_signal(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._running = False
        self._stop_event.set()
    
    def stop(self):
        """Stop the scheduler gracefully."""
        logger.info("Stopping scheduler...")
        self._running = False
        self._stop_event.set()


def get_last_run_info() -> Optional[dict]:
    """Get information about the last scheduled run."""
    last_run_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'last_scheduled_run.json'
    )
    
    if os.path.exists(last_run_file):
        with open(last_run_file, 'r') as f:
            return json.load(f)
    return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scheduled Document Digestion Service',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scheduler.py                    # Run as daemon (default: midnight)
  python scheduler.py --once             # Run once immediately, then exit
  python scheduler.py --time 02:30       # Run daily at 2:30 AM UTC
  python scheduler.py --test             # Run sync now (for testing)
  python scheduler.py --status           # Show last run info

For Plesk Cron (recommended):
  Add to crontab:
  0 0 * * * cd /var/www/vhosts/domain.com/rag-system && /usr/bin/python3 scheduler.py --once
        """
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run sync once and exit (for cron integration). Skipped if the '
             'last run is within --interval-days; combine a daily cron entry '
             'with --interval-days 3 for an every-3-days schedule.'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='With --once: run even if the last run is within the interval'
    )
    parser.add_argument(
        '--time',
        type=str,
        default=os.getenv('SYNC_TIME', '00:00'),
        help='Time to run sync in HH:MM format, 24-hour UTC '
             '(default: SYNC_TIME env var or 00:00)'
    )
    parser.add_argument(
        '--interval-days',
        type=int,
        default=int(os.getenv('SYNC_INTERVAL_DAYS', '1')),
        help='Run sync every N days (default: SYNC_INTERVAL_DAYS env var or 1). '
             'Set to 2 or 3 to check for changed documents every 2-3 days.'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run sync immediately for testing'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without making them'
    )
    parser.add_argument(
        '--webhook',
        type=str,
        default=os.getenv('SYNC_WEBHOOK_URL'),
        help='Webhook URL for sync result notifications '
             '(default: SYNC_WEBHOOK_URL env var)'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show information about the last scheduled run'
    )
    
    args = parser.parse_args()
    
    if args.status:
        info = get_last_run_info()
        if info:
            print("\nLast Scheduled Run:")
            print("=" * 50)
            print(f"Status: {info.get('status', 'unknown')}")
            print(f"Time: {info.get('timestamp', 'unknown')}")
            if info.get('stats'):
                stats = info['stats']
                print(f"Files Added: {stats.get('files_added', 0)}")
                print(f"Files Updated: {stats.get('files_updated', 0)}")
                print(f"Files Skipped: {stats.get('files_skipped', 0)}")
                print(f"Files Deleted: {stats.get('files_deleted', 0)}")
            if info.get('error'):
                print(f"Error: {info['error']}")
            print("=" * 50)
        else:
            print("No scheduled run history found.")
        return 0
    
    # Create scheduler
    scheduler = ScheduledIndexer(
        run_time=args.time,
        dry_run=args.dry_run,
        notification_webhook=args.webhook,
        interval_days=args.interval_days
    )

    if args.once or args.test:
        # Run once and exit (--test always forces)
        result = scheduler.run_once(force=args.force or args.test)
        status = result.get('status', 'unknown')

        if status == 'success':
            print("\n✅ Sync completed successfully!")
            stats = result.get('stats', {})
            print(f"   Added: {stats.get('files_added', 0)}")
            print(f"   Updated: {stats.get('files_updated', 0)}")
            print(f"   Skipped: {stats.get('files_skipped', 0)}")
            return 0
        elif status == 'skipped':
            print(f"\n⏭️ Sync skipped: {result.get('reason')}")
            return 0
        else:
            print(f"\n❌ Sync failed: {result.get('error', 'Unknown error')}")
            return 1
    else:
        # Run as daemon
        every = 'daily' if args.interval_days == 1 else f'every {args.interval_days} days'
        print(f"\n🕐 Starting scheduler daemon (sync at {args.time} UTC, {every})")
        print("   Press Ctrl+C to stop\n")
        scheduler.run_daemon()
        return 0


if __name__ == "__main__":
    sys.exit(main())
