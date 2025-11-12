# view_logs.py - Utility to view answer logs

import json
from datetime import datetime
from answer_logger import AnswerLogger

def main():
    """View recent answer logs in a clean format"""
    
    logger = AnswerLogger()
    
    print("📋 RAG SYSTEM ANSWER LOG VIEWER")
    print("=" * 50)
    
    # Get statistics
    stats = logger.get_stats()
    
    print(f"\n📊 LOG STATISTICS:")
    print(f"  Total entries: {stats['total_entries']}")
    if stats['total_entries'] > 0:
        print(f"  First entry: {stats['first_entry']}")
        print(f"  Last entry: {stats['last_entry']}")
        print(f"  Average response time: {stats['average_response_time']}")
        print(f"  Cache hit rate: {stats['cache_hit_rate']}")
        print(f"  Log file size: {stats['log_file_size']} bytes")
    
    if stats['total_entries'] == 0:
        print("\n📭 No entries found. Start using the RAG system to generate logs!")
        return
    
    print(f"\n" + "=" * 50)
    
    while True:
        print(f"\nOPTIONS:")
        print(f"  1. View recent entries (last 5)")
        print(f"  2. View recent entries (last 10)")
        print(f"  3. Search logs")
        print(f"  4. Export logs")
        print(f"  5. View plain text log file")
        print(f"  6. Exit")
        
        choice = input(f"\nSelect option (1-6): ").strip()
        
        if choice == '1':
            show_recent_entries(logger, 5)
        elif choice == '2':
            show_recent_entries(logger, 10)
        elif choice == '3':
            search_logs(logger)
        elif choice == '4':
            export_logs(logger)
        elif choice == '5':
            show_plain_text_log(logger)
        elif choice == '6':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please choose 1-6.")

def show_recent_entries(logger: AnswerLogger, count: int):
    """Show recent log entries"""
    
    entries = logger.get_recent_logs(count)
    
    print(f"\n📝 LAST {count} ENTRIES:")
    print("-" * 40)
    
    for i, entry in enumerate(reversed(entries), 1):  # Show newest first
        timestamp = datetime.fromisoformat(entry['timestamp'])
        
        print(f"\n{i}. {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Q: {entry['question'][:80]}{'...' if len(entry['question']) > 80 else ''}")
        print(f"   A: {entry['answer'][:100]}{'...' if len(entry['answer']) > 100 else ''}")
        
        metadata = entry.get('metadata', {})
        if metadata:
            details = []
            if metadata.get('cached'):
                details.append("CACHED")
            if metadata.get('response_time'):
                details.append(f"{metadata['response_time']:.2f}s")
            if metadata.get('query_type'):
                details.append(metadata['query_type'])
            
            if details:
                print(f"   ({', '.join(details)})")

def search_logs(logger: AnswerLogger):
    """Search through logs"""
    
    query = input(f"\n🔍 Enter search term: ").strip()
    if not query:
        print("❌ Please enter a search term.")
        return
    
    results = logger.search_logs(query, limit=20)
    
    print(f"\n🔍 SEARCH RESULTS for '{query}': {len(results)} found")
    print("-" * 50)
    
    if not results:
        print("No matches found.")
        return
    
    for i, entry in enumerate(results, 1):
        timestamp = datetime.fromisoformat(entry['timestamp'])
        
        print(f"\n{i}. {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Q: {entry['question']}")
        
        # Highlight search term in answer (simple highlighting)
        answer = entry['answer']
        if query.lower() in answer.lower():
            # Find the context around the search term
            start_idx = max(0, answer.lower().find(query.lower()) - 50)
            end_idx = min(len(answer), start_idx + 200)
            context = answer[start_idx:end_idx]
            if start_idx > 0:
                context = "..." + context
            if end_idx < len(answer):
                context = context + "..."
            print(f"   A: {context}")
        else:
            print(f"   A: {answer[:100]}{'...' if len(answer) > 100 else ''}")

def export_logs(logger: AnswerLogger):
    """Export logs in different formats"""
    
    print(f"\n📤 EXPORT OPTIONS:")
    print(f"  1. Plain text (.txt)")
    print(f"  2. CSV (.csv)")
    print(f"  3. JSON (.json)")
    
    choice = input(f"\nSelect format (1-3): ").strip()
    
    formats = {'1': 'txt', '2': 'csv', '3': 'json'}
    
    if choice not in formats:
        print("❌ Invalid choice.")
        return
    
    format_type = formats[choice]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"rag_logs_export_{timestamp}.{format_type}"
    
    try:
        logger.export_logs(filename, format_type)
        print(f"✅ Logs exported to: {filename}")
    except Exception as e:
        print(f"❌ Export failed: {e}")

def show_plain_text_log(logger: AnswerLogger):
    """Show the plain text log file contents"""
    
    try:
        with open(logger.log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n📄 PLAIN TEXT LOG CONTENTS:")
        print("=" * 60)
        print(content)
        print("=" * 60)
        
        print(f"\n💡 TIP: You can copy-paste directly from the above content!")
        print(f"Log file location: {logger.log_file}")
        
    except FileNotFoundError:
        print(f"❌ Log file not found: {logger.log_file}")
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

if __name__ == "__main__":
    main()