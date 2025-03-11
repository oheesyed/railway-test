import sys
from agency_swarm import Agency
from .PersonalAssistant.PersonalAssistant import PersonalAssistant

# Initialize the Personal Assistant agent
assistant = PersonalAssistant()

# Create the agency with the Personal Assistant agent
agency = Agency(
    [assistant],  # Single agent setup with PersonalAssistant as the entry point
    shared_instructions="agency_manifesto.md",
    temperature=0.5,
    max_prompt_tokens=32000,  # Increased from 25000 to 32000
)

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--gradio":
        agency.demo_gradio(share=True)  # Set to True to get a public URL
    else:
        # Default to demo mode
        agency.run_demo()
