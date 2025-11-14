"""
Admin Routes and Collection Management
Restricted admin interface for system management
"""

from flask import Blueprint, request, jsonify, send_from_directory
from admin_auth import require_admin
from system_stats import system_stats
# from folder_indexer import FolderIndexer  # Temporarily disabled due to numpy compatibility
# from auth import authenticate_google_drive  # Temporarily disabled
import json
import os
import threading
import time
from datetime import datetime
import traceback
from vector_store import VectorStore
from config import INDEXED_FOLDERS_FILE

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Global variables for background tasks
indexing_status = {
    'running': False,
    'progress': 0,
    'message': 'Ready',
    'started_at': None,
    'completed_at': None,
    'error': None,
    'logs': []
}

indexing_lock = threading.Lock()

@admin_bp.route('/dashboard')
def admin_dashboard():
    """Serve the admin dashboard HTML with client-side authentication"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG System Admin Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; }
        .loading-container { display: flex; justify-content: center; align-items: center; height: 100vh; flex-direction: column; }
        .loading { width: 40px; height: 40px; border: 4px solid #334155; border-top: 4px solid #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .auth-error { text-align: center; padding: 40px; color: #ef4444; }
        .auth-button { background: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 16px; margin-top: 20px; }
        .auth-button:hover { background: #2563eb; }
    </style>
</head>
<body>
    <div id="loading-screen" class="loading-container">
        <div class="loading"></div>
        <p>Verifying authentication...</p>
    </div>
    
    <div id="auth-error" class="auth-error" style="display: none;">
        <h2>Authentication Required</h2>
        <p>You need to be authenticated as an admin to access this dashboard.</p>
        <button class="auth-button" onclick="redirectToLogin()">Login with Google</button>
    </div>
    
    <div id="dashboard-content" style="display: none;"></div>

    <script>
        async function checkAuth() {
            const token = localStorage.getItem('authToken');
            if (!token) {
                showAuthError();
                return false;
            }
            
            try {
                const response = await fetch('/auth/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: token })
                });
                
                const data = await response.json();
                if (data.valid && data.user.is_admin) {
                    await loadDashboard();
                    return true;
                } else {
                    showAuthError();
                    return false;
                }
            } catch (error) {
                console.error('Auth check error:', error);
                showAuthError();
                return false;
            }
        }
        
        function showAuthError() {
            document.getElementById('loading-screen').style.display = 'none';
            document.getElementById('auth-error').style.display = 'block';
        }
        
        function redirectToLogin() {
            fetch('/auth/login')
                .then(response => response.json())
                .then(data => {
                    if (data.auth_url) window.location.href = data.auth_url;
                });
        }
        
        async function loadDashboard() {
            const token = localStorage.getItem('authToken');
            
            try {
                const response = await fetch('/admin/dashboard-content', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                if (response.ok) {
                    const html = await response.text();
                    document.getElementById('loading-screen').style.display = 'none';
                    document.getElementById('dashboard-content').innerHTML = html;
                    document.getElementById('dashboard-content').style.display = 'block';
                } else {
                    showAuthError();
                }
            } catch (error) {
                console.error('Dashboard load error:', error);
                showAuthError();
            }
        }
        
        document.addEventListener('DOMContentLoaded', checkAuth);
    </script>
</body>
</html>
    """

@admin_bp.route('/dashboard-content')
@require_admin
def admin_dashboard_content():
    """Return the dashboard content HTML for authenticated users"""
    return """
    <style>
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 30px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3); }
        .header h1 { font-size: 2.5rem; font-weight: 700; color: #f8fafc; margin-bottom: 10px; }
        .header p { color: #94a3b8; font-size: 1.1rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 25px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); }
        .stat-card h3 { color: #3b82f6; font-size: 1.2rem; margin-bottom: 15px; }
        .stat-item { display: flex; justify-content: space-between; margin-bottom: 10px; padding: 8px 0; border-bottom: 1px solid #334155; }
        .stat-item:last-child { border-bottom: none; }
        .stat-label { color: #94a3b8; }
        .stat-value { color: #f8fafc; font-weight: 600; }
        .btn { background: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 16px; margin: 5px; }
        .btn:hover { background: #2563eb; }
        .btn.success { background: #10b981; }
        .btn.success:hover { background: #059669; }
        .actions-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .action-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 25px; text-align: center; }
        .action-card h3 { color: #10b981; margin-bottom: 15px; }
        .action-card p { color: #94a3b8; margin-bottom: 20px; }
    </style>
    
    <div class="container">
        <div class="header">
            <h1>🛠️ RAG System Admin Dashboard</h1>
            <p>System Administration & Collection Management</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>🖥️ System Health</h3>
                <div class="stat-item">
                    <span class="stat-label">CPU Usage</span>
                    <span id="cpu-usage" class="stat-value">Loading...</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Memory Usage</span>
                    <span id="memory-usage" class="stat-value">Loading...</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Disk Usage</span>
                    <span id="disk-usage" class="stat-value">Loading...</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Uptime</span>
                    <span id="uptime" class="stat-value">Loading...</span>
                </div>
            </div>
            
            <div class="stat-card">
                <h3>📚 Collections</h3>
                <div class="stat-item">
                    <span class="stat-label">Total Collections</span>
                    <span id="total-collections" class="stat-value">Loading...</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Total Documents</span>
                    <span id="total-documents" class="stat-value">Loading...</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Last Updated</span>
                    <span id="last-updated" class="stat-value">Loading...</span>
                </div>
            </div>
            
            <div class="stat-card">
                <h3>🚀 Application</h3>
                <div class="stat-item">
                    <span class="stat-label">Server Status</span>
                    <span class="stat-value">🟢 Online</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">API Version</span>
                    <span class="stat-value">v1.0</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Environment</span>
                    <span class="stat-value">Development</span>
                </div>
            </div>
        </div>
        
        <div class="actions-grid">
            <div class="action-card">
                <h3>🔄 Update Collections</h3>
                <p>Scan and index new documents from 7MM Resources shared drive</p>
                <button class="btn success" onclick="updateCollections()">Update Collections</button>
                <div id="update-status" style="margin-top: 10px;"></div>
            </div>
            
            <div class="action-card">
                <h3>🧹 System Maintenance</h3>
                <p>Clear caches and optimize system performance</p>
                <button class="btn" onclick="clearCache()">Clear Cache</button>
            </div>
            
            <div class="action-card">
                <h3>📊 System Info</h3>
                <p>View system logs and export data</p>
                <button class="btn" onclick="refreshStats()">Refresh Stats</button>
            </div>
        </div>
    </div>
    
    <script>
        let refreshInterval;
        
        async function refreshStats() {
            const token = localStorage.getItem('authToken');
            try {
                const response = await fetch('/admin/stats/system', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    updateStatsDisplay(data);
                }
            } catch (error) {
                console.error('Stats refresh error:', error);
            }
        }
        
        function updateStatsDisplay(stats) {
            if (stats.health) {
                document.getElementById('cpu-usage').textContent = stats.health.cpu_percent + '%';
                document.getElementById('memory-usage').textContent = stats.health.memory_percent + '%';
                document.getElementById('disk-usage').textContent = stats.health.disk_percent + '%';
                document.getElementById('uptime').textContent = stats.health.uptime;
            }
            
            if (stats.collections) {
                document.getElementById('total-collections').textContent = stats.collections.total_collections;
                document.getElementById('total-documents').textContent = stats.collections.total_documents;
                document.getElementById('last-updated').textContent = stats.collections.last_updated || 'Never';
            }
        }
        
        async function updateCollections() {
            const token = localStorage.getItem('authToken');
            const updateButton = document.querySelector('button[onclick="updateCollections()"]');
            const statusDiv = document.getElementById('update-status');
            
            try {
                updateButton.disabled = true;
                updateButton.textContent = 'Updating...';
                statusDiv.innerHTML = '<div style="color: #3b82f6;">Starting collection update...</div>';
                
                const response = await fetch('/admin/collections/update', { 
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                if (response.ok) {
                    statusDiv.innerHTML = '<div style="color: #10b981;">Collection update started successfully!</div>';
                } else {
                    statusDiv.innerHTML = `<div style="color: #ef4444;">Update failed: ${data.error}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div style="color: #ef4444;">Error: ${error.message}</div>`;
            } finally {
                updateButton.disabled = false;
                updateButton.textContent = 'Update Collections';
            }
        }
        
        async function clearCache() {
            const token = localStorage.getItem('authToken');
            try {
                const response = await fetch('/admin/system/clear-cache', { 
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                if (response.ok) {
                    alert('Cache cleared successfully!');
                } else {
                    alert('Failed to clear cache: ' + data.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        // Auto-refresh stats every 30 seconds
        refreshInterval = setInterval(refreshStats, 30000);
        
        // Initial load
        refreshStats();
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            if (refreshInterval) clearInterval(refreshInterval);
        });
    </script>
    """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG System Admin Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
            line-height: 1.6;
        }
        
        .loading-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            flex-direction: column;
        }
        
        .loading {
            display: inline-block;
            width: 40px;
            height: 40px;
            border: 4px solid #334155;
            border-top: 4px solid #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .auth-error {
            text-align: center;
            padding: 40px;
            color: #ef4444;
        }
        
        .auth-button {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 20px;
        }
        
        .auth-button:hover {
            background: #2563eb;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #94a3b8;
            font-size: 1.1rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            border-color: #3b82f6;
        }
        
        .stat-card h3 {
            color: #3b82f6;
            font-size: 1.2rem;
            margin-bottom: 15px;
        }
        
        .stat-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #334155;
        }
        
        .stat-item:last-child {
            border-bottom: none;
        }
        
        .stat-label {
            color: #94a3b8;
        }
        
        .stat-value {
            color: #f8fafc;
            font-weight: 600;
        }
        
        .controls {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
        }
        
        .controls h2 {
            color: #f8fafc;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }
        
        .control-row {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .btn {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.2s ease;
            min-width: 150px;
        }
        
        .btn:hover {
            background: #2563eb;
            transform: translateY(-1px);
        }
        
        .btn:disabled {
            background: #64748b;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-danger {
            background: #dc2626;
        }
        
        .btn-danger:hover {
            background: #b91c1c;
        }
        
        .btn-success {
            background: #059669;
        }
        
        .btn-success:hover {
            background: #047857;
        }
        
        .progress-container {
            background: #0f172a;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            border: 1px solid #334155;
        }
        
        .progress-bar {
            background: #334155;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #3b82f6, #1d4ed8);
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .log-container {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            margin-top: 30px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .log-container h3 {
            color: #f8fafc;
            margin-bottom: 15px;
        }
        
        .log-entry {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9rem;
            padding: 5px 0;
            color: #94a3b8;
            border-bottom: 1px solid #1e293b;
        }
        
        .collections-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .collections-table th,
        .collections-table td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #334155;
        }
        
        .collections-table th {
            background: #0f172a;
            color: #3b82f6;
            font-weight: 600;
        }
        
        .collections-table td {
            color: #e2e8f0;
        }
        
        .status-healthy {
            color: #10b981;
        }
        
        .status-error {
            color: #ef4444;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #334155;
            border-radius: 50%;
            border-top-color: #3b82f6;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .hidden {
            display: none;
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }
        
        .alert-success {
            background: #064e3b;
            border: 1px solid #047857;
            color: #6ee7b7;
        }
        
        .alert-error {
            background: #7f1d1d;
            border: 1px solid #dc2626;
            color: #fca5a5;
        }
        
        .alert-info {
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            color: #93c5fd;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 RAG System Admin Dashboard</h1>
            <p>System administration and collection management for ethan.sexton@7mountainsmedia.com</p>
        </div>

        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <h3>📊 System Health</h3>
                <div id="systemStats">Loading...</div>
            </div>
            
            <div class="stat-card">
                <h3>💾 Collections</h3>
                <div id="collectionStats">Loading...</div>
            </div>
            
            <div class="stat-card">
                <h3>🚀 Application</h3>
                <div id="applicationStats">Loading...</div>
            </div>
        </div>

        <div class="controls">
            <h2>🎛️ System Controls</h2>
            
            <div class="control-row">
                <button class="btn" onclick="refreshStats()">🔄 Refresh Stats</button>
                <button class="btn" onclick="checkSystemHealth()">❤️ Health Check</button>
                <button class="btn" onclick="viewLogs()">📝 View Logs</button>
                <button class="btn" onclick="clearCache()">🗑️ Clear Cache</button>
            </div>
            
            <div class="control-row">
                <button class="btn btn-success" onclick="updateCollections()" id="updateBtn">
                    📁 Update Collections
                </button>
                <button class="btn btn-danger" onclick="resetSystem()" id="resetBtn">
                    🔄 Reset System
                </button>
            </div>
            
            <div class="progress-container hidden" id="progressContainer">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                </div>
                <div id="progressText">Ready</div>
            </div>
        </div>

        <div class="controls">
            <h2>📁 Collection Details</h2>
            <div id="collectionsDetail">Loading...</div>
        </div>

        <div class="log-container" id="logContainer">
            <h3>📝 Recent System Logs</h3>
            <div id="logEntries">Loading logs...</div>
        </div>
    </div>

    <script>
        const API_BASE = '/admin';
        let refreshInterval;
        
        // Get auth token from localStorage
        function getAuthToken() {
            return localStorage.getItem('authToken');
        }
        
        // Make authenticated API request
        async function apiRequest(url, options = {}) {
            const token = getAuthToken();
            if (!token) {
                window.location.href = '/auth/login?redirect=' + encodeURIComponent(window.location.pathname);
                return;
            }
            
            const headers = {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                ...options.headers
            };
            
            const response = await fetch(url, {
                ...options,
                headers
            });
            
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login?redirect=' + encodeURIComponent(window.location.pathname);
                return;
            }
            
            return response;
        }
        
        // Format bytes
        function formatBytes(bytes, decimals = 2) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const dm = decimals < 0 ? 0 : decimals;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
        }
        
        // Format percentage
        function formatPercent(value, decimals = 1) {
            return parseFloat(value).toFixed(decimals) + '%';
        }
        
        // Load system stats
        async function loadSystemStats() {
            try {
                const response = await apiRequest(`${API_BASE}/stats/system`);
                const data = await response.json();
                
                document.getElementById('systemStats').innerHTML = `
                    <div class="stat-item">
                        <span class="stat-label">CPU Usage:</span>
                        <span class="stat-value">${formatPercent(data.system.cpu_percent)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Memory Usage:</span>
                        <span class="stat-value">${formatPercent(data.system.memory.percent)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Memory Available:</span>
                        <span class="stat-value">${formatBytes(data.system.memory.available)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Disk Usage:</span>
                        <span class="stat-value">${formatPercent(data.system.disk.percent)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Uptime:</span>
                        <span class="stat-value">${data.process.uptime_formatted}</span>
                    </div>
                `;
            } catch (error) {
                document.getElementById('systemStats').innerHTML = '<div class="alert alert-error">Error loading system stats</div>';
            }
        }
        
        // Load collection stats
        async function loadCollectionStats() {
            try {
                const response = await apiRequest(`${API_BASE}/stats/collections`);
                const data = await response.json();
                
                document.getElementById('collectionStats').innerHTML = `
                    <div class="stat-item">
                        <span class="stat-label">Total Collections:</span>
                        <span class="stat-value">${data.total_collections}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Total Documents:</span>
                        <span class="stat-value">${data.total_documents.toLocaleString()}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Healthy Collections:</span>
                        <span class="stat-value">${data.collections.filter(c => c.status === 'healthy').length}</span>
                    </div>
                `;
                
                // Load detailed collections table
                loadCollectionDetails(data.collections);
                
            } catch (error) {
                document.getElementById('collectionStats').innerHTML = '<div class="alert alert-error">Error loading collection stats</div>';
            }
        }
        
        // Load collection details table
        function loadCollectionDetails(collections) {
            const html = `
                <table class="collections-table">
                    <thead>
                        <tr>
                            <th>Folder Name</th>
                            <th>Location</th>
                            <th>Documents</th>
                            <th>Last Indexed</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${collections.map(collection => `
                            <tr>
                                <td>${collection.folder_name}</td>
                                <td>${collection.location}</td>
                                <td>${(collection.total_documents || 0).toLocaleString()}</td>
                                <td>${collection.indexed_at || 'Unknown'}</td>
                                <td class="status-${collection.status}">${collection.status}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            
            document.getElementById('collectionsDetail').innerHTML = html;
        }
        
        // Load application stats
        async function loadApplicationStats() {
            try {
                const response = await apiRequest(`${API_BASE}/stats/application`);
                const data = await response.json();
                
                document.getElementById('applicationStats').innerHTML = `
                    <div class="stat-item">
                        <span class="stat-label">Environment:</span>
                        <span class="stat-value">${data.environment}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Debug Mode:</span>
                        <span class="stat-value">${data.debug_mode ? 'On' : 'Off'}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Log Level:</span>
                        <span class="stat-value">${data.log_level}</span>
                    </div>
                `;
            } catch (error) {
                document.getElementById('applicationStats').innerHTML = '<div class="alert alert-error">Error loading application stats</div>';
            }
        }
        
        // Load logs
        async function loadLogs() {
            try {
                const response = await apiRequest(`${API_BASE}/stats/logs`);
                const data = await response.json();
                
                document.getElementById('logEntries').innerHTML = data.logs
                    .map(log => `<div class="log-entry">${log}</div>`)
                    .join('');
            } catch (error) {
                document.getElementById('logEntries').innerHTML = '<div class="alert alert-error">Error loading logs</div>';
            }
        }
        
        // Update collections
        async function updateCollections() {
            const updateBtn = document.getElementById('updateBtn');
            const progressContainer = document.getElementById('progressContainer');
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            
            // Disable button and show progress
            updateBtn.disabled = true;
            updateBtn.innerHTML = '🔄 Updating...';
            progressContainer.classList.remove('hidden');
            progressFill.style.width = '10%';
            progressText.textContent = 'Starting collection update...';
            
            try {
                // Start the update process
                const response = await apiRequest(`${API_BASE}/collections/update`, {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    throw new Error('Failed to start collection update');
                }
                
                // Poll for progress
                const pollProgress = async () => {
                    try {
                        const progressResponse = await apiRequest(`${API_BASE}/collections/update/status`);
                        const progressData = await progressResponse.json();
                        
                        progressFill.style.width = progressData.progress + '%';
                        progressText.textContent = progressData.message;
                        
                        if (progressData.running) {
                            setTimeout(pollProgress, 2000); // Check every 2 seconds
                        } else {
                            // Update complete
                            updateBtn.disabled = false;
                            updateBtn.innerHTML = '📁 Update Collections';
                            progressContainer.classList.add('hidden');
                            
                            if (progressData.error) {
                                alert('Update completed with errors: ' + progressData.error);
                            } else {
                                alert('Collections updated successfully!');
                            }
                            
                            // Refresh stats
                            refreshStats();
                        }
                    } catch (error) {
                        console.error('Error polling progress:', error);
                    }
                };
                
                // Start polling
                setTimeout(pollProgress, 1000);
                
            } catch (error) {
                updateBtn.disabled = false;
                updateBtn.innerHTML = '📁 Update Collections';
                progressContainer.classList.add('hidden');
                alert('Error starting collection update: ' + error.message);
            }
        }
        
        // Reset system (placeholder)
        async function resetSystem() {
            if (!confirm('Are you sure you want to reset the system? This will clear caches and restart services.')) {
                return;
            }
            
            try {
                const response = await apiRequest(`${API_BASE}/system/reset`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    alert('System reset successfully!');
                    refreshStats();
                } else {
                    alert('Error resetting system');
                }
            } catch (error) {
                alert('Error resetting system: ' + error.message);
            }
        }
        
        // Clear cache
        async function clearCache() {
            try {
                const response = await apiRequest(`${API_BASE}/system/clear-cache`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    alert('Cache cleared successfully!');
                } else {
                    alert('Error clearing cache');
                }
            } catch (error) {
                alert('Error clearing cache: ' + error.message);
            }
        }
        
        // Check system health
        async function checkSystemHealth() {
            try {
                const response = await apiRequest(`${API_BASE}/health`);
                const data = await response.json();
                
                if (data.status === 'healthy') {
                    alert('✅ System is healthy!');
                } else {
                    alert('⚠️ System health issues detected: ' + data.message);
                }
            } catch (error) {
                alert('Error checking system health: ' + error.message);
            }
        }
        
        // View logs (toggle visibility)
        function viewLogs() {
            const logContainer = document.getElementById('logContainer');
            logContainer.style.display = logContainer.style.display === 'none' ? 'block' : 'none';
            
            if (logContainer.style.display !== 'none') {
                loadLogs();
            }
        }
        
        // Refresh all stats
        function refreshStats() {
            loadSystemStats();
            loadCollectionStats();
            loadApplicationStats();
            loadLogs();
        }
        
        // Initialize dashboard
        function initDashboard() {
            refreshStats();
            
            // Auto-refresh every 30 seconds
            refreshInterval = setInterval(refreshStats, 30000);
        }
        
        // Start dashboard when page loads
        document.addEventListener('DOMContentLoaded', initDashboard);
        
        // Clean up interval when page unloads
        window.addEventListener('beforeunload', () => {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        });
    </script>
</body>
</html>
@admin_bp.route('/stats/system')
@require_admin
def get_system_stats():
    """Get system health statistics"""
    try:
        stats = system_stats.get_system_health()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/stats/collections')
@require_admin
def get_collection_stats():
    """Get collection statistics"""
    try:
        stats = system_stats.get_collection_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/stats/application')
@require_admin
def get_application_stats():
    """Get application statistics"""
    try:
        stats = system_stats.get_application_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/stats/logs')
@require_admin
def get_logs():
    """Get recent log entries"""
    try:
        logs = system_stats.get_recent_logs()
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e), 'logs': []}), 500

@admin_bp.route('/health')
@require_admin
def health_check():
    """Perform comprehensive health check"""
    try:
        system_health = system_stats.get_system_health()
        collection_stats = system_stats.get_collection_stats()
        
        # Determine overall health
        issues = []
        
        # Check system resources
        if system_health['system']['cpu_percent'] > 90:
            issues.append('High CPU usage')
        
        if system_health['system']['memory']['percent'] > 90:
            issues.append('High memory usage')
        
        if system_health['system']['disk']['percent'] > 90:
            issues.append('High disk usage')
        
        # Check collections
        error_collections = [c for c in collection_stats.get('collections', []) if c.get('status') == 'error']
        if error_collections:
            issues.append(f'{len(error_collections)} collection(s) have errors')
        
        if issues:
            return jsonify({
                'status': 'warning',
                'message': '; '.join(issues),
                'details': {
                    'system': system_health,
                    'collections': collection_stats
                }
            })
        else:
            return jsonify({
                'status': 'healthy',
                'message': 'All systems operational',
                'details': {
                    'system': system_health,
                    'collections': collection_stats
                }
            })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@admin_bp.route('/collections/update', methods=['POST'])
@require_admin
def update_collections():
    """Start background collection update process"""
    global indexing_status
    
    with indexing_lock:
        if indexing_status['running']:
            return jsonify({'error': 'Update already in progress'}), 400
        
        # Reset status
        indexing_status.update({
            'running': True,
            'progress': 0,
            'message': 'Starting collection update...',
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'error': None,
            'logs': []
        })
    
    # Start background thread
    thread = threading.Thread(target=_update_collections_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Collection update started'})

@admin_bp.route('/collections/update/status')
@require_admin
def get_update_status():
    """Get status of collection update process"""
    return jsonify(indexing_status)

def _update_collections_background():
    """Background function to update collections - simplified version"""
    global indexing_status
    
    try:
        # Update progress
        indexing_status.update({
            'progress': 10,
            'message': 'Starting collection update...'
        })
        
        # TODO: Temporarily simplified - need to fix numpy compatibility first
        indexing_status.update({
            'progress': 50,
            'message': 'Collection update temporarily disabled due to package compatibility issues.'
        })
        
        time.sleep(2)  # Simulate work
        
        # Complete
        indexing_status.update({
            'running': False,
            'progress': 100,
            'message': 'Collection update feature temporarily disabled. Please fix numpy/spacy compatibility first.',
            'completed_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        indexing_status.update({
            'running': False,
            'progress': 0,
            'message': 'Collection update failed',
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        })
        
        # Log the full traceback
        indexing_status['logs'].append(f"Error: {traceback.format_exc()}")

@admin_bp.route('/system/reset', methods=['POST'])
@require_admin
def reset_system():
    """Reset system caches and restart services"""
    try:
        # Clear any caches here
        # This is a placeholder - implement actual reset logic as needed
        
        return jsonify({'message': 'System reset completed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/system/clear-cache', methods=['POST'])
@require_admin
def clear_cache():
    """Clear system caches"""
    try:
        # Clear any application caches here
        # This is a placeholder - implement actual cache clearing logic
        
        return jsonify({'message': 'Cache cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/collections/<collection_id>/reset', methods=['POST'])
@require_admin
def reset_collection(collection_id):
    """Reset a specific collection"""
    try:
        # Load indexed folders
        if os.path.exists(INDEXED_FOLDERS_FILE):
            with open(INDEXED_FOLDERS_FILE, 'r') as f:
                indexed_folders = json.load(f)
        else:
            return jsonify({'error': 'No indexed folders found'}), 404
        
        # Find the folder
        if collection_id not in indexed_folders:
            return jsonify({'error': 'Collection not found'}), 404
        
        folder_info = indexed_folders[collection_id]
        collection_name = folder_info.get('collection_name', f'folder_{collection_id}')
        
        # Reset the collection
        vector_store = VectorStore(collection_name=collection_name)
        vector_store.collection.delete()  # This will delete all documents
        
        # Remove from indexed folders
        del indexed_folders[collection_id]
        
        # Save updated indexed folders
        with open(INDEXED_FOLDERS_FILE, 'w') as f:
            json.dump(indexed_folders, f, indent=2)
        
        return jsonify({'message': f'Collection {folder_info["name"]} reset successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
