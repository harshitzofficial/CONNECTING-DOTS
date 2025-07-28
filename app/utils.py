# Utility functions (see previous chat for full code)
"""
Utility functions for document processing
"""

import logging
import hashlib
import re
from pathlib import Path
from typing import List, Optional
import fitz

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/app/output/processing.log')
        ]
    )

def validate_pdf(pdf_path: Path) -> bool:
    """Validate PDF file"""
    try:
        if not pdf_path.exists():
            return False
        
        if pdf_path.stat().st_size == 0:
            return False
        
        # Try to open with PyMuPDF
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
        
        # Check constraints
        if page_count == 0 or page_count > 50:
            return False
        
        return True
        
    except Exception:
        return False

def get_file_hash(file_path: Path) -> str:
    """Get SHA256 hash of file"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return ""

def chunk_text(text: str, max_tokens: int = 200, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks"""
    if not text:
        return []
    
    words = text.split()
    if len(words) <= max_tokens:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(words):
        end = min(start + max_tokens, len(words))
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        
        if end >= len(words):
            break
            
        start = end - overlap
    
    return chunks

def remove_stopwords(text: str, additional_stopwords: List[str] = None) -> str:
    """Remove stopwords from text"""
    # Basic English stopwords
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
    }
    
    if additional_stopwords:
        stopwords.update(additional_stopwords)
    
    words = text.lower().split()
    filtered_words = [word for word in words if word not in stopwords]
    
    return ' '.join(filtered_words)

def detect_language(text: str) -> str:
    """Simple language detection"""
    # Very basic language detection
    # In production, use a proper language detection library
    
    # Check for common English patterns
    english_indicators = ['the', 'and', 'or', 'is', 'are', 'was', 'were', 'a', 'an']
    english_count = sum(1 for word in english_indicators if word in text.lower())
    
    if english_count > 3:
        return 'en'
    
    return 'unknown'

def clean_json_output(data: dict) -> dict:
    """Clean JSON output for consistent formatting"""
    if isinstance(data, dict):
        return {k: clean_json_output(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [clean_json_output(item) for item in data]
    elif isinstance(data, str):
        return data.strip()
    else:
        return data
