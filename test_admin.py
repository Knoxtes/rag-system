#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print('🔑 Environment variables loaded:')
client_id = os.getenv('GOOGLE_CLIENT_ID', 'Not set')
print(f'   GOOGLE_CLIENT_ID: {client_id[:20]}...')
print(f'   ALLOWED_DOMAINS: {os.getenv("ALLOWED_DOMAINS", "Not set")}')
print(f'   OAUTH_REDIRECT_URI: {os.getenv("OAUTH_REDIRECT_URI", "Not set")}')

# Test admin functionality
sys.path.append('.')

try:
    from admin_auth import ADMIN_EMAIL
    print(f'✅ Admin email configured: {ADMIN_EMAIL}')
    
    from system_stats import system_stats
    health = system_stats.get_system_health()
    print('✅ System stats working:')
    cpu_percent = health['system']['cpu_percent']
    memory_percent = health['system']['memory']['percent']
    uptime = health['process']['uptime_formatted']
    print(f'   📊 CPU: {cpu_percent:.1f}%')
    print(f'   💾 Memory: {memory_percent:.1f}%')
    print(f'   ⏱️ Uptime: {uptime}')
    
    collections = system_stats.get_collection_stats()
    total_collections = collections['total_collections']
    total_documents = collections['total_documents']
    print(f'   📁 Collections: {total_collections}')
    print(f'   📄 Documents: {total_documents}')
    
    print('✅ Admin functionality fully operational!')
    print()
    print('🎯 Next steps:')
    print('   1. Start the server: python chat_api.py')
    print('   2. Login as ethan.sexton@7mountainsmedia.com')
    print('   3. Access admin at: http://localhost:5000/admin/dashboard')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()