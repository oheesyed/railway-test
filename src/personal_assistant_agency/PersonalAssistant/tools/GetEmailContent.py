from agency_swarm.tools import BaseTool
from pydantic import Field
from googleapiclient.discovery import build
import os
import json
from google.oauth2 import service_account
import base64
from typing import Optional, List
from bs4 import BeautifulSoup, Comment
import re
import html
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = str(Path(__file__).resolve().parents[3])
if src_dir not in sys.path:
    sys.path.append(src_dir)

from personal_assistant_agency.PersonalAssistant.tools.GoogleServicesUtils import GoogleServicesUtils

load_dotenv()


class GetEmailContent(BaseTool):
    """
    Tool for fetching full content of specific Gmail emails.
    Can fetch by email ID or search criteria.
    """

    email_ids: Optional[List[str]] = Field(
        default=None, description="List of specific email IDs to fetch"
    )
    search_query: str = Field(
        default="",
        description="Gmail search query to find specific emails (e.g. 'from:example@gmail.com subject:important')",
    )
    max_results: int = Field(
        default=1,
        description="Maximum number of emails to fetch when using search_query",
    )

    def clean_html_content(self, content: str) -> str:
        """Clean HTML content and extract readable text."""
        try:
            # Unescape HTML entities
            content = html.unescape(content)

            # Remove style and script tags
            content = re.sub(r"<style.*?</style>", "", content, flags=re.DOTALL)
            content = re.sub(r"<script.*?</script>", "", content, flags=re.DOTALL)

            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")

            # Remove hidden elements
            for hidden in soup.find_all(
                style=re.compile(r"display:\s*none|visibility:\s*hidden")
            ):
                hidden.decompose()

            # Remove comments
            for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
                comment.extract()

            # Get text content
            text = soup.get_text(separator="\n", strip=True)

            # Clean up excessive whitespace and empty lines
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = "\n".join(lines)

            # Remove any remaining HTML-like artifacts
            text = re.sub(r"<[^>]+>", "", text)
            text = re.sub(r"\[if.*?\[endif\]", "", text, flags=re.DOTALL)

            return text.strip()
        except Exception as e:
            return f"Error cleaning HTML: {str(e)}\nOriginal content: {content}"

    def run(self):
        """
        Fetches full content of specified emails.
        Returns a formatted string containing complete email content.
        """
        try:
            # Get credentials using GoogleServicesUtils
            auth_tool = GoogleServicesUtils()
            creds = auth_tool.run()

            service = build("gmail", "v1", credentials=creds)

            # Get message IDs either directly or via search
            message_ids = self.email_ids or []
            if not message_ids and self.search_query:
                query = f"label:unread {self.search_query}".strip()
                results = (
                    service.users()
                    .messages()
                    .list(userId="me", q=query, maxResults=self.max_results)
                    .execute()
                )

                messages = results.get("messages", [])
                message_ids = [msg["id"] for msg in messages]

            if not message_ids:
                return "No emails found matching the criteria."

            email_contents = []
            for msg_id in message_ids:
                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg_id, format="full")
                    .execute()
                )

                headers = msg["payload"]["headers"]
                subject = next(
                    (h["value"] for h in headers if h["name"] == "Subject"),
                    "No Subject",
                )
                sender = next(
                    (h["value"] for h in headers if h["name"] == "From"),
                    "Unknown Sender",
                )
                date = next(
                    (h["value"] for h in headers if h["name"] == "Date"), "No Date"
                )

                # Get email body
                body = ""
                if "parts" in msg["payload"]:
                    # Try to find text/plain part first
                    for part in msg["payload"]["parts"]:
                        if part["mimeType"] == "text/plain" and "data" in part["body"]:
                            body = base64.urlsafe_b64decode(
                                part["body"]["data"]
                            ).decode("utf-8")
                            break
                    # If no text/plain, try text/html
                    if not body:
                        for part in msg["payload"]["parts"]:
                            if (
                                part["mimeType"] == "text/html"
                                and "data" in part["body"]
                            ):
                                html_content = base64.urlsafe_b64decode(
                                    part["body"]["data"]
                                ).decode("utf-8")
                                body = self.clean_html_content(html_content)
                                break
                elif "body" in msg["payload"] and "data" in msg["payload"]["body"]:
                    content = base64.urlsafe_b64decode(
                        msg["payload"]["body"]["data"]
                    ).decode("utf-8")
                    if msg["payload"].get("mimeType") == "text/html":
                        body = self.clean_html_content(content)
                    else:
                        body = content
                else:
                    body = "No readable content"

                email_contents.append(
                    f"From: {sender}\n"
                    f"Subject: {subject}\n"
                    f"Date: {date}\n"
                    f"\nContent:\n{body}\n"
                    f"{'-'*50}\n"
                )

            return "\n".join(email_contents)

        except Exception as e:
            return f"Error fetching email content: {str(e)}"


if __name__ == "__main__":
    # Test with search query instead of specific email ID
    tool = GetEmailContent(search_query="YOUR_EMAIL_ID", max_results=1)
    print(tool.run())

    # Test with more specific search
    tool = GetEmailContent(search_query="is:unread newer_than:1d", max_results=1)
    print(tool.run())
