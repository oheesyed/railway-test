from agency_swarm.tools import BaseTool
from pydantic import Field
from googleapiclient.discovery import build
import os
import json
from google.oauth2 import service_account
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = str(Path(__file__).resolve().parents[3])
if src_dir not in sys.path:
    sys.path.append(src_dir)

from personal_assistant_agency.PersonalAssistant.tools.GoogleServicesUtils import GoogleServicesUtils

load_dotenv()

class ListUnreadEmails(BaseTool):
    """
    Tool for listing unread emails from Gmail inbox with metadata only.
    Returns a list of unread emails with their subject, sender, date and a brief snippet.
    """
    max_results: int = Field(
        default=10,
        description="Maximum number of unread emails to fetch"
    )
    search_query: str = Field(
        default="",
        description="Optional Gmail search query to filter emails (e.g. 'from:example@gmail.com')"
    )

    def run(self):
        """
        Lists unread emails from Gmail with metadata only.
        Returns a formatted string containing email summaries.
        """
        try:
            # Get credentials using GoogleServicesUtils
            auth_tool = GoogleServicesUtils()
            creds = auth_tool.run()
            
            service = build('gmail', 'v1', credentials=creds)
            
            # Combine UNREAD label with optional search query
            query = "label:unread"
            if self.search_query:
                query += f" {self.search_query}"
                
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=self.max_results
            ).execute()

            messages = results.get('messages', [])
            if not messages:
                return "No unread messages found."

            # Use a set to track seen message IDs
            seen_ids = set()
            email_summaries = []
            
            for message in messages:
                if message['id'] in seen_ids:
                    continue
                seen_ids.add(message['id'])
                
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['Subject', 'From', 'Date']
                ).execute()

                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'No Date')
                snippet = msg.get('snippet', 'No preview available')[:100] + '...' # Limit snippet length

                email_summaries.append(
                    f"ID: {message['id']}\n"
                    f"From: {sender}\n"
                    f"Subject: {subject}\n"
                    f"Date: {date}\n"
                    f"Preview: {snippet}\n"
                    f"{'-' * 50}"
                )

                # Stop after max_results unique emails
                if len(email_summaries) >= self.max_results:
                    break

            return "\n\n".join(email_summaries)

        except Exception as e:
            return f"Error listing emails: {str(e)}"

if __name__ == "__main__":
    tool = ListUnreadEmails(max_results=5)
    print(tool.run()) 