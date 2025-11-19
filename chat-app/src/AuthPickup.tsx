import React, { useEffect } from 'react';
import { Loader2 } from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_API_URL || process.env.REACT_APP_API_BASE_URL || 'http://localhost:3000';

const AuthPickup: React.FC = () => {
  useEffect(() => {
    const pickupTokens = async () => {
      try {
        console.log('AuthPickup: Attempting to pickup tokens from Flask server...');
        
        const response = await fetch(`${API_BASE_URL}/auth/pickup`, {
          method: 'GET',
          credentials: 'include', // Important for session cookies
        });

        console.log('AuthPickup: Response status:', response.status);
        const data = await response.json();
        console.log('AuthPickup: Response data:', data);

        if (response.ok && data.success) {
          console.log('AuthPickup: Tokens retrieved successfully');
          console.log('AuthPickup: User email:', data.user_info.email);
          
          // Store the tokens in localStorage
          localStorage.setItem('rag_auth_token', data.token);
          localStorage.setItem('user_info', JSON.stringify(data.user_info));
          localStorage.setItem('is_admin', data.is_admin.toString());
          
          console.log('AuthPickup: Tokens stored in localStorage');
          
          // Redirect to main app
          setTimeout(() => {
            console.log('AuthPickup: Redirecting to main app...');
            window.location.href = '/';
          }, 500);
          
        } else {
          console.error('AuthPickup: Failed to pickup tokens:', data);
          // Redirect back to login
          setTimeout(() => {
            console.log('AuthPickup: Redirecting to login due to error...');
            window.location.href = '/?auth_error=pickup_failed';
          }, 2000);
        }
      } catch (error) {
        console.error('AuthPickup: Error picking up tokens:', error);
        // Redirect back to login
        setTimeout(() => {
          console.log('AuthPickup: Redirecting to login due to error...');
          window.location.href = '/?auth_error=network_error';
        }, 2000);
      }
    };

    pickupTokens();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 text-center">
        <div className="mb-8">
          <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <Loader2 className="w-10 h-10 text-white animate-spin" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Completing Authentication</h1>
          <p className="text-gray-600">Please wait while we finalize your login...</p>
        </div>

        <div className="flex items-center justify-center space-x-2 text-gray-500">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
          <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" style={{ animationDelay: '0.1s' }}></div>
          <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
        </div>

        <div className="mt-6 text-xs text-gray-500">
          <p>This should only take a moment...</p>
        </div>
      </div>
    </div>
  );
};

export default AuthPickup;