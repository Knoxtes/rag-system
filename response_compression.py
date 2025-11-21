# response_compression.py - Compress large API responses for faster transfer

import gzip
import base64
import json
from typing import Any, Dict
from config import ENABLE_RESPONSE_COMPRESSION, COMPRESSION_THRESHOLD


def should_compress(data: Dict[str, Any]) -> bool:
    """
    Determine if response should be compressed based on size.
    
    Args:
        data: Response data dictionary
        
    Returns:
        True if compression would be beneficial
    """
    if not ENABLE_RESPONSE_COMPRESSION:
        return False
    
    # Estimate JSON size
    try:
        json_str = json.dumps(data, ensure_ascii=False)
        size_bytes = len(json_str.encode('utf-8'))
        return size_bytes > COMPRESSION_THRESHOLD
    except:
        return False


def compress_text(text: str) -> Dict[str, str]:
    """
    Compress text and return base64-encoded compressed data.
    
    Args:
        text: Text to compress
        
    Returns:
        Dict with 'compressed' (base64 string) and 'original_size', 'compressed_size'
    """
    try:
        # Compress
        text_bytes = text.encode('utf-8')
        compressed = gzip.compress(text_bytes, compresslevel=6)  # Balance speed/ratio
        
        # Base64 encode for JSON transport
        compressed_b64 = base64.b64encode(compressed).decode('ascii')
        
        return {
            'compressed': compressed_b64,
            'original_size': len(text_bytes),
            'compressed_size': len(compressed),
            'encoding': 'gzip+base64'
        }
    except Exception as e:
        print(f"❌ Compression error: {e}")
        return None


def decompress_text(compressed_b64: str) -> str:
    """
    Decompress base64-encoded gzipped text.
    
    Args:
        compressed_b64: Base64-encoded compressed data
        
    Returns:
        Original text
    """
    try:
        # Decode base64
        compressed = base64.b64decode(compressed_b64)
        
        # Decompress
        decompressed = gzip.decompress(compressed)
        
        return decompressed.decode('utf-8')
    except Exception as e:
        print(f"❌ Decompression error: {e}")
        return None


def compress_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compress large fields in response data.
    
    Performance Impact: 70-80% reduction in transfer size for large responses
    
    Args:
        data: Response dictionary
        
    Returns:
        Modified response with compressed fields
    """
    if not should_compress(data):
        return data
    
    compressed_data = data.copy()
    compression_applied = False
    
    # Compress answer field if large
    if 'answer' in compressed_data and isinstance(compressed_data['answer'], str):
        answer_size = len(compressed_data['answer'].encode('utf-8'))
        
        if answer_size > 10000:  # 10KB threshold for answer
            compressed_answer = compress_text(compressed_data['answer'])
            
            if compressed_answer:
                # Calculate compression ratio
                ratio = compressed_answer['compressed_size'] / compressed_answer['original_size']
                
                # Only compress if we get >30% reduction
                if ratio < 0.7:
                    compressed_data['answer_compressed'] = compressed_answer['compressed']
                    compressed_data['answer'] = f"[COMPRESSED: {compressed_answer['original_size']} bytes → {compressed_answer['compressed_size']} bytes]"
                    compressed_data['compression_encoding'] = 'gzip+base64'
                    compression_applied = True
    
    # Compress document content if present
    if 'documents' in compressed_data and isinstance(compressed_data['documents'], list):
        for doc in compressed_data['documents']:
            if 'content' in doc and isinstance(doc['content'], str):
                content_size = len(doc['content'].encode('utf-8'))
                
                if content_size > 5000:  # 5KB threshold for document content
                    compressed_content = compress_text(doc['content'])
                    
                    if compressed_content:
                        ratio = compressed_content['compressed_size'] / compressed_content['original_size']
                        
                        if ratio < 0.7:
                            doc['content_compressed'] = compressed_content['compressed']
                            doc['content'] = f"[COMPRESSED: {compressed_content['original_size']} bytes]"
                            doc['compression_encoding'] = 'gzip+base64'
                            compression_applied = True
    
    # Add metadata if compression was applied
    if compression_applied:
        compressed_data['_compression'] = {
            'enabled': True,
            'encoding': 'gzip+base64',
            'note': 'Decompress compressed fields on client side'
        }
    
    return compressed_data


def get_compression_stats(original_data: Dict, compressed_data: Dict) -> Dict[str, Any]:
    """Get compression statistics for monitoring"""
    try:
        original_size = len(json.dumps(original_data, ensure_ascii=False).encode('utf-8'))
        compressed_size = len(json.dumps(compressed_data, ensure_ascii=False).encode('utf-8'))
        
        return {
            'original_bytes': original_size,
            'compressed_bytes': compressed_size,
            'reduction_bytes': original_size - compressed_size,
            'reduction_percent': round((1 - compressed_size / original_size) * 100, 2) if original_size > 0 else 0,
            'compression_ratio': round(compressed_size / original_size, 3) if original_size > 0 else 1.0
        }
    except:
        return {'error': 'Failed to calculate stats'}


if __name__ == "__main__":
    # Test compression
    print("🧪 Testing response compression...\n")
    
    # Test large response
    test_response = {
        'answer': "This is a very long answer. " * 1000,  # ~30KB
        'documents': [
            {
                'filename': 'test.pdf',
                'content': "Document content here. " * 500,  # ~15KB
                'url': 'https://example.com/test.pdf'
            }
        ]
    }
    
    print(f"Original response size: {len(json.dumps(test_response).encode('utf-8'))} bytes")
    
    # Compress
    compressed = compress_response(test_response)
    
    print(f"Compressed response size: {len(json.dumps(compressed).encode('utf-8'))} bytes")
    
    # Get stats
    stats = get_compression_stats(test_response, compressed)
    print(f"\n📊 Compression Stats:")
    print(f"  Original: {stats['original_bytes']} bytes")
    print(f"  Compressed: {stats['compressed_bytes']} bytes")
    print(f"  Reduction: {stats['reduction_bytes']} bytes ({stats['reduction_percent']}%)")
    print(f"  Ratio: {stats['compression_ratio']}")
    
    # Test decompression
    if 'answer_compressed' in compressed:
        decompressed_answer = decompress_text(compressed['answer_compressed'])
        matches = decompressed_answer == test_response['answer']
        print(f"\n✓ Decompression {'successful' if matches else 'FAILED'}")
