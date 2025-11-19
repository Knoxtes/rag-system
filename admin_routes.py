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

def run_collection_update():
    """Background collection update process"""
    global indexing_status
    
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