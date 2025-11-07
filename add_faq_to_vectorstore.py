#!/usr/bin/env python3
"""
Add Creative Department FAQ to vector store
"""
import os
import hashlib
from vector_store import VectorStore
from embeddings import LocalEmbedder

# Read the FAQ document
faq_path = "Creative_Department_FAQ_Enhanced.md"
with open(faq_path, 'r', encoding='utf-8') as f:
    faq_content = f.read()

# Split into reasonable chunks (by section)
chunks = []
current_chunk = ""
current_title = ""

for line in faq_content.split('\n'):
    # New section starting with ### Q:
    if line.startswith('### Q:'):
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'metadata': {
                    'source': faq_path,
                    'question': current_title,
                    'document_type': 'FAQ'
                }
            })
        current_chunk = line + '\n'
        current_title = line.replace('### Q:', '').strip()
    else:
        current_chunk += line + '\n'

# Add the last chunk
if current_chunk:
    chunks.append({
        'text': current_chunk.strip(),
        'metadata': {
            'source': faq_path,
            'question': current_title,
            'document_type': 'FAQ'
        }
    })

print(f"✓ Parsed FAQ into {len(chunks)} question-answer pairs")

# Initialize embeddings model
print("Loading embedding model...")
embedder = LocalEmbedder()
print("✓ Model loaded")

# Add to vector store
vs = VectorStore()
texts = [chunk['text'] for chunk in chunks]
metadatas = [chunk['metadata'] for chunk in chunks]

# Generate embeddings
print(f"Generating embeddings for {len(texts)} chunks...")
embeddings_list = embedder.embed_documents(texts)
print("✓ Embeddings generated")

# Generate IDs
ids = [hashlib.md5(text.encode()).hexdigest() for text in texts]

vs.add_documents(texts, embeddings_list, metadatas, ids)
print(f"✓ Successfully added {len(chunks)} FAQ entries to vector store")
print(f"✓ FAQ is now searchable in your RAG system")
