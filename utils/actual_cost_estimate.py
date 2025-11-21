"""
ACTUAL Cost Estimation for 7MM Resources Drive
Based on real data: 4,500 text files (7.94 GB, 2.1B tokens) + 1,000 images
"""

# Your actual data
TEXT_FILES = 4500
TOTAL_GB = 7.94
TOTAL_TOKENS = 2_100_000_000  # 2.1 billion tokens
IMAGES = 1000

# Pricing (November 2025)
VERTEX_EMBEDDING_COST_PER_1M_CHARS = 0.025  # $0.025 per 1M characters
DOCUMENTAI_COST_PER_PAGE = 0.0015  # $1.50 per 1,000 pages

# Conversions
# 1 token ≈ 4 characters (industry standard)
TOTAL_CHARS = TOTAL_TOKENS * 4
AVG_PAGES_PER_IMAGE = 1  # Images = 1 page each

print("=" * 80)
print("COST ESTIMATION FOR 7MM RESOURCES FULL INDEXING")
print("=" * 80)
print(f"\nYour Drive Contents:")
print(f"  Text files: {TEXT_FILES:,}")
print(f"  Total size: {TOTAL_GB:.2f} GB")
print(f"  Total tokens: {TOTAL_TOKENS:,}")
print(f"  Images: {IMAGES:,}")
print()

# 1. Vertex AI Embeddings Cost
print("=" * 80)
print("1. VERTEX AI EMBEDDINGS (text-embedding-004)")
print("=" * 80)
print(f"  Total characters: {TOTAL_CHARS:,}")
print(f"  Cost per 1M chars: ${VERTEX_EMBEDDING_COST_PER_1M_CHARS}")
embedding_cost = (TOTAL_CHARS / 1_000_000) * VERTEX_EMBEDDING_COST_PER_1M_CHARS
print(f"  TOTAL COST: ${embedding_cost:.2f}")
print()

# 2. Document AI OCR Cost
print("=" * 80)
print("2. DOCUMENT AI OCR (images only)")
print("=" * 80)
print(f"  Images to process: {IMAGES:,}")
print(f"  Total pages: {IMAGES:,} (1 page per image)")
print(f"  Cost per page: ${DOCUMENTAI_COST_PER_PAGE}")
documentai_cost = IMAGES * DOCUMENTAI_COST_PER_PAGE
print(f"  TOTAL COST: ${documentai_cost:.2f}")
print()

# 3. Total Cost
print("=" * 80)
print("TOTAL ESTIMATED COST")
print("=" * 80)
total_cost = embedding_cost + documentai_cost
print(f"  Vertex AI Embeddings:  ${embedding_cost:>8.2f}")
print(f"  Document AI OCR:       ${documentai_cost:>8.2f}")
print(f"  " + "-" * 30)
print(f"  TOTAL:                 ${total_cost:>8.2f}")
print("=" * 80)
print()

# 4. Cost per query (ongoing)
print("=" * 80)
print("ONGOING QUERY COSTS (after indexing)")
print("=" * 80)
GEMINI_FLASH_INPUT_COST = 0.075 / 1_000_000  # $0.075 per 1M tokens
GEMINI_FLASH_OUTPUT_COST = 0.30 / 1_000_000  # $0.30 per 1M tokens
AVG_CONTEXT_TOKENS = 3000  # Average context retrieved per query
AVG_OUTPUT_TOKENS = 500  # Average response length

query_input_cost = AVG_CONTEXT_TOKENS * GEMINI_FLASH_INPUT_COST
query_output_cost = AVG_OUTPUT_TOKENS * GEMINI_FLASH_OUTPUT_COST
query_total = query_input_cost + query_output_cost

print(f"  Model: Gemini 2.5 Flash")
print(f"  Average context: {AVG_CONTEXT_TOKENS:,} tokens")
print(f"  Average response: {AVG_OUTPUT_TOKENS:,} tokens")
print(f"  Cost per query: ${query_total:.6f}")
print(f"  Cost per 1,000 queries: ${query_total * 1000:.2f}")
print(f"  Cost per 10,000 queries: ${query_total * 10000:.2f}")
print()

# 5. Monthly estimates
print("=" * 80)
print("MONTHLY COST ESTIMATES (100 users)")
print("=" * 80)
queries_per_user_per_day = 5
users = 100
days_per_month = 30
monthly_queries = queries_per_user_per_day * users * days_per_month
monthly_cost = monthly_queries * query_total

print(f"  Users: {users}")
print(f"  Queries per user/day: {queries_per_user_per_day}")
print(f"  Total queries/month: {monthly_queries:,}")
print(f"  Monthly query cost: ${monthly_cost:.2f}")
print()

# 6. First year total
print("=" * 80)
print("FIRST YEAR TOTAL")
print("=" * 80)
first_year = total_cost + (monthly_cost * 12)
print(f"  One-time indexing:     ${total_cost:>8.2f}")
print(f"  12 months of queries:  ${monthly_cost * 12:>8.2f}")
print(f"  " + "-" * 30)
print(f"  FIRST YEAR TOTAL:      ${first_year:>8.2f}")
print("=" * 80)
print()

# 7. Cost breakdown
print("IMPORTANT NOTES:")
print("  ✓ Text files (Docs/Sheets): FREE export (no OCR)")
print("  ✓ Only images use Document AI OCR")
print("  ✓ Embeddings cached - reindexing same content is FREE")
print("  ✓ Google Cloud free tier: $300 credits")
print(f"  ✓ Free tier covers: {300/total_cost:.1f}x full reindexing")
print(f"  ✓ Or: {300/monthly_cost:.1f} months of queries (100 users)")
print()
print("OPTIMIZATION TIPS:")
print("  • Index only folders you need (not all 4,500 files)")
print("  • Skip large images if text alternative exists")
print("  • Cache embeddings to avoid reprocessing")
print("  • Use query cache to reduce duplicate API calls")
