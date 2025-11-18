"""
Re-authenticate with Google Drive to enable Shared Drives access

This script:
1. Deletes the old token.pickle (which has limited scopes)
2. Forces re-authentication with new scopes that include shared drives access
"""
import os
from pathlib import Path

def main():
    print("\n" + "="*80)
    print("  Google Drive Re-Authentication for Shared Drives")
    print("="*80 + "\n")
    
    token_file = Path("token.pickle")
    
    if token_file.exists():
        print("📄 Found existing token.pickle")
        print("   This token has limited permissions (no shared drives access)")
        print("\n❓ Do you want to delete it and re-authenticate with full permissions?")
        print("   This will give the application access to:")
        print("   • Your personal Google Drive files")
        print("   • Shared Drives you have access to")
        print("   • Team Drives")
        print()
        
        response = input("Delete old token and re-authenticate? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("\n❌ Cancelled - keeping existing token")
            print("   Note: You won't be able to access shared drives without re-authentication")
            return
        
        try:
            os.remove(token_file)
            print("\n✅ Deleted token.pickle")
        except Exception as e:
            print(f"\n❌ Error deleting token: {e}")
            return
    else:
        print("ℹ️  No existing token found (this is fine for first-time setup)")
    
    print("\n" + "="*80)
    print("  Starting Authentication Process")
    print("="*80 + "\n")
    
    print("Running: python auth.py\n")
    
    # Import and run authentication
    try:
        from auth import authenticate_google_drive
        
        service = authenticate_google_drive(interactive=True)
        
        if service:
            print("\n" + "="*80)
            print("  ✅ RE-AUTHENTICATION SUCCESSFUL!")
            print("="*80 + "\n")
            
            print("Testing shared drives access...")
            
            # Test shared drives access
            try:
                response = service.drives().list(
                    pageSize=10,
                    fields='drives(id, name)'
                ).execute()
                
                shared_drives = response.get('drives', [])
                
                if shared_drives:
                    print(f"\n✅ Found {len(shared_drives)} Shared Drive(s):")
                    for i, drive in enumerate(shared_drives, 1):
                        print(f"   {i}. {drive['name']}")
                    
                    print("\n✅ Shared drives access confirmed!")
                else:
                    print("\nℹ️  No shared drives found (you may not be a member of any)")
                    print("   If you expect to see shared drives, check:")
                    print("   • You're logged in with the correct Google account")
                    print("   • You have been added to the shared drive in Google Drive")
                
            except Exception as e:
                print(f"\n⚠️  Error checking shared drives: {e}")
                print("   The authentication might still work - try running folder_indexer.py")
            
            print("\n📋 Next Steps:")
            print("   1. Run: python csv_fix_menu.py")
            print("   2. Select Option 1 (Fix Database)")
            print("   3. When prompted, you should now see shared drives!")
            
        else:
            print("\n❌ Authentication failed")
            print("   Please check:")
            print("   • credentials.json is present in this directory")
            print("   • Your Google account has access to shared drives")
            print("   • You completed the authorization in the browser")
            
    except Exception as e:
        print(f"\n❌ Error during authentication: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
