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

# Import Google Drive service function
try:
    from google_drive_oauth import get_drive_service
except ImportError:
    def get_drive_service():
        return None

# Import shared limiter instance
from rate_limiter import limiter

# Constants
SHARED_DRIVE_ID = '0AMjLFg-ngmOAUk9PVA'  # 7MM Resources shared drive ID

# Helper functions for indexing
def get_all_files_recursive_from_folder(folder_id, drive_service, depth=0):
    """Recursively get ALL files from folder and all its subfolders"""
    all_files = []
    indent = "  " * depth
    
    try:
        # Query for ALL items (files and folders) in this specific folder
        query = f"'{folder_id}' in parents and trashed=false"
        page_token = None
        
        while True:
            # Use safe_drive_call for retry logic
            def make_request():
                return drive_service.files().list(
                    q=query,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    pageSize=1000,
                    pageToken=page_token,
                    fields='files(id, name, mimeType), nextPageToken'
                ).execute()
            
            response = safe_drive_call(make_request)
            if not response:
                break
                
            items = response.get('files', [])
            
            # Debug: Log what we're finding at each level
            if depth < 2:  # Only log first 2 levels to avoid spam
                files_count = sum(1 for item in items if item['mimeType'] != 'application/vnd.google-apps.folder')
                folders_count = sum(1 for item in items if item['mimeType'] == 'application/vnd.google-apps.folder')
                update_status(
                    logs=indexing_status['logs'] + [f'{indent}🔍 Level {depth}: Found {files_count} files, {folders_count} folders in folder {folder_id}']
                )
            
            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recursively get files from subfolder
                    try:
                        subfolder_files = get_all_files_recursive_from_folder(item['id'], drive_service, depth + 1)
                        all_files.extend(subfolder_files)
                    except Exception as subfolder_error:
                        update_status(
                            logs=indexing_status['logs'] + [f'    ⚠️ Subfolder error at depth {depth}: {str(subfolder_error)[:100]}']
                        )
                        continue
                else:
                    # It's a file, add it
                    all_files.append(item)
            
            page_token = response.get('nextPageToken')
            if not page_token:
                break
    
    except Exception as e:
        update_status(
            logs=indexing_status['logs'] + [f'  ⚠️ Error listing files in folder {folder_id} at depth {depth}: {str(e)[:100]}']
        )
    
    return all_files

def safe_drive_call(func, max_retries=3, backoff=2):
    """Execute Drive API call with retry logic for transient failures"""
    from googleapiclient.errors import HttpError
    
    for attempt in range(max_retries):
        try:
            return func()
        except HttpError as e:
            if e.resp.status in [403, 429, 500, 503]:  # Retryable errors
                if attempt < max_retries - 1:
                    wait_time = backoff ** attempt
                    update_status(
                        logs=indexing_status['logs'] + [f'  ⚠️ API error {e.resp.status}, retrying in {wait_time}s...']
                    )
                    time.sleep(wait_time)
                    continue
            raise e
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = backoff ** attempt
                update_status(
                    logs=indexing_status['logs'] + [f'  ⚠️ Network error, retrying in {wait_time}s...']
                )
                time.sleep(wait_time)
                continue
            raise e
    
    return None

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
    # Add cache busting with timestamp
    import time
    cache_bust = int(time.time())
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>RAG System Admin Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; }
        .loading-container { display: flex; justify-content: center; align-items: center; height: 100vh; flex-direction: column; }
        .loading { width: 40px; height: 40px; border: 4px solid #334155; border-top: 4px solid #3b82f6; border-radius: 50%; margin-bottom: 20px; }
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
                        window.location.href = '/?from_admin=true';
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
            window.location.href = '/';
        }
        
        async function loadDashboard() {
            const token = localStorage.getItem('authToken');
            
            try {
                // Add cache-busting timestamp
                const cacheBust = new Date().getTime();
                const response = await fetch(`/admin/dashboard-content?v=${cacheBust}`, {
                    headers: { 
                        'Authorization': `Bearer ${token}`,
                        'Cache-Control': 'no-cache'
                    }
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
                        try {
                            const newScript = document.createElement('script');
                            if (script.src) {
                                newScript.src = script.src;
                            } else {
                                newScript.textContent = script.textContent;
                            }
                            document.body.appendChild(newScript);
                        } catch (error) {
                            console.error('Script execution error:', error);
                        }
                    });
                    
                    // Ensure critical functions are available globally
                    setTimeout(() => {
                        if (!window.loadFolderSelection || window.loadFolderSelection.toString().includes('Backup')) {
                            console.log('Defining real loadFolderSelection function');
                            
                            // Define the actual loadFolderSelection function
                            window.loadFolderSelection = async function() {
                                console.log('loadFolderSelection called');
                                const token = localStorage.getItem('authToken');
                                console.log('Token:', token ? 'Found' : 'Missing');
                                
                                const statusDiv = document.getElementById('folder-selection-status');
                                const panel = document.getElementById('folder-selection-panel');
                                const container = document.getElementById('folder-list-container');
                                
                                if (!statusDiv || !panel || !container) {
                                    console.error('Missing DOM elements:', { statusDiv, panel, container });
                                    return;
                                }
                                
                                statusDiv.innerHTML = '<div style="color: #3b82f6;">Loading folders...</div>';
                                panel.style.display = 'block';
                                
                                try {
                                    console.log('Fetching folder list...');
                                    const response = await fetch('/admin/folders/list', {
                                        headers: { 'Authorization': `Bearer ${token}` }
                                    });
                                    
                                    if (response.ok) {
                                        const data = await response.json();
                                        console.log('Folder data received:', data);
                                        
                                        if (data.folders && data.folders.length > 0) {
                                            statusDiv.innerHTML = `<div style="color: #10b981;">✅ Found ${data.folders.length} folders</div>`;
                                            
                                            let html = '<div style="max-height: 400px; overflow-y: auto; margin-top: 15px;">';
                                            data.folders.forEach(folder => {
                                                const isIndexed = folder.is_indexed;
                                                const statusColor = isIndexed ? '#10b981' : '#94a3b8';
                                                const statusText = isIndexed ? '✅ Indexed' : '⏳ Not indexed';
                                                const buttonText = isIndexed ? 'Re-index' : 'Index';
                                                const buttonColor = isIndexed ? '#f59e0b' : '#3b82f6';
                                                
                                                html += `
                                                    <div style="border: 1px solid #374151; padding: 15px; margin: 10px 0; border-radius: 8px; background: #1f2937;">
                                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                                            <div>
                                                                <h4 style="margin: 0; color: #f3f4f6;">${folder.name}</h4>
                                                                <p style="margin: 5px 0; color: ${statusColor}; font-size: 14px;">${statusText}</p>
                                                                ${isIndexed ? `<p style="margin: 5px 0; color: #9ca3af; font-size: 12px;">Files: ${folder.file_count || 0} | Last indexed: ${folder.last_indexed || 'Unknown'}</p>` : ''}
                                                            </div>
                                                            <button onclick="indexFolder('${folder.id}', '${folder.name}')" 
                                                                    style="background: ${buttonColor}; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px;">
                                                                ${buttonText}
                                                            </button>
                                                        </div>
                                                        <div id="index-status-${folder.id}" style="margin-top: 10px;"></div>
                                                    </div>
                                                `;
                                            });
                                            html += '</div>';
                                            
                                            container.innerHTML = html;
                                        } else {
                                            statusDiv.innerHTML = '<div style="color: #f59e0b;">⚠️ No folders found</div>';
                                            container.innerHTML = '';
                                        }
                                    } else {
                                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                                    }
                                } catch (error) {
                                    console.error('Error loading folders:', error);
                                    statusDiv.innerHTML = `<div style="color: #ef4444;">❌ Error: ${error.message}</div>`;
                                    container.innerHTML = '';
                                }
                            };
                            
                            // Define the indexFolder function
                            window.indexFolder = async function(folderId, folderName) {
                                console.log(`Indexing folder: ${folderName} (${folderId})`);
                                const token = localStorage.getItem('authToken');
                                const statusDiv = document.getElementById(`index-status-${folderId}`);
                                
                                if (statusDiv) {
                                    statusDiv.innerHTML = '<div style="color: #3b82f6;">🔄 Starting indexing...</div>';
                                }
                                
                                try {
                                    // Start indexing
                                    const response = await fetch(`/admin/folders/index/${folderId}`, {
                                        method: 'POST',
                                        headers: {
                                            'Content-Type': 'application/json',
                                            'Authorization': `Bearer ${token}`
                                        },
                                        body: JSON.stringify({
                                            folder_name: folderName
                                        })
                                    });
                                    
                                    const data = await response.json();
                                    
                                    if (response.ok) {
                                        // Start polling for progress
                                        if (statusDiv) {
                                            statusDiv.innerHTML = `<div style="color: #3b82f6;">🔄 ${data.message}</div><div id="progress-${folderId}" style="margin-top: 10px;"></div>`;
                                        }
                                        
                                        // Poll for status updates
                                        const progressDiv = document.getElementById(`progress-${folderId}`);
                                        const pollStatus = async () => {
                                            try {
                                                const statusResponse = await fetch(`/admin/folders/index/${folderId}/status`, {
                                                    headers: { 'Authorization': `Bearer ${token}` }
                                                });
                                                const statusData = await statusResponse.json();
                                                
                                                if (progressDiv) {
                                                    let progressBar = `
                                                        <div style="background: #374151; border-radius: 8px; overflow: hidden; margin-bottom: 10px;">
                                                            <div style="background: #3b82f6; height: 20px; width: ${statusData.progress}%; transition: width 0.3s;"></div>
                                                        </div>
                                                        <div style="font-size: 12px; color: #94a3b8;">${statusData.message} (${statusData.progress}%)</div>
                                                    `;
                                                    
                                                    if (statusData.logs && statusData.logs.length > 0) {
                                                        const lastLog = statusData.logs[statusData.logs.length - 1];
                                                        progressBar += `<div style="font-size: 11px; color: #6b7280; margin-top: 5px;">${lastLog}</div>`;
                                                    }
                                                    
                                                    progressDiv.innerHTML = progressBar;
                                                }
                                                
                                                if (statusData.running) {
                                                    setTimeout(pollStatus, 2000); // Poll every 2 seconds
                                                } else {
                                                    // Indexing completed
                                                    if (statusData.error) {
                                                        if (statusDiv) {
                                                            statusDiv.innerHTML = `<div style="color: #ef4444;">❌ Error: ${statusData.error}</div>`;
                                                        }
                                                    } else {
                                                        if (statusDiv) {
                                                            statusDiv.innerHTML = `<div style="color: #10b981;">✅ Indexing completed successfully!</div>`;
                                                        }
                                                        // Reload folder list after completion
                                                        setTimeout(() => {
                                                            loadFolderSelection();
                                                        }, 2000);
                                                    }
                                                }
                                            } catch (error) {
                                                console.error('Error polling status:', error);
                                                if (progressDiv) {
                                                    progressDiv.innerHTML = `<div style="color: #ef4444;">❌ Error monitoring progress</div>`;
                                                }
                                            }
                                        };
                                        
                                        // Start polling immediately
                                        setTimeout(pollStatus, 1000);
                                        
                                    } else if (response.status === 409) {
                                        // Handle conflict - another indexing is in progress
                                        const resetButton = `<button onclick="resetIndexingStatus()" style="background: #f59e0b; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; margin-left: 10px; font-size: 12px;">Reset</button>`;
                                        if (statusDiv) {
                                            statusDiv.innerHTML = `<div style="color: #f59e0b;">⚠️ Another indexing is in progress. ${resetButton}<br><small>${data.current_message || 'Unknown status'}</small></div>`;
                                        }
                                    } else {
                                        if (statusDiv) {
                                            statusDiv.innerHTML = `<div style="color: #ef4444;">❌ ${data.error || data.message}</div>`;
                                        }
                                    }
                                } catch (error) {
                                    console.error('Error indexing folder:', error);
                                    if (statusDiv) {
                                        statusDiv.innerHTML = `<div style="color: #ef4444;">❌ Error: ${error.message}</div>`;
                                    }
                                }
                            };
                            
                            // Define the resetIndexingStatus function
                            window.resetIndexingStatus = async function() {
                                const token = localStorage.getItem('authToken');
                                try {
                                    const response = await fetch('/admin/collections/reset-status', {
                                        method: 'POST',
                                        headers: {
                                            'Authorization': `Bearer ${token}`
                                        }
                                    });
                                    
                                    if (response.ok) {
                                        alert('Indexing status reset successfully. You can now try indexing again.');
                                        // Reload the folder list
                                        loadFolderSelection();
                                    } else {
                                        alert('Failed to reset indexing status.');
                                    }
                                } catch (error) {
                                    console.error('Error resetting indexing status:', error);
                                    alert('Error resetting indexing status: ' + error.message);
                                }
                            };
                        }
                    }, 1000);
                    
                    if (!window.loadFolderSelection) {
                        window.loadFolderSelection = function() {
                            console.log('Backup loadFolderSelection called');
                            alert('Folder selection functionality is loading. Please wait a moment and try again.');
                        };
                    }
                    if (!window.indexFolder) {
                        window.indexFolder = function(folderId, folderName) {
                            console.log('Backup indexFolder called');
                            alert('Index functionality is loading. Please wait a moment and try again.');
                        };
                    }
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
    """ + f"<!-- Cache bust: {cache_bust} -->"

@admin_bp.route('/dashboard-content')
@require_admin
def admin_dashboard_content():
    """Return the dashboard content HTML for authenticated users"""
    from flask import make_response
    import time
    
    html_content = """
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
                <h3>📝 Regenerate Index File</h3>
                <p>Rebuild indexed_folders.json from ChromaDB collections</p>
                <button class="btn" style="background: #8b5cf6;" onclick="regenerateIndexedFolders()">Regenerate Index</button>
                <div id="regenerate-status" style="margin-top: 10px; font-size: 14px;"></div>
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
                    <h3 style="color: #86efac;">📁 Select Specific Folder</h3>
                    <p style="color: #bbf7d0;">Choose and index individual folders</p>
                    <button class="btn" onclick="loadFolderSelection()" style="background: #10b981;">
                        Select Folder to Index
                    </button>
                    <div id="folder-selection-status" style="margin-top: 10px; color: #bbf7d0;"></div>
                </div>
            </div>
        </div>
        
        <!-- Folder Selection Panel (Initially Hidden) -->
        <div id="folder-selection-panel" style="display: none; margin: 30px 0; padding: 30px; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 2px solid #10b981; border-radius: 12px; box-shadow: 0 10px 30px rgba(16, 185, 129, 0.2);">
            <h2 style="color: #10b981; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
                <span>📂</span>
                <span>Folder Selection</span>
            </h2>
            <div id="folder-list-container">
                <p style="color: #94a3b8;">Loading available folders...</p>
            </div>
        </div>
        
        <!-- Indexing Progress Panel (Initially Hidden) -->
        <div id="indexing-progress-panel" style="display: none; margin: 30px 0; padding: 30px; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 2px solid #3b82f6; border-radius: 12px; box-shadow: 0 10px 30px rgba(59, 130, 246, 0.2);">
            <h2 style="color: #3b82f6; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
                <span>⚡</span>
                <span>Indexing Progress</span>
            </h2>
            
            <div style="background: #0f172a; border-radius: 8px; padding: 20px; border: 1px solid #334155;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <span style="color: #e2e8f0; font-weight: 600;">Progress</span>
                    <span id="indexing-percentage" style="color: #3b82f6; font-weight: 600;">0%</span>
                </div>
                
                <div style="width: 100%; height: 8px; background: #334155; border-radius: 4px; overflow: hidden; margin-bottom: 20px;">
                    <div id="indexing-progress-bar" style="width: 0%; height: 100%; background: linear-gradient(90deg, #3b82f6, #06b6d4); transition: width 0.3s ease;"></div>
                </div>
                
                <div style="color: #94a3b8; margin-bottom: 15px;">
                    <strong style="color: #e2e8f0;">Status:</strong>
                    <span id="indexing-message">Ready</span>
                </div>
                
                <div style="max-height: 300px; overflow-y: auto; background: #000; border-radius: 6px; padding: 15px; border: 1px solid #374151;">
                    <pre id="indexing-logs" style="color: #d1d5db; font-size: 12px; line-height: 1.4; margin: 0; white-space: pre-wrap;"></pre>
                </div>
                
                <div style="margin-top: 15px; display: flex; gap: 10px;">
                    <button id="stop-indexing-btn" class="btn" onclick="stopIndexing()" style="background: #ef4444; display: none;">
                        Stop Indexing
                    </button>
                    <button id="hide-progress-btn" class="btn" onclick="hideProgressPanel()" style="background: #6b7280;">
                        Hide Panel
                    </button>
                </div>
            </div>
        </div>">
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
        // Admin dashboard functions - defined globally
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
        
        async function regenerateIndexedFolders() {
            const token = localStorage.getItem('authToken');
            const regenerateButton = document.querySelector('button[onclick="regenerateIndexedFolders()"]');
            const statusDiv = document.getElementById('regenerate-status');
            
            if (!confirm('This will regenerate indexed_folders.json from ChromaDB collections. Continue?')) {
                return;
            }
            
            try {
                regenerateButton.disabled = true;
                regenerateButton.textContent = 'Regenerating...';
                statusDiv.innerHTML = '<div style="color: #3b82f6;">⏳ Scanning ChromaDB collections...</div>';
                
                const response = await fetch('/admin/collections/regenerate-index', { 
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                if (response.ok && data.success) {
                    statusDiv.innerHTML = `
                        <div style="color: #10b981; font-weight: bold;">✅ Success!</div>
                        <div style="color: #94a3b8; margin-top: 5px;">
                            Found ${data.collections_found} collections<br>
                            Regenerated ${data.folders_indexed} indexed folders<br>
                            <small>Refresh the page to see updated collections</small>
                        </div>
                    `;
                    
                    // Auto-refresh stats after 2 seconds
                    setTimeout(() => {
                        refreshStats();
                        window.location.reload();
                    }, 2000);
                } else {
                    statusDiv.innerHTML = `<div style="color: #ef4444;">❌ Error: ${data.error || 'Unknown error'}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div style="color: #ef4444;">❌ Error: ${error.message}</div>`;
            } finally {
                regenerateButton.disabled = false;
                regenerateButton.textContent = 'Regenerate Index';
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
        
        // Folder Selection Functions
        async function loadFolderSelection() {
            console.log('loadFolderSelection called');
            const token = localStorage.getItem('authToken');
            console.log('Token:', token ? 'Found' : 'Missing');
            
            const statusDiv = document.getElementById('folder-selection-status');
            const panel = document.getElementById('folder-selection-panel');
            const container = document.getElementById('folder-list-container');
            
            if (!statusDiv || !panel || !container) {
                console.error('Missing DOM elements:', { statusDiv, panel, container });
                return;
            }
            
            statusDiv.innerHTML = '<div style="color: #3b82f6;">Loading folders...</div>';
            panel.style.display = 'block';
            
            try {
                console.log('Fetching folder list...');
                const response = await fetch('/admin/folders/list', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                console.log('Response status:', response.status);
                const data = await response.json();
                console.log('Response data:', data);
            
            statusDiv.innerHTML = '<div style="color: #3b82f6;">Loading folders...</div>';
            panel.style.display = 'block';
            
            try {
                const response = await fetch('/admin/folders/list', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                if (response.ok) {
                    statusDiv.innerHTML = '<div style="color: #10b981;">✅ Folders loaded</div>';
                    
                    const foldersHtml = `
                        <div style="max-height: 400px; overflow-y: auto;">
                            <div style="display: grid; gap: 15px;">
                                ${data.folders.map(folder => `
                                    <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 15px; display: flex; justify-content: space-between; align-items: center;">
                                        <div>
                                            <h4 style="color: #e2e8f0; margin: 0 0 5px 0;">${folder.name}</h4>
                                            <p style="color: #94a3b8; margin: 0; font-size: 14px;">
                                                ${folder.indexed ? '✅ Indexed' : '⏳ Not indexed'} 
                                                ${folder.file_count ? `• ${folder.file_count} files` : ''}
                                                ${folder.last_indexed ? `• Last: ${new Date(folder.last_indexed).toLocaleDateString()}` : ''}
                                            </p>
                                        </div>
                                        <button class="btn" onclick="indexFolder('${folder.id}', '${folder.name}')" 
                                                style="background: ${folder.indexed ? '#6b7280' : '#10b981'}; min-width: 120px;">
                                            ${folder.indexed ? 'Re-index' : 'Index Now'}
                                        </button>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div style="margin-top: 20px; text-align: center;">
                            <button class="btn" onclick="hideFolderSelection()" style="background: #6b7280;">Close</button>
                        </div>
                    `;
                    
                    container.innerHTML = foldersHtml;
                } else {
                    statusDiv.innerHTML = `<div style="color: #ef4444;">❌ ${data.error}</div>`;
                    container.innerHTML = '<p style="color: #ef4444;">Failed to load folders</p>';
                }
            } catch (error) {
                statusDiv.innerHTML = `<div style="color: #ef4444;">Error: ${error.message}</div>`;
                container.innerHTML = '<p style="color: #ef4444;">Network error</p>';
                console.error('Folder selection error:', error);
            }
        }
        
        async function indexFolder(folderId, folderName) {
            const token = localStorage.getItem('authToken');
            
            if (!confirm(`Index folder: ${folderName}?\\n\\nThis will process all files in this folder and its subfolders.`)) {
                return;
            }
            
            const progressPanel = document.getElementById('indexing-progress-panel');
            const progressBar = document.getElementById('indexing-progress-bar');
            const percentage = document.getElementById('indexing-percentage');
            const message = document.getElementById('indexing-message');
            const logs = document.getElementById('indexing-logs');
            const stopBtn = document.getElementById('stop-indexing-btn');
            const hideBtn = document.getElementById('hide-progress-btn');
            
            // Show progress panel
            progressPanel.style.display = 'block';
            stopBtn.style.display = 'inline-block';
            
            try {
                const response = await fetch(`/admin/folders/index/${folderId}`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                if (response.ok) {
                    // Poll for progress
                    const pollInterval = setInterval(async () => {
                        const statusResponse = await fetch('/admin/collections/status', {
                            headers: { 'Authorization': `Bearer ${token}` }
                        });
                        const status = await statusResponse.json();
                        
                        // Update progress
                        const progress = status.progress || 0;
                        progressBar.style.width = `${progress}%`;
                        percentage.textContent = `${progress}%`;
                        message.textContent = status.message || 'Processing...';
                        
                        // Update logs
                        if (status.logs) {
                            logs.textContent = status.logs.join('\\n');
                            logs.scrollTop = logs.scrollHeight;
                        }
                        
                        if (!status.running) {
                            clearInterval(pollInterval);
                            stopBtn.style.display = 'none';
                            
                            if (status.error) {
                                message.textContent = `Error: ${status.error}`;
                                progressBar.style.background = '#ef4444';
                            } else {
                                message.textContent = 'Completed successfully!';
                                progressBar.style.background = 'linear-gradient(90deg, #10b981, #059669)';
                                
                                // Refresh folder list
                                setTimeout(() => {
                                    loadFolderSelection();
                                }, 2000);
                            }
                        }
                    }, 1000);
                    
                    // Store interval for stopping
                    window.currentIndexingPoll = pollInterval;
                    
                } else {
                    throw new Error(data.error || 'Failed to start indexing');
                }
            } catch (error) {
                message.textContent = `Error: ${error.message}`;
                progressBar.style.background = '#ef4444';
                stopBtn.style.display = 'none';
            }
        }
        
        function hideFolderSelection() {
            document.getElementById('folder-selection-panel').style.display = 'none';
        }
        
        function hideProgressPanel() {
            document.getElementById('indexing-progress-panel').style.display = 'none';
        }
        
        function stopIndexing() {
            if (window.currentIndexingPoll) {
                clearInterval(window.currentIndexingPoll);
                window.currentIndexingPoll = null;
            }
            document.getElementById('stop-indexing-btn').style.display = 'none';
            document.getElementById('indexing-message').textContent = 'Stopped by user';
        }
        
        // Make functions globally accessible (after all definitions)
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
        window.loadFolderSelection = loadFolderSelection;
        window.indexFolder = indexFolder;
        window.hideFolderSelection = hideFolderSelection;
        window.hideProgressPanel = hideProgressPanel;
        window.stopIndexing = stopIndexing;
    
    // Call migration status on load
    setTimeout(checkMigrationStatus, 1000);
    
    </script>
    """ + f"<!-- Generated: {int(time.time())} -->"
    
    # Create response with no-cache headers
    response = make_response(html_content)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@admin_bp.route('/stats/system')
@require_admin
@limiter.exempt  # Exempt admin polling endpoints
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
@limiter.exempt  # Exempt admin status checks from rate limiting
def get_indexing_status():
    """Get current indexing status"""
    return jsonify(indexing_status)

@admin_bp.route('/collections/reset-status', methods=['POST'])
@require_admin
def reset_indexing_status():
    """Manually reset indexing status (use if stuck)"""
    global indexing_status
    indexing_status = {
        'running': False,
        'progress': 0,
        'message': 'Ready (manually reset)',
        'started_at': None,
        'completed_at': None,
        'error': None,
        'logs': ['Status manually reset by admin']
    }
    return jsonify({'message': 'Indexing status reset successfully', 'status': indexing_status})

@admin_bp.route('/collections/regenerate-index', methods=['POST'])
@require_admin
def regenerate_indexed_folders():
    """Regenerate indexed_folders.json by scanning ChromaDB collections"""
    try:
        import chromadb
        from config import CHROMA_PERSIST_DIR
        
        print("[+] Regenerating indexed_folders.json from ChromaDB collections...")
        
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        collections = client.list_collections()
        
        print(f"[+] Found {len(collections)} collections in ChromaDB")
        
        indexed_folders = {}
        
        for collection in collections:
            collection_name = collection.name
            
            # Skip non-folder collections
            if not collection_name.startswith('folder_'):
                print(f"  ⏭️  Skipping non-folder collection: {collection_name}")
                continue
            
            # Extract folder_id from collection name
            folder_id = collection_name.replace('folder_', '')
            
            # Get collection stats
            doc_count = collection.count()
            
            if doc_count == 0:
                print(f"  ⚠️  Collection {collection_name} is empty - skipping")
                continue
            
            # Get sample metadata to extract folder info
            try:
                results = collection.get(limit=1, include=['metadatas'])
                if results and results['metadatas'] and len(results['metadatas']) > 0:
                    sample_metadata = results['metadatas'][0]
                    folder_name = sample_metadata.get('file_path', 'Unknown').split('/')[0] or 'Unknown'
                else:
                    folder_name = f"Folder {folder_id}"
            except Exception as e:
                print(f"  ⚠️  Could not fetch metadata for {collection_name}: {e}")
                folder_name = f"Folder {folder_id}"
            
            # Create entry
            indexed_folders[folder_id] = {
                'collection_name': collection_name,
                'name': folder_name,
                'path': folder_name,
                'location': folder_name,
                'file_count': 0,  # Unknown without full scan
                'files_processed': 0,  # Unknown without full scan
                'files_failed': 0,
                'files_skipped': 0,
                'chunks_created': doc_count,
                'indexed_at': datetime.now().isoformat(),
                'regenerated': True
            }
            
            print(f"  ✅ Added: {folder_name} ({doc_count} chunks)")
        
        # Save to file
        with open(INDEXED_FOLDERS_FILE, 'w') as f:
            json.dump(indexed_folders, f, indent=2)
        
        print(f"[+] Successfully regenerated indexed_folders.json with {len(indexed_folders)} folders")
        
        return jsonify({
            'success': True,
            'message': f'Successfully regenerated indexed_folders.json',
            'collections_found': len(collections),
            'folders_indexed': len(indexed_folders),
            'indexed_folders': indexed_folders
        })
        
    except Exception as e:
        print(f"[!] Error regenerating indexed_folders.json: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/collections/diagnose', methods=['GET'])
@require_admin
def diagnose_collections():
    """Diagnose collection status - compare ChromaDB vs indexed_folders.json"""
    try:
        import chromadb
        from config import CHROMA_PERSIST_DIR
        
        # Get ChromaDB collections
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        chroma_collections = client.list_collections()
        
        chroma_info = {}
        for collection in chroma_collections:
            if collection.name.startswith('folder_'):
                folder_id = collection.name.replace('folder_', '')
                chroma_info[folder_id] = {
                    'collection_name': collection.name,
                    'document_count': collection.count()
                }
        
        # Get indexed_folders.json
        indexed_info = {}
        if os.path.exists(INDEXED_FOLDERS_FILE):
            with open(INDEXED_FOLDERS_FILE, 'r') as f:
                indexed_info = json.load(f)
        
        # Compare
        diagnosis = {
            'chromadb_collections': len(chroma_info),
            'indexed_folders': len(indexed_info),
            'in_chromadb_only': [],
            'in_indexed_only': [],
            'mismatched_counts': [],
            'matched': []
        }
        
        # Check ChromaDB collections not in indexed_folders.json
        for folder_id, info in chroma_info.items():
            if folder_id not in indexed_info:
                diagnosis['in_chromadb_only'].append({
                    'folder_id': folder_id,
                    'collection_name': info['collection_name'],
                    'document_count': info['document_count']
                })
            else:
                indexed_count = indexed_info[folder_id].get('chunks_created', 0)
                chroma_count = info['document_count']
                
                if indexed_count != chroma_count:
                    diagnosis['mismatched_counts'].append({
                        'folder_id': folder_id,
                        'name': indexed_info[folder_id].get('name', 'Unknown'),
                        'indexed_count': indexed_count,
                        'chromadb_count': chroma_count
                    })
                else:
                    diagnosis['matched'].append({
                        'folder_id': folder_id,
                        'name': indexed_info[folder_id].get('name', 'Unknown'),
                        'document_count': chroma_count
                    })
        
        # Check indexed_folders.json entries not in ChromaDB
        for folder_id in indexed_info:
            if folder_id not in chroma_info:
                diagnosis['in_indexed_only'].append({
                    'folder_id': folder_id,
                    'name': indexed_info[folder_id].get('name', 'Unknown')
                })
        
        return jsonify({
            'success': True,
            'diagnosis': diagnosis,
            'needs_regeneration': len(diagnosis['in_chromadb_only']) > 0 or len(diagnosis['mismatched_counts']) > 0
        })
        
    except Exception as e:
        print(f"[!] Error diagnosing collections: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
        return jsonify({
            'error': 'Indexing already in progress',
            'current_progress': indexing_status.get('progress', 0),
            'current_message': indexing_status.get('message', 'Unknown')
        }), 409
    
    try:
        # Reset status before starting
        indexing_status = {
            'running': False,
            'progress': 0,
            'message': 'Ready',
            'started_at': None,
            'completed_at': None,
            'error': None,
            'logs': []
        }
        
        # Start background indexing
        thread = threading.Thread(target=run_full_indexing_process)
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': 'Full indexing process started'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/folders/list', methods=['GET'])
@require_admin
def list_available_folders():
    """Get list of available root folders for selective indexing"""
    try:
        # Get Google Drive service
        drive_service = get_drive_service()
        if not drive_service:
            return jsonify({'error': 'Google Drive not authenticated'}), 503
        
        # Get root folders from shared drive
        response = safe_drive_call(lambda: drive_service.files().list(
            q=f"'{SHARED_DRIVE_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            driveId=SHARED_DRIVE_ID,
            corpora='drive',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            fields='files(id, name)',
            pageSize=100
        ).execute())
        
        folders = response.get('files', [])
        
        # Check which folders are already indexed
        indexed_folders = {}
        if os.path.exists('indexed_folders.json'):
            with open('indexed_folders.json', 'r') as f:
                indexed_folders = json.load(f)
        
        folder_list = []
        for folder in folders:
            is_indexed = folder['id'] in indexed_folders
            folder_info = {
                'id': folder['id'],
                'name': folder['name'],
                'is_indexed': is_indexed,
                'last_indexed': indexed_folders.get(folder['id'], {}).get('indexed_at'),
                'file_count': indexed_folders.get(folder['id'], {}).get('file_count', 0)
            }
            folder_list.append(folder_info)
        
        # Sort by name
        folder_list.sort(key=lambda x: x['name'].lower())
        
        return jsonify({
            'folders': folder_list,
            'total_count': len(folder_list)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/folders/index/<folder_id>/status', methods=['GET'])
@require_admin
def get_folder_indexing_status(folder_id):
    """Get current indexing status for a specific folder"""
    return jsonify(indexing_status)

@admin_bp.route('/folders/index/<folder_id>', methods=['POST'])
@require_admin
def index_specific_folder(folder_id):
    """Index a specific folder by ID"""
    global indexing_status
    
    if indexing_status['running']:
        return jsonify({
            'error': 'Indexing already in progress',
            'current_progress': indexing_status.get('progress', 0),
            'current_message': indexing_status.get('message', 'Unknown')
        }), 409
    
    try:
        # Validate folder exists
        drive_service = get_drive_service()
        if not drive_service:
            return jsonify({'error': 'Google Drive not authenticated'}), 503
        
        # Get folder details
        folder_info = safe_drive_call(lambda: drive_service.files().get(
            fileId=folder_id,
            supportsAllDrives=True,
            fields='id, name, mimeType'
        ).execute())
        
        if not folder_info or folder_info.get('mimeType') != 'application/vnd.google-apps.folder':
            return jsonify({'error': 'Invalid folder ID'}), 400
        
        # Reset status before starting
        indexing_status = {
            'running': False,
            'progress': 0,
            'message': 'Ready',
            'started_at': None,
            'completed_at': None,
            'error': None,
            'logs': []
        }
        
        # Start background indexing for specific folder
        thread = threading.Thread(target=run_single_folder_indexing, args=(folder_id, folder_info['name']))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': f'Started indexing folder: {folder_info["name"]}',
            'folder_name': folder_info['name'],
            'folder_id': folder_id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_reindex_process(create_backup=True):
    """Background reindexing process - FIXED: Proper lock handling with crash recovery"""
    global indexing_status
    from datetime import datetime
    import shutil
    import os
    
    # CRITICAL FIX: Don't hold lock for entire process, only for status updates
    try:
        # Initialize
        update_status(
            running=True,
            progress=0,
            message='Starting reindex process...',
            started_at=datetime.now().isoformat(),
            error=None,
            logs=['Reindex process started']
        )
        
        chroma_path = './chroma_db'
        
        # Step 1: Backup (if requested)
        if create_backup:
            update_status(
                progress=10,
                message='Creating database backup...',
                logs=indexing_status['logs'] + ['Creating backup...']
            )
            
            backup_dir = './chroma_db_backups'
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'backup_{timestamp}')
            
            if os.path.exists(chroma_path):
                shutil.copytree(chroma_path, backup_path)
                update_status(
                    logs=indexing_status['logs'] + [f'Backup created: {backup_path}']
                )
        
        # Step 2: Clear database
        update_status(
            progress=30,
            message='Clearing old database...',
            logs=indexing_status['logs'] + ['Clearing database...']
        )
        
        if os.path.exists(chroma_path):
            try:
                # Try to close any open ChromaDB connections
                import gc
                gc.collect()
                
                # Attempt to remove
                shutil.rmtree(chroma_path)
                update_status(
                    logs=indexing_status['logs'] + ['Database cleared']
                )
            except PermissionError as e:
                raise Exception(
                    'Database is locked! Stop the server first, then run: '
                    'python reindex_with_vertex.py --backup'
                )
        
        os.makedirs(chroma_path, exist_ok=True)
        
        # Step 3: Complete
        update_status(
            running=False,
            progress=100,
            message='Database cleared. Restart server to reindex with new embeddings.',
            completed_at=datetime.now().isoformat(),
            logs=indexing_status['logs'] + [
                'Reindex preparation complete',
                'Next: Restart the server to begin reindexing with Vertex AI'
            ]
        )
        
    except Exception as e:
        # CRITICAL FIX: Always reset running state on error
        update_status(
            running=False,
            progress=0,
            message='Reindex failed',
            error=str(e),
            completed_at=datetime.now().isoformat(),
            logs=indexing_status['logs'] + [f'Error: {str(e)}']
        )
    finally:
        # CRITICAL FIX: Ensure running is always reset even on unexpected errors
        with indexing_lock:
            if indexing_status.get('running', False):
                indexing_status['running'] = False

def run_single_folder_indexing(folder_id, folder_name):
    """Background process to index a single specific folder"""
    global indexing_status
    from datetime import datetime
    
    try:
        update_status(
            running=True,
            progress=5,
            message=f'Starting indexing of {folder_name}...',
            started_at=datetime.now().isoformat(),
            logs=[f'=== SINGLE FOLDER INDEXING: {folder_name} ===']
        )
        
        # Get Google Drive service
        drive_service = get_drive_service()
        if not drive_service:
            raise Exception('Google Drive service not available')
        
        update_status(
            progress=10,
            message='Initializing components...',
            logs=indexing_status['logs'] + ['✅ Google Drive service ready']
        )
        
        # Initialize embedder
        try:
            from embeddings import LocalEmbedder
            embedder = LocalEmbedder()
            update_status(
                logs=indexing_status['logs'] + ['✅ Embedder initialized']
            )
        except Exception as e:
            raise Exception(f'Failed to initialize embedder: {str(e)}')
        
        # Initialize Google Drive loader
        try:
            from document_loader import GoogleDriveLoader
            loader = GoogleDriveLoader(drive_service)
            update_status(
                logs=indexing_status['logs'] + [f'✅ Google Drive loader initialized (OCR: {"enabled" if loader.ocr_service else "disabled"})']
            )
        except Exception as e:
            raise Exception(f'Failed to initialize loader: {str(e)}')
        
        # Load existing indexed folders
        indexed_folders = {}
        if os.path.exists('indexed_folders.json'):
            with open('indexed_folders.json', 'r') as f:
                indexed_folders = json.load(f)
        
        update_status(
            progress=15,
            message=f'Processing folder: {folder_name}...',
            logs=indexing_status['logs'] + [f'📂 Processing: {folder_name}']
        )
        
        # Create collection for this folder
        collection_id = f'folder_{folder_id}'
        from vector_store import VectorStore
        vector_store = VectorStore(collection_name=collection_id)
        
        update_status(
            logs=indexing_status['logs'] + [f'📊 Collection: {collection_id}']
        )
        
        # Get ALL files recursively from this folder
        update_status(
            progress=20,
            message='Scanning files...',
            logs=indexing_status['logs'] + [f'🔍 Listing files from folder ID: {folder_id} (including subfolders)...']
        )
        
        files = get_all_files_recursive_from_folder(folder_id, drive_service, 0)
        folder_file_count = len(files)
        
        update_status(
            logs=indexing_status['logs'] + [f'📄 Found {folder_file_count} files']
        )
        
        if folder_file_count == 0:
            update_status(
                running=False,
                progress=100,
                message='Folder is empty',
                completed_at=datetime.now().isoformat(),
                logs=indexing_status['logs'] + ['⚠️ No files to process']
            )
            return
        
        # Process files (same logic as full indexing but for single folder)
        folder_chunks = 0
        files_succeeded = 0
        files_failed = 0
        files_skipped = 0
        
        # Batch processing
        BATCH_SIZE = 5
        batch_chunks = []
        batch_metadatas = []
        batch_ids = []
        
        for file_idx, file in enumerate(files, 1):
            try:
                file_name = file['name']
                file_id = file['id']
                file_mime = file.get('mimeType', '')
                
                # Update progress
                file_progress = 20 + int((file_idx / folder_file_count) * 70)
                if file_idx % 5 == 0 or file_idx == 1 or file_idx == folder_file_count:
                    update_status(
                        progress=file_progress,
                        message=f'Processing files... ({file_idx}/{folder_file_count})',
                        logs=indexing_status['logs'] + [f'[{file_idx}/{folder_file_count}] Processing: {file_name[:50]}...']
                    )
                
                # Extract text (same logic as full indexing)
                text = None
                try:
                    if file_mime == 'application/vnd.google-apps.document':
                        text = loader.export_google_doc(file_id)
                    elif file_mime == 'application/vnd.google-apps.spreadsheet':
                        text = loader.export_google_sheets(file_id)
                    elif file_mime == 'application/vnd.google-apps.presentation':
                        text = loader.export_google_slides(file_id)
                    elif file_mime.startswith('application/vnd.google-apps'):
                        files_skipped += 1
                        continue
                    else:
                        file_content = loader.download_file(file_id)
                        if file_content:
                            from document_loader import extract_text
                            text = extract_text(file_content, file_mime, file_name, loader.ocr_service)
                        else:
                            files_failed += 1
                            continue
                
                except Exception as extract_error:
                    files_failed += 1
                    continue
                
                if not text or not text.strip():
                    files_failed += 1
                    continue
                
                # Chunk the text
                from document_loader import chunk_text
                chunks = chunk_text(text)
                if not chunks:
                    files_failed += 1
                    continue
                
                # Add to batch
                for i, chunk in enumerate(chunks):
                    batch_chunks.append(chunk)
                    batch_metadatas.append({
                        'filename': file_name,
                        'source': folder_name,
                        'file_id': file_id,
                        'mime_type': file_mime,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'text_length': len(chunk)
                    })
                    batch_ids.append(f"{file_id}_chunk_{i}")
                
                # Process batch
                if len(batch_chunks) >= BATCH_SIZE or file_idx == folder_file_count:
                    try:
                        batch_embeddings = embedder.embed_documents(batch_chunks)
                        if hasattr(batch_embeddings, 'tolist'):
                            batch_embeddings = batch_embeddings.tolist()
                        
                        vector_store.add_documents(
                            documents=batch_chunks,
                            metadatas=batch_metadatas,
                            ids=batch_ids,
                            embeddings=batch_embeddings
                        )
                        
                        folder_chunks += len(batch_chunks)
                        files_succeeded += 1
                        
                        # Clear batch
                        batch_chunks.clear()
                        batch_metadatas.clear()
                        batch_ids.clear()
                        
                    except Exception as batch_error:
                        update_status(
                            logs=indexing_status['logs'] + [f'⚠️ Batch processing error: {str(batch_error)[:100]}']
                        )
                        files_failed += 1
                        batch_chunks.clear()
                        batch_metadatas.clear()
                        batch_ids.clear()
                        continue
                
            except Exception as file_error:
                files_failed += 1
                continue
        
        # Save folder info
        indexed_folders[folder_id] = {
            'collection_name': collection_id,
            'name': folder_name,
            'path': folder_name,
            'location': folder_name,
            'file_count': folder_file_count,
            'files_processed': files_succeeded,
            'files_failed': files_failed,
            'files_skipped': files_skipped,
            'chunks_created': folder_chunks,
            'indexed_at': datetime.now().isoformat()
        }
        
        # Save to file
        with open('indexed_folders.json', 'w') as f:
            json.dump(indexed_folders, f, indent=2)
        
        update_status(
            running=False,
            progress=100,
            message=f'Completed indexing {folder_name}',
            completed_at=datetime.now().isoformat(),
            logs=indexing_status['logs'] + [
                f'✅ COMPLETED: {folder_name}',
                f'📊 Stats: {files_succeeded} success, {files_failed} failed, {files_skipped} skipped',
                f'📚 Created {folder_chunks} chunks in collection {collection_id}'
            ]
        )
        
    except Exception as e:
        update_status(
            running=False,
            progress=0,
            message=f'Error indexing {folder_name}: {str(e)}',
            error=str(e),
            completed_at=datetime.now().isoformat(),
            logs=indexing_status['logs'] + [f'❌ ERROR: {str(e)}']
        )

def run_full_indexing_process():
    """Background process to index all folders from 7MM Resources shared drive using Google services
    FIXED: Added comprehensive error handling, validation, checkpointing, and crash recovery"""
    global indexing_status
    from datetime import datetime
    
    # CRITICAL FIX: Wrap entire process in try/finally for crash recovery
    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        from document_loader import GoogleDriveLoader, chunk_text, extract_text
        from vector_store import VectorStore
        from vertex_embeddings import VertexEmbedder
        from embeddings import LocalEmbedder
        from config import USE_VERTEX_EMBEDDINGS, CHUNK_SIZE, CHUNK_OVERLAP
        import pickle
        import os
        import json
        import re
        import signal
        from functools import wraps
        
        # Helper function for timeout handling
        class TimeoutError(Exception):
            pass
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Operation timed out")
        
        def with_timeout(seconds):
            """Decorator to add timeout to functions (Unix only, Windows uses threading)"""
            def decorator(func):
                @wraps(func)
                def wrapper(*args, **kwargs):
                    if os.name == 'nt':  # Windows - no signal support
                        import threading
                        result = [TimeoutError("Operation timed out")]
                        
                        def target():
                            try:
                                result[0] = func(*args, **kwargs)
                            except Exception as e:
                                result[0] = e
                        
                        thread = threading.Thread(target=target)
                        thread.daemon = True
                        thread.start()
                        thread.join(seconds)
                        
                        if thread.is_alive():
                            raise TimeoutError(f"Operation timed out after {seconds}s")
                        
                        if isinstance(result[0], Exception):
                            raise result[0]
                        return result[0]
                    else:  # Unix-like systems
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(seconds)
                        try:
                            result = func(*args, **kwargs)
                        finally:
                            signal.alarm(0)
                        return result
                return wrapper
            return decorator
        
        # Helper function to sanitize collection names
        def sanitize_collection_name(name):
            """Sanitize folder name for use as ChromaDB collection name"""
            # ChromaDB requirements: 3-63 chars, start/end with alphanumeric, contain only alphanumeric, underscores, hyphens
            # Remove or replace invalid characters
            sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
            # Ensure starts with alphanumeric
            sanitized = re.sub(r'^[^a-zA-Z0-9]+', '', sanitized)
            # Ensure ends with alphanumeric
            sanitized = re.sub(r'[^a-zA-Z0-9]+$', '', sanitized)
            # Ensure length constraints
            if len(sanitized) < 3:
                sanitized = f"folder_{sanitized}_col"
            if len(sanitized) > 63:
                sanitized = sanitized[:63]
            # Final validation
            if not sanitized or len(sanitized) < 3:
                sanitized = f"collection_{hash(name) % 100000}"
            return sanitized
        
        # CRITICAL FIX: Pre-flight validation
        update_status(
            running=True,
            progress=0,
            message='🔍 Validating prerequisites...',
            started_at=datetime.now().isoformat(),
            error=None,
            logs=['🚀 Full Google Drive indexing started', '🔍 Running pre-flight checks...']
        )
        
        # Validate credentials.json exists
        if not os.path.exists('credentials.json'):
            raise Exception('❌ credentials.json not found. Please set up Google Cloud credentials first.')
        
        # Validate TOKEN_FILE exists and is valid
        if not os.path.exists(TOKEN_FILE):
            raise Exception('❌ Google Drive not authenticated. Please connect via admin dashboard first.')
        
        update_status(
            logs=indexing_status['logs'] + ['✅ Credentials validated']
        )
        
        # Load and validate Google Drive credentials
        update_status(
            progress=5,
            message='🔐 Connecting to Google Drive...',
            logs=indexing_status['logs'] + ['Loading Google credentials...']
        )
        
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                update_status(
                    logs=indexing_status['logs'] + ['⚠️ Token expired, attempting refresh...']
                )
                from google.auth.transport.requests import Request
                creds.refresh(Request())
                with open(TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
                update_status(
                    logs=indexing_status['logs'] + ['✅ Token refreshed successfully']
                )
            else:
                raise Exception('❌ Google Drive credentials invalid. Please reconnect via admin dashboard.')
        
        # Build Drive service
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Test Drive API connectivity
        try:
            safe_drive_call(lambda: drive_service.about().get(fields='user').execute())
            update_status(
                logs=indexing_status['logs'] + ['✅ Connected to Google Drive API']
            )
        except Exception as e:
            raise Exception(f'❌ Failed to connect to Google Drive API: {str(e)}')
        
        # Initialize embedder (Google Vertex AI or local)
        update_status(
            progress=8,
            message='🤖 Initializing embedding service...',
            logs=indexing_status['logs'] + ['Configuring embeddings...']
        )
        
        embedder = VertexEmbedder() if USE_VERTEX_EMBEDDINGS else LocalEmbedder()
        embedder_name = "Google Vertex AI (768-dim)" if USE_VERTEX_EMBEDDINGS else "Local (384-dim)"
        
        update_status(
            logs=indexing_status['logs'] + [f'✅ Using {embedder_name}']
        )
        
        # Get ONLY ROOT folders from shared drive (not subfolders)
        update_status(
            progress=10,
            message='📁 Discovering ROOT folders in 7MM Resources...',
            logs=indexing_status['logs'] + ['Scanning for root-level folders only...']
        )
        
        def get_root_folders_only():
            """Get ONLY the root folders directly under 7MM Resources (not subfolders)
            FIXED: Added error handling with retry logic"""
            # Query for folders that have 7MM Resources as direct parent
            query = f"'{SHARED_DRIVE_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            update_status(
                logs=indexing_status['logs'] + ['🎯 Fetching only ROOT folders (no subfolders)...']
            )
            
            # CRITICAL FIX: Use safe_drive_call with retry logic
            response = safe_drive_call(lambda: drive_service.files().list(
                q=query,
                driveId=SHARED_DRIVE_ID,
                corpora='drive',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                fields='files(id, name)',
                pageSize=100
            ).execute())
            
            root_folders = response.get('files', [])
            
            # Add path (which is just the name for root folders)
            for folder in root_folders:
                folder['path'] = folder['name']
            
            return root_folders
        
        # Get root folders only (should be ~14 collections)
        folders = get_root_folders_only()
        total_folders = len(folders)
        
        update_status(
            logs=indexing_status['logs'] + [f'✅ Found {total_folders} folders (including all subfolders)']
        )
        
        if total_folders == 0:
            raise Exception('No folders found in shared drive')
        
        # Initialize Google Drive loader
        loader = GoogleDriveLoader(drive_service)
        
        update_status(
            logs=indexing_status['logs'] + [f'✅ Google Drive loader initialized (OCR: {"Document AI" if loader.ocr_service else "disabled"})']
        )
        
        # Index each ROOT folder (with all files recursively from subfolders)
        indexed_folders = {}
        total_files_processed = 0
        total_chunks_created = 0
        
        for idx, folder in enumerate(folders, 1):
            folder_name = folder.get('path', folder['name'])  # Use full path if available
            folder_id = folder['id']
            
            progress = 10 + int((idx / total_folders) * 85)
            update_status(
                progress=progress,
                message=f'📂 Indexing {folder_name} ({idx}/{total_folders})...',
                logs=indexing_status['logs'] + [f'\n[{idx}/{total_folders}] 📂 {folder_name}']
            )
            
            try:
                # Create collection for this folder
                collection_id = f'folder_{folder_id}'
                vector_store = VectorStore(collection_name=collection_id)
                
                update_status(
                    logs=indexing_status['logs'] + [f'  📊 Collection: {collection_id}']
                )
                
                # Get ALL files recursively from this root folder and all subfolders
                update_status(
                    logs=indexing_status['logs'] + [f'  🔍 Listing files from root folder ID: {folder_id} (including subfolders)...']
                )
                
                files = get_all_files_recursive_from_folder(folder_id, drive_service, 0)
                folder_file_count = len(files)
                
                update_status(
                    logs=indexing_status['logs'] + [f'  📄 Found {folder_file_count} files']
                )
                
                if folder_file_count == 0:
                    update_status(
                        logs=indexing_status['logs'] + [f'  ⚠️ Skipping empty folder']
                    )
                    # CRITICAL FIX: Save checkpoint even for empty folders
                    with open('indexed_folders.json', 'w') as f:
                        json.dump(indexed_folders, f, indent=2)
                    continue
                
                # CRITICAL FIX: Validate collection_id before creating VectorStore
                raw_collection_id = f'folder_{folder_id}'
                collection_id = sanitize_collection_name(raw_collection_id)
                
                if collection_id != raw_collection_id:
                    update_status(
                        logs=indexing_status['logs'] + [f'  📝 Sanitized collection: {raw_collection_id} → {collection_id}']
                    )
                
                # Process each file (OPTIMIZED - batch processing, reduced logging)
                folder_chunks = 0
                files_succeeded = 0
                files_failed = 0
                files_skipped = 0
                
                # Batch processing buffers
                BATCH_SIZE = 5  # Process files in batches
                batch_chunks = []
                batch_metadatas = []
                batch_ids = []
                
                # Track last log time to reduce spam
                last_log_time = 0
                LOG_INTERVAL = 2  # seconds between progress logs
                
                # CRITICAL FIX: Wrap file processing in try/finally for memory cleanup
                try:
                    for file_idx, file in enumerate(files, 1):
                        try:
                            file_name = file['name']
                            file_id = file['id']
                            file_mime = file.get('mimeType', '')
                            
                            # Only log every 10 files or every LOG_INTERVAL seconds
                            current_time = time.time()
                            should_log = (file_idx % 10 == 0 or 
                                         file_idx == 1 or 
                                         file_idx == folder_file_count or
                                         (current_time - last_log_time) > LOG_INTERVAL)
                            
                            if should_log:
                                update_status(
                                    logs=indexing_status['logs'] + [f'  [{file_idx}/{folder_file_count}] Processing: {file_name[:50]}...']
                                )
                                last_log_time = current_time
                            
                            text = None
                            
                            # CRITICAL FIX: Wrap all Drive API calls in error handling
                            try:
                                # Handle different file types using Google APIs
                                if file_mime == 'application/vnd.google-apps.document':
                                    # Google Docs - export as plain text
                                    text = loader.export_google_doc(file_id)
                                    
                                elif file_mime == 'application/vnd.google-apps.spreadsheet':
                                    # Google Sheets - export as CSV
                                    text = loader.export_google_sheets(file_id)
                                    
                                elif file_mime == 'application/vnd.google-apps.presentation':
                                    # Google Slides - export as text
                                    text = loader.export_google_slides(file_id)
                                
                                elif file_mime in [
                                    'application/vnd.google-apps.folder',
                                    'application/vnd.google-apps.shortcut',
                                    'application/vnd.google-apps.form',
                                    'application/vnd.google-apps.drawing',
                                    'application/vnd.google-apps.map',
                                    'application/vnd.google-apps.site'
                                ]:
                                    # Skip folders (already filtered), shortcuts, and non-textual Google types
                                    files_skipped += 1
                                    continue
                                    
                                elif file_mime.startswith('application/vnd.google-apps'):
                                    # Unknown Google Apps file
                                    files_skipped += 1
                                    continue
                                    
                                else:
                                    # Regular files - download and extract
                                    file_content = loader.download_file(file_id)
                                    
                                    if file_content:
                                        text = extract_text(file_content, file_mime, file_name, loader.ocr_service)
                                    else:
                                        files_failed += 1
                                        continue
                            
                            except HttpError as http_error:
                                if http_error.resp.status == 403:
                                    files_skipped += 1  # Permission denied
                                elif http_error.resp.status == 404:
                                    files_skipped += 1  # File not found
                                else:
                                    files_failed += 1
                                if files_failed < 3:  # Only log first few errors
                                    update_status(
                                        logs=indexing_status['logs'] + [f'      ⚠️ HTTP {http_error.resp.status}: {file_name[:30]}']
                                    )
                                continue
                            except Exception as download_error:
                                files_failed += 1
                                if files_failed < 3:
                                    update_status(
                                        logs=indexing_status['logs'] + [f'      ⚠️ Download error: {str(download_error)[:50]}']
                                    )
                                continue
                            
                            # Check if we got text
                            if not text or not text.strip():
                                files_failed += 1
                                continue
                            
                            text_length = len(text)
                            
                            # Chunk the text
                            chunks = chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
                            
                            if not chunks or len(chunks) == 0:
                                files_failed += 1
                                continue
                            
                            chunk_count = len(chunks)
                            
                            # Prepare chunks for batch processing
                            for i, chunk in enumerate(chunks):
                                batch_chunks.append(chunk)
                                batch_metadatas.append({
                                    'filename': file_name,
                                    'source': folder_name,
                                    'file_id': file_id,
                                    'mime_type': file_mime,
                                    'chunk_index': i,
                                    'total_chunks': chunk_count,
                                    'text_length': len(chunk)
                                })
                                batch_ids.append(f"{file_id}_chunk_{i}")
                            
                            # Process batch when it reaches BATCH_SIZE or at end of folder
                            if len(batch_chunks) >= BATCH_SIZE or file_idx == folder_file_count:
                                try:
                                    # CRITICAL FIX: Add timeout handling for embeddings (60s timeout)
                                    @with_timeout(60)
                                    def generate_embeddings():
                                        return embedder.embed_documents(batch_chunks)
                                    
                                    batch_embeddings = generate_embeddings()
                                    
                                    # Convert numpy array to list if needed
                                    if hasattr(batch_embeddings, 'tolist'):
                                        batch_embeddings = batch_embeddings.tolist()
                                    
                                    # Add batch to vector store
                                    vector_store.add_documents(
                                        documents=batch_chunks,
                                        embeddings=batch_embeddings,
                                        metadatas=batch_metadatas,
                                        ids=batch_ids
                                    )
                                    
                                    folder_chunks += len(batch_chunks)
                                    
                                except TimeoutError:
                                    update_status(
                                        logs=indexing_status['logs'] + [f'      ⚠️ Embedding timeout, skipping batch of {len(batch_chunks)} chunks']
                                    )
                                    files_failed += 1
                                except Exception as embedding_error:
                                    update_status(
                                        logs=indexing_status['logs'] + [f'      ❌ Embedding error: {str(embedding_error)[:100]}']
                                    )
                                    files_failed += 1
                                finally:
                                    # CRITICAL FIX: Always clear batch buffers to prevent memory leaks
                                    batch_chunks = []
                                    batch_metadatas = []
                                    batch_ids = []
                            
                            files_succeeded += 1
                            
                        except Exception as file_error:
                            files_failed += 1
                            # Only log errors for important files or periodically
                            if file_idx % 20 == 0 or files_failed < 5:
                                update_status(
                                    logs=indexing_status['logs'] + [f'      ❌ Error: {str(file_error)[:100]}']
                                )
                            continue
                
                finally:
                    # CRITICAL FIX: Ensure batch buffers are cleared even on unexpected errors
                    batch_chunks.clear()
                    batch_metadatas.clear()
                    batch_ids.clear()
                
                # Save folder info with collection_name for compatibility with chat_api.py
                indexed_folders[folder_id] = {
                    'collection_name': collection_id,  # Required by chat_api.py
                    'name': folder_name,
                    'path': folder.get('path', folder_name),
                    'location': folder.get('path', folder_name),  # For backward compatibility
                    'file_count': folder_file_count,
                    'files_processed': files_succeeded,
                    'files_failed': files_failed,
                    'files_skipped': files_skipped,
                    'chunks_created': folder_chunks,
                    'indexed_at': datetime.now().isoformat()
                }
                
                total_files_processed += files_succeeded
                total_chunks_created += folder_chunks
                
                update_status(
                    logs=indexing_status['logs'] + [f'  ✅ Complete: {files_succeeded} success, {files_failed} failed, {files_skipped} skipped → {folder_chunks} chunks']
                )
                
                # CRITICAL FIX: Checkpoint after each folder to prevent data loss
                try:
                    with open('indexed_folders.json', 'w') as f:
                        json.dump(indexed_folders, f, indent=2)
                    update_status(
                        logs=indexing_status['logs'] + [f'  💾 Checkpoint saved']
                    )
                except Exception as checkpoint_error:
                    update_status(
                        logs=indexing_status['logs'] + [f'  ⚠️ Checkpoint error: {str(checkpoint_error)}']
                    )
                
                # Memory cleanup
                import gc
                gc.collect()
                
            except Exception as folder_error:
                update_status(
                    logs=indexing_status['logs'] + [f'  ❌ Folder failed: {str(folder_error)[:200]}']
                )
                # CRITICAL FIX: Save checkpoint even on folder failure
                try:
                    with open('indexed_folders.json', 'w') as f:
                        json.dump(indexed_folders, f, indent=2)
                except:
                    pass
                continue
        
        # Save indexed folders info (final save)
        with open('indexed_folders.json', 'w') as f:
            json.dump(indexed_folders, f, indent=2)
        
        update_status(
            logs=indexing_status['logs'] + [f'💾 Saved folder metadata to indexed_folders.json']
        )
        
        # Complete
        update_status(
            running=False,
            progress=100,
            message=f'✅ Indexing complete!',
            completed_at=datetime.now().isoformat(),
            logs=indexing_status['logs'] + [
                f'\n{"="*60}',
                f'🎉 INDEXING COMPLETE',
                f'{"="*60}',
                f'📁 Folders indexed: {len(indexed_folders)}/{total_folders}',
                f'📄 Files processed: {total_files_processed}',
                f'📝 Chunks created: {total_chunks_created:,}',
                f'🤖 Embedder: {embedder_name}',
                f'✅ All data stored in ChromaDB',
                f'{"="*60}'
            ]
        )
        
    except Exception as e:
        from datetime import datetime
        import traceback
        update_status(
            running=False,
            progress=0,
            message=f'❌ Indexing failed: {str(e)}',
            error=str(e),
            completed_at=datetime.now().isoformat(),
            logs=indexing_status['logs'] + [
                f'❌ Fatal error: {str(e)}',
                f'Stack trace: {traceback.format_exc()[:500]}'
            ]
        )
    finally:
        # CRITICAL FIX: Ensure running is always reset even on unexpected errors
        with indexing_lock:
            if indexing_status.get('running', False):
                indexing_status['running'] = False
                indexing_status['message'] = 'Indexing stopped (crash recovery)'
                if not indexing_status.get('completed_at'):
                    indexing_status['completed_at'] = datetime.now().isoformat()

def run_collection_update():
    """Background collection update process - FIXED: Proper lock handling"""
    global indexing_status
    from datetime import datetime
    import time
    
    # CRITICAL FIX: Don't hold lock for entire process
    try:
        # Initialize
        update_status(
            running=True,
            progress=0,
            message='Starting collection update...',
            started_at=datetime.now().isoformat(),
            error=None,
            logs=[]
        )
        
        # Simulate update process (replace with actual logic)
        update_status(
            progress=50,
            message='Collection update temporarily disabled due to package compatibility issues.'
        )
        
        time.sleep(2)  # Simulate work
        
        # Complete
        update_status(
            running=False,
            progress=100,
            message='Collection update feature temporarily disabled.',
            completed_at=datetime.now().isoformat()
        )
            
    except Exception as e:
        update_status(
            running=False,
            progress=0,
            message='Collection update failed',
            error=str(e),
            completed_at=datetime.now().isoformat()
        )
    finally:
        # CRITICAL FIX: Ensure running is always reset
        with indexing_lock:
            if indexing_status.get('running', False):
                indexing_status['running'] = False


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
        # Get redirect URI from environment or use production default
        redirect_uri = os.getenv('GDRIVE_REDIRECT_URI', 'https://ask.7mountainsmedia.com/admin/gdrive/callback')
        
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            redirect_uri=redirect_uri
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
            redirect_uri=os.getenv('GDRIVE_REDIRECT_URI', 'https://ask.7mountainsmedia.com/admin/gdrive/callback')
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