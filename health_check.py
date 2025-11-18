"""
Health check endpoint for monitoring and load balancers
Provides system status, dependency checks, and configuration validation
"""

from flask import Flask, jsonify
import os
import sys
from datetime import datetime
import importlib.util

app = Flask(__name__)


def check_dependency(module_name: str) -> bool:
    """Check if a Python module is available"""
    return importlib.util.find_spec(module_name) is not None


def check_file_exists(filepath: str) -> bool:
    """Check if required file exists"""
    return os.path.exists(filepath)


def check_env_var(var_name: str) -> bool:
    """Check if environment variable is set and not default"""
    value = os.getenv(var_name)
    defaults = ['your_', 'your-']
    return value is not None and not any(default in value.lower() for default in defaults)


@app.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint
    Returns 200 OK if system is running
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'service': 'rag-system'
    }), 200


@app.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check - verifies system is ready to serve requests
    Checks dependencies, configuration, and required files
    """
    checks = {
        'dependencies': {
            'chromadb': check_dependency('chromadb'),
            'google.generativeai': check_dependency('google.generativeai'),
            'sentence_transformers': check_dependency('sentence_transformers'),
            'streamlit': check_dependency('streamlit'),
        },
        'configuration': {
            'google_api_key': check_env_var('GOOGLE_API_KEY'),
            'project_id': check_env_var('PROJECT_ID'),
        },
        'files': {
            'config.py': check_file_exists('config.py'),
            'rag_system.py': check_file_exists('rag_system.py'),
            '.env.example': check_file_exists('.env.example'),
        }
    }
    
    # Determine overall status
    all_deps_ok = all(checks['dependencies'].values())
    all_config_ok = all(checks['configuration'].values())
    all_files_ok = all(checks['files'].values())
    
    is_ready = all_deps_ok and all_files_ok
    status_code = 200 if is_ready else 503
    
    return jsonify({
        'status': 'ready' if is_ready else 'not_ready',
        'timestamp': datetime.now().isoformat(),
        'checks': checks,
        'warnings': [] if all_config_ok else ['Configuration incomplete - check environment variables']
    }), status_code


@app.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness check - verifies the application is alive
    Simple check that returns OK if the process is running
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.now().isoformat(),
        'python_version': sys.version,
        'pid': os.getpid()
    }), 200


@app.route('/health/metrics', methods=['GET'])
def metrics():
    """
    Basic metrics endpoint
    Returns system information and statistics
    """
    import psutil
    
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        # Check vector database if exists
        vector_db_size = 0
        if os.path.exists('chroma_db'):
            for root, dirs, files in os.walk('chroma_db'):
                vector_db_size += sum(os.path.getsize(os.path.join(root, f)) for f in files)
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_mb': memory_info.rss / 1024 / 1024,
                'disk_usage_percent': psutil.disk_usage('/').percent,
            },
            'application': {
                'vector_db_size_mb': vector_db_size / 1024 / 1024,
                'python_version': sys.version,
                'uptime_seconds': (datetime.now() - datetime.fromtimestamp(process.create_time())).total_seconds()
            }
        }), 200
    except ImportError:
        return jsonify({
            'error': 'psutil not installed - install with: pip install psutil'
        }), 500
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Run health check server
    # Note: For production, use a proper WSGI server like gunicorn
    port = int(os.getenv('HEALTH_CHECK_PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
