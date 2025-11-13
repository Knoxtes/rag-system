import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, FileText, ExternalLink, Database, Loader2, Folder, FolderOpen, Search, ChevronRight, ChevronDown } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

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
}

interface FolderItem {
  id: string;
  name: string;
  type: 'folder' | 'file';
  mimeType: string;
  webViewLink: string;
  modifiedTime: string;
  size: number;
  hasChildren: boolean;
  parent_id: string;
  children?: FolderItem[];
  isLoaded?: boolean;
  isExpanded?: boolean;
}

// Folder Tree Component
const FolderTreeItem: React.FC<{
  item: FolderItem;
  onToggle: (id: string) => void;
  onFileSelect: (file: FolderItem) => void;
  level: number;
}> = ({ item, onToggle, onFileSelect, level }) => {
  const handleToggle = () => {
    if (item.type === 'folder') {
      onToggle(item.id);
    } else {
      onFileSelect(item);
    }
  };

  const paddingLeft = level * 16; // 16px per level

  return (
    <div style={{ paddingLeft: `${paddingLeft}px` }}>
      <div 
        className="flex items-center py-1 px-2 hover:bg-gray-700 rounded cursor-pointer transition-colors duration-200"
        onClick={handleToggle}
      >
        {item.type === 'folder' && (
          <span className="mr-2 text-gray-400">
            {item.isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </span>
        )}
        
        {item.type === 'folder' ? (
          item.isExpanded ? (
            <FolderOpen className="w-4 h-4 mr-2 text-blue-400" />
          ) : (
            <Folder className="w-4 h-4 mr-2 text-blue-400" />
          )
        ) : (
          <FileText className="w-4 h-4 mr-2 text-gray-400" />
        )}
        
        <span className="text-gray-200 text-sm truncate">{item.name}</span>
      </div>
      
      {item.type === 'folder' && item.isExpanded && item.children && (
        <div>
          {item.children.map(child => (
            <FolderTreeItem
              key={child.id}
              item={child}
              onToggle={onToggle}
              onFileSelect={onFileSelect}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [collections, setCollections] = useState<Record<string, Collection>>({});
  const [selectedCollection, setSelectedCollection] = useState<string>('');
  const [isConnected, setIsConnected] = useState(false);
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFolders, setShowFolders] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize app
  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Check health
      const healthResponse = await axios.get(`${API_BASE_URL}/health`);
      setIsConnected(healthResponse.data.rag_initialized);

      // Get available collections
      const collectionsResponse = await axios.get(`${API_BASE_URL}/collections`);
      setCollections(collectionsResponse.data.collections);
      
      // Set first collection as default
      const firstCollection = Object.keys(collectionsResponse.data.collections)[0];
      if (firstCollection) {
        setSelectedCollection(firstCollection);
      }

      // Load root folders
      await loadFolders();

      // Add welcome message
      const welcomeMessage: Message = {
        id: Date.now().toString(),
        text: `Welcome to the RAG Chat Assistant! 🤖\n\nI'm ready to help you find information from your indexed documents. Ask me anything about your business processes, documents, or data.\n\n**Available Collections:** ${Object.keys(collectionsResponse.data.collections).length}`,
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages([welcomeMessage]);

    } catch (error) {
      console.error('Failed to initialize app:', error);
      setIsConnected(false);
    }
  };

  // Load folders from Google Drive
  const loadFolders = async (parentId: string = '') => {
    try {
      const response = await axios.get(`${API_BASE_URL}/folders`, {
        params: { parent_id: parentId }
      });
      
      if (parentId === '') {
        // Loading root folders
        const rootFolders = response.data.items.map((item: any) => ({
          ...item,
          isExpanded: false,
          isLoaded: false,
          children: []
        }));
        setFolders(rootFolders);
      } else {
        // Loading subfolders
        return response.data.items.map((item: any) => ({
          ...item,
          isExpanded: false,
          isLoaded: false,
          children: []
        }));
      }
    } catch (error) {
      console.error('Failed to load folders:', error);
      return [];
    }
  };

  // Toggle folder expansion and load children if needed
  const toggleFolder = async (folderId: string) => {
    const updateFolders = (items: FolderItem[]): FolderItem[] => {
      return items.map(item => {
        if (item.id === folderId) {
          const newExpanded = !item.isExpanded;
          if (newExpanded && !item.isLoaded) {
            // Load children
            loadFolders(folderId).then(children => {
              setFolders(prevFolders => updateFolderChildren(prevFolders, folderId, children));
            });
            return { ...item, isExpanded: newExpanded, isLoaded: true };
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
    if (file.webViewLink) {
      window.open(file.webViewLink, '_blank');
    }
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
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        message: inputText,
        collection: selectedCollection
      });

      const assistantMessage: Message = {
        id: (Date.now() + 2).toString(),
        text: response.data.answer,
        sender: 'assistant',
        timestamp: new Date(),
        documents: response.data.documents || []
      };

      // Remove loading message and add real response
      setMessages(prev => prev.slice(0, -1).concat([assistantMessage]));

    } catch (error) {
      console.error('Failed to send message:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 3).toString(),
        text: 'Sorry, I encountered an error processing your request. Please make sure the API server is running.',
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
    try {
      await axios.post(`${API_BASE_URL}/switch-collection`, {
        collection: collectionId
      });
      setSelectedCollection(collectionId);
    } catch (error) {
      console.error('Failed to switch collection:', error);
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
      className="bg-dark-800 border border-dark-600 rounded-lg p-3 mt-2 hover:border-blue-500 transition-colors group"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-500/10 rounded-lg">
            <FileText className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-200 truncate max-w-xs">
              {document.filename}
            </p>
            <p className="text-xs text-gray-400">{document.type}</p>
          </div>
        </div>
        <a
          href={document.url}
          target="_blank"
          rel="noopener noreferrer"
          className="opacity-0 group-hover:opacity-100 transition-opacity p-2 text-gray-400 hover:text-blue-400"
        >
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>
    </motion.div>
  );

  return (
    <div className="min-h-screen bg-dark-950 flex">
      {/* Sidebar */}
      <div className="w-80 bg-dark-900 border-r border-dark-800 p-6">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">RAG Assistant</h1>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-400">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Collections */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Database className="w-5 h-5 mr-2" />
            Collections
          </h3>
          <div className="space-y-2">
            {Object.entries(collections).map(([id, collection]) => (
              <button
                key={id}
                onClick={() => switchCollection(id)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  selectedCollection === id
                    ? 'bg-blue-500/20 border border-blue-500/30 text-blue-300'
                    : 'bg-dark-800 hover:bg-dark-700 text-gray-300'
                }`}
              >
                <div className="font-medium text-sm truncate">{collection.name}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {collection.files_processed} files • {collection.location}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="bg-dark-800 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-300 mb-3">Session Stats</h4>
          <div className="space-y-2 text-xs text-gray-400">
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
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
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
                      ? 'bg-blue-500' 
                      : 'bg-green-500'
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
                      ? 'bg-blue-500 text-white ml-3'
                      : 'bg-dark-800 text-gray-100 mr-3'
                  }`}>
                    {message.isLoading ? (
                      <div className="flex items-center space-x-3">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-sm">Thinking...</span>
                        <TypingIndicator />
                      </div>
                    ) : (
                      <>
                        <div className="prose prose-sm prose-invert max-w-none">
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                              // Custom link styling
                              a: ({ node, children, ...props }) => (
                                <a {...props} className="text-blue-400 hover:text-blue-300 underline" target="_blank" rel="noopener noreferrer">
                                  {children}
                                </a>
                              ),
                              // Custom code styling
                              code: ({ node, ...props }) => (
                                <code {...props} className="bg-dark-700 text-green-400 px-1 py-0.5 rounded text-sm" />
                              ),
                              // Custom table styling
                              table: ({ node, ...props }) => (
                                <table {...props} className="border-collapse border border-dark-600" />
                              ),
                              th: ({ node, ...props }) => (
                                <th {...props} className="border border-dark-600 px-3 py-2 bg-dark-700 font-semibold" />
                              ),
                              td: ({ node, ...props }) => (
                                <td {...props} className="border border-dark-600 px-3 py-2" />
                              ),
                            }}
                          >
                            {message.text}
                          </ReactMarkdown>
                        </div>

                        {/* Document Previews */}
                        {message.documents && message.documents.length > 0 && (
                          <div className="mt-4 space-y-2">
                            <p className="text-xs text-gray-400 font-medium">Referenced Documents:</p>
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

        {/* Input Area */}
        <div className="border-t border-dark-800 p-6">
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
                className="w-full bg-dark-800 border border-dark-600 rounded-xl px-4 py-3 pr-12 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={isLoading || !inputText.trim() || !isConnected}
              className="p-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-shrink-0"
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
      <div className="w-80 bg-dark-900 border-l border-dark-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Folder className="w-5 h-5 mr-2" />
            Drive Files
          </h3>
          <button
            onClick={() => setShowFolders(!showFolders)}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            {showFolders ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </div>
        
        {showFolders && (
          <div className="bg-dark-800 rounded-lg h-full max-h-screen overflow-hidden flex flex-col">
            <div className="p-3 border-b border-dark-600">
              <input
                type="text"
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-dark-700 text-white placeholder-gray-400 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex-1 p-2 overflow-y-auto">
              {folders.map(folder => (
                <FolderTreeItem
                  key={folder.id}
                  item={folder}
                  onToggle={toggleFolder}
                  onFileSelect={handleFileSelect}
                  level={0}
                />
              ))}
              {folders.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Folder className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Loading folders...</p>
                </div>
              )}
            </div>
          </div>
        )}
        
        {!showFolders && (
          <div className="text-center py-8 text-gray-500">
            <Folder className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Click above to browse drive files</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
