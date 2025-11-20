"""
Health monitoring and system diagnostics for the RAG system
"""
import os
import sys
import psutil
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SystemHealthMonitor:
    """Monitor system health and resource usage"""
    
    def __init__(self):
        self.start_time = datetime.now()
    
    def get_memory_usage(self):
        """Get current memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
            'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
            'percent': round(process.memory_percent(), 2)
        }
    
    def get_cpu_usage(self):
        """Get current CPU usage"""
        return {
            'percent': round(psutil.cpu_percent(interval=1), 2),
            'count': psutil.cpu_count()
        }
    
    def get_disk_usage(self, path='.'):
        """Get disk usage for given path"""
        disk = psutil.disk_usage(path)
        return {
            'total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
            'used_gb': round(disk.used / 1024 / 1024 / 1024, 2),
            'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
            'percent': round(disk.percent, 2)
        }
    
    def get_uptime(self):
        """Get application uptime"""
        uptime = datetime.now() - self.start_time
        return {
            'seconds': uptime.total_seconds(),
            'formatted': str(uptime).split('.')[0]
        }
    
    def check_dependencies(self):
        """Check if critical dependencies are available"""
        dependencies = {
            'chroma_db': False,
            'logs_dir': False,
            'credentials': False,
            'token': False
        }
        
        # Check ChromaDB directory
        if os.path.exists('./chroma_db'):
            dependencies['chroma_db'] = True
        
        # Check logs directory
        if os.path.exists('./logs'):
            dependencies['logs_dir'] = True
        
        # Check credentials
        if os.path.exists('./credentials.json'):
            dependencies['credentials'] = True
        
        # Check token
        if os.path.exists('./token.pickle'):
            dependencies['token'] = True
        
        return dependencies
    
    def check_log_size(self):
        """Check size of log files"""
        log_dir = Path('./logs')
        if not log_dir.exists():
            return {'total_mb': 0, 'files': []}
        
        total_size = 0
        log_files = []
        
        for log_file in log_dir.glob('*.log'):
            size = log_file.stat().st_size
            total_size += size
            log_files.append({
                'name': log_file.name,
                'size_mb': round(size / 1024 / 1024, 2),
                'modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
            })
        
        return {
            'total_mb': round(total_size / 1024 / 1024, 2),
            'files': sorted(log_files, key=lambda x: x['size_mb'], reverse=True)
        }
    
    def get_health_status(self):
        """Get comprehensive health status"""
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime': self.get_uptime(),
            'memory': self.get_memory_usage(),
            'cpu': self.get_cpu_usage(),
            'disk': self.get_disk_usage(),
            'dependencies': self.check_dependencies(),
            'logs': self.check_log_size()
        }
        
        # Determine overall health status
        warnings = []
        
        if health['memory']['percent'] > 80:
            warnings.append('High memory usage')
            health['status'] = 'warning'
        
        if health['cpu']['percent'] > 80:
            warnings.append('High CPU usage')
            health['status'] = 'warning'
        
        if health['disk']['percent'] > 80:
            warnings.append('Low disk space')
            health['status'] = 'warning'
        
        if not health['dependencies']['chroma_db']:
            warnings.append('ChromaDB directory not found')
            health['status'] = 'warning'
        
        if health['logs']['total_mb'] > 100:
            warnings.append('Log files exceeding 100MB')
            health['status'] = 'warning'
        
        if warnings:
            health['warnings'] = warnings
        
        return health
    
    def log_health_status(self):
        """Log current health status"""
        health = self.get_health_status()
        
        if health['status'] == 'healthy':
            logger.info(f"System healthy - Memory: {health['memory']['percent']}%, "
                       f"CPU: {health['cpu']['percent']}%, "
                       f"Disk: {health['disk']['percent']}%")
        elif health['status'] == 'warning':
            logger.warning(f"System warnings: {', '.join(health.get('warnings', []))}")
        
        return health


# Global health monitor instance
health_monitor = SystemHealthMonitor()


def perform_health_check():
    """Perform a comprehensive health check"""
    try:
        health_status = health_monitor.get_health_status()
        return health_status
    except Exception as e:
        logger.error(f"Error performing health check: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


if __name__ == '__main__':
    # Run health check from command line
    import json
    health = perform_health_check()
    print(json.dumps(health, indent=2))
