"""
System Statistics Module
Provides system health metrics for the admin dashboard
"""

import psutil
import time
from datetime import datetime, timedelta

class SystemStats:
    """Collect and provide system statistics"""
    
    def __init__(self):
        self.start_time = time.time()
    
    def get_stats(self):
        """Get current system statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = self._format_bytes(memory.used)
            memory_total = self._format_bytes(memory.total)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = self._format_bytes(disk.used)
            disk_total = self._format_bytes(disk.total)
            
            # Uptime
            uptime_seconds = time.time() - self.start_time
            uptime = self._format_uptime(uptime_seconds)
            
            return {
                'health': {
                    'cpu_percent': round(cpu_percent, 1),
                    'memory_percent': round(memory_percent, 1),
                    'memory_used': memory_used,
                    'memory_total': memory_total,
                    'disk_percent': round(disk_percent, 1),
                    'disk_used': disk_used,
                    'disk_total': disk_total,
                    'uptime': uptime
                },
                'collections': self._get_collection_stats(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_collection_stats(self):
        """Get collection statistics"""
        try:
            # This would normally query your vector store
            # For now, returning placeholder data
            return {
                'total_collections': 13,
                'total_documents': 3911,
                'last_updated': 'Never'
            }
        except Exception:
            return {
                'total_collections': 0,
                'total_documents': 0,
                'last_updated': 'Unknown'
            }
    
    def _format_bytes(self, bytes_value):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    def _format_uptime(self, seconds):
        """Format uptime in human readable format"""
        uptime_delta = timedelta(seconds=int(seconds))
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
        
        return " ".join(parts)

# Global instance
system_stats = SystemStats()
