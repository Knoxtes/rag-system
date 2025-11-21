"""
Cost Estimation for Full Indexing Run
Based on actual indexing from indexed_folders.json
"""

import json

# Load indexed data
with open('indexed_folders.json') as f:
    folders = json.load(f)

# Pricing (as of 2025)
VERTEX_EMBEDDING_COST_PER_1K_CHARS = 0.000025  # $0.025 per 1M chars = $0.000025 per 1K chars
DOCUMENTAI_COST_PER_PAGE = 0.0015  # $1.50 per 1,000 pages = $0.0015 per page

# Assumptions
AVG_CHARS_PER_DOCUMENT = 2000  # Average characters per file before chunking
AVG_PAGES_PER_PDF = 5  # Average pages in PDF files
PDF_RATIO = 0.3  # Estimate 30% of files are PDFs needing OCR

# Calculate totals
total_files = sum(folder['file_count'] for folder in folders.values())
total_folders = len(folders)

print("=" * 70)
print("COST ESTIMATION FOR FULL INDEXING")
print("=" * 70)
print(f"\nIndexing Summary:")
print(f"  Folders indexed: {total_folders}")
print(f"  Total files: {total_files}")
print()

# Vertex AI Embeddings Cost
total_chars = total_files * AVG_CHARS_PER_DOCUMENT
embedding_cost = (total_chars / 1000) * VERTEX_EMBEDDING_COST_PER_1K_CHARS

print("Vertex AI Embeddings:")
print(f"  Estimated total characters: {total_chars:,}")
print(f"  Cost: ${embedding_cost:.4f}")
print()

# Document AI OCR Cost (only for PDFs)
pdf_files = int(total_files * PDF_RATIO)
total_pages = pdf_files * AVG_PAGES_PER_PDF
documentai_cost = total_pages * DOCUMENTAI_COST_PER_PAGE

print("Document AI OCR:")
print(f"  Estimated PDF files: {pdf_files}")
print(f"  Estimated pages: {total_pages}")
print(f"  Cost: ${documentai_cost:.4f}")
print()

# Total
total_cost = embedding_cost + documentai_cost

print("=" * 70)
print(f"TOTAL ESTIMATED COST: ${total_cost:.2f}")
print("=" * 70)
print()

# Cost breakdown by folder
print("Cost by Folder (top 5 most expensive):")
folder_costs = []
for folder_id, info in folders.items():
    files = info['file_count']
    chars = files * AVG_CHARS_PER_DOCUMENT
    emb_cost = (chars / 1000) * VERTEX_EMBEDDING_COST_PER_1K_CHARS
    
    pdfs = int(files * PDF_RATIO)
    pages = pdfs * AVG_PAGES_PER_PDF
    ocr_cost = pages * DOCUMENTAI_COST_PER_PAGE
    
    folder_total = emb_cost + ocr_cost
    folder_costs.append((info['name'], files, folder_total))

folder_costs.sort(key=lambda x: x[2], reverse=True)
for name, files, cost in folder_costs[:5]:
    print(f"  {name:30s}: ${cost:.4f} ({files} files)")

print()
print("Notes:")
print("  • Actual costs may vary based on file sizes")
print("  • Google Sheets/Docs export is FREE (no OCR needed)")
print("  • Only binary files (PDFs, images) use Document AI")
print("  • Embeddings are cached - reindexing same content costs less")
print("  • First $300 in Google Cloud credits may cover this")
