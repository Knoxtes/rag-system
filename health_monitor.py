"""
Health monitoring and system checks for production deployment
"""

import os
import sys
import time
import psutil
import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from threading import Thread
import requests

health_bp = Blueprint('health', __name__)

class SystemMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.health_checks = {
            'database': False,
            'google_drive': False,
            'rag_system': False,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'cpu_usage': 0.0
        }
        
    def check_system_resources(self):
        """Check system resource usage"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            self.health_checks['memory_usage'] = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.health_checks['disk_usage'] = (disk.used / disk.total) * 100
            
            # CPU usage
            self.health_checks['cpu_usage'] = psutil.cpu_percent(interval=1)
            
            return True
        except Exception as e:
            logging.error(f"System resource check failed: {e}")
            return False
    
    def check_database_connection(self):
        """Check database/ChromaDB connection"""
        try:
            # Import here to avoid circular imports
            from vector_store import get_collection_info
            # Perform a simple database operation
            result = get_collection_info()
            self.health_checks['database'] = True
            return True
        except Exception as e:
            logging.error(f"Database health check failed: {e}")
            self.health_checks['database'] = False
            return False
    
    def check_google_drive_connection(self):
        """Check Google Drive API connectivity"""
        try:
            from auth import authenticate_google_drive
            service = authenticate_google_drive()
            if service:
                self.health_checks['google_drive'] = True
                return True
        except Exception as e:
            logging.error(f"Google Drive health check failed: {e}")
            
        self.health_checks['google_drive'] = False
        return False
    
    def check_rag_system(self):
        """Check RAG system initialization"""
        try:
            # Check if RAG system is properly initialized
            from chat_api import rag_system, multi_collection_rag
            if rag_system and multi_collection_rag:
                self.health_checks['rag_system'] = True
                return True
        except Exception as e:
            logging.error(f"RAG system health check failed: {e}")
            
        self.health_checks['rag_system'] = False
        return False
    
    def run_all_checks(self):
        """Run all health checks"""
        self.check_system_resources()
        self.check_database_connection()
        self.check_google_drive_connection()
        self.check_rag_system()
        return self.health_checks

# Global monitor instance
monitor = SystemMonitor()

@health_bp.route('/health/detailed')
def detailed_health():
    """Detailed health check endpoint"""
    checks = monitor.run_all_checks()
    
    # Calculate uptime
    uptime = datetime.now() - monitor.start_time
    uptime_seconds = int(uptime.total_seconds())
    
    # Determine overall status
    critical_checks = ['database', 'rag_system']
    overall_status = 'healthy'
    
    if not all(checks[check] for check in critical_checks):
        overall_status = 'unhealthy'
    elif checks['memory_usage'] > 90 or checks['disk_usage'] > 90:
        overall_status = 'warning'
    
    return jsonify({
        'status': overall_status,
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': uptime_seconds,
        'checks': {
            'database': {
                'status': 'pass' if checks['database'] else 'fail',
                'description': 'ChromaDB vector database connectivity'
            },
            'google_drive': {
                'status': 'pass' if checks['google_drive'] else 'fail',
                'description': 'Google Drive API connectivity'
            },
            'rag_system': {
                'status': 'pass' if checks['rag_system'] else 'fail',
                'description': 'RAG system initialization'
            },
            'system_resources': {
                'status': 'pass' if checks['memory_usage'] < 90 and checks['disk_usage'] < 90 else 'warn',
                'memory_usage_percent': checks['memory_usage'],
                'disk_usage_percent': checks['disk_usage'],
                'cpu_usage_percent': checks['cpu_usage']
            }
        },
        'version': os.getenv('APP_VERSION', '1.0.0'),
        'environment': os.getenv('FLASK_ENV', 'development')
    })

@health_bp.route('/health/liveness')
def liveness():
    """Simple liveness probe for Kubernetes/Docker"""
    return jsonify({'status': 'alive', 'timestamp': datetime.now().isoformat()})

@health_bp.route('/health/readiness')
def readiness():
    """Readiness probe - check if app can handle requests"""
    checks = monitor.run_all_checks()
    
    if checks['database'] and checks['rag_system']:
        return jsonify({'status': 'ready', 'timestamp': datetime.now().isoformat()})
    else:
        return jsonify({
            'status': 'not_ready',
            'timestamp': datetime.now().isoformat(),
            'issues': [k for k, v in checks.items() if not v and k in ['database', 'rag_system']]
        }), 503

# Background health monitoring
def background_health_monitor():
    """Run health checks in background and log issues"""
    while True:
        try:
            checks = monitor.run_all_checks()
            
            # Log warnings for high resource usage
            if checks['memory_usage'] > 85:
                logging.warning(f"High memory usage: {checks['memory_usage']:.1f}%")
            
            if checks['disk_usage'] > 85:
                logging.warning(f"High disk usage: {checks['disk_usage']:.1f}%")
            
            if checks['cpu_usage'] > 85:
                logging.warning(f"High CPU usage: {checks['cpu_usage']:.1f}%")
            
            # Log critical service failures
            if not checks['database']:
                logging.error("Database connectivity check failed")
            
            if not checks['rag_system']:
                logging.error("RAG system check failed")
            
            time.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            logging.error(f"Background health monitoring error: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

# Start background monitoring
health_monitor_thread = Thread(target=background_health_monitor, daemon=True)
health_monitor_thread.start()