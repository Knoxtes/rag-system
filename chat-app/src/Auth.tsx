import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || process.env.REACT_APP_API_BASE_URL || 'http://localhost:3000';

// Create Auth Context
const AuthContext = createContext<{
  user: any;
  isAuthenticated: boolean;
  login: () => void;
  logout: () => void;
  loading: boolean;
} | null>(null);

// Auth Provider Component
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check if user just completed OAuth authentication
    const urlParams = new URLSearchParams(window.location.search);
    const authComplete = urlParams.get('auth_complete');
    const fromAdmin = urlParams.get('from_admin');
    
    console.log('Auth component mounted');
    console.log('URL params check - authComplete:', authComplete, 'fromAdmin:', fromAdmin);
    console.log('Current URL:', window.location.href);
    
    // Always check auth status on component mount
    checkAuthStatus();
    
    if (authComplete === 'true' || fromAdmin === 'true') {
      console.log('Authentication completion detected, cleaning URL...');
      // Clear the URL parameters to clean up the URL
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
    }
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('rag_auth_token');
      console.log('Checking auth status. Token found:', !!token);
      
      if (!token) {
        console.log('No token found in localStorage');
        setLoading(false);
        return;
      }

      console.log('Token found, verifying with backend...');
      
      // Verify token with backend
      const response = await axios.post(`${API_BASE_URL}/auth/verify`, {
        token
      });

      console.log('Auth verification response:', response.data);

      if (response.data.valid) {
        console.log('Token is valid. User authenticated:', response.data.user);
        setUser(response.data.user);
        setIsAuthenticated(true);
        
        // Set default authorization header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        
        // Store user info in consistent format
        localStorage.setItem('rag_auth_token', token); // Keep backward compatibility
        console.log('Authentication successful!');
      } else {
        console.log('Token invalid, clearing stored data');
        // Token invalid, clear it
        localStorage.removeItem('rag_auth_token');
        localStorage.removeItem('user_info');
        delete axios.defaults.headers.common['Authorization'];
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      console.log('Clearing stored auth data due to error');
      localStorage.removeItem('rag_auth_token');
      localStorage.removeItem('user_info');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
      console.log('Auth check completed');
    }
  };

  const login = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/auth/login`);
      window.location.href = response.data.auth_url;
    } catch (error) {
      console.error('Login failed:', error);
      alert('Failed to initiate login. Please try again.');
    }
  };

  const logout = async () => {
    try {
      await axios.post(`${API_BASE_URL}/auth/logout`);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('rag_auth_token');
      localStorage.removeItem('user_info');
      localStorage.removeItem('is_admin'); // Clear admin flag
      delete axios.defaults.headers.common['Authorization'];
      setUser(null);
      setIsAuthenticated(false);
      window.location.reload();
    }
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Login Component
export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const handleLogin = async () => {
    setIsLoggingIn(true);
    await login();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 text-center">
        <div className="mb-8">
          <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">RAG Chat Assistant</h1>
          <p className="text-gray-600">Secure document intelligence for your organization</p>
        </div>

        <div className="mb-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-center mb-2">
              <svg className="w-5 h-5 text-blue-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-blue-700 font-medium">Organization Access Only</span>
            </div>
            <p className="text-blue-600 text-sm">
              Please sign in with your organization Google account to access the document assistant.
            </p>
          </div>

          <button
            onClick={handleLogin}
            disabled={isLoggingIn}
            className="w-full bg-white border-2 border-gray-300 hover:border-gray-400 focus:border-blue-500 rounded-lg px-6 py-3 flex items-center justify-center transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoggingIn ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Redirecting...
              </div>
            ) : (
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Sign in with Google
              </div>
            )}
          </button>
        </div>

        <div className="text-xs text-gray-500">
          <p className="mb-1">🔒 Secure authentication via Google OAuth 2.0</p>
          <p>📋 Access to indexed organizational documents</p>
        </div>
      </div>
    </div>
  );
};

// User Menu Component
export const UserMenu: React.FC = () => {
  const { user, logout } = useAuth();
  const [showMenu, setShowMenu] = useState(false);

  if (!user) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="flex items-center space-x-2 text-gray-300 hover:text-white transition-colors"
      >
        <img
          src={user.picture || '/api/placeholder/32/32'}
          alt={user.name}
          className="w-8 h-8 rounded-full"
        />
        <span className="hidden md:block text-sm">{user.name}</span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {showMenu && (
        <div className="absolute right-0 mt-2 w-48 bg-dark-700 rounded-lg shadow-lg border border-dark-600 z-50">
          <div className="p-3 border-b border-dark-600">
            <p className="text-sm text-white font-medium">{user.name}</p>
            <p className="text-xs text-gray-400">{user.email}</p>
            {user.is_admin && (
              <span className="inline-block mt-1 px-2 py-1 text-xs bg-blue-600 text-white rounded-full">
                Admin
              </span>
            )}
          </div>
          {user.is_admin && (
            <a
              href="/admin/dashboard"
              className="block px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-dark-600 transition-colors border-b border-dark-600"
              onClick={() => setShowMenu(false)}
            >
              🛠️ Admin Dashboard
            </a>
          )}
          <button
            onClick={() => {
              setShowMenu(false);
              logout();
            }}
            className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-dark-600 transition-colors"
          >
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
};