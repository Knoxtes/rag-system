"""
Simple Re-authentication Script

Just deletes the old token and runs the authentication.
No complicated code - just works!
"""
import os
from pathlib import Path

print("\n" + "="*80)
print("  SIMPLE RE-AUTHENTICATION FOR SHARED DRIVES")
print("="*80 + "\n")

token_file = Path("token.pickle")

# Step 1: Delete old token
if token_file.exists():
    print("🗑️  Deleting old authentication token...")
    try:
        os.remove(token_file)
        print("✅ Old token deleted\n")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   You may need to close any programs using the token file\n")
        input("Press Enter to exit...")
        exit(1)
else:
    print("ℹ️  No old token found (first time setup)\n")

# Step 2: Run authentication
print("="*80)
print("  STEP-BY-STEP INSTRUCTIONS")
print("="*80 + "\n")

print("What will happen:")
print("  1. Your web browser will open automatically")
print("  2. You'll see a Google sign-in page")
print("  3. Sign in with your Google account (the one with shared drive access)")
print("  4. Click 'Allow' to grant permissions")
print("  5. You'll see 'Authorization successful!' message")
print("  6. The browser window will close automatically")
print("  7. Return to this terminal - you're done!")

print("\n⚠️  IMPORTANT:")
print("   • Use the Google account that has access to your shared drives")
print("   • When prompted, click 'Allow' to grant ALL permissions")
print("   • Don't close the terminal until you see 'Connected successfully!'")

input("\n▶  Press Enter to start authentication...")

# Import and run
try:
    print("\n" + "="*80)
    from auth import authenticate_google_drive
    
    service = authenticate_google_drive(interactive=True)
    
    if service:
        print("\n" + "="*80)
        print("  ✅ SUCCESS! Testing shared drives access...")
        print("="*80 + "\n")
        
        # Test shared drives
        try:
            response = service.drives().list(
                pageSize=10,
                fields='drives(id, name)'
            ).execute()
            
            shared_drives = response.get('drives', [])
            
            if shared_drives:
                print(f"✅ SHARED DRIVES FOUND: {len(shared_drives)}\n")
                for i, drive in enumerate(shared_drives, 1):
                    print(f"   {i}. {drive['name']}")
                
                print("\n" + "="*80)
                print("  🎉 SHARED DRIVES ACCESS CONFIRMED!")
                print("="*80)
            else:
                print("ℹ️  No shared drives found.")
                print("   This could mean:")
                print("   • You're not a member of any shared drives")
                print("   • You signed in with the wrong Google account")
                print("\n   If you expect to see shared drives, try:")
                print("   • Run this script again with the correct account")
                print("   • Ask your admin to add you to the shared drive")
        except Exception as e:
            print(f"⚠️  Could not test shared drives: {e}")
            print("   The authentication might still work though!")
        
        print("\n" + "="*80)
        print("  NEXT STEPS")
        print("="*80)
        print("\n  Now you can:")
        print("  1. Run: python folder_indexer.py")
        print("     → You should now see your shared drives!")
        print("\n  2. Or use the menu: python csv_fix_menu.py")
        print("     → Select Option 1 to fix the database")
        
    else:
        print("\n" + "="*80)
        print("  ❌ AUTHENTICATION FAILED")
        print("="*80)
        print("\n  Possible issues:")
        print("  • credentials.json is missing or invalid")
        print("  • Browser blocked the popup")
        print("  • You cancelled the authorization")
        print("\n  Try running this script again.")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

input("\n\n▶  Press Enter to exit...")
