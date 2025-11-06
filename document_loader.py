# document_loader.py - Load and process all file types with Shared Drive support

import io
from googleapiclient.http import MediaIoBaseDownload
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from pptx import Presentation
import pandas as pd
from config import (
    CHUNK_SIZE, 
    CHUNK_OVERLAP, 
    USE_PARENT_DOCUMENT_RETRIEVAL, 
    PARENT_CHUNK_SIZE
)
# --- OPTIMIZATION: Use Langchain for robust, standard chunning ---
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re


class GoogleDriveLoader:
    """Download and process files from Google Drive and Shared Drives"""
    
    def __init__(self, service):
        self.service = service
    
    # --- REMOVED: list_files() method was unused (dead code) ---
    
    def download_file(self, file_id):
        """Download file content"""
        try:
            request = self.service.files().get_media(fileId=file_id, supportsAllDrives=True)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_content.seek(0)
            return file_content
        except Exception as e:
            print(f"  Error downloading: {e}")
            return None
    
    def export_google_doc(self, file_id):
        """Export Google Docs as text"""
        try:
            request = self.service.files().export_media(
                fileId=file_id, 
                mimeType='text/plain'
            )
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            return file_content.getvalue().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"  Error exporting: {e}")
            return None
    
    def export_google_slides(self, file_id):
        """Export Google Slides as text"""
        # Slides export to text/plain is surprisingly effective
        return self.export_google_doc(file_id)
    
    def export_google_sheets(self, file_id):
        """Export Google Sheets as CSV"""
        try:
            request = self.service.files().export_media(
                fileId=file_id, 
                mimeType='text/csv'
            )
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            return file_content.getvalue().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"  Error exporting: {e}")
            return None

# --- Text Extraction Functions (Largely Unchanged) ---

def extract_text_from_pptx(file_content):
    """Extract text from PowerPoint"""
    try:
        prs = Presentation(file_content)
        text_parts = []
        
        for slide_num, slide in enumerate(prs.slides, 1):
            slide_text = [f"[Slide {slide_num}]"]
            
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text.strip())
            
            # Only add slide if it has text content
            if len(slide_text) > 1:
                text_parts.append("\n".join(slide_text))
        
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"  Error extracting PPTX: {e}")
        return ""


def extract_text_from_xlsx(file_content):
    """Extract text from Excel"""
    try:
        df_dict = pd.read_excel(file_content, sheet_name=None, engine='openpyxl')
        text_parts = []
        
        for sheet_name, df in df_dict.items():
            # Skip empty sheets
            if df.empty:
                continue
                
            sheet_text = [f"[Sheet: {sheet_name}]"]
            
            headers = " | ".join([str(col) for col in df.columns if str(col)])
            sheet_text.append(f"Headers: {headers}")
            
            # Index ALL rows
            for idx, row in df.iterrows():
                row_text = " | ".join([str(val) for val in row.values if pd.notna(val) and str(val).strip()])
                if row_text:
                    sheet_text.append(row_text)
            
            text_parts.append("\n".join(sheet_text))
        
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"  Error extracting Excel: {e}")
        return ""


def extract_text_from_csv(file_content):
    """Extract text from CSV"""
    try:
        file_content.seek(0)
        # Try to read with a safety limit first
        df = pd.read_csv(file_content, nrows=50000) # Limit to 50k rows for safety
        
        text_parts = ["[CSV Data]"]
        headers = " | ".join([str(col) for col in df.columns if str(col)])
        text_parts.append(f"Headers: {headers}")
        
        # Index ALL loaded rows
        for idx, row in df.iterrows():
            row_text = " | ".join([str(val) for val in row.values if pd.notna(val) and str(val).strip()])
            if row_text:
                text_parts.append(row_text)
        
        return "\n".join(text_parts)
    except Exception as e:
        # Fallback for very large or malformed CSVs
        print(f"  Pandas CSV read failed ({e}), falling back to raw text.")
        file_content.seek(0)
        return file_content.read().decode('utf-8', errors='ignore')


def extract_text(file_content, mime_type):
    """Extract text from any supported file type"""
    try:
        if mime_type == 'application/pdf':
            pdf_reader = PdfReader(file_content)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        
        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            doc = DocxDocument(file_content)
            processed_paragraphs = []
            current_heading = ""
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                
                # Check for built-in heading styles
                if para.style and para.style.name.lower().startswith('heading'):
                    current_heading = text
                    processed_paragraphs.append(f"\n\n[TOPIC: {current_heading}]\n")
                # Fallback heuristic
                elif para.style and para.style.name.lower().startswith('title') or (text.isupper() and len(text.split()) < 10):
                    current_heading = text
                    processed_paragraphs.append(f"\n\n[TOPIC: {current_heading}]\n")
                else:
                    # Prepend context
                    if current_heading:
                        processed_paragraphs.append(f"[{current_heading}] {text}")
                    else:
                        processed_paragraphs.append(text)
                        
            return "\n".join(processed_paragraphs)
        
        elif mime_type in ['application/vnd.openxmlformats-officedocument.presentationml.presentation',
                           'application/vnd.ms-powerpoint']:
            return extract_text_from_pptx(file_content)
        
        elif mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            return extract_text_from_xlsx(file_content)
        
        elif mime_type == 'text/csv':
            return extract_text_from_csv(file_content)
        
        elif mime_type == 'text/plain':
            return file_content.read().decode('utf-8', errors='ignore')
        
        else:
            return ""
    except Exception as e:
        print(f"  Error extracting text: {e}")
        return ""


# --- ENHANCED: Semantic-aware text splitters ---

# Primary splitter - for child chunks (used in retrieval)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=lambda text: len(text.split()),  # Use word count
    separators=["\n\n\n", "\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""],  # Semantic boundaries
    is_separator_regex=False
)

# Parent splitter - for parent document retrieval (larger context)
parent_splitter = None
if USE_PARENT_DOCUMENT_RETRIEVAL:
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=PARENT_CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP * 2,  # More overlap for parent chunks
        length_function=lambda text: len(text.split()),
        separators=["\n\n\n", "\n\n", "\n", ". ", " ", ""],
        is_separator_regex=False
    )


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP, return_parents=False):
    """
    Recursively split text into overlapping chunks using Langchain.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in words
        overlap: Overlap size in words
        return_parents: If True and parent retrieval enabled, return (child_chunks, parent_chunks)
    
    Returns:
        List of text chunks, or tuple of (child_chunks, parent_chunks) if return_parents=True
    """
    if not text or len(text.strip()) == 0:
        return [] if not return_parents else ([], [])
    
    # Get child chunks
    child_chunks = text_splitter.split_text(text)
    
    # Optionally get parent chunks
    if return_parents and USE_PARENT_DOCUMENT_RETRIEVAL and parent_splitter:
        parent_chunks = parent_splitter.split_text(text)
        return (child_chunks, parent_chunks)
    
    return child_chunks

# --- DELETED: Old _split_text_with_overlap and old chunk_text ---

