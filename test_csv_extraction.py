import pandas as pd
import sys

# Test CSV extraction to see exactly what's being read
csv_path = r"C:\Users\Notxe\Downloads\Altoona-6 Month Sales Projection (2).csv"

print("Testing CSV extraction...")
print("="*80)

try:
    # Read the CSV
    df = pd.read_csv(csv_path)
    
    print(f"\nTotal rows read by pandas: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print(f"\nColumns: {list(df.columns)}")
    
    # Check January 2025 column
    if 'Jan-2025' in df.columns:
        jan_col = df['Jan-2025']
        # Convert to numeric, handling $ and commas
        jan_numeric = pd.to_numeric(jan_col.replace('[\$,]', '', regex=True), errors='coerce')
        total = jan_numeric.sum()
        non_zero = jan_numeric[jan_numeric > 0].count()
        
        print(f"\nJan-2025 Analysis:")
        print(f"  Non-zero entries: {non_zero}")
        print(f"  Total revenue: ${total:,.2f}")
        print(f"\nFirst 10 non-zero Jan-2025 values:")
        print(jan_numeric[jan_numeric > 0].head(10))
    
    # Now test what our document_loader would create
    print("\n" + "="*80)
    print("Testing document_loader extraction...")
    print("="*80)
    
    text_parts = ["[CSV Data - COMPLETE FILE]"]
    headers = " | ".join([str(col) for col in df.columns if str(col)])
    text_parts.append(f"Headers: {headers}")
    
    row_count = 0
    for idx, row in df.iterrows():
        row_text = " | ".join([str(val) for val in row.values if pd.notna(val) and str(val).strip()])
        if row_text:
            text_parts.append(row_text)
            row_count += 1
    
    full_text = "\n".join(text_parts)
    
    print(f"\nRows processed: {row_count}")
    print(f"Total text length: {len(full_text)} characters")
    print(f"Total text lines: {len(text_parts)}")
    print(f"\nFirst 500 characters:")
    print(full_text[:500])
    print(f"\nLast 500 characters:")
    print(full_text[-500:])
    
    # Check for the marker
    has_marker = "COMPLETE FILE" in full_text[:200]
    print(f"\nHas COMPLETE FILE marker in first 200 chars: {has_marker}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
