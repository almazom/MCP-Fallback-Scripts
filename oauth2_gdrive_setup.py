#!/usr/bin/env python3
"""
Google Drive OAuth2 Setup for Personal Gmail Accounts
Based on expert research findings - bypasses service account limitations
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes for Google Drive access
SCOPES = ['https://www.googleapis.com/auth/drive']

def setup_oauth2_credentials():
    """Set up OAuth2 credentials for Google Drive access."""
    
    # Client configuration from your existing setup
    client_config = {
        "installed": {
            "client_id": "1085816236005-rrgavnu2odcvbrofa31o6le9ndacjc7o.apps.googleusercontent.com",
            "client_secret": "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",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    creds = None
    token_file = '/home/almaz/MCP/FALLBACK_SCRIPTS/oauth2_token.json'
    
    # Check if we already have valid credentials
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=9090, prompt='consent')
        
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    
    return creds

def test_drive_access(creds):
    """Test Google Drive access with OAuth2 credentials."""
    
    service = build('drive', 'v3', credentials=creds)
    
    # Test: List files
    print("🔍 Testing Google Drive access...")
    results = service.files().list(pageSize=10, fields="files(id, name)").execute()
    items = results.get('files', [])
    
    if not items:
        print("❌ No files found")
        return False
    else:
        print(f"✅ Found {len(items)} files:")
        for item in items[:5]:
            print(f"  - {item['name']} ({item['id']})")
    
    # Test: Create a test file
    print("\n📝 Testing file creation...")
    file_metadata = {
        'name': 'oauth2_test_file.txt'
    }
    media_body = 'Test file created via OAuth2 authentication'
    
    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media_body
        ).execute()
        
        print(f"✅ File created successfully! ID: {file.get('id')}")
        
        # Clean up: Delete the test file
        service.files().delete(fileId=file.get('id')).execute()
        print("🧹 Test file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ File creation failed: {e}")
        return False

def configure_rclone_oauth():
    """Configure rclone with OAuth2 token."""
    
    token_file = '/home/almaz/MCP/FALLBACK_SCRIPTS/oauth2_token.json'
    if not os.path.exists(token_file):
        print("❌ OAuth2 token not found. Run setup first.")
        return False
    
    # Read the OAuth2 token
    with open(token_file, 'r') as f:
        token_data = json.load(f)
    
    # Create rclone configuration entry
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
    return True

if __name__ == "__main__":
    print("🔐 Google Drive OAuth2 Setup")
    print("=" * 40)
    
    try:
        print("\n1. Setting up OAuth2 credentials...")
        creds = setup_oauth2_credentials()
        
        print("\n2. Testing Google Drive access...")
        success = test_drive_access(creds)
        
        if success:
            print("\n3. Configuring rclone...")
            configure_rclone_oauth()
            print("\n🎉 SUCCESS! OAuth2 setup complete!")
            print("\n🚀 Next steps:")
            print("   - Test: rclone lsd mydrive_oauth_working:")
            print("   - Upload: rclone copy file.txt mydrive_oauth_working:folder/")
            print("   - Update gdrive_manager.sh to use 'mydrive_oauth_working' remote")
        else:
            print("\n❌ Setup failed. Check your credentials and try again.")
            
    except Exception as e:
        print(f"\n💥 Error during setup: {e}")
        print("🔧 This might be the OAuth consent screen redirect issue.")
        print("💡 Try the manual token approach instead.")