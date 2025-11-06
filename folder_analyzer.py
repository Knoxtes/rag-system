"""
Folder Hierarchy Analyzer
Analyzes the folder structure CSV and provides insights
"""

import csv
import os
from collections import defaultdict, Counter


def analyze_folder_structure(csv_path):
    """Analyze the folder structure from CSV"""
    
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        print("Please provide the correct path to your folder structure CSV.")
        return
    
    print("=" * 80)
    print("📊 FOLDER STRUCTURE ANALYSIS")
    print("=" * 80)
    
    folders = []
    markets = set()
    years = set()
    categories = defaultdict(int)
    depth_distribution = Counter()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            folders.append(row)
            
            # Extract depth
            depth = int(row.get('Level', 0))
            depth_distribution[depth] += 1
            
            # Extract markets (level 2 under Market Resources)
            path = row.get('Folder Path', '')
            if path.startswith('Drive/Market Resources/'):
                parts = path.split('/')
                if len(parts) >= 3:
                    markets.add(parts[2])
            
            # Extract years
            folder_name = row.get('Folder Name', '')
            if folder_name.startswith('20') and folder_name[:4].isdigit():
                years.add(folder_name[:4])
            
            # Extract categories (level 3 folders)
            if depth == 3:
                categories[folder_name] += 1
    
    # Print summary
    print(f"\n📁 Total Folders: {len(folders)}")
    print(f"📊 Max Depth: {max(depth_distribution.keys())}")
    print(f"🌳 Average Depth: {sum(d*c for d,c in depth_distribution.items()) / len(folders):.1f}")
    
    print(f"\n🏢 Markets Identified: {len(markets)}")
    for market in sorted(markets):
        print(f"   - {market}")
    
    print(f"\n📅 Years Found: {len(years)}")
    for year in sorted(years):
        print(f"   - {year}")
    
    print(f"\n📂 Depth Distribution:")
    for depth in sorted(depth_distribution.keys()):
        count = depth_distribution[depth]
        bar = "█" * (count // 20)
        print(f"   Level {depth}: {count:4d} folders {bar}")
    
    print(f"\n🔝 Top 15 Categories (Level 3 folders):")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"   {count:3d}x {category}")
    
    # Find deepest paths
    print(f"\n🌲 Deepest Folder Paths (Level {max(depth_distribution.keys())}):")
    deep_paths = [f for f in folders if int(f.get('Level', 0)) == max(depth_distribution.keys())]
    for folder in deep_paths[:5]:
        path = folder.get('Folder Path', '')
        # Shorten path for display
        path_parts = path.split('/')
        if len(path_parts) > 4:
            short_path = '/'.join(path_parts[:2]) + '/.../' + '/'.join(path_parts[-2:])
        else:
            short_path = path
        print(f"   {short_path}")
    
    print("\n" + "=" * 80)
    print("✅ Analysis Complete!")
    print("=" * 80)
    
    return {
        "total_folders": len(folders),
        "markets": sorted(markets),
        "years": sorted(years),
        "max_depth": max(depth_distribution.keys()),
        "top_categories": dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)[:20])
    }


if __name__ == "__main__":
    # Try to find the CSV
    possible_paths = [
        r"c:\Users\Notxe\Downloads\Untitled spreadsheet - Folder Structure.csv",
        "Folder Structure.csv",
        "../Folder Structure.csv"
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if csv_path:
        print(f"📄 Found CSV: {csv_path}\n")
        analyze_folder_structure(csv_path)
    else:
        print("❌ Could not find folder structure CSV.")
        print("Please provide the path as argument:")
        print('   python folder_analyzer.py "path/to/your/Folder Structure.csv"')
