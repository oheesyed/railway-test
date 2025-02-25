from agency_swarm.tools import BaseTool
from datetime import datetime
import pytz

class GetCurrentTime(BaseTool):
    """
    Tool for getting the current time in a formatted string.
    Returns the current date and time in a human-readable format.
    """

    def run(self):
        """
        Gets the current time and formats it into a readable string.
        Returns both date and time information.
        """
        try:
            # Get current time in local timezone
            local_tz = datetime.now().astimezone().tzinfo
            current_time = datetime.now(local_tz)
            
            # Format the output
            formatted_time = current_time.strftime("%I:%M %p")
            formatted_date = current_time.strftime("%A, %B %d, %Y")
            
            return f"Current Time: {formatted_time}\nDate: {formatted_date}"

        except Exception as e:
            return f"Error getting current time: {str(e)}"

if __name__ == "__main__":
    tool = GetCurrentTime()
    print(tool.run()) 