# main.py - Main menu
import sys
import os
import json
from config import INDEXED_FOLDERS_FILE

# Validate startup configuration
try:
    from startup_validation import validate_startup
    if not validate_startup():
        print("\n⚠️  System has validation errors. Please fix them before continuing.")
        print("Some features may not work properly.")
        response = input("\nContinue anyway? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Exiting...")
            sys.exit(1)
except ImportError:
    print("⚠️  startup_validation.py not found. Skipping validation checks.")

# --- REMOVED: Debug prints for google.generativeai ---

def print_menu():
    print("\n" + "=" * 80)
    print("GOOGLE DRIVE RAG SYSTEM")
    print("=" * 80)
    print("\n1. Test Authentication")
    print("2. Index Specific Folders (Creates separate chat modes)")
    print("3. 🌟 Unified Q&A System (Smart search across ALL folders)")
    print("4. Individual Folder Q&A System (Legacy mode)")
    print("5. Check Status")
    print("6. Clear & Reset ALL Indexes")
    print("7. Exit")
    print("\n---")
    # --- ✅ FIX: Corrected filename ---
    print("To run the Web App, stop this and run: streamlit run app.py")
    print("=" * 80)


def test_auth():
    from auth import test_authentication
    test_authentication()


def run_folder_indexer():
    from folder_indexer import main as folder_main
    folder_main()


def load_indexed_folders():
    """Helper to load the folder log"""
    if os.path.exists(INDEXED_FOLDERS_FILE):
        with open(INDEXED_FOLDERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def select_chat_mode():
    """
    Asks the user which indexed folder (collection) they want to chat with.
    Returns the collection_name and display_name if one is selected.
    """
    print("\n" + "=" * 80)
    print("SELECT CHAT MODE")
    print("=" * 80)
    
    indexed_folders = load_indexed_folders()
    
    if not indexed_folders:
        print("\n⚠️  No folders have been indexed yet!")
        print("Please run option 2 'Index Specific Folders' first.")
        return None, None
        
    print("\nWhich topic do you want to chat about?\n")
    
    # Create a list of tuples: (folder_id, folder_info)
    folder_list = list(indexed_folders.items())
    
    for i, (folder_id, info) in enumerate(folder_list, 1):
        print(f"{i}. {info['name']} ({info['location']})")
        print(f"   (Files processed: {info.get('files_processed', 'N/A')}, Last indexed: {info.get('indexed_at', 'N/A')})")

    print("\n" + "=" * 80)
    
    try:
        choice = input(f"Select (1-{len(folder_list)}): ").strip()
        choice_idx = int(choice) - 1
        
        if 0 <= choice_idx < len(folder_list):
            folder_id, info = folder_list[choice_idx]
            collection_name = info.get('collection_name')
            display_name = f"{info['name']} ({info['location']})"
            
            if not collection_name:
                print(f"✗ Error: Folder '{info['name']}' is in the log but has no 'collection_name'.")
                print("Try re-indexing this folder.")
                return None, None
                
            return collection_name, display_name
        else:
            print("Invalid selection.")
            return None, None
            
    except ValueError:
        print("Invalid input.")
        return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

def run_unified_rag():
    """
    Start the unified RAG system that searches across all collections
    with intelligent folder routing
    """
    from unified_rag_system import interactive_unified_mode
    interactive_unified_mode()

def run_legacy_rag():
    """
    Legacy mode: Prompts user to select a chat mode first, then starts
    the interactive mode for that specific collection.
    """
    from rag_system import interactive_mode
    
    collection_name, display_name = select_chat_mode()
    
    if collection_name and display_name:
        interactive_mode(
            collection_name=collection_name,
            collection_display_name=display_name
        )

def clear_index():
    print("\n" + "=" * 80)
    print("WARNING: This will delete ALL indexed data from ChromaDB")
    print("and clear the log of indexed folders.")
    print("This will delete ALL collections, not just one.")
    print("=" * 80)
    
    confirm = input("Are you sure? (type 'yes' to confirm): ").strip().lower()
    
    if confirm == 'yes':
        try:
            from vector_store import VectorStore
            # Init default store just to get the client
            # Pass a dummy name, we just need the client object
            vs = VectorStore(collection_name="temp.admin.collection") 
            
            all_collections = vs.list_all_collections()
            
            if not all_collections or all_collections == ["temp.admin.collection"]:
                print("No collections found in database.")
            else:
                print(f"Found {len(all_collections)} collections to delete...")
                for col_name in all_collections:
                    if col_name == "temp.admin.collection": continue
                    vs.delete_collection_by_name(col_name)
            
            # Delete the temp collection
            vs.delete_collection_by_name("temp.admin.collection")
            
            # Also clear the 'indexed_folders.json' log
            if os.path.exists(INDEXED_FOLDERS_FILE):
                os.remove(INDEXED_FOLDERS_FILE)
                print(f"✓ {INDEXED_FOLDERS_FILE} log cleared.")
            
            print("\n✓ All indexes and logs cleared.")
            
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
    
    indexed_log = "✓" if os.path.exists(INDEXED_FOLDERS_FILE) else "✗"
    print(f"{indexed_log} {INDEXED_FOLDERS_FILE} (log of indexed folders)")

    try:
        from vector_store import VectorStore
        vs = VectorStore(collection_name="temp.admin.collection") # Use dummy name
        collections = vs.list_all_collections()
        print(f"✓ Vector DB Client OK. Found {len(collections)} collections:")
        count = 0
        for col_name in collections:
            if col_name == "temp.admin.collection": continue
            stats = VectorStore(collection_name=col_name).get_stats()
            print(f"  - {col_name} ({stats['total_documents']} documents)")
            count += 1
        if count == 0:
            print("  (No collections indexed yet)")
        vs.delete_collection_by_name("temp.admin.collection")
    except Exception as e:
        print(f"✗ Vector DB Client: {e}")
    
    from config import PROJECT_ID
    if PROJECT_ID == "your-project-id":
        print("✗ PROJECT_ID not set in environment variable")
    else:
        print(f"✓ PROJECT_ID: {PROJECT_ID}")


def main():
    while True:
        print_menu()
        choice = input("Select (1-7): ").strip()
        
        if choice == '1':
            test_auth()
        elif choice == '2':
            run_folder_indexer()
        elif choice == '3':
            run_unified_rag()
        elif choice == '4':
            run_legacy_rag()
        elif choice == '5':
            check_status()
        elif choice == '6':
            clear_index()
        elif choice == '7':
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