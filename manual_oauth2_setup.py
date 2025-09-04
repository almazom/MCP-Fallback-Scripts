#!/usr/bin/env python3
"""
Manual Google Drive OAuth2 Setup for Headless Servers
Generates authorization URL for manual completion
"""

import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Scopes for Google Drive access
SCOPES = ['https://www.googleapis.com/auth/drive']

def create_manual_oauth_url():
    """Generate OAuth2 authorization URL for manual completion."""
    
    # Client configuration 
    client_config = {
        "installed": {
            "client_id": "1085816236005-rrgavnu2odcvbrofa31o6le9ndacjc7o.apps.googleusercontent.com",
            "client_secret": "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",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost:8080"]
        }
    }
    
    # Create flow
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri='http://localhost:8080'
    )
    
    # Generate authorization URL
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    print("🔐 Google Drive Manual OAuth2 Setup")
    print("=" * 50)
    print()
    print("📋 STEP 1: Open this URL in your browser:")
    print("=" * 50)
    print(auth_url)
    print("=" * 50)
    print()
    print("📋 STEP 2: Complete the authorization")
    print("  1. Click the URL above")
    print("  2. Login with your Google account")
    print("  3. Grant permissions to access Google Drive")
    print("  4. You'll be redirected to localhost:8080")
    print("  5. Copy the FULL redirect URL (including the 'code' parameter)")
    print()
    print("📋 STEP 3: Run the completion script")
    print("  python3 complete_oauth2_setup.py 'PASTE_REDIRECT_URL_HERE'")
    print()
    
    # Save flow state for completion
    flow_state = {
        'client_config': client_config,
        'scopes': SCOPES,
        'state': state
    }
    
    with open('/home/almaz/MCP/FALLBACK_SCRIPTS/oauth_flow_state.json', 'w') as f:
        json.dump(flow_state, f, indent=2)
    
    print("💾 Flow state saved. Ready for completion step.")
    
    return auth_url

if __name__ == "__main__":
    create_manual_oauth_url()