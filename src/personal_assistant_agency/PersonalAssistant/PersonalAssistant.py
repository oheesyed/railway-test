from agency_swarm.agents import Agent


class PersonalAssistant(Agent):
    def __init__(self):
        super().__init__(
            name="PersonalAssistant",
            description="An AI assistant that manages emails, calendar, and time-related tasks",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[],
            tools_folder="./tools",
            temperature=0.3,
            max_prompt_tokens=2000,
        )

    def response_validator(self, message):
        """Validate and clean up responses to prevent loops and duplicates"""
        # If message starts with multiple identical sections, keep only the last one
        sections = message.split("🐤 PersonalAssistant 🗣️ @User")
        if len(sections) > 1:
            # Keep only the last meaningful section
            return "🐤 PersonalAssistant 🗣️ @User" + sections[-1]
        return message
