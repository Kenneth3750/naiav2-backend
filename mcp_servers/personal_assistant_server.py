import sys
import os
import django
from pathlib import Path
from fastmcp import FastMCP, Client
from starlette.responses import JSONResponse
from typing import Annotated
from pydantic import Field

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure Django BEFORE importing any functions
print("Configuring Django...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naia.settings.dev')

try:
    django.setup()
    print("✓ Django configured successfully")
except Exception as django_error:
    print(f"✗ Django setup failed: {django_error}")
    print("Warning: Some functions may not work properly")

# Now import the functions from apps.personal.functions (after Django is set up)
try:
    from apps.personal.functions import (
        get_current_news,
        get_weather,
        send_email_on_behalf_of_user,
        search_contacts_by_name,
        read_calendar_events,
        create_calendar_event,
        read_user_emails
    )
    from apps.researcher.functions import explain_naia_roles
    print("✓ Successfully imported personal assistant functions")
except ImportError as e:
    print(f"✗ Error importing functions: {e}")
    sys.exit(1)

# Initialize MCP server
mcp = FastMCP(
    name="NAIAPersonalAssistantMCPServer"
)

@mcp.tool(
    name="get_current_news"
)
def get_current_news_tool(
    location: Annotated[str, Field(description="The location to get news from (city, country, or region). Example: 'Barranquilla', 'Colombia', 'Atlántico'")],
    user_id: Annotated[int, Field(description="The ID of the user requesting the news")],
    status: Annotated[str, Field(description="A concise description of the task being performed, using conjugated verbs (e.g., 'Getting news from...', 'Searching news about...') in the same language as the user's question")],
    query: Annotated[str, Field(description="Specific query to search for news. Example: 'latest news from Barranquilla', 'breaking news Colombia', 'recent news Atlántico', written in the same language as the user's question")],
    language: Annotated[str, Field(description="The language in which the news should be retrieved. Example: 'es' for Spanish, 'en' for English, always use the two letter ISO 639-1 code")]
) -> dict:
    """
    Gets the latest news from a specific location with modern and attractive visualization.

    Use for current events, news updates, or when users want to stay informed about what's
    happening in a specific location. The function provides visually appealing news displays
    with images, sources, and timestamps.

    Examples: "What's happening in Barranquilla?", "Latest news from Colombia",
    "Breaking news from the coast"

    Returns news results with modern HTML visualization.
    """
    try:
        return get_current_news(location, user_id, status, query, language)
    except Exception as e:
        return {"error": f"News retrieval failed: {str(e)}"}

@mcp.tool(
    name="get_weather"
)
def get_weather_tool(
    location: Annotated[str, Field(description="The location to get weather for (city, country, or region). Example: 'Barranquilla', 'Bogotá', 'Medellín'")],
    user_id: Annotated[int, Field(description="The ID of the user requesting the weather")],
    status: Annotated[str, Field(description="A concise description of the task being performed, using conjugated verbs (e.g., 'Checking weather for...', 'Getting weather for...') in the same language as the user's question")]
) -> dict:
    """
    Gets weather information for a specific location with modern and attractive visualization.

    Use for weather conditions, forecasts, climate information, or when users ask about
    temperature, humidity, wind conditions, or general weather status.

    Examples: "How's the weather in Medellín?", "What's the temperature today?",
    "Weather forecast for this week"

    Returns weather data with elegant visual presentation.
    """
    try:
        return get_weather(location, user_id, status)
    except Exception as e:
        return {"error": f"Weather retrieval failed: {str(e)}"}

@mcp.tool(
    name="send_email_on_behalf_of_user"
)
def send_email_tool(
    to_email_or_name: Annotated[str, Field(description="The recipient's email address OR the name of the contact. Examples: 'juan.perez@uninorte.edu.co' or 'Juan Pérez' or 'Dr. García'. When user selects from multiple options (e.g., 'el segundo', 'opción 1'), use the specific email address of that contact. If the user wants to send the email to himself, put 'myself' in this field.")],
    subject: Annotated[str, Field(description="The subject of the email to send")],
    body: Annotated[str, Field(description="The body content of the email to send")],
    user_id: Annotated[int, Field(description="The ID of the user requesting the email")],
    status: Annotated[str, Field(description="A concise description of the email task being performed, using conjugated verbs (e.g., 'Enviando correo a...', 'Sending email to...') in the same language as the user's question")]
) -> dict:
    """
    Sends an email on behalf of the user using their Microsoft Graph API token.

    Can accept either an email address or a contact name. If a name is provided and multiple
    contacts are found, it will show options for the user to choose from. The AI can then
    identify the user's selection and call this function again with the specific email.

    Use when users want to send professional correspondence, messages, or share information
    via email within the university environment.

    Examples: "Send an email to my professor", "Draft a message to Dr. García",
    "Email the coordinator about my project"

    Returns success confirmation or error message with sending status.
    """
    try:
        return send_email_on_behalf_of_user(to_email_or_name, subject, body, user_id, status)
    except Exception as e:
        return {"error": f"Email sending failed: {str(e)}"}

@mcp.tool(
    name="search_contacts_by_name"
)
def search_contacts_tool(
    name: Annotated[str, Field(description="The name to search for. Can be partial name, first name, last name, or full name. Example: 'Juan', 'Pérez', 'Dr. García'")],
    user_id: Annotated[int, Field(description="The ID of the user making the search")],
    status: Annotated[str, Field(description="A concise description of the search task being performed, using conjugated verbs (e.g., 'Buscando contacto...', 'Searching for contact...') in the same language as the user's question")]
) -> dict:
    """
    Searches for contacts by name using Microsoft Graph API.

    Useful when the user specifically wants to find someone's contact information without
    sending an email immediately. Perfect for looking up professors, administrators,
    colleagues, or any university personnel.

    Examples: "Find Dr. García's contact", "Look up Professor Martinez",
    "Search for the coordinator's email"

    Returns contact results with HTML display showing names, emails, and departments.
    """
    try:
        return search_contacts_by_name(name, user_id, status)
    except Exception as e:
        return {"error": f"Contact search failed: {str(e)}"}

@mcp.tool(
    name="read_calendar_events"
)
def read_calendar_events_tool(
    start_date: Annotated[str, Field(description="Start date in YYYY-MM-DD format. Calculate this based on the user's request and current Bogotá date")],
    end_date: Annotated[str, Field(description="End date in YYYY-MM-DD format. Calculate this based on the user's request and current Bogotá date")],
    user_id: Annotated[int, Field(description="The ID of the user requesting calendar information")],
    status: Annotated[str, Field(description="A concise description of the task being performed, using conjugated verbs (e.g., 'Consultando calendario...', 'Checking calendar...', 'Revisando eventos...') in the same language as the user's question")]
) -> dict:
    """
    Reads and displays calendar events for a specified date range. Shows events in a visual format.

    Perfect for schedule management and planning. Use when users ask about their agenda,
    upcoming meetings, appointments, or want to check their availability for specific dates.

    Examples: "What's on my calendar today?", "Show me my schedule for this week",
    "Do I have any meetings tomorrow?", "Check my agenda for next Monday"

    Returns calendar events with elegant visual presentation showing times, titles, and details.
    """
    try:
        return read_calendar_events(start_date, end_date, user_id, status)
    except Exception as e:
        return {"error": f"Calendar reading failed: {str(e)}"}

@mcp.tool(
    name="create_calendar_event"
)
def create_calendar_event_tool(
    title: Annotated[str, Field(description="Title or subject of the reminder/event. Examples: 'Estudiar para examen de matemáticas', 'Recordatorio: entregar proyecto', 'Cita médica', 'Llamar a mamá'")],
    start_datetime: Annotated[str, Field(description="Start date and time in YYYY-MM-DDTHH:MM format (Colombia time). Calculate this based on the user's request and current date/time. Example: '2025-07-10T14:30'")],
    end_datetime: Annotated[str, Field(description="End date and time in YYYY-MM-DDTHH:MM format (Colombia time). Calculate this based on the user's request. If not specified, default to 1 hour after start time. Example: '2025-07-10T15:30'")],
    user_id: Annotated[int, Field(description="The ID of the user creating the event")],
    description: Annotated[str, Field(description="Optional description or notes for the event. Can include additional details, location, or any relevant information")] = "",
    status: Annotated[str, Field(description="A concise description of the task being performed, using conjugated verbs (e.g., 'Creando recordatorio...', 'Creating reminder...', 'Agendando evento...') in the same language as the user's question")] = "Creating calendar event..."
) -> dict:
    """
    Creates a personal reminder or event in the user's calendar.

    Perfect for setting up personal appointments, deadlines, study sessions, or any personal
    reminders. Does not involve other people - this is for personal time management and
    organization within the university context.

    Examples: "Remind me to study for my exam tomorrow", "Create a reminder to submit my project",
    "Schedule a study session for Friday", "Add a reminder to call my advisor"

    Returns success confirmation with event details or error message.
    """
    try:
        return create_calendar_event(title, start_datetime, end_datetime, user_id, description, status)
    except Exception as e:
        return {"error": f"Calendar event creation failed: {str(e)}"}

@mcp.tool(
    name="read_user_emails"
)
def read_user_emails_tool(
    user_id: Annotated[int, Field(description="The ID of the user requesting email information")],
    max_emails: Annotated[int, Field(description="Maximum number of emails to retrieve (default: 10, max: 50)")] = 10,
    unread_only: Annotated[bool, Field(description="If true, only returns unread emails (default: false)")] = False,
    search_query: Annotated[str | None, Field(description="Search query for subject, sender, or content (optional)")] = None,
    read_full_content: Annotated[bool, Field(description="Set to true when user asks specific questions about email content (use only when NOT using specific_subject). Default: false")] = False,
    specific_subject: Annotated[str | None, Field(description="OPTIMIZATION: Use when user asks about a specific email that was already shown/displayed. Put the exact or partial subject here. This automatically enables full content reading and limits results for efficiency")] = None,
    status: Annotated[str, Field(description="Status message for tracking in user's language")] = "Reading emails..."
) -> dict:
    """
    Reads user emails without marking them as read. Includes advanced filtering and optimization options.

    Use specific_subject for optimal performance when user asks about a previously shown email.
    Perfect for checking unread messages, searching for specific emails, or reviewing recent correspondence.

    OPTIMIZATION STRATEGY:
    - Use specific_subject when user asks about a specific email that was previously shown
    - Use read_full_content=true when user asks general content questions but no specific email context
    - Default mode for browsing emails, listing, or checking for new ones

    Examples: "Check my emails", "Any new messages?", "Search for emails from my professor",
    "What does that meeting email say?", "Show me unread emails"

    Returns email list with modern HTML presentation, preserving read/unread status.
    """
    try:
        return read_user_emails(user_id, max_emails, unread_only, search_query, read_full_content, specific_subject, status)
    except Exception as e:
        return {"error": f"Email reading failed: {str(e)}"}

@mcp.tool(
    name="explain_naia_roles"
)
def explain_naia_roles_tool(
    user_id: Annotated[int, Field(description="The ID of the user requesting the role explanation")],
    status: Annotated[str, Field(description="A concise description of the role explanation task being performed, using conjugated verbs (e.g., 'Explicando los roles de NAIA...', 'Showing NAIA's capabilities...') in the same language as the user's question")],
    auto_slide_interval: Annotated[int, Field(description="The interval in milliseconds for auto-advancing the carousel slides. Default is 3000ms (3 seconds)")] = 3000,
) -> dict:
    """
    Generate a carousel with explanations of all five NAIA roles.

    ALWAYS use this function when users ask about what roles NAIA has or ask for an
    explanation of NAIA's capabilities. Perfect for introducing new users to the platform
    or when users want to explore other available services.

    Examples: "What can NAIA do?", "Tell me about your roles", "What services do you offer?",
    "Show me NAIA's capabilities", "What other roles are available?"

    Returns an interactive carousel showcasing all NAIA roles with descriptions and capabilities.
    """
    try:
        return explain_naia_roles(auto_slide_interval, user_id, status)
    except Exception as e:
        return {"error": f"Role explanation failed: {str(e)}"}

@mcp.resource("file://personal_assistant/info")
def personal_assistant_info():
    """Basic information about NAIA Personal Assistant services and capabilities."""
    return {
        "role": "Personal Assistant",
        "university": "Universidad del Norte",
        "location": "Barranquilla, Colombia",
        "available_services": [
            "Current news retrieval with visualization",
            "Weather information and forecasts",
            "Email composition and sending",
            "Contact search and directory lookup",
            "Calendar event management",
            "Personal reminder creation",
            "Email reading and management",
            "NAIA roles explanation"
        ],
        "specialization": "Administrative support and task management within university environment",
        "capabilities": [
            "Microsoft Graph API integration for emails and calendar",
            "News and weather data with modern visualizations",
            "Professional correspondence assistance",
            "Schedule and appointment management",
            "Contact directory access",
            "Personal productivity tools"
        ],
        "description": "MCP server providing personal assistant and administrative support services for NAIA"
    }

@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    return JSONResponse({"status": "ok", "server": "NAIA Personal Assistant MCP"})

# REST API Endpoints for easier integration
@mcp.custom_route("/api/tools", methods=["GET"])
async def list_tools_endpoint(request):
    """List all available personal assistant tools in REST format"""
    tools = [
        {"name": "get_current_news", "description": "Get current news with modern visualization", "endpoint": "/api/news"},
        {"name": "get_weather", "description": "Get weather information and forecasts", "endpoint": "/api/weather"},
        {"name": "send_email_on_behalf_of_user", "description": "Send emails using Microsoft Graph", "endpoint": "/api/email"},
        {"name": "search_contacts_by_name", "description": "Search university contacts", "endpoint": "/api/contacts"},
        {"name": "read_calendar_events", "description": "Read calendar events for date range", "endpoint": "/api/calendar"},
        {"name": "create_calendar_event", "description": "Create personal calendar events", "endpoint": "/api/calendar/create"},
        {"name": "read_user_emails", "description": "Read user emails with filtering", "endpoint": "/api/emails"},
        {"name": "explain_naia_roles", "description": "Show NAIA roles carousel", "endpoint": "/api/roles"}
    ]
    return JSONResponse({"tools": tools, "mcp_endpoint": "/mcp/v1", "protocol": "MCP + REST"})

@mcp.custom_route("/api/news", methods=["POST"])
async def get_news_rest(request):
    """REST endpoint for news retrieval"""
    try:
        data = await request.json()
        result = get_current_news(
            location=data.get("location", ""),
            user_id=data.get("user_id", 1),
            status=data.get("status", "Getting news..."),
            query=data.get("query", ""),
            language=data.get("language", "en")
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@mcp.custom_route("/api/weather", methods=["POST"])
async def get_weather_rest(request):
    """REST endpoint for weather information"""
    try:
        data = await request.json()
        result = get_weather(
            location=data.get("location", ""),
            user_id=data.get("user_id", 1),
            status=data.get("status", "Getting weather...")
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@mcp.custom_route("/api/email", methods=["POST"])
async def send_email_rest(request):
    """REST endpoint for sending emails"""
    try:
        data = await request.json()
        result = send_email_on_behalf_of_user(
            to_email_or_name=data.get("to_email_or_name", ""),
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            user_id=data.get("user_id", 1),
            status=data.get("status", "Sending email...")
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    print("Starting NAIA Personal Assistant MCP Server...")
    print(f"Project root: {project_root}")
    print()
    print("MCP Tools:")
    print("   - get_current_news")
    print("   - get_weather")
    print("   - send_email_on_behalf_of_user")
    print("   - search_contacts_by_name")
    print("   - read_calendar_events")
    print("   - create_calendar_event")
    print("   - read_user_emails")
    print("   - explain_naia_roles")
    print()
    print("REST Endpoints:")
    print("   - GET  /api/tools (list all tools)")
    print("   - POST /api/news (get current news)")
    print("   - POST /api/weather (get weather info)")
    print("   - POST /api/email (send email)")
    print("   - GET  /health (health check)")
    print()
    print("MCP Protocol: http://localhost:9002/mcp/v1")

    mcp.run(transport="http",
    host="0.0.0.0",
    port=9003)