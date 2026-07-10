# main.py - Main menu

import sys
import os


def print_menu():
    print("\n" + "=" * 80)
    print("GOOGLE DRIVE RAG SYSTEM")
    print("=" * 80)
    print("\n1. Test Authentication")
    print("2. Index Specific Folders (Recommended for POC)")
    print("3. Start Q&A System (Command Line)")
    print("4. Check Status")
    print("5. Clear & Reset Index")
    print("6. Exit")
    print("\n---")
    print("To run the Web App, stop this and run: streamlit run app.py")
    print("=" * 80)


def test_auth():
    from auth import test_authentication
    test_authentication()


def run_folder_indexer():
    from folder_indexer import main as folder_main
    folder_main()


def run_rag():
    from rag_system import interactive_mode
    interactive_mode()

# --- NEW: Clear Index Function ---
def clear_index():
    print("\n" + "=" * 80)
    print("WARNING: This will delete all indexed data from ChromaDB")
    print("and clear the log of indexed folders.")
    print("=" * 80)
    
    confirm = input("Are you sure? (type 'yes' to confirm): ").strip().lower()
    
    if confirm == 'yes':
        try:
            from vector_store import VectorStore
            vs = VectorStore()
            vs.clear_collection()
            
            # Also clear the 'indexed_folders.json' log
            if os.path.exists('indexed_folders.json'):
                os.remove('indexed_folders.json')
                print("✓ Indexed folder log cleared.")
        except Exception as e:
            print(f"✗ Error during clearing: {e}")
    else:
        print("Cancelled.")


def check_status():
    print("\nChecking status...\n")
    
    files = ['credentials.json', 'config.py']
    for f in files:
        exists = "✓" if os.path.exists(f) else "✗"
        print(f"{exists} {f}")
    
    token = "✓" if os.path.exists('token.pickle') else "✗"
    print(f"{token} token.pickle (auth)")
    
    try:
        from vector_store import VectorStore
        vs = VectorStore()
        stats = vs.get_stats()
        print(f"✓ Vector DB: {stats['total_documents']} documents")
    except Exception as e:
        print(f"✗ Vector DB: {e}")
    
    from config import PROJECT_ID
    if PROJECT_ID == "YOUR_PROJECT_ID":
        print("✗ PROJECT_ID not set in config.py")
    else:
        print(f"✓ PROJECT_ID: {PROJECT_ID}")


def main():
    while True:
        print_menu()
        choice = input("Select (1-6): ").strip()
        
        if choice == '1':
            test_auth()
        elif choice == '2':
            run_folder_indexer()
        elif choice == '3':
            run_rag()
        elif choice == '4':
            check_status()
        elif choice == '5':
            clear_index()
        elif choice == '6':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)