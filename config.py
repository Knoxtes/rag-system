# config.py - Configuration settings

import os
import sys

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
# Load GOOGLE_API_KEY from environment variable
try:
    from dotenv import load_dotenv
    # Try to load .env file if python-dotenv is installed
    if os.path.exists('.env'):
        load_dotenv()
except ImportError:
    # python-dotenv not installed, rely on system environment variables
    pass

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Validate GOOGLE_API_KEY
if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_gemini_api_key_here":
    print("\n" + "="*80, file=sys.stderr)
    print("WARNING: GOOGLE_API_KEY is not set or is using placeholder value!", file=sys.stderr)
    print("="*80, file=sys.stderr)
    print("\nThe application will not work without a valid Google Gemini API key.", file=sys.stderr)
    print("\nTo fix this:", file=sys.stderr)
    print("1. Get your API key from: https://aistudio.google.com/app/apikey", file=sys.stderr)
    print("2. Create a .env file (copy from .env.example)", file=sys.stderr)
    print("3. Add this line to .env: GOOGLE_API_KEY=your_actual_key_here", file=sys.stderr)
    print("4. Or set it as an environment variable: export GOOGLE_API_KEY=your_key", file=sys.stderr)
    print("\n" + "="*80 + "\n", file=sys.stderr)
    # Don't exit here, let the application handle it gracefully
    GOOGLE_API_KEY = None

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

# OCR Settings
OCR_ENABLED = True  # Enable/disable OCR processing for images
OCR_BACKEND = "easyocr"  # Options: "easyocr", "tesseract", "google_vision"
OCR_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence score for OCR text (0.0-1.0)
OCR_LANGUAGES = ["en"]  # Languages for OCR processing (e.g., ["en", "es", "fr"])
OCR_GPU_ENABLED = True  # Use GPU acceleration for EasyOCR (if available)

# Text Clarification Settings
TEXT_CLARIFICATION_ENABLED = True  # Enable/disable AI text clarification for OCR
CLARIFICATION_MODEL_TEMPERATURE = 0.1  # AI model temperature for text clarification (0.0-1.0)
CLARIFICATION_MAX_TOKENS = 2000  # Maximum tokens for clarified text output
AUTO_CLARIFY_OCR = True  # Automatically clarify all OCR text
CLARIFICATION_MIN_LENGTH = 20  # Minimum text length to trigger clarification

# Text Quality Filter Settings
TEXT_QUALITY_FILTER_ENABLED = True  # Enable/disable text quality filtering
QUALITY_MIN_READABLE_RATIO = 0.6  # Minimum ratio of readable words (0.0-1.0)
QUALITY_MAX_SPECIAL_CHAR_RATIO = 0.3  # Maximum ratio of special characters (0.0-1.0)
QUALITY_MIN_COHERENCE_SCORE = 0.4  # Minimum coherence score (0.0-1.0)
QUALITY_MIN_CONTENT_LENGTH = 50  # Minimum meaningful content length
QUALITY_MIN_OVERALL_SCORE = 0.3  # Minimum overall quality score (0.0-1.0)
QUALITY_OCR_THRESHOLD = 0.25  # Lower threshold for known OCR content (0.0-1.0)

# Supported image formats for OCR
OCR_SUPPORTED_FORMATS = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 
    'image/bmp', 'image/gif', 'image/webp'
}

