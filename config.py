# config.py - Configuration settings

import os

# Google Cloud Settings - CHANGE THIS!
PROJECT_ID = "rag-chatbot-475316"  # ⚠️ Replace with your actual project ID
LOCATION = "us-central1"

# File paths
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.pickle"
INDEXED_FOLDERS_FILE = "indexed_folders.json"

# ChromaDB Settings
CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "google_drive_docs" 

# Embedding Settings
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"  # UPGRADED: Better quality, similar speed (384 -> 512 dims)
# Alternatives:
# EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast but basic
# EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"  # Best quality, slower

# --- Reranker model ---
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Chunking Settings (Used by document_loader.py)
CHUNK_SIZE = 400  # INCREASED: Larger chunks = better context retention
CHUNK_OVERLAP = 100  # INCREASED: More overlap = better boundary preservation

# Hybrid Search Settings
USE_HYBRID_SEARCH = True  # Combine BM25 (keyword) + dense (semantic) search
BM25_WEIGHT = 0.3  # Weight for keyword search (0.0-1.0)
DENSE_WEIGHT = 0.7  # Weight for semantic search (should sum to 1.0)

# Retrieval Settings
TOP_K_RESULTS = 20  # INCREASED: More results for richer context
INITIAL_RETRIEVAL_COUNT = 100  # INCREASED: Cast wider net before reranking
DIVERSITY_THRESHOLD = 0.85  # Similarity threshold for deduplication (0-1)
MAX_CHUNKS_PER_FILE = 4  # INCREASED: Allow more chunks from highly relevant files

# RAG System Settings
# ⚠️ Set this in your environment!
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MAX_CONTEXT_CHARACTERS = 8000  # OPTIMIZED: Reduced from 12000 to save API costs (33% reduction)

# Query Caching Settings (NEW - for cost optimization)
ENABLE_QUERY_CACHE = True  # Cache frequent queries to reduce API calls
CACHE_TTL_SECONDS = 300  # Cache lifetime: 5 minutes
CACHE_MAX_SIZE = 1000  # Maximum number of cached queries

# Advanced Retrieval Settings
USE_PARENT_DOCUMENT_RETRIEVAL = True  # Retrieve small chunks, return larger parent context
PARENT_CHUNK_SIZE = 800  # Size of parent chunks (2x child chunks)
USE_CONTEXTUAL_COMPRESSION = True  # Filter retrieved chunks to only relevant sentences

# Agent Settings
MAX_AGENT_ITERATIONS = 8  # Maximum tool calls before forcing final answer
AGENT_TEMPERATURE = 0.3   # Lower = more focused, higher = more creative

# Synthesis Settings (OPTIMIZED for cost)
ENABLE_MULTI_QUERY = True  # Generate multiple query variations for better recall
ENABLE_CROSS_ENCODER_FUSION = True  # Re-rank combined results from multiple queries
SYNTHESIS_CONTEXT_WINDOW = 15000  # OPTIMIZED: Reduced from 20000 to save costs (25% reduction)
MIN_SOURCES_FOR_SYNTHESIS = 3  # Minimum sources to consider for synthesis questions
SYNTHESIS_QUERY_THRESHOLD = 0.7  # Confidence threshold to trigger synthesis mode (0-1, higher = more selective)

# Google Drive Settings
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]

