"""
System Statistics and Health Monitoring
Provides detailed system information for admin dashboard
"""

import psutil
import os
import time
import json
from datetime import datetime, timedelta
from vector_store import VectorStore
from config import INDEXED_FOLDERS_FILE
import traceback

class SystemStats:
    def __init__(self):
        self.start_time = datetime.now()
    
    def get_system_health(self):
        """Get comprehensive system health statistics"""
        try:
            # Basic system info
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Process info
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # Uptime
            uptime = datetime.now() - self.start_time
            
            return {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory': {
                        'total': memory.total,
                        'available': memory.available,
                        'used': memory.used,
                        'percent': memory.percent
                    },
                    'disk': {
                        'total': disk.total,
                        'used': disk.used,
                        'free': disk.free,
                        'percent': (disk.used / disk.total) * 100
                    }
                },
                'process': {
                    'memory_rss': process_memory.rss,
                    'memory_vms': process_memory.vms,
                    'pid': os.getpid(),
                    'uptime_seconds': uptime.total_seconds(),
                    'uptime_formatted': str(uptime).split('.')[0]
                }
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_collection_stats(self):
        """Get statistics for all vector store collections"""
        stats = {
            'collections': [],
            'total_documents': 0,
            'total_collections': 0,
            'indexed_folders': {}
        }
        
        try:
            # Load indexed folders info
            if os.path.exists(INDEXED_FOLDERS_FILE):
                with open(INDEXED_FOLDERS_FILE, 'r') as f:
                    indexed_folders = json.load(f)
                    stats['indexed_folders'] = indexed_folders
            
            # Get collection stats
            for folder_id, folder_info in stats['indexed_folders'].items():
                collection_name = folder_info.get('collection_name', f'folder_{folder_id}')
                
                try:
                    vector_store = VectorStore(collection_name=collection_name)
                    collection_stats = vector_store.get_stats()
                    
                    collection_info = {
                        'collection_name': collection_name,
                        'folder_name': folder_info.get('name', 'Unknown'),
                        'location': folder_info.get('location', 'Unknown'),
                        'indexed_at': folder_info.get('indexed_at', 'Unknown'),
                        'files_processed': folder_info.get('files_processed', 0),
                        'total_documents': collection_stats.get('total_documents', 0),
                        'status': 'healthy'
                    }
                    
                    stats['collections'].append(collection_info)
                    stats['total_documents'] += collection_info['total_documents']
                    
                except Exception as e:
                    stats['collections'].append({
                        'collection_name': collection_name,
                        'folder_name': folder_info.get('name', 'Unknown'),
                        'location': folder_info.get('location', 'Unknown'),
                        'status': 'error',
                        'error': str(e)
                    })
            
            stats['total_collections'] = len(stats['collections'])
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def get_recent_logs(self, lines=50):
        """Get recent log entries"""
        logs = []
        log_file = 'logs/rag_system.log'
        
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    
                    for line in recent_lines:
                        line = line.strip()
                        if line:
                            logs.append(line)
        except Exception as e:
            logs.append(f"Error reading logs: {str(e)}")
        
        return logs
    
    def get_application_stats(self):
        """Get application-specific statistics"""
        return {
            'python_version': os.sys.version,
            'working_directory': os.getcwd(),
            'environment': os.getenv('FLASK_ENV', 'development'),
            'debug_mode': os.getenv('DEBUG', 'False').lower() == 'true',
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'configured_domains': os.getenv('ALLOWED_DOMAINS', '').split(','),
            'cors_origins': os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
        }

# Global instance
system_stats = SystemStats()
