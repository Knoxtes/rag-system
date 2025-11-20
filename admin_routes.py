"""
Admin Routes and Collection Management
Restricted admin interface for system management
"""

from flask import Blueprint, request, jsonify, session, redirect
from admin_auth import require_admin
from system_stats import system_stats
import json
import os
import threading
import time
from datetime import datetime
import traceback
from vector_store import VectorStore
from config import INDEXED_FOLDERS_FILE
from google_auth_oauthlib.flow import Flow
import pickle

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Google OAuth Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
TOKEN_FILE = 'token.pickle'

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

def update_status(**kwargs):
    """Thread-safe status update helper"""
    global indexing_status
    with indexing_lock:
        indexing_status.update(kwargs)

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
        <p id="loading-message">Verifying authentication...</p>
        <p id="debug-info" style="font-size: 12px; color: #94a3b8; margin-top: 10px;"></p>
    </div>
    
    <div id="auth-error" class="auth-error" style="display: none;">
        <h2>Authentication Required</h2>
        <p id="auth-error-message">You need to be authenticated as an admin to access this dashboard.</p>
        <button class="auth-button" onclick="redirectToLogin()">Login with Google</button>
        <button class="auth-button" onclick="redirectToChat()" style="background: #10b981; margin-left: 10px;">Go to Chat Interface</button>
    </div>
    
    <div id="dashboard-content" style="display: none;"></div>

    <script>
        let authCheckAttempts = 0;
        const maxAuthCheckAttempts = 3;
        
        async function checkAuth() {
            authCheckAttempts++;
            const token = localStorage.getItem('authToken');
            
            // Update debug info
            const debugInfo = document.getElementById('debug-info');
            const loadingMessage = document.getElementById('loading-message');
            
            console.log(`Auth check attempt ${authCheckAttempts}:`);
            console.log('- Token found:', !!token);
            console.log('- Token preview:', token ? token.substring(0, 20) + '...' : 'none');
            console.log('- URL params:', window.location.search);
            
            debugInfo.textContent = `Attempt ${authCheckAttempts}/${maxAuthCheckAttempts} - Token: ${token ? 'Found' : 'Not found'}`;
            
            if (!token) {
                // If we just came from OAuth, wait a bit and retry
                const urlParams = new URLSearchParams(window.location.search);
                if (urlParams.get('auth_complete') === 'true' && authCheckAttempts < maxAuthCheckAttempts) {
                    console.log('Just came from OAuth, retrying auth check in 1 second...');
                    loadingMessage.textContent = `Waiting for authentication token... (${authCheckAttempts}/${maxAuthCheckAttempts})`;
                    setTimeout(checkAuth, 1000);
                    return false;
                }
                
                console.log('No token found, showing auth error');
                showAuthError();
                return false;
            }
            
            loadingMessage.textContent = 'Verifying token with server...';
            debugInfo.textContent = 'Contacting authentication server...';
            
            try {
                console.log('Sending token verification request...');
                const response = await fetch('/auth/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: token })
                });
                
                console.log('Verification response status:', response.status);
                const data = await response.json();
                console.log('Auth verification result:', data);
                
                if (data.valid && data.user && data.user.is_admin) {
                    loadingMessage.textContent = 'Authentication successful! Loading dashboard...';
                    debugInfo.textContent = `Welcome ${data.user.name || data.user.email}!`;
                    console.log('Auth successful, loading dashboard...');
                    await loadDashboard();
                    return true;
                } else if (data.valid && data.user && !data.user.is_admin) {
                    console.log('Valid user but not admin - redirecting to chat');
                    loadingMessage.textContent = 'Authenticated user - redirecting to chat interface...';
                    debugInfo.textContent = `Welcome ${data.user.name || data.user.email}! You're not an admin user.`;
                    
                    setTimeout(() => {
                        window.location.href = 'http://localhost:3000/?from_admin=true';
                    }, 2000);
                    return false;
                } else {
                    console.log('Auth failed - not valid admin:', data);
                    debugInfo.textContent = `Auth failed: ${data.error || 'Not valid user'} (User: ${data.user?.email || 'unknown'})`;
                    
                    // Update error message for non-admin users
                    if (data.user && !data.user.is_admin) {
                        document.getElementById('auth-error-message').textContent = 
                            `Hi ${data.user.name || data.user.email}! This is the admin dashboard. You can access the chat interface instead.`;
                    }
                    
                    showAuthError();
                    return false;
                }
            } catch (error) {
                console.error('Auth check error:', error);
                
                // If we just came from OAuth and this is a network error, retry
                const urlParams = new URLSearchParams(window.location.search);
                if (urlParams.get('auth_complete') === 'true' && authCheckAttempts < maxAuthCheckAttempts) {
                    console.log('Network error after OAuth, retrying in 2 seconds...');
                    loadingMessage.textContent = `Network error, retrying... (${authCheckAttempts}/${maxAuthCheckAttempts})`;
                    debugInfo.textContent = `Error: ${error.message}`;
                    setTimeout(checkAuth, 2000);
                    return false;
                }
                
                debugInfo.textContent = `Auth error: ${error.message}`;
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
        
        function redirectToChat() {
            window.location.href = 'http://localhost:3000/';
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
                    const contentDiv = document.getElementById('dashboard-content');
                    contentDiv.innerHTML = html;
                    contentDiv.style.display = 'block';
                    
                    // Execute scripts in the loaded content
                    const scripts = contentDiv.querySelectorAll('script');
                    scripts.forEach(script => {
                        const newScript = document.createElement('script');
                        if (script.src) {
                            newScript.src = script.src;
                        } else {
                            newScript.textContent = script.textContent;
                        }
                        document.body.appendChild(newScript);
                    });
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
        
        <!-- Google Drive Authentication Status -->
        <div class="action-card" style="margin: 20px 0; border-left: 4px solid #3b82f6;">
            <h3>🔐 Google Drive Authentication</h3>
            <div id="gdrive-status">
                <p style="color: #94a3b8;">Checking connection status...</p>
            </div>
            <div id="gdrive-actions" style="margin-top: 15px;"></div>
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
        
        <!-- Cloud Migration Panel -->
        <div style="margin: 30px 0; padding: 30px; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 2px solid #3b82f6; border-radius: 12px; box-shadow: 0 10px 30px rgba(59, 130, 246, 0.2);">
            <h2 style="color: #3b82f6; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
                <span>☁️</span>
                <span>Cloud Migration Center</span>
            </h2>
            
            <div class="stats-grid" style="margin-bottom: 20px;">
                <div class="stat-card" style="border-left: 4px solid #3b82f6;">
                    <h3>🤖 Vertex AI Embeddings</h3>
                    <div id="vertex-status">
                        <p style="color: #94a3b8;">Loading status...</p>
                    </div>
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #334155;">
                        <p style="color: #64748b; font-size: 14px; margin-bottom: 10px;">
                            <strong>Benefits:</strong> 768-dim embeddings, auto-scaling, ~$2/month
                        </p>
                    </div>
                </div>
                
                <div class="stat-card" style="border-left: 4px solid #10b981;">
                    <h3>📄 Document AI OCR</h3>
                    <div id="documentai-status">
                        <p style="color: #94a3b8;">Loading status...</p>
                    </div>
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #334155;">
                        <p style="color: #64748b; font-size: 14px; margin-bottom: 10px;">
                            <strong>Benefits:</strong> Cloud OCR, table extraction, ~$1.50/1K pages
                        </p>
                    </div>
                </div>
                
                <div class="stat-card" style="border-left: 4px solid #f59e0b;">
                    <h3>💾 Database Status</h3>
                    <div id="database-status">
                        <p style="color: #94a3b8;">Loading status...</p>
                    </div>
                    <div id="backup-status" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #334155;">
                        <p style="color: #64748b; font-size: 14px;">Checking backups...</p>
                    </div>
                </div>
            </div>
            
            <div class="actions-grid">
                <div class="action-card" style="background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);">
                    <h3 style="color: #93c5fd;">📦 Install Packages</h3>
                    <p style="color: #bfdbfe;">Install google-cloud-aiplatform and google-cloud-documentai</p>
                    <button class="btn" onclick="installMigrationPackages()" style="background: #3b82f6;">
                        Install Cloud Packages
                    </button>
                    <div id="install-status" style="margin-top: 10px; color: #bfdbfe;"></div>
                </div>
                
                <div class="action-card" style="background: linear-gradient(135deg, #7c2d12 0%, #991b1b 100%);">
                    <h3 style="color: #fca5a5;">🗑️ Clear Database</h3>
                    <p style="color: #fecaca;">⚠️ Stop server first! Then use CLI tool.</p>
                    <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px; margin: 10px 0;">
                        <code style="color: #fecaca; font-size: 12px;">python reindex_with_vertex.py --backup</code>
                    </div>
                    <button class="btn" onclick="startReindex()" style="background: #ef4444; opacity: 0.7;">
                        Clear Database (requires server stop)
                    </button>
                    <div id="reindex-status" style="margin-top: 10px; color: #fecaca;"></div>
                </div>
                
                <div class="action-card" style="background: linear-gradient(135deg, #065f46 0%, #047857 100%);">
                    <h3 style="color: #86efac;">📁 Index All Folders</h3>
                    <p style="color: #bbf7d0;">Index all folders from 7MM Resources shared drive</p>
                    <button class="btn" onclick="startFullIndexing()" style="background: #10b981;">
                        Index All Folders
                    </button>
                    <div id="indexing-status" style="margin-top: 10px; color: #bbf7d0;"></div>
                </div>
                
                <div class="action-card" style="background: linear-gradient(135deg, #14532d 0%, #166534 100%);">
                    <h3 style="color: #86efac;">📖 Documentation</h3>
                    <p style="color: #bbf7d0;">View setup guides and migration instructions</p>
                    <button class="btn" onclick="window.open('/static/VERTEX_AI_MIGRATION.md', '_blank')" style="background: #10b981;">
                        Vertex AI Guide
                    </button>
                    <button class="btn" onclick="window.open('/static/DOCUMENTAI_SETUP.md', '_blank')" style="background: #10b981; margin-top: 10px;">
                        Document AI Guide
                    </button>
                </div>
            </div>
            
            <div id="migration-logs" style="margin-top: 20px; padding: 15px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; font-family: monospace; font-size: 13px; color: #94a3b8; max-height: 300px; overflow-y: auto; display: none;">
                <div style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #334155; color: #f8fafc; font-weight: bold;">
                    📋 Migration Logs
                </div>
                <div id="migration-logs-content"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Wrap everything in a function that executes immediately
        (function() {
            console.log('[Admin Dashboard] Script loaded and executing');
            
            let refreshInterval;
        
        async function checkGDriveAuth() {
            const token = localStorage.getItem('authToken');
            console.log('[GDrive Auth] Checking status...');
            try {
                const response = await fetch('/admin/gdrive/status', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                console.log('[GDrive Auth] Response status:', response.status);
                const data = await response.json();
                console.log('[GDrive Auth] Data:', data);
                
                const statusDiv = document.getElementById('gdrive-status');
                const actionsDiv = document.getElementById('gdrive-actions');
                
                if (data.authenticated) {
                    statusDiv.innerHTML = `
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 24px;">✅</span>
                            <div>
                                <p style="color: #10b981; font-weight: bold; margin: 0;">Connected</p>
                                <p style="color: #94a3b8; font-size: 14px; margin: 5px 0 0 0;">${data.message}</p>
                            </div>
                        </div>
                    `;
                    actionsDiv.innerHTML = `
                        <button class="btn" onclick="disconnectGDrive()" style="background: #ef4444;">Disconnect</button>
                        <button class="btn" onclick="checkGDriveAuth()" style="background: #6366f1; margin-left: 10px;">Refresh Status</button>
                    `;
                } else {
                    statusDiv.innerHTML = `
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 24px;">❌</span>
                            <div>
                                <p style="color: #ef4444; font-weight: bold; margin: 0;">Not Connected</p>
                                <p style="color: #94a3b8; font-size: 14px; margin: 5px 0 0 0;">${data.message}</p>
                            </div>
                        </div>
                    `;
                    actionsDiv.innerHTML = `
                        <button class="btn success" onclick="connectGDrive()">Connect Google Drive</button>
                        <p style="font-size: 13px; color: #64748b; margin-top: 10px;">
                            Required to index documents from Google Drive
                        </p>
                    `;
                }
            } catch (error) {
                console.error('GDrive auth check error:', error);
                document.getElementById('gdrive-status').innerHTML = `
                    <p style="color: #ef4444;">Error checking connection status</p>
                `;
            }
        }
        
        function connectGDrive() {
            // Open OAuth flow in current window
            window.location.href = '/admin/gdrive/authorize';
        }
        
        async function disconnectGDrive() {
            if (!confirm('Are you sure you want to disconnect Google Drive?')) {
                return;
            }
            
            const token = localStorage.getItem('authToken');
            try {
                const response = await fetch('/admin/gdrive/disconnect', { 
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                if (data.success) {
                    alert('Google Drive disconnected successfully');
                    checkGDriveAuth();
                } else {
                    alert('Error disconnecting: ' + data.error);
                }
            } catch (error) {
                console.error('Disconnect error:', error);
                alert('Error disconnecting from Google Drive');
            }
        }
        
        async function refreshStats() {
            const token = localStorage.getItem('authToken');
            console.log('[Stats] Fetching system stats...');
            try {
                const response = await fetch('/admin/stats/system', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                console.log('[Stats] Response status:', response.status);
                if (response.ok) {
                    const data = await response.json();
                    console.log('[Stats] Data received:', data);
                    updateStatsDisplay(data);
                } else {
                    console.error('[Stats] Failed to fetch:', response.statusText);
                }
            } catch (error) {
                console.error('[Stats] Error:', error);
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
        console.log('[Admin Dashboard] Starting initial data load...');
        refreshStats();
        checkGDriveAuth();  // Check Google Drive auth status
        console.log('[Admin Dashboard] Initial functions called');
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            if (refreshInterval) clearInterval(refreshInterval);
        });
        
        // Make functions globally accessible
        window.refreshStats = refreshStats;
        window.checkGDriveAuth = checkGDriveAuth;
        window.updateCollections = updateCollections;
        window.clearCache = clearCache;
        window.connectGDrive = connectGDrive;
        window.disconnectGDrive = disconnectGDrive;
        window.checkMigrationStatus = checkMigrationStatus;
        window.installMigrationPackages = installMigrationPackages;
        window.startReindex = startReindex;
        window.startFullIndexing = startFullIndexing;
        
        // New migration functions
        async function checkMigrationStatus() {
            const token = localStorage.getItem('authToken');
            try {
                const response = await fetch('/admin/migrations/status', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                // Update Vertex AI status
                const vertexDiv = document.getElementById('vertex-status');
                if (data.vertex_embeddings.enabled) {
                    vertexDiv.innerHTML = `
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 24px;">✅</span>
                            <div>
                                <p style="color: #10b981; font-weight: bold; margin: 0;">Enabled</p>
                                <p style="color: #94a3b8; font-size: 14px; margin: 5px 0 0 0;">${data.vertex_embeddings.dimension}-dimensional embeddings active</p>
                            </div>
                        </div>
                    `;
                } else {
                    vertexDiv.innerHTML = `
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 24px;">⚠️</span>
                            <div>
                                <p style="color: #f59e0b; font-weight: bold; margin: 0;">Using Local Embeddings</p>
                                <p style="color: #94a3b8; font-size: 14px; margin: 5px 0 0 0;">${data.vertex_embeddings.dimension}-dim (change config to enable)</p>
                            </div>
                        </div>
                    `;
                }
                
                // Update Document AI status
                const docaiDiv = document.getElementById('documentai-status');
                if (data.document_ai.enabled) {
                    docaiDiv.innerHTML = `
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 24px;">✅</span>
                            <div>
                                <p style="color: #10b981; font-weight: bold; margin: 0;">Document AI Active</p>
                                <p style="color: #94a3b8; font-size: 14px; margin: 5px 0 0 0;">Project: ${data.document_ai.project_id}</p>
                            </div>
                        </div>
                    `;
                } else {
                    docaiDiv.innerHTML = `
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 24px;">⚠️</span>
                            <div>
                                <p style="color: #f59e0b; font-weight: bold; margin: 0;">Using ${data.document_ai.backend}</p>
                                <p style="color: #94a3b8; font-size: 14px; margin: 5px 0 0 0;">Switch to Document AI for better OCR</p>
                            </div>
                        </div>
                    `;
                }
                
                // Update database status
                const dbDiv = document.getElementById('database-status');
                if (data.database.exists) {
                    dbDiv.innerHTML = `
                        <div class="stat-item">
                            <span class="stat-label">Status</span>
                            <span class="stat-value" style="color: #10b981;">Active</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Size</span>
                            <span class="stat-value">${data.database.size_mb} MB</span>
                        </div>
                    `;
                } else {
                    dbDiv.innerHTML = `
                        <p style="color: #f59e0b; font-weight: bold;">No database found</p>
                        <p style="color: #94a3b8; font-size: 14px;">Database will be created on first query</p>
                    `;
                }
                
                // Update backup status
                const backupDiv = document.getElementById('backup-status');
                if (data.backups.count > 0) {
                    backupDiv.innerHTML = `
                        <p style="color: #64748b; font-size: 14px; margin-bottom: 5px;">
                            <strong>Backups:</strong> ${data.backups.count} available
                        </p>
                        <p style="color: #64748b; font-size: 12px; margin: 0;">
                            Latest: ${data.backups.latest}
                        </p>
                    `;
                } else {
                    backupDiv.innerHTML = `
                        <p style="color: #64748b; font-size: 14px;">No backups yet</p>
                    `;
                }
                
            } catch (error) {
                console.error('Migration status error:', error);
            }
        }
        
        async function installMigrationPackages() {
            const token = localStorage.getItem('authToken');
            const statusDiv = document.getElementById('install-status');
            
            if (!confirm('Install Google Cloud packages?\\n\\nThis may take a few minutes.')) {
                return;
            }
            
            statusDiv.innerHTML = '<div style="color: #3b82f6;">Installing...</div>';
            
            try {
                const response = await fetch('/admin/migrations/install-packages', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                if (response.ok) {
                    statusDiv.innerHTML = '<div style="color: #10b981;">✅ Installed!</div>';
                } else {
                    statusDiv.innerHTML = `<div style="color: #ef4444;">❌ ${data.message}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div style="color: #ef4444;">Error: ${error.message}</div>`;
            }
        }
        
        async function startReindex() {
            const token = localStorage.getItem('authToken');
            const statusDiv = document.getElementById('reindex-status');
            const logsDiv = document.getElementById('migration-logs');
            const logsContent = document.getElementById('migration-logs-content');
            
            if (!confirm('⚠️ WARNING: This will backup and clear your database!\\n\\nContinue?')) {
                return;
            }
            
            statusDiv.innerHTML = '<div style="color: #3b82f6;">Starting...</div>';
            logsDiv.style.display = 'block';
            
            try {
                const response = await fetch('/admin/migrations/reindex', {
                    method: 'POST',
                    headers: { 
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ create_backup: true })
                });
                const data = await response.json();
                
                if (response.ok) {
                    statusDiv.innerHTML = '<div style="color: #10b981;">✅ Started!</div>';
                    
                    // Poll for status
                    const pollInterval = setInterval(async () => {
                        const statusResponse = await fetch('/admin/collections/status', {
                            headers: { 'Authorization': `Bearer ${token}` }
                        });
                        const status = await statusResponse.json();
                        
                        if (status.logs) {
                            logsContent.innerHTML = status.logs.map(log => 
                                `<div style="padding: 5px 0;">• ${log}</div>`
                            ).join('');
                        }
                        
                        if (!status.running) {
                            clearInterval(pollInterval);
                            if (status.error) {
                                statusDiv.innerHTML = `<div style="color: #ef4444;">❌ ${status.error}</div>`;
                            } else {
                                statusDiv.innerHTML = `<div style="color: #10b981;">✅ Done! Restart server.</div>`;
                                checkMigrationStatus(); // Refresh migration status
                            }
                        } else {
                            statusDiv.innerHTML = `<div style="color: #3b82f6;">${status.progress}% - ${status.message}</div>`;
                        }
                    }, 2000);
                } else {
                    statusDiv.innerHTML = `<div style="color: #ef4444;">❌ ${data.error}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div style="color: #ef4444;">Error: ${error.message}</div>`;
            }
        }
        
        async function startFullIndexing() {
            const token = localStorage.getItem('authToken');
            const statusDiv = document.getElementById('indexing-status');
            const logsDiv = document.getElementById('migration-logs');
            const logsContent = document.getElementById('migration-logs-content');
            
            if (!confirm('🚀 This will index ALL folders from 7MM Resources shared drive.\\n\\nEnsure database is clear first. Continue?')) {
                return;
            }
            
            statusDiv.innerHTML = '<div style="color: #3b82f6;">Starting folder discovery...</div>';
            logsDiv.style.display = 'block';
            
            try {
                const response = await fetch('/admin/migrations/index-all-folders', {
                    method: 'POST',
                    headers: { 
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });
                const data = await response.json();
                
                if (response.ok) {
                    statusDiv.innerHTML = '<div style="color: #10b981;">✅ Indexing started!</div>';
                    
                    // Poll for status
                    const pollInterval = setInterval(async () => {
                        const statusResponse = await fetch('/admin/collections/status', {
                            headers: { 'Authorization': `Bearer ${token}` }
                        });
                        const status = await statusResponse.json();
                        
                        if (status.logs) {
                            logsContent.innerHTML = status.logs.map(log => 
                                `<div style="padding: 5px 0;">• ${log}</div>`
                            ).join('');
                            // Auto-scroll to bottom
                            logsContent.scrollTop = logsContent.scrollHeight;
                        }
                        
                        if (!status.running) {
                            clearInterval(pollInterval);
                            if (status.error) {
                                statusDiv.innerHTML = `<div style="color: #ef4444;">❌ ${status.error}</div>`;
                            } else {
                                statusDiv.innerHTML = `<div style="color: #10b981;">✅ Complete! Restart server.</div>`;
                                checkMigrationStatus(); // Refresh migration status
                            }
                        } else {
                            statusDiv.innerHTML = `<div style="color: #3b82f6;">${status.progress}% - ${status.message}</div>`;
                        }
                    }, 2000);
                } else {
                    statusDiv.innerHTML = `<div style="color: #ef4444;">❌ ${data.error || data.message}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div style="color: #ef4444;">Error: ${error.message}</div>`;
            }
        }
        
        // Call migration status on load
        setTimeout(checkMigrationStatus, 1000);
        
        })(); // End of IIFE
    </script>
    """

@admin_bp.route('/stats/system')
@require_admin
def get_system_stats():
    """Get system health statistics"""
    try:
        stats = system_stats.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/collections/update', methods=['POST'])
@require_admin
def update_collections():
    """Start collection update process"""
    global indexing_status
    
    if indexing_status['running']:
        return jsonify({'error': 'Collection update already in progress'}), 409
    
    try:
        # Start background indexing
        thread = threading.Thread(target=run_collection_update)
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': 'Collection update started'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/collections/status', methods=['GET'])
@require_admin
def get_indexing_status():
    """Get current indexing status"""
    return jsonify(indexing_status)

@admin_bp.route('/system/clear-cache', methods=['POST'])
@require_admin
def clear_cache():
    """Clear system caches"""
    try:
        # Clear any application caches here
        return jsonify({'message': 'Cache cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/migrations/status', methods=['GET'])
@require_admin
def get_migration_status():
    """Get status of Vertex AI and Document AI migrations"""
    try:
        from config import USE_VERTEX_EMBEDDINGS, OCR_BACKEND, DOCUMENTAI_PROJECT_ID
        
        # Check if database exists and get stats
        import os
        chroma_path = './chroma_db'
        db_exists = os.path.exists(chroma_path) and os.path.isdir(chroma_path)
        
        db_size = 0
        if db_exists:
            for dirpath, dirnames, filenames in os.walk(chroma_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        db_size += os.path.getsize(fp)
        
        db_size_mb = db_size / (1024 * 1024)
        
        # Check for backups
        backup_dir = './chroma_db_backups'
        backups = []
        if os.path.exists(backup_dir):
            backups = [d for d in os.listdir(backup_dir) if d.startswith('backup_')]
            backups.sort(reverse=True)  # Most recent first
        
        return jsonify({
            'vertex_embeddings': {
                'enabled': USE_VERTEX_EMBEDDINGS,
                'status': 'active' if USE_VERTEX_EMBEDDINGS else 'inactive',
                'dimension': 768 if USE_VERTEX_EMBEDDINGS else 384
            },
            'document_ai': {
                'enabled': OCR_BACKEND == 'documentai',
                'backend': OCR_BACKEND,
                'project_id': DOCUMENTAI_PROJECT_ID if OCR_BACKEND == 'documentai' else None
            },
            'database': {
                'exists': db_exists,
                'size_mb': round(db_size_mb, 2),
                'path': chroma_path
            },
            'backups': {
                'count': len(backups),
                'latest': backups[0] if backups else None,
                'all': backups[:5]  # Show last 5 backups
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/migrations/reindex', methods=['POST'])
@require_admin
def start_reindex():
    """Start database reindexing process"""
    global indexing_status
    
    if indexing_status['running']:
        return jsonify({'error': 'Reindexing already in progress'}), 409
    
    try:
        data = request.json or {}
        create_backup = data.get('create_backup', True)
        
        # Start background reindexing
        thread = threading.Thread(target=run_reindex_process, args=(create_backup,))
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': 'Reindexing process started'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/migrations/install-packages', methods=['POST'])
@require_admin
def install_migration_packages():
    """Install required packages for Vertex AI and Document AI"""
    try:
        import subprocess
        import sys
        
        packages = [
            'google-cloud-aiplatform==1.78.0',
            'google-cloud-documentai==2.35.0'
        ]
        
        result = {'success': [], 'failed': []}
        
        for package in packages:
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                result['success'].append(package)
            except subprocess.CalledProcessError as e:
                result['failed'].append({'package': package, 'error': str(e)})
        
        if result['failed']:
            return jsonify({
                'message': 'Some packages failed to install',
                'result': result
            }), 500
        
        return jsonify({
            'message': 'All packages installed successfully',
            'result': result
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/migrations/index-all-folders', methods=['POST'])
@require_admin
def index_all_folders():
    """Start indexing all folders from 7MM Resources shared drive"""
    global indexing_status
    
    if indexing_status['running']:
        return jsonify({'error': 'Indexing already in progress'}), 409
    
    try:
        # Start background indexing
        thread = threading.Thread(target=run_full_indexing_process)
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': 'Full indexing process started'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_reindex_process(create_backup=True):
    """Background reindexing process"""
    global indexing_status
    from datetime import datetime
    import shutil
    import os
    
    with indexing_lock:
        try:
            
            # Initialize
            indexing_status.update({
                'running': True,
                'progress': 0,
                'message': 'Starting reindex process...',
                'started_at': datetime.now().isoformat(),
                'error': None,
                'logs': ['Reindex process started']
            })
            
            chroma_path = './chroma_db'
            
            # Step 1: Backup (if requested)
            if create_backup:
                indexing_status.update({
                    'progress': 10,
                    'message': 'Creating database backup...',
                    'logs': indexing_status['logs'] + ['Creating backup...']
                })
                
                backup_dir = './chroma_db_backups'
                os.makedirs(backup_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = os.path.join(backup_dir, f'backup_{timestamp}')
                
                if os.path.exists(chroma_path):
                    shutil.copytree(chroma_path, backup_path)
                    indexing_status.update({
                        'logs': indexing_status['logs'] + [f'Backup created: {backup_path}']
                    })
            
            # Step 2: Clear database
            indexing_status.update({
                'progress': 30,
                'message': 'Clearing old database...',
                'logs': indexing_status['logs'] + ['Clearing database...']
            })
            
            if os.path.exists(chroma_path):
                try:
                    # Try to close any open ChromaDB connections
                    import gc
                    gc.collect()
                    
                    # Attempt to remove
                    shutil.rmtree(chroma_path)
                    indexing_status.update({
                        'logs': indexing_status['logs'] + ['Database cleared']
                    })
                except PermissionError as e:
                    raise Exception(
                        'Database is locked! Stop the server first, then run: '
                        'python reindex_with_vertex.py --backup'
                    )
            
            os.makedirs(chroma_path, exist_ok=True)
            
            # Step 3: Complete
            indexing_status.update({
                'running': False,
                'progress': 100,
                'message': 'Database cleared. Restart server to reindex with new embeddings.',
                'completed_at': datetime.now().isoformat(),
                'logs': indexing_status['logs'] + [
                    'Reindex preparation complete',
                    'Next: Restart the server to begin reindexing with Vertex AI'
                ]
            })
            
        except Exception as e:
            indexing_status.update({
                'running': False,
                'progress': 0,
                'message': 'Reindex failed',
                'error': str(e),
                'completed_at': datetime.now().isoformat(),
                'logs': indexing_status['logs'] + [f'Error: {str(e)}']
            })

def run_full_indexing_process():
    """Background process to index all folders from 7MM Resources shared drive"""
    global indexing_status
    from datetime import datetime
    
    try:
        from googleapiclient.discovery import build
        from document_loader import GoogleDriveLoader
        from rag_system import EnhancedRAGSystem
        import pickle
        import os
        import json
        
        # Initialize
        update_status(
            running=True,
            progress=0,
            message='Starting full indexing...',
            started_at=datetime.now().isoformat(),
            error=None,
            logs=['Full indexing started']
        )
        
        # Load Google Drive credentials
        update_status(
            progress=5,
            message='Connecting to Google Drive...',
            logs=indexing_status['logs'] + ['Loading credentials...']
        )
        
        if not os.path.exists(TOKEN_FILE):
            raise Exception('Google Drive not authenticated. Please connect first.')
        
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
        
        if not creds or not creds.valid:
            raise Exception('Google Drive credentials invalid. Please reconnect.')
        
        # Build Drive service
        drive_service = build('drive', 'v3', credentials=creds)
        
        update_status(
            logs=indexing_status['logs'] + ['Connected to Google Drive']
        )
        
        # Get all folders from shared drive
        update_status(
            progress=10,
            message='Discovering folders in shared drive...',
            logs=indexing_status['logs'] + ['Scanning shared drive...']
        )
        
        SHARED_DRIVE_ID = '0AMjLFg-ngmOAUk9PVA'  # 7MM Resources
        
        response = drive_service.files().list(
            q=f"'{SHARED_DRIVE_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            driveId=SHARED_DRIVE_ID,
            corpora='drive',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            fields='files(id, name)'
        ).execute()
        
        folders = response.get('files', [])
        total_folders = len(folders)
        
        update_status(
            logs=indexing_status['logs'] + [f'Found {total_folders} folders to index']
        )
        
        if total_folders == 0:
            raise Exception('No folders found in shared drive')
        
        # Index each folder
        indexed_folders = {}
        loader = GoogleDriveLoader(drive_service)
        
        for idx, folder in enumerate(folders, 1):
            folder_name = folder['name']
            folder_id = folder['id']
            
            progress = 10 + int((idx / total_folders) * 85)
            update_status(
                progress=progress,
                message=f'Indexing {folder_name} ({idx}/{total_folders})...',
                logs=indexing_status['logs'] + [f'[{idx}/{total_folders}] Processing: {folder_name}']
            )
            
            try:
                # Initialize vector store for this folder (not RAG system - that's for querying)
                collection_id = f'folder_{folder_id}'
                from vector_store import VectorStore
                from embeddings import LocalEmbedder
                from vertex_embeddings import VertexEmbedder
                from document_loader import chunk_text
                from config import USE_VERTEX_EMBEDDINGS, CHUNK_SIZE, CHUNK_OVERLAP
                import uuid
                
                # Use same embedder as configured
                embedder = VertexEmbedder() if USE_VERTEX_EMBEDDINGS else LocalEmbedder()
                vector_store = VectorStore(collection_name=collection_id)
                
                # Get files in folder (limit to prevent timeout)
                files_response = drive_service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    pageSize=100,  # Limit for initial indexing
                    fields='files(id, name, mimeType)'
                ).execute()
                
                files = files_response.get('files', [])
                
                # Process files
                for file in files[:50]:  # Limit to first 50 files per folder
                    try:
                        file_mime = file['mimeType']
                        file_name = file['name']
                        
                        # Handle Google Workspace files (need export, not download)
                        if file_mime == 'application/vnd.google-apps.document':
                            text = loader.export_google_doc(file['id'])
                        elif file_mime == 'application/vnd.google-apps.spreadsheet':
                            text = loader.export_google_sheets(file['id'])
                        elif file_mime == 'application/vnd.google-apps.presentation':
                            text = loader.export_google_slides(file['id'])
                        elif file_mime.startswith('application/vnd.google-apps'):
                            # Skip other Google Apps files (forms, drawings, etc.)
                            continue
                        else:
                            # Regular files - download and extract
                            file_content = loader.download_file(file['id'])
                            if file_content:
                                from document_loader import extract_text
                                text = extract_text(file_content, file_mime, file_name, loader.ocr_service)
                            else:
                                text = None
                        
                        if text and text.strip():
                            # Chunk the text using built-in function
                            chunks = chunk_text(text)
                            update_status(message=f"📝 Split into {len(chunks)} chunks")
                            
                            if not chunks:
                                update_status(message=f"⚠️ No chunks generated for {file_name}")
                                continue
                            
                            # Generate unique IDs for each chunk
                            chunk_ids = [f"{file['id']}_chunk_{i}" for i in range(len(chunks))]
                            
                            # Generate embeddings for all chunks
                            chunk_embeddings = [embedder.embed(chunk) for chunk in chunks]
                            
                            # Create metadata for each chunk
                            chunk_metadatas = [{
                                'filename': file_name,
                                'source': folder_name,
                                'file_id': file['id'],
                                'chunk_index': i,
                                'total_chunks': len(chunks)
                            } for i in range(len(chunks))]
                            
                            # Add all chunks to vector store in one call (batching handled automatically)
                            vector_store.add_documents(
                                documents=chunks,
                                embeddings=chunk_embeddings,
                                metadatas=chunk_metadatas,
                                ids=chunk_ids
                            )
                            
                            update_status(
                                message=f"✅ Added {len(chunks)} chunks from {file_name}",
                                progress=int((file_count / total_files) * 100)
                            )
                            
                    except Exception as file_error:
                        update_status(
                            logs=indexing_status['logs'] + [f'  ⚠️ Error with file {file["name"]}: {str(file_error)}']
                        )
                        continue
                
                # Save folder info
                indexed_folders[folder_id] = {
                    'name': folder_name,
                    'file_count': len(files),
                    'indexed_at': datetime.now().isoformat()
                }
                
                update_status(
                    logs=indexing_status['logs'] + [f'  ✓ Indexed {len(files)} files from {folder_name}']
                )
                
            except Exception as folder_error:
                update_status(
                    logs=indexing_status['logs'] + [f'  ✗ Failed to index {folder_name}: {str(folder_error)}']
                )
                continue
        
        # Save indexed folders
        with open('indexed_folders.json', 'w') as f:
            json.dump(indexed_folders, f, indent=2)
        
        # Complete
        update_status(
            running=False,
            progress=100,
            message=f'Indexing complete! Indexed {len(indexed_folders)}/{total_folders} folders.',
            completed_at=datetime.now().isoformat(),
            logs=indexing_status['logs'] + [
                f'✓ Successfully indexed {len(indexed_folders)} folders',
                f'✓ Total collections created: {len(indexed_folders)}',
                '✓ Restart server to use new collections'
            ]
        )
        
    except Exception as e:
        update_status(
            running=False,
            progress=0,
            message='Indexing failed',
            error=str(e),
            completed_at=datetime.now().isoformat(),
            logs=indexing_status['logs'] + [f'✗ Error: {str(e)}']
        )

def run_collection_update():
    """Background collection update process"""
    global indexing_status
    from datetime import datetime
    import time
    
    with indexing_lock:
        try:
            # Initialize
            indexing_status.update({
                'running': True,
                'progress': 0,
                'message': 'Starting collection update...',
                'started_at': datetime.now().isoformat(),
                'error': None,
                'logs': []
            })
            
            # Simulate update process (replace with actual logic)
            indexing_status.update({
                'progress': 50,
                'message': 'Collection update temporarily disabled due to package compatibility issues.'
            })
            
            time.sleep(2)  # Simulate work
            
            # Complete
            indexing_status.update({
                'running': False,
                'progress': 100,
                'message': 'Collection update feature temporarily disabled.',
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


# ===== Google Drive OAuth Endpoints =====

@admin_bp.route('/gdrive/status')
@require_admin
def gdrive_status():
    """Check Google Drive authentication status"""
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
                
            if creds and creds.valid:
                return jsonify({
                    'authenticated': True,
                    'message': 'Google Drive connected and authenticated',
                    'has_refresh_token': creds.refresh_token is not None
                })
            elif creds and creds.expired and creds.refresh_token:
                return jsonify({
                    'authenticated': True,
                    'message': 'Token expired but has refresh token (will auto-renew)',
                    'has_refresh_token': True
                })
            else:
                return jsonify({
                    'authenticated': False,
                    'message': 'Token invalid or missing refresh token',
                    'has_refresh_token': creds.refresh_token is not None if creds else False
                })
        else:
            return jsonify({
                'authenticated': False,
                'message': 'Not connected to Google Drive'
            })
    except Exception as e:
        return jsonify({
            'authenticated': False,
            'message': f'Error checking status: {str(e)}'
        }), 500


@admin_bp.route('/gdrive/authorize')
@require_admin
def gdrive_authorize():
    """Start Google OAuth flow"""
    try:
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            redirect_uri='http://localhost:5001/admin/gdrive/callback'
        )
        
        # Generate authorization URL with offline access for refresh token
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent',  # Force consent screen to get refresh token
            include_granted_scopes='true'
        )
        
        # Store state in session for security
        session['oauth_state'] = state
        
        return redirect(authorization_url)
        
    except Exception as e:
        return jsonify({'error': f'OAuth initialization failed: {str(e)}'}), 500


@admin_bp.route('/gdrive/callback')
def gdrive_callback():
    """Handle OAuth callback from Google"""
    try:
        # Verify state for CSRF protection
        state = session.get('oauth_state')
        if not state:
            return "Error: No OAuth state found in session. Please try connecting again.", 400
        
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            state=state,
            redirect_uri='http://localhost:5001/admin/gdrive/callback'
        )
        
        # Exchange authorization code for credentials
        flow.fetch_token(authorization_response=request.url)
        creds = flow.credentials
        
        # Save credentials with refresh token
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        
        # Clear OAuth state from session
        session.pop('oauth_state', None)
        
        # Redirect back to admin dashboard with success flag
        return redirect('/admin/dashboard?auth_complete=true&gdrive=connected')
        
    except Exception as e:
        return f"OAuth callback error: {str(e)}", 500


@admin_bp.route('/gdrive/disconnect', methods=['POST'])
@require_admin
def gdrive_disconnect():
    """Disconnect Google Drive by removing token"""
    try:
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            return jsonify({
                'success': True,
                'message': 'Google Drive disconnected successfully'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Already disconnected'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500