"""
CSV Auto-Fetch - Complete Solution Menu

Simple menu interface to fix and verify CSV data loss issue
"""
import subprocess
import sys
from pathlib import Path

def print_banner():
    print("\n" + "="*80)
    print("  CSV AUTO-FETCH FIX - Complete Solution")
    print("="*80)

def print_menu():
    print("\n📋 MENU:")
    print("  1. 🔧 Fix Database (Automated cleanup and re-index)")
    print("  2. ✅ Verify CSV Auto-Fetch (Run all tests)")
    print("  3. 🔑 Re-authenticate Google Drive (Enable Shared Drives)")
    print("  4. 🚀 Start Chat System")
    print("  5. 📖 View Documentation")
    print("  6. 🧪 Run Diagnostic Tests")
    print("  7. ❌ Exit")
    print()

def run_reauth():
    print("\n" + "="*80)
    print("  Re-authenticate for Shared Drives Access")
    print("="*80 + "\n")
    print("This will:")
    print("  1. Delete your current Google Drive token")
    print("  2. Open your browser for authorization")
    print("  3. Test shared drives access automatically")
    print()
    
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    try:
        subprocess.run([sys.executable, "simple_reauth.py"])
    except Exception as e:
        print(f"\n❌ Error: {e}")
    print("\n" + "="*80)
    print("  Running Database Fix")
    print("="*80 + "\n")
    print("This will:")
    print("  1. Backup current database")
    print("  2. Delete chroma_db directory")
    print("  3. Guide you through re-indexing")
    print()
    
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    try:
        subprocess.run([sys.executable, "fix_csv_indexing.py"])
    except Exception as e:
        print(f"\n❌ Error: {e}")

def run_verification():
    print("\n" + "="*80)
    print("  Running Verification Tests")
    print("="*80 + "\n")
    
    try:
        result = subprocess.run([sys.executable, "verify_csv_autofetch.py"])
        return result.returncode == 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def start_chat():
    print("\n" + "="*80)
    print("  Starting Chat System")
    print("="*80 + "\n")
    print("Starting start_chat_system.py...")
    print("Press Ctrl+C to stop the chat system and return to menu\n")
    
    try:
        subprocess.run([sys.executable, "start_chat_system.py"])
    except KeyboardInterrupt:
        print("\n\n✅ Chat system stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def view_docs():
    print("\n" + "="*80)
    print("  Documentation")
    print("="*80 + "\n")
    
    doc_file = Path("CSV_AUTOFETCH_SOLUTION.md")
    if doc_file.exists():
        print(f"📖 Opening {doc_file}...")
        
        # Try to open with default markdown viewer
        try:
            import webbrowser
            # Try to convert to HTML view or just open in default editor
            if sys.platform == "win32":
                import os
                os.startfile(str(doc_file))
            else:
                subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", str(doc_file)])
        except:
            # Fallback: print first 50 lines
            with open(doc_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:50]
                print(''.join(lines))
                print(f"\n... ({len(lines)} lines shown, see {doc_file} for full documentation)")
    else:
        print("❌ Documentation file not found: CSV_AUTOFETCH_SOLUTION.md")

def run_diagnostics():
    print("\n" + "="*80)
    print("  Diagnostic Tests")
    print("="*80 + "\n")
    
    tests = [
        ("test_csv_extraction.py", "CSV Extraction Test", "Verify pandas reads CSV correctly"),
        ("test_csv_fetch.py", "CSV Fetch Test", "Check if CSV chunks exist in database"),
        ("test_metadata_check.py", "Metadata Check", "Examine metadata structure"),
        ("check_altoona_chunks.py", "Altoona Chunks", "Analyze Altoona CSV specifically"),
        ("test_boolean_metadata.py", "Boolean Metadata", "Test ChromaDB boolean support"),
    ]
    
    print("Available diagnostic tests:\n")
    for i, (script, name, desc) in enumerate(tests, 1):
        print(f"  {i}. {name}")
        print(f"     {desc}")
        print()
    
    print("  0. Run all tests")
    print()
    
    try:
        choice = input("Select test (0-5, or 'back'): ").strip()
        
        if choice.lower() == 'back':
            return
        
        choice_num = int(choice)
        
        if choice_num == 0:
            # Run all tests
            for script, name, desc in tests:
                print(f"\n{'='*80}")
                print(f"  Running: {name}")
                print(f"{'='*80}\n")
                try:
                    subprocess.run([sys.executable, script])
                except Exception as e:
                    print(f"❌ Error running {script}: {e}")
                print()
        elif 1 <= choice_num <= len(tests):
            script, name, desc = tests[choice_num - 1]
            print(f"\n{'='*80}")
            print(f"  Running: {name}")
            print(f"{'='*80}\n")
            try:
                subprocess.run([sys.executable, script])
            except Exception as e:
                print(f"❌ Error running {script}: {e}")
        else:
            print("❌ Invalid choice")
    except ValueError:
        print("❌ Invalid input")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_quick_start():
    print("\n" + "="*80)
    print("  QUICK START GUIDE")
    print("="*80 + "\n")
    print("Problem: CSV files showing only 10% of data")
    print("   Example: Altoona showing $43,767 instead of $450,866\n")
    print("Solution: 3 Simple Steps")
    print("   1. Run Option 1: Fix Database (automated)")
    print("   2. Run Option 2: Verify (confirm it worked)")
    print("   3. Run Option 3: Start Chat System\n")
    print("Expected Result:")
    print("   Query: 'What is January 2025 Altoona sales total?'")
    print("   Answer: $450,866.30 (100% complete data)")
    print()
    print("Press Enter to continue...")
    input()

def main():
    workspace = Path(__file__).parent
    
    # Check if we're in the right directory
    if not (workspace / "folder_indexer.py").exists():
        print("❌ Error: Cannot find folder_indexer.py")
        print(f"   Current directory: {workspace}")
        print("   Please run this script from the rag-system directory")
        return
    
    # Show quick start on first run
    show_quick_start()
    
    while True:
        print_banner()
        print_menu()
        
        try:
            choice = input("Select option (1-7): ").strip()
            
            if choice == '1':
                run_fix()
            elif choice == '2':
                success = run_verification()
                if success:
                    print("\n" + "="*80)
                    print("  ✅ ALL TESTS PASSED!")
                    print("="*80)
                    print("\nYou can now:")
                    print("  • Start the chat system (Option 4)")
                    print("  • Test with: 'What is January 2025 Altoona sales total?'")
                    print("  • Expected result: $450,866.30")
                else:
                    print("\n" + "="*80)
                    print("  ❌ TESTS FAILED")
                    print("="*80)
                    print("\nRecommended action:")
                    print("  • Run Option 1 (Fix Database)")
                    print("  • Then run Option 2 again (Verify)")
            elif choice == '3':
                run_reauth()
            elif choice == '4':
                start_chat()
            elif choice == '5':
                view_docs()
            elif choice == '6':
                run_diagnostics()
            elif choice == '7':
                print("\n✅ Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-7.")
            
            if choice in ['1', '2', '3', '6']:
                input("\nPress Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\n✅ Exiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
