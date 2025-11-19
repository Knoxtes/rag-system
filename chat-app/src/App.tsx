import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, FileText, ExternalLink, Database, Loader2, Folder, FolderOpen, Search, ChevronRight, ChevronDown, Sun, Moon, Download } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import axios from 'axios';
import { AuthProvider, useAuth, LoginPage } from './Auth';
import AuthPickup from './AuthPickup';

const API_BASE_URL = process.env.REACT_APP_API_URL || process.env.REACT_APP_API_BASE_URL || 'http://localhost:3000';

// Debug logging for API configuration
console.log('API_BASE_URL configured as:', API_BASE_URL);
console.log('Environment variables:', {
  REACT_APP_API_URL: process.env.REACT_APP_API_URL,
  REACT_APP_API_BASE_URL: process.env.REACT_APP_API_BASE_URL,
  NODE_ENV: process.env.NODE_ENV
});

// Configure axios interceptors for auth
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('rag_auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('rag_auth_token');
      localStorage.removeItem('user_info');
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

interface Document {
  filename: string;
  url: string;
  type: string;
  extension: string;
}

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  documents?: Document[];
  isLoading?: boolean;
}

interface Collection {
  name: string;
  location: string;
  files_processed: number;
  indexed_at: string;
  is_combined?: boolean;
}

interface FolderItem {
  id: string;
  name: string;
  type: 'folder' | 'file';
  mimeType: string;
  webViewLink: string;
  hasChildren: boolean;
  parent_id: string;
  children?: FolderItem[];
  isLoaded?: boolean;
  isExpanded?: boolean;
  isSearchResult?: boolean;
  isPrefetched?: boolean;
  isPreloading?: boolean;
}

// Folder Tree Component
const FolderTreeItem: React.FC<{
  item: FolderItem;
  onToggle: (id: string) => void;
  onFileSelect: (file: FolderItem) => void;
  level: number;
  selectedFileId?: string | null;
}> = ({ item, onToggle, onFileSelect, level, selectedFileId }) => {
  const handleToggle = () => {
    if (item.type === 'folder' && !item.isSearchResult) {
      onToggle(item.id);
    } else {
      onFileSelect(item);
    }
  };

  const paddingLeft = level * 16; // 16px per level

  // Get appropriate icon based on file type
  const getFileIcon = () => {
    if (item.type === 'folder') {
      return item.isExpanded ? (
        <FolderOpen className="w-4 h-4 mr-2 text-blue-400" />
      ) : (
        <Folder className="w-4 h-4 mr-2 text-blue-400" />
      );
    }
    
    // File type icons based on mimeType
    const mimeType = item.mimeType;
    if (mimeType.includes('pdf')) {
      return <FileText className="w-4 h-4 mr-2 text-red-400" />;
    } else if (mimeType.includes('document') || mimeType.includes('word')) {
      return <FileText className="w-4 h-4 mr-2 text-blue-400" />;
    } else if (mimeType.includes('spreadsheet') || mimeType.includes('excel')) {
      return <FileText className="w-4 h-4 mr-2 text-green-400" />;
    } else if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) {
      return <FileText className="w-4 h-4 mr-2 text-orange-400" />;
    } else if (mimeType.includes('image')) {
      return <FileText className="w-4 h-4 mr-2 text-purple-400" />;
    }
    
    return <FileText className="w-4 h-4 mr-2 text-gray-400" />;
  };



  const isSelected = item.type === 'file' && selectedFileId === item.id;

  return (
    <div style={{ paddingLeft: `${paddingLeft}px` }}>
      <div 
        className={`flex items-center py-1 px-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded cursor-pointer transition-colors duration-200 ${
          item.isSearchResult ? 'bg-gray-200 dark:bg-gray-800/50' : ''
        } ${
          isSelected ? 'bg-brand-green/20 dark:bg-blue-900/40 border border-brand-green dark:border-blue-500/50' : ''
        }`}
        onClick={handleToggle}
        title={item.name}
      >
        {item.type === 'folder' && !item.isSearchResult && (
          <span className="mr-2 text-brand-dark dark:text-gray-400">
            {item.isPreloading ? (
              <div className="w-4 h-4 animate-spin">
                <div className="w-3 h-3 border border-brand-green dark:border-blue-400 border-t-transparent rounded-full"></div>
              </div>
            ) : item.isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </span>
        )}
        
        {getFileIcon()}
        
        <div className="flex-1 min-w-0">
          <span className={`text-sm truncate block ${
            item.isPrefetched ? 'text-brand-green dark:text-green-200' : 'text-brand-dark dark:text-gray-200'
          }`}>
            {item.name}
          </span>
        </div>
        
        {item.isPrefetched && (
          <span className="text-xs text-brand-green dark:text-green-400 ml-2 flex-shrink-0" title="Prefetched for faster access">⚡</span>
        )}
        
        {item.isSearchResult && (
          <Search className="w-3 h-3 text-yellow-400 flex-shrink-0 ml-1" />
        )}
      </div>
      
      {item.type === 'folder' && item.isExpanded && item.children && !item.isSearchResult && (
        <div>
          {item.children.map(child => (
            <FolderTreeItem
              key={child.id}
              item={child}
              onToggle={onToggle}
              onFileSelect={onFileSelect}
              level={level + 1}
              selectedFileId={selectedFileId}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const ChatApp: React.FC = () => {
  const { isAuthenticated } = useAuth();
  
  // Theme state with localStorage persistence
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('rag_theme');
    return (saved as 'light' | 'dark') || 'dark';
  });

  // Apply theme to document root
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('rag_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [collections, setCollections] = useState<Record<string, Collection>>({});
  const [selectedCollection, setSelectedCollection] = useState<string>('');
  const [isCollectionSwitching, setIsCollectionSwitching] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [initComplete, setInitComplete] = useState(false);
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFolders, setShowFolders] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FolderItem | null>(null);
  const [cacheInfo, setCacheInfo] = useState<{total_entries: number; cached_responses: number}>({total_entries: 0, cached_responses: 0});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const initializeApp = useCallback(async () => {
    try {
      console.log('🚀 Initializing app...');
      console.log('🌐 API Base URL:', API_BASE_URL);
      
      // Check health with retry logic
      let healthResponse;
      let retries = 0;
      const maxRetries = 5; // Increased retries
      
      while (retries < maxRetries) {
        try {
          console.log(`🔍 Health check attempt ${retries + 1}/${maxRetries}...`);
          healthResponse = await axios.get(`${API_BASE_URL}/api/health`, { 
            timeout: 15000, // Increased timeout
            headers: {
              'Cache-Control': 'no-cache',
              'Pragma': 'no-cache'
            }
          });
          console.log('✅ Health check successful:', healthResponse.data);
          break;
        } catch (error: any) {
          retries++;
          console.log(`❌ Health check attempt ${retries} failed:`, {
            message: error.message,
            status: error.response?.status,
            data: error.response?.data,
            url: `${API_BASE_URL}/api/health`
          });
          if (retries < maxRetries) {
            const delay = Math.min(2000 * retries, 10000); // Exponential backoff
            console.log(`⏳ Waiting ${delay}ms before retry...`);
            await new Promise(resolve => setTimeout(resolve, delay));
          } else {
            throw error;
          }
        }
      }

      // Check if RAG is properly initialized
      const ragInitialized = healthResponse?.data?.rag_initialized;
      const backendStatus = healthResponse?.data?.flask_backend;
      
      console.log('🤖 RAG Status:', { ragInitialized, backendStatus });
      
      setIsConnected(ragInitialized === true && backendStatus === 'healthy');

      // Get available collections
      console.log('📚 Loading collections...');
      const collectionsResponse = await axios.get(`${API_BASE_URL}/collections`);
      const fetchedCollections = collectionsResponse.data.collections;
      
      console.log('✅ Collections loaded:', Object.keys(fetchedCollections).length);
      
      // Add ALL_COLLECTIONS option if there are multiple collections
      const collectionsWithAll = {
        ...fetchedCollections,
        ...(Object.keys(fetchedCollections).filter(k => k !== 'ALL_COLLECTIONS').length > 1 ? {
          'ALL_COLLECTIONS': {
            name: 'All Collections',
            location: 'Multi-collection search',
            files_processed: Object.values(fetchedCollections)
              .filter((col: any) => !col.is_combined)
              .reduce((sum: number, col: any) => sum + col.files_processed, 0),
            indexed_at: 'Combined',
            is_combined: true
          }
        } : {})
      };
      
      setCollections(collectionsWithAll);
      
      // Set ALL_COLLECTIONS as default if available, otherwise first collection
      if (collectionsWithAll['ALL_COLLECTIONS']) {
        setSelectedCollection('ALL_COLLECTIONS');
      } else {
        const firstCollection = Object.keys(collectionsWithAll)[0];
        if (firstCollection) {
          setSelectedCollection(firstCollection);
        }
      }

      // Note: Folders will be loaded separately after authentication is complete

      // For welcome message, count actual collections (excluding ALL_COLLECTIONS)
      const actualCollections = Object.keys(collectionsWithAll).filter(k => k !== 'ALL_COLLECTIONS');
      const welcomeMessage: Message = {
        id: Date.now().toString(),
        text: `Welcome to 7 Mountains Media Ask Assistant! 🤖\n\nI'm ready to help you find information from your ${actualCollections.length} indexed collections. Ask me anything about your business processes, documents, or data.`,
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages([welcomeMessage]);
      setInitComplete(true);
      console.log('✅ App initialization completed!');

    } catch (error: any) {
      console.error('❌ Failed to initialize app:', error);
      console.error('🔍 Error details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.config?.url,
        timeout: error.code === 'ECONNABORTED'
      });
      
      setIsConnected(false);
      
      // Show a user-friendly message with specific error info
      const errorMessage = error.response?.status 
        ? `⚠️ **Backend Connection Issue (${error.response.status})**\n\nServer returned: ${error.response.status} ${error.response.statusText}\n\nURL: ${API_BASE_URL}\n\n*Please check if the server is running and try refreshing.*`
        : '⚠️ **Backend Connection Issue**\n\nThe system is starting up or the server may be unreachable.\n\n*Please wait a moment and try refreshing the page.*';
      
      setMessages([{
        id: `error-${Date.now()}`,
        text: errorMessage,
        sender: 'assistant' as const,
        timestamp: new Date()
      }]);
      
      // Retry connection after a delay
      setTimeout(() => {
        console.log('🔄 Retrying app initialization...');
        initializeApp();
      }, 15000); // Increased retry delay
    }
  }, []);

  // Initialize app when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      console.log('User authenticated, initializing app...');
      if (!initComplete) {
        initializeApp();
      }
    }
  }, [isAuthenticated, initializeApp, initComplete]);

  // Initial app initialization (without folders)
  useEffect(() => {
    initializeApp();
  }, [initializeApp]);

  // Enhanced batch loading for multiple folders
  const loadFoldersBatch = async (folderIds: string[]) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/folders/batch`, {
        folder_ids: folderIds
      }, { timeout: 20000 });
      
      return response.data;
    } catch (error) {
      console.error('Failed to batch load folders:', error);
      return {};
    }
  };

  // Enhanced progressive folder loading with prefetching
  const loadFolders = useCallback(async (parentId: string = '') => {
    try {
      const response = await axios.get(`${API_BASE_URL}/folders`, {
        params: { parent_id: parentId }
      });
      
      // Track cache usage
      if (response.data.cached) {
        setCacheInfo(prev => ({
          total_entries: prev.total_entries,
          cached_responses: prev.cached_responses + 1
        }));
      }
      
      if (parentId === '') {
        // Loading root folders with smart prefetching
        const rootFolders = response.data.items.map((item: any) => ({
          ...item,
          isExpanded: false,
          isLoaded: false,
          children: [],
          isPrefetched: false,
          isPreloading: false
        }));
        setFolders(rootFolders);
        
        // Intelligent prefetching: Load top 5 most likely folders in background
        const priorityFolders = rootFolders.slice(0, 5).map((folder: any) => folder.id);
        if (priorityFolders.length > 0) {
          setTimeout(() => {
            console.log('🚀 Starting smart prefetch for popular folders...');
            const startTime = performance.now();
            
            loadFoldersBatch(priorityFolders).then(batchResults => {
              setFolders(prevFolders => 
                prevFolders.map(folder => {
                  if (batchResults[folder.id]?.items) {
                    return {
                      ...folder,
                      children: batchResults[folder.id].items.map((item: any) => ({
                        ...item,
                        isExpanded: false,
                        isLoaded: false,
                        children: []
                      })),
                      isLoaded: true,
                      isPrefetched: true
                    };
                  }
                  return folder;
                })
              );
              
              const prefetchTime = performance.now() - startTime;
              console.log(`✨ Prefetched ${priorityFolders.length} folders in ${prefetchTime.toFixed(1)}ms`);
            });
          }, 800); // Reduced delay for faster prefetch
        }
        
        // Show info about shared drive and cache status
        if (response.data.shared_drive_name) {
          const cacheStatus = response.data.cached ? ' (cached ⚡)' : ' (fresh)';
          console.log(`📁 Loaded ${rootFolders.length} root folders from ${response.data.shared_drive_name}${cacheStatus}`);
        }
      } else {
        // Loading subfolders
        return response.data.items.map((item: any) => ({
          ...item,
          isExpanded: false,
          isLoaded: false,
          children: []
        }));
      }
    } catch (error: any) {
      console.warn('Google Drive folders not available:', error);
      if (parentId === '') {
        // Set empty folders array for root level and show helpful message
        setFolders([]);
        console.log('Google Drive integration temporarily unavailable - you can still chat with indexed documents');
      }
      return [];
    }
  }, [setCacheInfo]);

  // Load folders when authentication becomes available
  useEffect(() => {
    if (isAuthenticated && initComplete) {
      console.log('🗂️ Loading Google Drive folders...');
      loadFolders().catch(error => {
        console.warn('Google Drive folders unavailable:', error);
      });
    }
  }, [isAuthenticated, initComplete, loadFolders]);

  // Search folders
  const searchFolders = async (query: string) => {
    if (!query || query.length < 2) {
      // Reset to root folders if search is cleared
      await loadFolders();
      return;
    }
    
    try {
      const response = await axios.get(`${API_BASE_URL}/folders/search`, {
        params: { q: query }  // Removed 'type' parameter for faster search
      });
      
      // Track cache usage for search too
      if (response.data.cached) {
        setCacheInfo(prev => ({
          total_entries: prev.total_entries,
          cached_responses: prev.cached_responses + 1
        }));
      }
      
      const searchResults = response.data.items.map((item: any) => ({
        ...item,
        isExpanded: false,
        isLoaded: true, // Search results don't need lazy loading
        children: [],
        isSearchResult: true // Mark as search result
      }));
      
      setFolders(searchResults);
      
      const cacheStatus = response.data.cached ? ' (cached)' : ' (fresh)';
      console.log(`Found ${searchResults.length} search results for "${query}"${cacheStatus}`);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  // Get cache status
  const getCacheStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/cache/status`);
      setCacheInfo({
        total_entries: response.data.total_entries,
        cached_responses: cacheInfo.cached_responses  // Keep current count
      });
    } catch (error) {
      console.error('Failed to get cache status:', error);
    }
  }, [cacheInfo.cached_responses]);

  // Load cache status on app init and periodically
  useEffect(() => {
    getCacheStatus();
    const interval = setInterval(getCacheStatus, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, [getCacheStatus]);

  // Debounced search
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);
  
  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
    
    // Clear previous timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
    
    // Set new timeout
    const timeout = setTimeout(() => {
      searchFolders(query);
    }, 300); // Reduced to 300ms for faster search response
    
    setSearchTimeout(timeout);
  };

  // Enhanced toggle with instant loading for prefetched folders
  const toggleFolder = async (folderId: string) => {
    const updateFolders = (items: FolderItem[]): FolderItem[] => {
      return items.map(item => {
        if (item.id === folderId) {
          const newExpanded = !item.isExpanded;
          
          if (newExpanded && !item.isLoaded && !item.isPrefetched) {
            // Show loading indicator for non-prefetched folders
            setFolders(prevFolders => 
              updateFolderStatus(prevFolders, folderId, { isPreloading: true })
            );
            
            // Load children with performance timing
            const startTime = performance.now();
            loadFolders(folderId).then(children => {
              const loadTime = performance.now() - startTime;
              console.log(`📂 Loaded '${item.name.slice(0, 25)}...' in ${loadTime.toFixed(1)}ms`);
              
              setFolders(prevFolders => updateFolderChildren(prevFolders, folderId, children));
            }).finally(() => {
              setFolders(prevFolders => 
                updateFolderStatus(prevFolders, folderId, { isPreloading: false })
              );
            });
            return { ...item, isExpanded: newExpanded, isLoaded: true };
          } else if (newExpanded && item.isPrefetched) {
            // Instant expansion for prefetched folders
            console.log(`⚡ Instant expansion of prefetched folder '${item.name.slice(0, 25)}...'`);
          }
          
          return { ...item, isExpanded: newExpanded };
        }
        if (item.children) {
          return { ...item, children: updateFolders(item.children) };
        }
        return item;
      });
    };
    
    setFolders(updateFolders);
  };

  // Helper function to update folder status
  const updateFolderStatus = (items: FolderItem[], folderId: string, status: Partial<FolderItem>): FolderItem[] => {
    return items.map(item => {
      if (item.id === folderId) {
        return { ...item, ...status };
      }
      if (item.children) {
        return { ...item, children: updateFolderStatus(item.children, folderId, status) };
      }
      return item;
    });
  };

  // Helper function to update folder children
  const updateFolderChildren = (items: FolderItem[], folderId: string, children: FolderItem[]): FolderItem[] => {
    return items.map(item => {
      if (item.id === folderId) {
        return { ...item, children };
      }
      if (item.children) {
        return { ...item, children: updateFolderChildren(item.children, folderId, children) };
      }
      return item;
    });
  };

  // Handle file selection
  const handleFileSelect = (file: FolderItem) => {
    if (file.type === 'file') {
      setSelectedFile(file);
      console.log(`📄 Selected file for targeted query: ${file.name}`);
    } else if (file.webViewLink) {
      window.open(file.webViewLink, '_blank');
    }
  };

  // Function to refresh access token
  const refreshAuthToken = async () => {
    const refreshToken = localStorage.getItem('rag_refresh_token');
    if (!refreshToken) {
      return false;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: refreshToken
        })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('rag_auth_token', data.access_token);
        return true;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }
    
    return false;
  };

  // Enhanced fetch with automatic token refresh
  const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
    const authToken = localStorage.getItem('rag_auth_token');
    
    // First attempt with current token
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}),
        ...options.headers,
      }
    });

    // If unauthorized and we have a refresh token, try to refresh
    if (response.status === 401 && localStorage.getItem('rag_refresh_token')) {
      const refreshSuccess = await refreshAuthToken();
      if (refreshSuccess) {
        // Retry with new token
        const newToken = localStorage.getItem('rag_auth_token');
        return fetch(url, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            ...(newToken ? { 'Authorization': `Bearer ${newToken}` } : {}),
            ...options.headers,
          }
        });
      }
    }

    return response;
  };

  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date()
    };

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      text: '',
      sender: 'assistant',
      timestamp: new Date(),
      isLoading: true
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      // Use fetchWithAuth instead of regular fetch for automatic token refresh
      const response = await fetchWithAuth(`${API_BASE_URL}/chat`, {
        method: 'POST',
        body: JSON.stringify({
          message: inputText,
          collection: selectedCollection,
          file_id: selectedFile?.id || null
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      // Update the assistant message with the complete response
      setMessages(prev => {
        const updated = [...prev];
        const responseText = data.answer || 'No response generated.';
        const isWorkspaceQuery = data.query_type === 'workspace';
        
        // Add workspace analysis indicator if applicable
        let finalText = responseText;
        if (isWorkspaceQuery && data.file_analyzed) {
          const fileName = data.documents?.[0]?.filename || 'selected file';
          finalText = `🔍 **Direct Document Analysis of "${fileName}"**\n\n${responseText}`;
        }
        
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          text: finalText,
          isLoading: false,
          documents: data.documents || []
        };
        return updated;
      });

    } catch (error: any) {
      console.error('Failed to send message:', error);
      let errorText = 'Sorry, I encountered an error processing your request. Please make sure the API server is running.';
      if (error.response?.status === 503) {
        errorText = 'The AI system is still initializing. Please wait a moment and try again.';
      } else if (error.response?.data?.code === 'SYSTEM_INITIALIZING') {
        errorText = 'The AI system is still loading. Please wait a few seconds and try your question again.';
      } else if (error.response?.status === 401) {
        errorText = 'Authentication expired. Please refresh the page and sign in again.';
      }
      const errorMessage: Message = {
        id: (Date.now() + 3).toString(),
        text: errorText,
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => prev.slice(0, -1).concat([errorMessage]));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const switchCollection = async (collectionId: string) => {
    if (isCollectionSwitching || selectedCollection === collectionId) return;
    
    setIsCollectionSwitching(true);
    const startTime = performance.now();
    
    try {
      console.log(`🔄 Switching to collection: ${collections[collectionId]?.name || collectionId}`);
      
      const response = await axios.post(`${API_BASE_URL}/switch-collection`, {
        collection: collectionId
      }, { timeout: 30000 }); // 30 second timeout for collection switching
      
      const switchTime = performance.now() - startTime;
      console.log(`✅ Collection switched in ${switchTime.toFixed(0)}ms`);
      
      setSelectedCollection(collectionId);
      
      // Add a brief success message
      const collectionName = collections[collectionId]?.name || collectionId;
      const isMultiCollection = collectionId === 'ALL_COLLECTIONS';
      const modeText = isMultiCollection ? 'multi-collection mode' : 'single collection mode';
      
      console.log(`📚 Now using ${collectionName} (${modeText})`);
      
    } catch (error: any) {
      console.error('❌ Failed to switch collection:', error);
      
      // Show user-friendly error message
      const errorMsg = error.response?.data?.error || error.message || 'Unknown error';
      alert(`Failed to switch collection: ${errorMsg}. Please try again.`);
    } finally {
      setIsCollectionSwitching(false);
    }
  };

  const TypingIndicator = () => (
    <div className="typing-indicator">
      <div className="typing-dot"></div>
      <div className="typing-dot"></div>
      <div className="typing-dot"></div>
    </div>
  );

  const DocumentPreview = ({ document }: { document: Document }) => (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-light-100 dark:bg-dark-800 border border-brand-mint dark:border-dark-600 rounded-lg p-3 mt-2 hover:border-brand-green dark:hover:border-blue-500 transition-colors group"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-brand-mint/30 dark:bg-blue-500/10 rounded-lg">
            <FileText className="w-4 h-4 text-brand-green dark:text-blue-400" />
          </div>
          <div>
            <p className="text-sm font-medium text-brand-dark dark:text-gray-200 truncate max-w-xs">
              {document.filename || 'Untitled'}
            </p>
            <div className="flex items-center gap-2 text-xs text-brand-dark/60 dark:text-gray-400">
              <span>{document.type || 'Document'}</span>
              {(document as any).collection && (
                <>
                  <span>•</span>
                  <span className="text-brand-green dark:text-blue-400">{(document as any).collection}</span>
                </>
              )}
              {(document as any).score !== undefined && (
                <>
                  <span>•</span>
                  <span className="text-green-600 dark:text-green-400">
                    {((document as any).score > 0 
                      ? `+${((document as any).score).toFixed(2)}` 
                      : ((document as any).score).toFixed(2))} relevance
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
        {document.url && (
          <a
            href={document.url}
            target="_blank"
            rel="noopener noreferrer"
            className="opacity-0 group-hover:opacity-100 transition-opacity p-2 text-brand-dark/60 dark:text-gray-400 hover:text-brand-green dark:hover:text-blue-400"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        )}
      </div>
    </motion.div>
  );

  return (
    <div className="h-screen bg-brand-white dark:bg-dark-950 flex transition-colors duration-200 overflow-hidden">
      {/* Sidebar */}
      <div className="w-80 bg-brand-green dark:bg-dark-900 border-r border-brand-green dark:border-dark-800 p-6 flex flex-col overflow-hidden">
        <div className="mb-8 flex-shrink-0">
          <div className="flex flex-col items-center mb-4">
            <img 
              src="/7MM White.webp"
              alt="7MM Logo" 
              style={{height: '10vw', minHeight: '80px', maxHeight: '130px'}}
              className="w-auto mb-3"
            />
            <h1 className="text-2xl font-bold text-brand-white dark:text-white">7MM Ask</h1>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-brand-white dark:text-gray-400">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Collections */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-brand-white dark:text-white mb-4 flex items-center">
            <Database className="w-5 h-5 mr-2" />
            Collections
          </h3>
            <div className="grid grid-cols-2 gap-2">
            {Object.entries(collections).map(([id, collection]) => {
              const isSelected = selectedCollection === id;
              const isLoading = isCollectionSwitching && isSelected;
              const isDisabled = isCollectionSwitching;
              
              return (
                <button
                  key={id}
                  onClick={() => switchCollection(id)}
                  disabled={isDisabled}
                  className={`text-left p-2 rounded-lg transition-all duration-200 relative ${
                    isSelected
                      ? 'bg-white dark:bg-blue-500/20 border-l-4 border-l-brand-green dark:border-l-blue-500 border border-gray-200 dark:border-blue-500/30 text-brand-dark dark:text-blue-300 scale-105'
                      : isDisabled
                        ? 'bg-gray-300 dark:bg-dark-800 text-gray-500 dark:text-gray-500 cursor-not-allowed opacity-50'
                        : 'bg-white dark:bg-dark-800 hover:bg-gray-100 dark:hover:bg-dark-700 text-brand-dark dark:text-gray-300 hover:scale-[1.02] border border-gray-200 dark:border-transparent'
                  }`}
                >
                  <div className="flex flex-col">
                    <div className="flex items-center justify-between mb-1">
                      <div className="font-medium text-xs truncate flex items-center flex-1 min-w-0">
                        <span className="truncate">{collection.name}</span>
                        {isSelected && (
                          <span className="ml-1 w-1.5 h-1.5 bg-brand-green rounded-full animate-pulse flex-shrink-0"></span>
                        )}
                        {collection.is_combined && (
                          <span className="ml-1 px-1 py-0.5 bg-purple-600 text-white text-[10px] rounded flex-shrink-0" title="Multi-collection mode">
                            ALL
                          </span>
                        )}
                      </div>
                      {/* Loading animation */}
                      {isLoading && (
                        <div className="flex-shrink-0 ml-1">
                          <div className="animate-spin w-3 h-3 border-2 border-brand-green dark:border-blue-400 border-t-transparent rounded-full"></div>
                        </div>
                      )}
                    </div>
                    <div className="text-[10px] text-gray-600 dark:text-gray-500 truncate">
                      {collection.files_processed} files
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Stats */}
        <div className="bg-white dark:bg-dark-800 rounded-lg p-4 mb-4 border border-white/20 dark:border-transparent">
          <h4 className="text-sm font-medium text-brand-dark dark:text-gray-300 mb-3">Session Stats</h4>
          <div className="space-y-2 text-xs text-gray-600 dark:text-gray-400">
            <div className="flex justify-between">
              <span>Messages:</span>
              <span>{messages.filter(m => m.sender === 'user').length}</span>
            </div>
            <div className="flex justify-between">
              <span>Active Collection:</span>
              <span className="truncate ml-2">
                {selectedCollection ? collections[selectedCollection]?.name : 'None'}
              </span>
            </div>
          </div>
        </div>

        {/* Theme Toggle */}
        <div className="bg-white dark:bg-dark-800 rounded-lg p-4 border border-white/20 dark:border-transparent mb-0">
          <h4 className="text-sm font-medium text-brand-dark dark:text-gray-300 mb-3">Theme</h4>
          <button
            onClick={toggleTheme}
            className="w-full flex items-center justify-between p-3 rounded-lg bg-gray-100 dark:bg-dark-700 hover:bg-gray-200 dark:hover:bg-dark-600 transition-colors"
          >
            <span className="text-sm text-brand-dark dark:text-gray-300">
              {theme === 'dark' ? 'Dark Mode' : 'Light Mode'}
            </span>
            {theme === 'dark' ? (
              <Sun className="w-5 h-5 text-yellow-400" />
            ) : (
              <Moon className="w-5 h-5 text-brand-dark" />
            )}
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Chat Messages - Scrollable */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 min-h-0">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-4xl flex ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'} space-x-3`}>
                  {/* Avatar */}
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.sender === 'user' 
                      ? 'bg-brand-green dark:bg-blue-500' 
                      : 'bg-brand-mint dark:bg-green-500'
                  }`}>
                    {message.sender === 'user' ? (
                      <User className="w-5 h-5 text-white" />
                    ) : (
                      <Bot className="w-5 h-5 text-white" />
                    )}
                  </div>

                  {/* Message Content */}
                  <div className={`rounded-2xl p-4 ${
                    message.sender === 'user'
                      ? 'bg-brand-green dark:bg-blue-500 text-white ml-3'
                      : 'bg-light-100 dark:bg-dark-800 text-brand-dark dark:text-gray-100 mr-3 border border-brand-mint/30 dark:border-transparent'
                  }`}>
                    {message.isLoading ? (
                      <div className="flex items-center space-x-3">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-sm">Thinking...</span>
                        <TypingIndicator />
                      </div>
                    ) : (
                      <>
                        <div className={`prose prose-sm max-w-none ${
                          message.sender === 'user' 
                            ? 'prose-invert' 
                            : 'dark:prose-invert prose-headings:text-brand-dark dark:prose-headings:text-white prose-p:text-brand-dark dark:prose-p:text-gray-100'
                        }`}>
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                              // Custom link styling
                              a: ({ node, children, ...props }) => (
                                <a {...props} className="text-brand-green dark:text-blue-400 hover:text-brand-green/80 dark:hover:text-blue-300 underline" target="_blank" rel="noopener noreferrer">
                                  {children}
                                </a>
                              ),
                              // Custom code styling
                              code: ({ node, ...props }) => (
                                <code {...props} className="bg-light-200 dark:bg-dark-700 text-brand-green dark:text-green-400 px-1 py-0.5 rounded text-sm" />
                              ),
                              // Custom table styling
                              table: ({ node, ...props }) => (
                                <table {...props} className="border-collapse border border-brand-mint dark:border-dark-600" />
                              ),
                              th: ({ node, ...props }) => (
                                <th {...props} className="border border-brand-mint dark:border-dark-600 px-3 py-2 bg-light-200 dark:bg-dark-700 font-semibold" />
                              ),
                              td: ({ node, ...props }) => (
                                <td {...props} className="border border-brand-mint dark:border-dark-600 px-3 py-2" />
                              ),
                            }}
                          >
                            {message.text}
                          </ReactMarkdown>
                        </div>

                        {/* Document Previews */}
                        {message.documents && message.documents.length > 0 && (
                          <div className="mt-4 space-y-2">
                            <p className="text-xs text-brand-dark/60 dark:text-gray-400 font-medium">Referenced Documents:</p>
                            {message.documents.map((doc, index) => (
                              <DocumentPreview key={index} document={doc} />
                            ))}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area - Fixed at bottom */}
        <div className="flex-shrink-0 bg-brand-green dark:bg-dark-950 border-t border-brand-green dark:border-dark-800 p-6">
          {/* Selected File Indicator */}
          {selectedFile && (
            <div className="mb-3">
              <div className="p-3 bg-white dark:bg-blue-900/30 border border-white/30 dark:border-blue-500/50 rounded-lg flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-brand-green dark:text-blue-400" />
                  <span className="text-sm text-brand-dark dark:text-blue-200">
                    🔍 <span className="font-semibold">Workspace Analysis</span> of: <span className="font-semibold">{selectedFile.name}</span>
                  </span>
                  <span className="text-xs bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300 px-2 py-1 rounded-full">
                    Direct Document Query
                  </span>
                </div>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="text-brand-green dark:text-blue-400 hover:text-brand-green/80 dark:hover:text-blue-300 transition-colors"
                  title="Clear file selection"
                >
                  <span className="text-lg">×</span>
                </button>
              </div>
              {/* File Action Buttons */}
              <div className="mt-2 flex gap-2">
                {selectedFile.webViewLink && (
                  <a
                    href={selectedFile.webViewLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-white dark:bg-blue-900/30 border border-white/30 dark:border-blue-500/50 rounded-lg text-sm text-brand-dark dark:text-blue-200 hover:bg-gray-50 dark:hover:bg-blue-900/50 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                    View on Google Drive
                  </a>
                )}
                <a
                  href={`${API_BASE_URL}/drive/download/${selectedFile.id}`}
                  download={selectedFile.name}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-brand-green dark:bg-blue-600 text-white rounded-lg text-sm hover:bg-brand-green/90 dark:hover:bg-blue-700 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Direct Download
                </a>
              </div>
            </div>
          )}
          <div className="flex items-end space-x-4">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask anything about your documents..."
                disabled={isLoading || !isConnected}
                className="w-full bg-white dark:bg-dark-800 border border-white/30 dark:border-dark-600 rounded-xl px-4 py-3 pr-12 text-brand-dark dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-white dark:focus:ring-blue-500 focus:border-transparent resize-none"
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={isLoading || !inputText.trim() || !isConnected}
              className="p-3 bg-white dark:bg-blue-500 text-brand-green dark:text-white rounded-xl hover:bg-white/90 dark:hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-shrink-0"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          
          {!isConnected && (
            <div className="mt-3 text-sm text-red-400 flex items-center">
              <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
              Not connected to API server. Please start the Flask server.
            </div>
          )}
        </div>
      </div>

      {/* Folder Browser Panel */}
      <div className="w-80 bg-brand-green dark:bg-dark-900 border-l border-brand-green dark:border-dark-800 p-6 flex flex-col overflow-hidden">
        <div className="flex items-center justify-between mb-4 flex-shrink-0">
          <h3 className="text-lg font-semibold text-brand-white dark:text-white flex items-center">
            <Folder className="w-5 h-5 mr-2" />
            Drive Files
            {cacheInfo.total_entries > 0 && (
              <div className="ml-2 flex items-center gap-2">
                <span className="px-2 py-1 bg-green-600 text-white text-xs rounded">
                  {cacheInfo.total_entries} cached
                </span>
                {cacheInfo.cached_responses > 0 && (
                  <span className="px-2 py-1 bg-brand-green dark:bg-blue-600 text-white text-xs rounded" title="Cache hits this session">
                    {cacheInfo.cached_responses} hits
                  </span>
                )}
              </div>
            )}
          </h3>
          <button
            onClick={() => setShowFolders(!showFolders)}
            className="p-2 text-brand-white dark:text-gray-400 hover:text-white dark:hover:text-white transition-colors"
          >
            {showFolders ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </div>
        
        {showFolders && (
          <div className="flex-1 bg-white dark:bg-dark-800 rounded-lg overflow-hidden flex flex-col border border-white/20 dark:border-transparent min-h-0">
            <div className="p-3 border-b border-gray-200 dark:border-dark-600">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Search files in 7MM Resources..."
                  value={searchQuery}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  className="flex-1 bg-gray-100 dark:bg-dark-700 text-brand-dark dark:text-white placeholder-gray-500 dark:placeholder-gray-400 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green dark:focus:ring-blue-500"
                />
                {searchQuery && (
                  <button
                    onClick={() => handleSearchChange('')}
                    className="px-3 py-2 bg-gray-100 dark:bg-dark-600 text-brand-dark dark:text-gray-400 hover:text-brand-green dark:hover:text-white rounded text-sm transition-colors"
                    title="Clear search"
                  >
                    ×
                  </button>
                )}
              </div>
              {searchQuery && (
                <div className="text-xs text-gray-600 dark:text-gray-500 mt-1">
                  {folders.length} result{folders.length !== 1 ? 's' : ''} found
                </div>
              )}
            </div>
            <div className="flex-1 overflow-y-auto">
              {folders.length > 0 && !searchQuery && (
                <div className="p-2 border-b border-gray-200 dark:border-dark-700">
                  <div className="text-xs text-gray-600 dark:text-gray-400 flex items-center">
                    <Database className="w-3 h-3 mr-1" />
                    7MM Resources ({folders.length} folders)
                  </div>
                </div>
              )}
              <div className="p-2">
                {folders.map(folder => (
                  <FolderTreeItem
                    key={folder.id}
                    item={folder}
                    onToggle={toggleFolder}
                    onFileSelect={handleFileSelect}
                    level={0}
                    selectedFileId={selectedFile?.id || null}
                  />
                ))}
                {folders.length === 0 && (
                  <div className="text-center py-8 text-gray-600 dark:text-gray-500">
                    <Folder className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    {searchQuery ? (
                      <p className="text-sm">No files found for "{searchQuery}"</p>
                    ) : (
                      <div>
                        <p className="text-sm">📁 Drive Folders Initializing</p>
                        <p className="text-xs text-gray-500 mt-1">Chat system is ready • Folders will load when available</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
            
            {/* Cache performance info */}
            {cacheInfo.cached_responses > 0 && (
              <div className="p-3 border-t border-dark-600 bg-dark-900">
                <div className="text-xs text-green-400 flex items-center justify-between">
                  <span>Performance: {cacheInfo.cached_responses} cached responses</span>
                  <span className="text-gray-500">{cacheInfo.total_entries} entries</span>
                </div>
              </div>
            )}
          </div>
        )}
        
        {!showFolders && (
          <div className="flex-1 text-center py-8 text-brand-white dark:text-gray-500">
            <Folder className="w-8 h-8 mx-auto mb-2 opacity-50 text-brand-white dark:text-gray-500" />
            <p className="text-sm">Click above to browse drive files</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Main App component with authentication
const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

// App content with authentication guard and routing
const AppContent: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();

  // Simple routing based on pathname
  const currentPath = window.location.pathname;

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Handle auth pickup route (this runs before authentication check)
  if (currentPath === '/auth-pickup') {
    return <AuthPickup />;
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return <ChatApp />;
};

export default App;
