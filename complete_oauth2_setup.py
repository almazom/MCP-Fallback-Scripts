#!/usr/bin/env python3
"""
Complete Manual Google Drive OAuth2 Setup
Processes the authorization code and sets up rclone
"""

import json
import sys
import os
from urllib.parse import urlparse, parse_qs
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

def complete_oauth_setup(redirect_url):
    """Complete OAuth2 setup using the redirect URL."""
    
    # Load flow state
    try:
        with open('/home/almaz/MCP/FALLBACK_SCRIPTS/oauth_flow_state.json', 'r') as f:
            flow_state = json.load(f)
    except FileNotFoundError:
        print("❌ Flow state not found. Run manual_oauth2_setup.py first.")
        return False
    
    # Parse the redirect URL to get the authorization code
    parsed_url = urlparse(redirect_url)
    query_params = parse_qs(parsed_url.query)
    
    if 'code' not in query_params:
        print("❌ No authorization code found in URL")
        print("🔧 Make sure you copied the complete redirect URL including '?code=...'")
        return False
    
    code = query_params['code'][0]
    print(f"✅ Found authorization code: {code[:20]}...")
    
    # Create flow and exchange code for token
    flow = Flow.from_client_config(
        flow_state['client_config'],
        scopes=flow_state['scopes'],
        redirect_uri='http://localhost:8080'
    )
    
    try:
        # Exchange authorization code for access token
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        print("✅ Successfully obtained OAuth2 credentials!")
        
        # Save credentials
        token_file = '/home/almaz/MCP/FALLBACK_SCRIPTS/oauth2_token.json'
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        
        print(f"💾 Credentials saved to {token_file}")
        
        # Test Google Drive access
        print("\n🔍 Testing Google Drive access...")
        success = test_drive_access(creds)
        
        if success:
            print("\n🚀 Configuring rclone...")
            configure_rclone_oauth(creds)
            print("\n🎉 SUCCESS! OAuth2 setup complete!")
            print("\n✅ Available commands:")
            print("   rclone lsd mydrive_oauth_working:")
            print("   rclone copy file.txt mydrive_oauth_working:folder/")
            print("   ./gdrive_manager.sh (update to use mydrive_oauth_working)")
            return True
        else:
            print("❌ Drive access test failed")
            return False
            
    except Exception as e:
        print(f"❌ Token exchange failed: {e}")
        return False

def test_drive_access(creds):
    """Test Google Drive access and create a test file."""
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # List files
        results = service.files().list(pageSize=5).execute()
        items = results.get('files', [])
        print(f"✅ Found {len(items)} files in your Drive")
        
        # Test file creation
        print("📝 Testing file creation...")
        file_metadata = {
            'name': 'oauth2_write_test.txt',
            'parents': []  # Root directory
        }
        
        # Create file content
        media_body = f'OAuth2 write test successful! Created: {os.popen("date").read().strip()}'
        
        file = service.files().create(
            body=file_metadata,
            media_body=media_body.encode('utf-8')
        ).execute()
        
        print(f"🎉 SUCCESS! Created file: {file.get('name')} (ID: {file.get('id')})")
        
        # Try to upload to Plaude folder if it exists
        try:
            # Search for Plaude folder
            query = "name='Plaude' and mimeType='application/vnd.google-apps.folder'"
            plaude_results = service.files().list(q=query).execute()
            plaude_items = plaude_results.get('files', [])
            
            if plaude_items:
                plaude_id = plaude_items[0]['id']
                print(f"📁 Found Plaude folder: {plaude_id}")
                
                # Create test file in Plaude folder
                plaude_file_metadata = {
                    'name': 'oauth2_plaude_test.txt',
                    'parents': [plaude_id]
                }
                
                plaude_file = service.files().create(
                    body=plaude_file_metadata,
                    media_body=f'OAuth2 test in Plaude folder! {os.popen("date").read().strip()}'.encode('utf-8')
                ).execute()
                
                print(f"🎉 SUCCESS! Created file in Plaude: {plaude_file.get('name')}")
            
        except Exception as e:
            print(f"ℹ️  Plaude folder test skipped: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Drive access failed: {e}")
        return False

def configure_rclone_oauth(creds):
    """Configure rclone with OAuth2 credentials."""
    
    # Convert credentials to rclone token format
    token_data = json.loads(creds.to_json())
    
    # Create rclone configuration
    rclone_config = f"""
[mydrive_oauth_working]
type = drive
client_id = 1085816236005-rrgavnu2odcvbrofa31o6le9ndacjc7o.apps.googleusercontent.com
client_secret = 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
scope = drive
token = {json.dumps(token_data)}
"""
    
    # Append to rclone config
    config_file = '/home/almaz/.config/rclone/rclone.conf'
    with open(config_file, 'a') as f:
        f.write(rclone_config)
    
    print("✅ rclone OAuth2 configuration added as 'mydrive_oauth_working'")
    print("🚀 Test with: rclone lsd mydrive_oauth_working:")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 complete_oauth2_setup.py 'REDIRECT_URL'")
        print("Example: python3 complete_oauth2_setup.py 'http://localhost:8080/?code=XXXX&scope=https://...'")
        sys.exit(1)
    
    redirect_url = sys.argv[1]
    success = complete_oauth_setup(redirect_url)
    
    if success:
        # Clean up flow state
        try:
            os.remove('/home/almaz/MCP/FALLBACK_SCRIPTS/oauth_flow_state.json')
            print("🧹 Cleaned up temporary files")
        except:
            pass
    else:
        print("💡 You can retry by running this command again with the correct URL")
        print("💡 Or run manual_oauth2_setup.py to get a new authorization URL")