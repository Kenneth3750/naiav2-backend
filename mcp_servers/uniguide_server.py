import sys
import os
import django
from pathlib import Path
from fastmcp import FastMCP, Client
from starlette.responses import JSONResponse

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

# Now import the functions from apps.uniguide.functions (after Django is set up)
try:
    from apps.uniguide.functions import (
        create_rag,
        query_university_rag,
        get_university_calendar_multi_month,
        get_virtual_campus_tour,
        search_internet_for_uni_answers,
        send_email,
        search_contacts_by_name,
        create_calendar_event
    )
    print("✓ Successfully imported uniguide functions")
except ImportError as e:
    print(f"✗ Error importing functions: {e}")
    sys.exit(1)
    
# Initialize MCP server
mcp = FastMCP(
    name="NAIAUniGuideMCPServer"
)

@mcp.tool(
        name="university_rag_query",
        description="Query the university RAG system for information about Universidad del Norte.",
        tags={"university", "rag", "query"},
        meta={"version": "1.0", "author": "NAIA-team"}
)
def university_rag_query(question: str, user_id: int = 1, k: int = 3, status: str = "Searching university documents...") -> dict:
    """
    Query the university RAG system for information about Universidad del Norte.
    
    Args:
        question: The question to search for in university documents
        user_id: User ID for tracking (default: 1)
        k: Number of results to return (default: 3)
        status: Status message for tracking
        
    Returns:
        Dictionary with resolved_rag content or error
    """
    try:
        return query_university_rag(user_id, question, k, status)
    except Exception as e:
        return {"error": f"RAG query failed: {str(e)}"}

@mcp.tool(
        name="get_campus_calendar",
        description="Get university calendar events for multiple months to find specific dates and events",
        tags={"university", "calendar", "query"},
        meta={"version": "1.0", "author": "NAIA-team"}
)
def get_campus_calendar(months: list[int], user_id: int = 1, status: str = "Fetching university calendar...") -> dict:
    """
    Get university calendar events for specified months.
    
    Args:
        months: List of month numbers (1-12) to search
        user_id: User ID for tracking
        status: Status message for tracking
        
    Returns:
        Dictionary with calendar events and HTML graph
    """
    try:
        return get_university_calendar_multi_month(user_id, months, status)
    except Exception as e:
        return {"error": f"Calendar fetch failed: {str(e)}"}

@mcp.tool(
        name="virtual_campus_tour",
        description="Generate an interactive virtual campus tour with images and detailed information about university facilities. Perfect for showcasing campus locations, providing facility details, and helping users explore the university virtually.",
        tags={"university", "tour", "virtual"},
        meta={"version": "1.0", "author": "NAIA-team"}
)
def virtual_campus_tour(area_filter: str = None, place_name: str = None, language: str = "Spanish", user_id: int = 1, status: str = "Generating virtual tour...") -> dict:
    """
    Generate an interactive virtual campus tour.
    
    Args:
        area_filter: Filter by category ("academic", "recreational", "services") or None for all
        place_name: Specific place name or None for category/all places
        language: Language for the tour interface
        user_id: User ID for tracking
        status: Status message for tracking
        
    Returns:
        Dictionary with HTML tour interface split between "display" and "graph"
    """
    try:
        return get_virtual_campus_tour(area_filter, place_name, language, user_id, status)
    except Exception as e:
        return {"error": f"Virtual tour failed: {str(e)}"}

@mcp.tool(
        name="search_university_internet",
        description="Search the internet for specific information about Universidad del Norte. Use ONLY for highly specific questions about campus facilities, architectural details, or very detailed information that requires direct observation. Do NOT use for academic policies, procedures, scholarships, or administrative processes (use university_rag_query for those).",
        tags={"university", "internet", "search"},
        meta={"version": "1.0", "author": "NAIA-team"}
)
def search_university_internet(query: str, user_id: int = 1, status: str = "Searching internet for university info...", image_query: str = "") -> dict:
    """
    Search the internet for specific information about Universidad del Norte.
    
    Args:
        query: The search query about the university
        user_id: User ID for tracking
        status: Status message for tracking
        image_query: Related image search query
        
    Returns:
        Dictionary with search results and image carousel
    """
    try:
        return search_internet_for_uni_answers(query, status, user_id, image_query)
    except Exception as e:
        return {"error": f"Internet search failed: {str(e)}"}

@mcp.tool(
        name="send_university_email",
        description="Send an email through the university email system. Use this function when users request to send an email to themselves or others.",
        tags={"university", "email", "send"},
        meta={"version": "1.0", "author": "NAIA-team"}
)
def send_university_email(to_email: str, subject: str, body: str, user_id: int = 1, status: str = "Sending email...") -> dict:
    """
    Send an email through the university email system.
    
    Args:
        to_email: Recipient email address (can use "mi correo" for user's own email)
        subject: Email subject
        body: Email body content
        user_id: User ID for tracking
        status: Status message for tracking
        
    Returns:
        Dictionary with success message or error
    """
    try:
        return send_email(to_email, subject, body, status, user_id)
    except Exception as e:
        return {"error": f"Email sending failed: {str(e)}"}

@mcp.tool(
        name="search_university_contacts",
        description="Search for contacts in the university directory. Use this function when users request to search for a contact in the university directory.",
        tags={"university", "contacts", "search"},
        meta={"version": "1.0", "author": "NAIA-team"}
)
def search_university_contacts(name: str, user_id: int = 1, status: str = "Searching contacts...") -> dict:
    """
    Search for contacts in the university directory.
    
    Args:
        name: Name to search for
        user_id: User ID for tracking
        status: Status message for tracking
        
    Returns:
        Dictionary with contact results and HTML display
    """
    try:
        return search_contacts_by_name(name, user_id, status)
    except Exception as e:
        return {"error": f"Contact search failed: {str(e)}"}

@mcp.tool(
        name="create_university_calendar_event",
        description="Create a personal calendar reminder for university events. Perfect for helping users save important university events to their personal calendar so they don't miss them.",
        tags={"university", "calendar", "event"},
        meta={"version": "1.0", "author": "NAIA-team"}
)
def create_university_calendar_event(title: str, start_datetime: str, end_datetime: str, user_id: int = 1, description: str = "", status: str = "Creating calendar event...") -> dict:
    """
    Create a calendar event/reminder.
    
    Args:
        title: Event title
        start_datetime: Start date and time in YYYY-MM-DDTHH:MM format (Colombia time)
        end_datetime: End date and time in YYYY-MM-DDTHH:MM format (Colombia time)
        user_id: User ID for tracking
        description: Optional event description
        status: Status message for tracking
        
    Returns:
        Dictionary with success message or error
    """
    try:
        return create_calendar_event(title, start_datetime, end_datetime, user_id, description, status)
    except Exception as e:
        return {"error": f"Calendar event creation failed: {str(e)}"}

@mcp.resource("file://university/info")
def university_info():
    """Basic information about Universidad del Norte and available services."""
    return {
        "university": "Universidad del Norte",
        "location": "Barranquilla, Colombia", 
        "available_services": [
            "RAG document search",
            "Virtual campus tour",
            "Calendar events",
            "Internet search",
            "Email services",
            "Contact directory",
            "Calendar management"
        ],
        "description": "MCP server providing university services and information"
    }

@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    return JSONResponse({"status": "ok", "server": "NAIA UniGuide MCP"})

# REST API Endpoints (opcional - para facilidad de uso)
@mcp.custom_route("/api/tools", methods=["GET"])
async def list_tools_endpoint(request):
    """Lista todas las herramientas disponibles en formato REST"""
    tools = [
        {"name": "university_rag_query", "description": "Search university documents using RAG", "endpoint": "/api/rag"},
        {"name": "get_campus_calendar", "description": "Get university calendar events", "endpoint": "/api/calendar"},
        {"name": "virtual_campus_tour", "description": "Generate virtual campus tour", "endpoint": "/api/tour"},
        {"name": "search_university_internet", "description": "Search internet for university info", "endpoint": "/api/search"},
        {"name": "send_university_email", "description": "Send university email", "endpoint": "/api/email"},
        {"name": "search_university_contacts", "description": "Search university contacts", "endpoint": "/api/contacts"},
        {"name": "create_university_calendar_event", "description": "Create calendar event", "endpoint": "/api/calendar/event"}
    ]
    return JSONResponse({"tools": tools, "mcp_endpoint": "/mcp/v1", "protocol": "MCP + REST"})

@mcp.custom_route("/api/email", methods=["POST"])
async def send_email_rest(request):
    """REST endpoint para enviar emails"""
    try:
        data = await request.json()
        result = send_email(
            to_email=data.get("to_email", ""),
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            status=data.get("status", "Sending email..."),
            user_id=data.get("user_id", 1)
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@mcp.custom_route("/api/rag", methods=["POST"])
async def rag_query_rest(request):
    """REST endpoint para consultas RAG"""
    try:
        data = await request.json()
        result = query_university_rag(
            user_id=data.get("user_id", 1),
            question=data.get("question", ""),
            k=data.get("k", 3),
            status=data.get("status", "Searching...")
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    print("Starting NAIA UniGuide MCP Server...")
    print(f"Project root: {project_root}")
    print()
    print("MCP Tools:")
    print("   - university_rag_query")
    print("   - get_campus_calendar") 
    print("   - virtual_campus_tour")
    print("   - search_university_internet")
    print("   - send_university_email")
    print("   - search_university_contacts")
    print("   - create_university_calendar_event")
    print()
    print("REST Endpoints:")
    print("   - GET  /api/tools (list all tools)")
    print("   - POST /api/email (send email)")
    print("   - POST /api/rag (RAG query)")
    print("   - GET  /health (health check)")
    print()
    print("MCP Protocol: http://localhost:9001/mcp/v1")
    
    mcp.run(transport="http", 
    host="0.0.0.0", 
    port=9001)