#!/usr/bin/env python3
"""
Google Drive OAuth2 Token Generator
Bypasses OAuth consent screen issues by using direct token exchange
"""

import json
import requests
import webbrowser
import socket
import threading
import time
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
import os

class OAuthHandler(BaseHTTPRequestHandler):
    def __init__(self, auth_code_holder, expected_state, *args, **kwargs):
        self.auth_code_holder = auth_code_holder
        self.expected_state = expected_state
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        # Verify state parameter for CSRF protection
        if 'state' not in query_params or query_params['state'][0] != self.expected_state:
            self.auth_code_holder['error'] = 'invalid_state'
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error_message = """
            <html>
            <body>
                <h1>❌ Security Error</h1>
                <p>Invalid state parameter. Possible CSRF attack detected.</p>
            </body>
            </html>
            """
            self.wfile.write(error_message.encode())
            threading.Thread(target=self.server.shutdown).start()
            return
        
        if 'code' in query_params:
            self.auth_code_holder['code'] = query_params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            success_message = """
            <html>
            <body>
                <h1>✅ Google Drive Authentication Successful!</h1>
                <p>You can close this browser tab and return to your terminal.</p>
                <p>Your Google Drive access is now configured!</p>
            </body>
            </html>
            """
            self.wfile.write(success_message.encode())
        elif 'error' in query_params:
            self.auth_code_holder['error'] = query_params['error'][0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error_message = f"""
            <html>
            <body>
                <h1>❌ Authentication Failed</h1>
                <p>Error: {query_params['error'][0]}</p>
                <p>Please check your Google Cloud Console configuration.</p>
            </body>
            </html>
            """
            self.wfile.write(error_message.encode())
        
        # Shutdown server after handling request
        threading.Thread(target=self.server.shutdown).start()
    
    def log_message(self, format, *args):
        pass  # Suppress default logging

def get_oauth_credentials():
    """Load OAuth2 credentials from environment or file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, '.env')
    
    client_id = None
    client_secret = None
    
    # Try to load from .env file
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('GOOGLE_CLIENT_ID='):
                    client_id = line.split('=', 1)[1].strip()
                elif line.startswith('GOOGLE_CLIENT_SECRET='):
                    client_secret = line.split('=', 1)[1].strip()
    
    if not client_id or not client_secret:
        print("❌ Error: Missing Google OAuth credentials in .env file")
        print("Required: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
        sys.exit(1)
    
    return client_id, client_secret

def generate_auth_url(client_id, redirect_uri, state):
    """Generate Google OAuth2 authorization URL with security state parameter"""
    base_url = "https://accounts.google.com/o/oauth2/auth"
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'https://www.googleapis.com/auth/drive',
        'access_type': 'offline',
        'prompt': 'consent',  # Force consent screen to bypass approval issues
        'state': state  # CSRF protection
    }
    
    from urllib.parse import urlencode
    param_string = urlencode(params)
    return f"{base_url}?{param_string}"

def exchange_code_for_tokens(client_id, client_secret, auth_code, redirect_uri):
    """Exchange authorization code for access and refresh tokens"""
    token_url = "https://oauth2.googleapis.com/token"
    
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Token exchange failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def create_rclone_config(tokens, client_id, client_secret):
    """Create rclone configuration with OAuth tokens and secure permissions"""
    config_dir = os.path.expanduser("~/.config/rclone")
    config_file = os.path.join(config_dir, "rclone.conf")
    
    os.makedirs(config_dir, exist_ok=True)
    
    # Set secure directory permissions (owner only)
    os.chmod(config_dir, 0o700)
    
    # Create rclone config content with proper JSON escaping
    import json
    token_json = {
        "access_token": tokens['access_token'],
        "token_type": "Bearer", 
        "refresh_token": tokens.get('refresh_token', ''),
        "expiry": "2025-12-31T23:59:59Z"
    }
    
    config_content = f"""[mydrive]
type = drive
client_id = {client_id}
client_secret = {client_secret}
scope = drive
token = {json.dumps(token_json)}
team_drive = 
"""
    
    # Write config with secure permissions
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    # Set secure file permissions (owner only)
    os.chmod(config_file, 0o600)
    
    print(f"✅ rclone configuration saved to: {config_file}")
    print(f"🔒 Security: Config file permissions set to owner-only (600)")

def main():
    print("🚀 Google Drive OAuth2 Token Generator")
    print("=" * 50)
    
    # Load credentials
    try:
        client_id, client_secret = get_oauth_credentials()
        print(f"✅ Loaded OAuth credentials")
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return
    
    # Generate secure random state for CSRF protection
    import secrets
    state = secrets.token_urlsafe(32)
    
    # Setup local server for OAuth callback
    redirect_port = 53682
    redirect_uri = f"http://localhost:{redirect_port}"
    
    # Test if port is available
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(('localhost', redirect_port))
        test_socket.close()
    except OSError:
        print(f"❌ Port {redirect_port} is in use. Trying alternative port...")
        redirect_port = 8080
        redirect_uri = f"http://localhost:{redirect_port}"
    
    # Generate authorization URL with secure state
    auth_url = generate_auth_url(client_id, redirect_uri, state)
    
    print(f"🔗 Opening browser for Google authentication...")
    print(f"🔒 Security: Using CSRF protection with state parameter")
    print(f"If browser doesn't open automatically, visit:")
    print(f"{auth_url}")
    print()
    
    # Setup OAuth callback server
    auth_code_holder = {'code': None, 'error': None}
    
    def handler(*args, **kwargs):
        return OAuthHandler(auth_code_holder, state, *args, **kwargs)
    
    try:
        server = HTTPServer(('localhost', redirect_port), handler)
        
        # Open browser
        webbrowser.open(auth_url)
        
        print("⏳ Waiting for Google authentication...")
        print("Complete the authentication in your browser...")
        
        # Handle one request (the OAuth callback)
        server.handle_request()
        
        if auth_code_holder['error']:
            print(f"❌ Authentication failed: {auth_code_holder['error']}")
            return
        
        if not auth_code_holder['code']:
            print("❌ No authorization code received")
            return
        
        print("✅ Authorization code received!")
        
        # Exchange code for tokens
        print("🔄 Exchanging authorization code for tokens...")
        tokens = exchange_code_for_tokens(client_id, client_secret, 
                                        auth_code_holder['code'], redirect_uri)
        
        if not tokens:
            print("❌ Failed to exchange code for tokens")
            return
        
        print("✅ OAuth tokens obtained successfully!")
        
        # Create rclone config
        create_rclone_config(tokens, client_id, client_secret)
        
        print("🎉 Google Drive authentication complete!")
        print("You can now use the gdrive_manager.sh script to access your Google Drive!")
        
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return

if __name__ == "__main__":
    main()