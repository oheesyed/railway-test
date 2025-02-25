from agency_swarm.tools import BaseTool
from pydantic import Field
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
import json
from google.oauth2 import service_account
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = str(Path(__file__).resolve().parents[3])
if src_dir not in sys.path:
    sys.path.append(src_dir)

from personal_assistant_agency.PersonalAssistant.tools.GoogleServicesUtils import GoogleServicesUtils

load_dotenv()

class FetchDailyMeetingSchedule(BaseTool):
    """
    Tool for fetching daily meeting schedule from Google Calendar.
    Can fetch from specific calendars or all calendars.
    """
    date: str = Field(
        ...,
        description="The date to fetch meetings for (YYYY-MM-DD format)"
    )
    calendar_id: str = Field(
        "all",
        description="The calendar ID to fetch from. Use 'all' for all calendars, 'primary' for main calendar, or specific calendar ID"
    )

    def run(self):
        """
        Fetches the daily meeting schedule from Google Calendar.
        Returns a formatted string containing meeting details.
        """
        try:
            # Get credentials using GoogleServicesUtils
            auth_tool = GoogleServicesUtils()
            creds = auth_tool.run()
            
            service = build('calendar', 'v3', credentials=creds)
            
            # Convert date string to datetime
            date_obj = datetime.strptime(self.date, '%Y-%m-%d')
            start_time = date_obj.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
            end_time = (date_obj + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat() + 'Z'

            all_events = []
            
            if self.calendar_id == "all":
                # Get list of all calendars
                calendar_list = service.calendarList().list().execute()
                calendars = calendar_list.get('items', [])
                
                # Fetch events from each calendar
                for calendar in calendars:
                    events_result = service.events().list(
                        calendarId=calendar['id'],
                        timeMin=start_time,
                        timeMax=end_time,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    
                    events = events_result.get('items', [])
                    for event in events:
                        event['calendarName'] = calendar['summary']  # Add calendar name
                        all_events.append(event)
                        
                # Sort all events by start time
                all_events.sort(key=lambda x: x['start'].get('dateTime', x['start'].get('date')))
                
            else:
                # Fetch from specific calendar
                events_result = service.events().list(
                    calendarId=self.calendar_id,
                    timeMin=start_time,
                    timeMax=end_time,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                all_events = events_result.get('items', [])

            if not all_events:
                return f"No meetings scheduled for {self.date}"

            schedule = []
            for event in all_events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                start_time = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%I:%M %p')
                end_time = datetime.fromisoformat(end.replace('Z', '+00:00')).strftime('%I:%M %p')
                
                calendar_name = event.get('calendarName', 'Primary Calendar')
                
                schedule.append(
                    f"Calendar: {calendar_name}\n"
                    f"Meeting: {event['summary']}\n"
                    f"Time: {start_time} - {end_time}\n"
                    f"{'Location: ' + event.get('location', 'No location specified') if event.get('location') else ''}\n"
                )

            return "\n".join(schedule)

        except Exception as e:
            return f"Error fetching calendar events: {str(e)}"

if __name__ == "__main__":
    # Test fetching from all calendars
    tool = FetchDailyMeetingSchedule(date="2025-02-10", calendar_id="all")
    print(tool.run()) 