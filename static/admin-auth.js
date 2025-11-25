// Admin authentication and dashboard loading script
let authCheckAttempts = 0;
const maxAuthCheckAttempts = 3;

async function checkAuth() {
    authCheckAttempts = authCheckAttempts + 1;
    const token = localStorage.getItem('authToken');

    const debugInfo = document.getElementById('debug-info');
    const loadingMessage = document.getElementById('loading-message');
    
    console.log('Auth check attempt ' + authCheckAttempts + ':');
    console.log('- Token found:', !!token);
    console.log('- Token preview:', token ? token.substring(0, 20) + '...' : 'none');
    console.log('- URL params:', window.location.search);
    
    debugInfo.textContent = 'Attempt ' + authCheckAttempts + '/' + maxAuthCheckAttempts + ' - Token: ' + (token ? 'Found' : 'Not found');
    
    if (!token) {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('auth_complete') === 'true' && authCheckAttempts < maxAuthCheckAttempts) {
            console.log('Just came from OAuth, retrying auth check in 1 second...');
            loadingMessage.textContent = 'Waiting for authentication token... (' + authCheckAttempts + '/' + maxAuthCheckAttempts + ')';
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
            debugInfo.textContent = 'Welcome ' + (data.user.name || data.user.email) + '!';
            console.log('Auth successful, loading dashboard...');
            await loadDashboard();
            return true;
        } else if (data.valid && data.user && !data.user.is_admin) {
            console.log('Valid user but not admin - redirecting to chat');
            loadingMessage.textContent = 'Authenticated user - redirecting to chat interface...';
            debugInfo.textContent = 'Welcome ' + (data.user.name || data.user.email) + '! You are not an admin user.';
            
            setTimeout(() => {
                window.location.href = '/?from_admin=true';
            }, 2000);
            return false;
        } else {
            console.log('Auth failed - not valid admin:', data);
            debugInfo.textContent = 'Auth failed: ' + (data.error || 'Not valid user') + ' (User: ' + (data.user?.email || 'unknown') + ')';

            if (data.user && !data.user.is_admin) {
                document.getElementById('auth-error-message').textContent = 
                    'Hi ' + (data.user.name || data.user.email) + '! This is the admin dashboard. You can access the chat interface instead.';
            }
            
            showAuthError();
            return false;
        }
    } catch (error) {
        console.error('Auth check error:', error);

        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('auth_complete') === 'true' && authCheckAttempts < maxAuthCheckAttempts) {
            console.log('Network error after OAuth, retrying in 2 seconds...');
            loadingMessage.textContent = 'Network error, retrying... (' + authCheckAttempts + '/' + maxAuthCheckAttempts + ')';
            debugInfo.textContent = 'Error: ' + error.message;
            setTimeout(checkAuth, 2000);
            return false;
        }
        
        debugInfo.textContent = 'Auth error: ' + error.message;
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
        const cacheBust = new Date().getTime();
        const response = await fetch('/admin/dashboard-content?v=' + cacheBust, {
            headers: { 
                'Authorization': 'Bearer ' + token,
                'Cache-Control': 'no-cache'
            }
        });
        
        if (response.ok) {
            const html = await response.text();
            document.getElementById('loading-screen').style.display = 'none';
            const contentDiv = document.getElementById('dashboard-content');
            contentDiv.innerHTML = html;
            contentDiv.style.display = 'block';

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
        } else {
            showAuthError();
        }
    } catch (error) {
        console.error('Dashboard load error:', error);
        showAuthError();
    }
}

document.addEventListener('DOMContentLoaded', checkAuth);
