from agency_swarm.tools import BaseTool
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import json
from pydantic import Field
from typing import Optional

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/calendar.readonly']

class GoogleServicesUtils(BaseTool):
    """A utility tool for handling Google OAuth authentication for Gmail and Calendar services."""
    
    name: str = "google_services"
    description: str = "Handles Google OAuth authentication for Gmail and Calendar services"
    credentials_path: Optional[str] = None
    token_path: Optional[str] = None
    
    # Try multiple possible locations for credentials
    def _find_credentials(self):
        possible_paths = [
            # Direct execution path
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), 'credentials.json'),
            # Current working directory
            os.path.join(os.getcwd(), 'credentials.json'),
            # Src directory
            os.path.join(os.getcwd(), 'src', 'credentials.json'),
            # User home directory
            os.path.expanduser('~/credentials.json')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def _find_token(self):
        possible_paths = [
            # Direct execution path
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), 'token.pickle'),
            # Current working directory
            os.path.join(os.getcwd(), 'token.pickle'),
            # Src directory
            os.path.join(os.getcwd(), 'src', 'token.pickle'),
            # User home directory
            os.path.expanduser('~/token.pickle')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def run(self):
        """Handles OAuth2 authentication flow for Google services."""
        self.credentials_path = self._find_credentials()
        self.token_path = self._find_token()
        
        print(f"Looking for credentials at: {self.credentials_path}")
        print(f"Looking for token at: {self.token_path}")
        
        # Try local development first
        creds = self._try_local_auth()
        if creds:
            return creds

        # Fallback to environment variables (Railway)
        creds = self._try_env_auth()
        if creds:
            return creds

        return "Error: No credentials found. Please set up Google OAuth credentials locally or provide environment variables."

    def _try_local_auth(self):
        """Attempt local authentication using token.pickle and credentials.json"""
        if self.token_path and os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                        with open(self.token_path, 'wb') as token:
                            pickle.dump(creds, token)
                    else:
                        return self._create_new_token()
                return creds
            except Exception as e:
                print(f"Local auth error: {str(e)}")
                pass

        return self._create_new_token()

    def _create_new_token(self):
        """Create new token using credentials.json"""
        if self.credentials_path and os.path.exists(self.credentials_path):
            try:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
                if self.token_path:
                    with open(self.token_path, 'wb') as token:
                        pickle.dump(creds, token)
                return creds
            except Exception as e:
                print(f"Token creation error: {str(e)}")
                pass
        return None

    def _try_env_auth(self):
        """Attempt authentication using environment variables"""
        token_info = os.getenv("GOOGLE_TOKEN_INFO")
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        
        if all([token_info, client_id, client_secret]):
            try:
                token_data = json.loads(token_info)
                return Credentials(
                    token=token_data.get('token'),
                    refresh_token=token_data.get('refresh_token'),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=SCOPES
                )
            except Exception as e:
                print(f"Environment auth error: {str(e)}")
                pass
        return None

if __name__ == "__main__":
    auth_tool = GoogleServicesUtils()
    result = auth_tool.run()
    print("Authentication successful!" if not isinstance(result, str) else result)