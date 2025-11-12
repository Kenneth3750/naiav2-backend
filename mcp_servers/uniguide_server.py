import sys
import os
import django
from pathlib import Path
from fastmcp import FastMCP, Client
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Annotated
from pydantic import Field
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables first
load_dotenv()

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

# Get MCP token from environment
MCP_TOKEN = os.getenv('uni_mcp_token')
if not MCP_TOKEN:
    print("⚠ Warning: No MCP token configured. Authentication disabled.")

# Fix Accept header middleware - OpenAI doesn't send text/event-stream
class AcceptHeaderFixMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Fix the Accept header to include text/event-stream for MCP protocol
        # OpenAI Realtime API doesn't send this header, but FastMCP requires it
        accept_header = request.headers.get("accept", "")
        if "text/event-stream" not in accept_header:
            # Create new headers with the required Accept header
            headers = dict(request.headers)
            if accept_header:
                headers["accept"] = f"{accept_header}, text/event-stream"
            else:
                headers["accept"] = "application/json, text/event-stream"

            # Rebuild request with fixed headers
            from starlette.datastructures import Headers
            request._headers = Headers(headers)

        return await call_next(request)

# Authentication middleware - TEMPORARILY DISABLED FOR TESTING
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # TEMPORARILY DISABLED - Allow all requests for testing OpenAI connection
        return await call_next(request)

        # Skip auth for health checks
        if request.url.path == "/health":
            return await call_next(request)

        # Check Bearer token if configured
        if MCP_TOKEN:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    {"error": "Missing or invalid Authorization header"},
                    status_code=401
                )

            token = auth_header.replace("Bearer ", "")
            if token != MCP_TOKEN:
                return JSONResponse(
                    {"error": "Invalid authentication token"},
                    status_code=403
                )

        return await call_next(request)

# Initialize MCP server with both middlewares
# AcceptHeaderFixMiddleware runs first to fix headers for OpenAI compatibility
# AuthMiddleware runs second (currently disabled for testing)
mcp = FastMCP(
    name="NAIAUniGuideMCPServer",
    middleware=[
        Middleware(AcceptHeaderFixMiddleware),
        Middleware(AuthMiddleware)
    ]
)

@mcp.tool(
        name="university_rag_query"
)
def university_rag_query(
    question: Annotated[str, Field(description="The academic or administrative question to search for in Universidad del Norte's official knowledge base. Use for policies, procedures, scholarships, certificates, requirements, academic programs, enrollment processes, and any procedural university information")],
    user_id: Annotated[int, Field(description="User ID for tracking purposes across university guide functions")] = 1,
    k: Annotated[int, Field(description="Number of relevant results to return from the RAG database")] = 3,
    status: Annotated[str, Field(description="Status message describing the search operation, use conjugated verbs in user's language (e.g., 'Consultando información universitaria...', 'Querying university information...')")] = "Searching university documents..."
) -> dict:
    """
    Query Universidad del Norte's official RAG database for verified academic and administrative information.
    
    PRIORITY 1 FUNCTION - ALWAYS TRY RAG FIRST for university information:
    Use for ALL administrative, academic, and procedural questions about Universidad del Norte.
    Contains verified and up-to-date official university information.
    
    INFORMATION AVAILABLE:
    - Academic flexibility and dual programs
    - UniNorte scholarships and financial aid
    - Certificates and official university documents  
    - Undergraduate-graduate program connections
    - Academic regulation exceptions
    - Graduation procedures and requirements
    - Academic and financial enrollment processes
    - Tutoring programs and academic monitoring
    - Professional internships and legal practices
    - University policies, procedures, and services
    
    EXAMPLES OF USE:
    - "¿Cómo solicito una beca?" → query_university_rag ONLY
    - "¿Cuáles son los requisitos de grado?" → query_university_rag ONLY
    - "What scholarships does UniNorte offer?"
    - "How do I get an academic certificate?"
    - "¿Qué materias se dan en el pregrado de ingeniería biomédica?"
    - "¿Cuál es el pensum de medicina?"
    
    CRITICAL RULES:
    - ONLY use for Universidad del Norte information, not other institutions
    - Information comes in JSON with key "resolved_rag" - use ONLY this retrieved information
    - Do NOT add information that wasn't retrieved from the function
    - If uncertain about information availability, ALWAYS try this function first
    - Check if menus are already attached to response before suggesting to provide them
    
    Returns official university information from verified knowledge base.
    """
    try:
        return query_university_rag(user_id, question, k, status)
    except Exception as e:
        return {"error": f"RAG query failed: {str(e)}"}

@mcp.tool(
        name="get_campus_calendar"
)
def get_campus_calendar(
    months: Annotated[list[int], Field(description="List of month numbers (1-12) to search for university events (e.g., [7, 8, 9] for July-September events)")] ,
    user_id: Annotated[int, Field(description="User ID for tracking calendar requests")] = 1,
    status: Annotated[str, Field(description="Status message for calendar search progress")] = "Fetching university calendar..."
) -> dict:
    """
    Get university calendar events for multiple months to find specific dates and timing of university activities.
    
    Use for date/timing questions like "cuándo es", "when is", "fecha de", when users mention
    specific months by name, or when they ask to verify/search calendar information.
    
    Examples: "When do classes start?", "cuándo son los finales", "búscalo en el calendario"
    
    Always suggest adding interesting events to personal calendar after showing results.
    Returns calendar events with HTML visualization.
    """
    try:
        return get_university_calendar_multi_month(user_id, months, status)
    except Exception as e:
        return {"error": f"Calendar fetch failed: {str(e)}"}

@mcp.tool(
        name="virtual_campus_tour"
)
def virtual_campus_tour(
    area_filter: Annotated[str | None, Field(description="Filter by category: 'academic', 'recreational', 'services', or None for complete tour")] = None,
    place_name: Annotated[str | None, Field(description="Specific facility name (e.g., 'biblioteca', 'piscina', 'cafetería') or None for overview")] = None,
    language: Annotated[str, Field(description="Language for tour interface: 'Spanish' or 'English'")] = "Spanish",
    user_id: Annotated[int, Field(description="User ID for tracking")] = 1,
    status: Annotated[str, Field(description="Status message for tour generation progress")] = "Generating virtual tour..."
) -> dict:
    """
    Generate interactive virtual campus tour with images and facility information.
    
    Use when users want to explore campus facilities, see university locations, or ask about
    specific places like "show me the campus", "where is the library", "tour virtual".
    
    Returns HTML interface with image galleries and detailed facility information.
    Cannot make reservations - only shows facility details and contact information.
    """
    try:
        return get_virtual_campus_tour(area_filter, place_name, language, user_id, status)
    except Exception as e:
        return {"error": f"Virtual tour failed: {str(e)}"}

@mcp.tool(
        name="search_university_internet"
)
def search_university_internet(
    query: Annotated[str, Field(description="The search query about Universidad del Norte. Use for: 1) Promotional/comparative queries like 'why study engineering at UniNorte vs other coast universities', 'what distinguishes UniNorte's medicine program', 'UniNorte advantages over other institutions'; 2) Fallback when RAG returns irrelevant information (e.g., user asks about curriculum but RAG returns scholarship info); 3) Highly specific physical details like 'how many floors does building J have', 'what color are the park benches', architectural measurements")],
    user_id: Annotated[int, Field(description="Unique identifier for the user making the request, used for tracking and logging purposes across all university guide functions")],
    image_query: Annotated[str, Field(description="Optional search query specifically for finding relevant images about the topic (e.g., 'Universidad del Norte campus', 'UniNorte facilities', 'engineering labs UniNorte'). Leave empty if no visual content is needed. ALways refer to UniNorte with location context (e.g., 'Universidad del Norte in Barranquilla', 'UniNorte Colombia') because it may be confused with other institutions with similar names.")],
    status: Annotated[str, Field(description="Descriptive status message explaining the current search operation, should use conjugated verbs in the same language as user's question (e.g., 'Buscando información sobre ventajas de UniNorte...', 'Searching for UniNorte competitive advantages...')")] = "Searching the internet..."
) -> dict:
    """
    Search the internet for Universidad del Norte information with three primary use cases:
    
    1) AUTOMATIC FALLBACK - Use when RAG database doesn't contain relevant information for user's specific question.
       Examples: user asks about curriculum details but RAG returns unrelated scholarship information, 
       user asks about specific procedures but RAG returns general policies.
    
    2) PROMOTIONAL/COMPARATIVE QUESTIONS - Use for queries comparing UniNorte advantages vs other universities.
       Examples: 'por qué estudiar ingeniería en la Universidad del Norte vs otras universidades de la costa',
       'qué diferencia el programa de medicina de UniNorte de otras instituciones',
       'why choose UniNorte over other Caribbean coast universities',
       'what makes UniNorte's engineering program better than competitors',
       questions about UniNorte's ranking, prestige, unique features, research capabilities, 
       international connections, campus quality, or competitive advantages.
    
    3) HIGHLY SPECIFIC PHYSICAL DETAILS - Use for architectural questions requiring direct observation.
       Examples: 'cuántos pisos tiene el edificio J', 'de qué color son las bancas del parque',
       'qué altura tiene la torre administrativa', specific measurements, construction details,
       or visual elements not available in official university documents.
    
    Always use as seamless fallback when RAG results don't match user's query - never announce 
    the fallback, just provide comprehensive information from internet sources.
    """
    try:
        return search_internet_for_uni_answers(query, status, user_id, image_query)
    except Exception as e:
        return {"error": f"Internet search failed: {str(e)}"}

@mcp.tool(
        name="send_university_email"
)
def send_university_email(
    to_email: Annotated[str, Field(description="Recipient email address. Can use 'mi correo' for user's own email or specific email addresses")],
    subject: Annotated[str, Field(description="Email subject line describing the content being sent")],
    body: Annotated[str, Field(description="Email body content with the information requested by the user")],
    user_id: Annotated[int, Field(description="User ID for tracking email requests")],
    status: Annotated[str, Field(description="Status message for email sending progress")] = "Sending email..."
) -> dict:
    """
    Send an email through the university email system when users explicitly request it.
    
    Use when users ask to send information via email like "Send me the details at my email",
    "Please email me the information", or "envíame eso por correo".
    
    Only use when user explicitly requests email delivery - not for general information sharing.
    Returns success confirmation or error message.
    """
    try:
        return send_email(to_email, subject, body, status, user_id)
    except Exception as e:
        return {"error": f"Email sending failed: {str(e)}"}

@mcp.tool(
        name="search_university_contacts"
)
def search_university_contacts(
    name: Annotated[str, Field(description="Name to search for in university directory. Can be partial name, first name, last name, or full name (e.g., 'Juan', 'Pérez', 'Dr. García')")],
    user_id: Annotated[int, Field(description="User ID for tracking contact search requests")],
    status: Annotated[str, Field(description="Status message for contact search progress")] = "Searching contacts..."
) -> dict:
    """
    Search for contacts in the university directory to find email addresses and contact information.
    
    Use when users want to find contact information for university staff, professors, or 
    administrative personnel, or when they need email addresses to send information to specific people.
    
    Examples: "busca el contacto de Dr. García", "find Professor Martinez email", 
    "necesito el email del coordinador de..."
    
    Returns contact results with HTML display of found directory entries.
    """
    try:
        return search_contacts_by_name(name, user_id, status)
    except Exception as e:
        return {"error": f"Contact search failed: {str(e)}"}

@mcp.tool(
        name="create_university_calendar_event"
)
def create_university_calendar_event(
    title: Annotated[str, Field(description="Event title/name for the calendar reminder")],
    start_datetime: Annotated[str, Field(description="Start date and time in YYYY-MM-DDTHH:MM format (Colombia time zone)")],
    end_datetime: Annotated[str, Field(description="End date and time in YYYY-MM-DDTHH:MM format (Colombia time zone)")],
    user_id: Annotated[int, Field(description="User ID for tracking calendar event creation")],
    description: Annotated[str, Field(description="Optional detailed description of the event")] = "",
    status: Annotated[str, Field(description="Status message for calendar event creation progress")] = "Creating calendar event..."
) -> dict:
    """
    Create a personal calendar reminder for university events to help users not miss important activities.
    
    Use when users want to save university events to their personal calendar after seeing 
    calendar information, or when they express interest in attending specific events.
    
    Examples: "add that event to my calendar", "remind me about the graduation ceremony",
    "I want to save that date so I don't forget"
    
    Perfect for creating personal reminders of university deadlines, events, or important dates.
    Returns success confirmation or error message.
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
    
    # Using HTTP transport with AcceptHeaderFixMiddleware to handle OpenAI's missing headers
    mcp.run(transport="http",
    host="0.0.0.0",
    port=9001)