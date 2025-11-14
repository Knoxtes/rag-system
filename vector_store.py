# vector_store.py - ChromaDB 1.2.1 compatible

import chromadb
from config import CHROMA_PERSIST_DIR, COLLECTION_NAME
import os
import sys

# Fix Windows console encoding for Unicode characters
if os.name == 'nt':  # Windows
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass

def safe_print(*args, **kwargs):
    """Safe print function that handles Unicode encoding errors on Windows"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_arg = arg.replace('📊', '[STATS]')
                safe_args.append(safe_arg)
            else:
                safe_args.append(str(arg))
        print(*safe_args, **kwargs)


class VectorStore:
    """ChromaDB 1.2.1 - Manages vector database collections"""
    
    def __init__(self, collection_name=COLLECTION_NAME, persist_directory=CHROMA_PERSIST_DIR):
        """
        Initialize the vector store for a SPECIFIC collection.
        :param collection_name: The name of the collection to use.
        :param persist_directory: The directory to persist the database.
        """
        print(f"Initializing vector database client at {persist_directory}...")
        
        os.makedirs(persist_directory, exist_ok=True)
        
        # This client is shared for all collections
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        print(f"Getting or creating collection: '{collection_name}'")
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        count = self.collection.count()
        print(f"[+] Collection '{self.collection_name}' ready. Documents: {count}")
    
    def add_documents(self, documents, embeddings, metadatas, ids):
        """Add documents to the specific collection - auto-persists"""
        try:
            if hasattr(embeddings, 'tolist'):
                embeddings = embeddings.tolist()
            
            batch_size = 4000
            for i in range(0, len(ids), batch_size):
                print(f"  Adding batch {i//batch_size + 1} to '{self.collection_name}'...")
                self.collection.add(
                    documents=documents[i:i + batch_size],
                    embeddings=embeddings[i:i + batch_size],
                    metadatas=metadatas[i:i + batch_size],
                    ids=ids[i:i + batch_size]
                )
        except Exception as e:
            print(f"  Error adding documents: {e}")
    
    def search(self, query_embedding, n_results=5):
        """Search for similar documents in this collection"""
        try:
            count = self.collection.count()
            
            if count == 0:
                print(f"[!] Collection '{self.collection_name}' is empty.")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
            
            actual_n_results = min(n_results, count)
            
            if actual_n_results <= 0:
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
            
            if hasattr(query_embedding, 'tolist'):
                query_embedding = query_embedding.tolist()
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=actual_n_results
            )
            
            return results
            
        except Exception as e:
            print(f"  Error searching: {e}")
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

    def clear_collection(self):
        """Clear all documents from THIS collection."""
        try:
            print(f"Clearing all documents from collection '{self.collection_name}'...")
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print("✓ Collection cleared.")
        except Exception as e:
            print(f"Error clearing collection: {e}")
            # Try to re-create just in case
            try:
                 self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e2:
                print(f"Fatal error re-creating collection: {e2}")

    def get_stats(self):
        """Get statistics for THIS collection"""
        return {
            'total_documents': self.collection.count(),
            'collection_name': self.collection_name
        }
    
    def peek(self, limit=5):
        """Peek at some documents in THIS collection"""
        try:
            result = self.collection.peek(limit=limit)
            return result
        except Exception as e:
            print(f"Error peeking: {e}")
            return None
    
    # --- Methods for managing ALL collections (used by main.py) ---
    
    def list_all_collections(self):
        """List all collections in the database"""
        print("Listing all collections...")
        collections = self.client.list_collections()
        return [c.name for c in collections]

    def delete_collection_by_name(self, collection_name):
        """Delete a specific collection by name"""
        try:
            print(f"Deleting collection '{collection_name}'...")
            self.client.delete_collection(name=collection_name)
            print(f"✓ Collection '{collection_name}' deleted.")
        except Exception as e:
            print(f"Error deleting collection '{collection_name}': {e}")


if __name__ == "__main__":
    # Test default collection
    vs_default = VectorStore()
    stats_default = vs_default.get_stats()
    safe_print(f"\n📊 Default Stats: {stats_default['total_documents']} documents in collection '{stats_default['collection_name']}'")
    
    # Test custom collection
    vs_custom = VectorStore(collection_name="my_test_collection")
    stats_custom = vs_custom.get_stats()
    safe_print(f"\n📊 Custom Stats: {stats_custom['total_documents']} documents in collection '{stats_custom['collection_name']}'")
    
    print("\nListing all collections:")
    print(vs_default.list_all_collections())