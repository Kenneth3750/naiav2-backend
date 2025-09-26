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

# Now import the functions from various apps (after Django is set up)
try:
    from apps.recepcionist.functions import (
        answer_question_of_uni_premises,
        query_recepcionist_rag,
        get_location_events,
        get_restaurants,
        get_location_places,
        send_email
    )
    from apps.personal.functions import search_contacts_by_name
    from apps.researcher.functions import explain_naia_roles
    print("✓ Successfully imported recepcionist functions")
except ImportError as e:
    print(f"✗ Error importing functions: {e}")
    sys.exit(1)

# Initialize MCP server
mcp = FastMCP(
    name="NAIARecepcionistMCPServer"
)

@mcp.tool(
    name="search_university_contacts"
)
def search_university_contacts(
    name: Annotated[str, Field(description="The name to search for. Can be partial name, first name, last name, or full name. Example: 'Juan', 'Pérez', 'Dr. García'")],
    user_id: Annotated[int, Field(description="The ID of the user making the search. Used for logging and tracking purposes")] = 1,
    status: Annotated[str, Field(description="A concise description of the search task being performed, using conjugated verbs (e.g., 'Buscando contacto...', 'Searching for contact...') in the same language as the user's question")] = "Searching contacts..."
) -> dict:
    """
    Searches for contacts by name using Microsoft Graph API. Useful when the user specifically wants to find someone's contact information without sending an email immediately.

    This function provides access to the university directory and returns contact information including email addresses and other details. Perfect for finding university staff, faculty, and employee information.

    Returns contact results with HTML display of found directory entries, including contact numbers for reference when sending emails.
    """
    try:
        return search_contacts_by_name(name, user_id, status)
    except Exception as e:
        return {"error": f"Contact search failed: {str(e)}"}

@mcp.tool(
    name="get_university_premises_info"
)
def get_university_premises_info(
    place: Annotated[str, Field(description="The specific place or facility within the university premises. Must be one of the exact names from the university facilities list",
                                 enum=[
                                     "Restaurante Bocas de Ceniza",
                                     "Restaurante du Nord Plaza",
                                     "Café du Nord",
                                     "Restaurante 1966",
                                     "du Nord Exprès",
                                     "du Nord Terrasse",
                                     "Le Petit",
                                     "La Esquina",
                                     "El Contenedor",
                                     "La Crepería",
                                     "du Nord H",
                                     "Vending Machines",
                                     "La Gelateria",
                                     "Hot Dogs",
                                     "Librería y Papelería KM5",
                                     "du Nord Store",
                                     "du Nord Graphique",
                                     "Almacen Mapuka",
                                     "Zonas Digitales",
                                     "Le Salón",
                                     "Gimnasio Uninorte",
                                     "Droguería",
                                     "Coliseo",
                                     "Centro Deportivo Roble Amarillo"
                                 ])],
    user_id: Annotated[int, Field(description="The ID of the user making the request, used for logging and tracking purposes")] = 1,
    status: Annotated[str, Field(description="A concise description of the question about university premises, using conjugated verbs (e.g., 'Buscando información sobre [lugar]')")] = "Getting premises information..."
) -> dict:
    """
    Answer questions about university premises, such as locations, facilities, and general information about the university campus.

    Provides detailed information about campus facilities including restaurants, gyms, stores, and other university locations. Returns comprehensive details about operating hours, services, locations, and visual content through image carousels.

    Note: Users may not use exact place names, so flexible matching is important. For example, users might say "graphique", "plaza", "bocas", etc.
    """
    try:
        return answer_question_of_uni_premises(place, user_id, status)
    except Exception as e:
        return {"error": f"Premises query failed: {str(e)}"}

@mcp.tool(
    name="search_restaurant_menus"
)
def search_restaurant_menus(
    question: Annotated[str, Field(description="An optimized search query that helps to retrieve the info that is needed to answer the user question or to give the best advice according to what the user is saying. Always put this query in spanish cause all the menus are in spanish, this may not be the language that you will use to give a final response, but it is the language that you must use to retrieve the information from the database.")],
    user_id: Annotated[int, Field(description="The ID of the user making the request, used for logging and tracking purposes")] = 1,
    status: Annotated[str, Field(description="A concise description of the search task, using conjugated verbs (e.g., 'Consultando precios del menú', 'Buscando opciones de comida') in the same language as the user's question")] = "Searching menu information...",
    k: Annotated[int, Field(description="Number of relevant documents to retrieve from the database. Default is 3 for most queries, use 5-7 for comprehensive menu searches.")] = 3,
    restaurant_menus: Annotated[list[str] | None, Field(description="Optional list of restaurant names to show menu displays for. Available options: ['du nord plaza', 'cafe du nord', 'du nord terrasse', 'bocas de ceniza', 'du nord expres', 'restaurante 1966']. Use null/empty if no menu display needed.")] = None
) -> dict:
    """
    Search for specific information about restaurant menus, prices, food options, and detailed information about du Nord dining establishments. This function has access to comprehensive menu data, pricing information, and specific details about food services on campus.

    Perfect for queries about restaurant menus, food prices, meal options, dietary restrictions, and dining services. Can also display visual menu interfaces for selected restaurants.

    Use when users ask about what's available to eat, menu prices, specific dishes, or dining recommendations on campus.
    """
    try:
        return query_recepcionist_rag(user_id, question, k, status, restaurant_menus)
    except Exception as e:
        return {"error": f"Restaurant menu search failed: {str(e)}"}

@mcp.tool(
    name="find_location_events"
)
def find_location_events(
    location: Annotated[str, Field(description="The location to search for events (city, neighborhood, or area). Examples: 'Barranquilla', 'Bogotá', 'New York'")] = "Barranquilla",
    event_query: Annotated[str, Field(description="Specific event or type of events to search for. Examples: 'concerts', 'art exhibitions', 'food festivals'")] = "concerts",
    user_id: Annotated[int, Field(description="The ID of the user making the request, used for logging and tracking purposes")] = 1,
    status: Annotated[str, Field(description="A concise description of the search task, using conjugated verbs (e.g., 'Buscando eventos en [ubicación]') in the same language as the user's question")] = "Searching for events..."
) -> dict:
    """
    Get events happening in a specific location using Google Events. Returns both elegant display and interactive calendar for events discovery.

    Perfect for finding concerts, festivals, cultural events, sports activities, and local happenings in any city or location. Provides comprehensive event information with images and details.

    Use when users want to know what's happening in a specific area or when they're looking for entertainment and activities.
    """
    try:
        return get_location_events(location, user_id, status, event_query)
    except Exception as e:
        return {"error": f"Events search failed: {str(e)}"}

@mcp.tool(
    name="find_local_restaurants"
)
def find_local_restaurants(
    location: Annotated[str, Field(description="The location to search for restaurants (city, neighborhood, or area). Examples: 'Barranquilla', 'Centro Histórico Cartagena', 'Zona Rosa Bogotá'")] = "Barranquilla",
    food_query: Annotated[str, Field(description="Specific type of food or restaurant to search for. Examples: 'restaurants', 'pizza', 'seafood', 'italian food', 'coffee shops', 'fast food'")] = "restaurants",
    user_id: Annotated[int, Field(description="The ID of the user making the request, used for logging and tracking purposes")] = 1,
    status: Annotated[str, Field(description="A concise description of the search task, using conjugated verbs (e.g., 'Buscando restaurantes de [tipo] en [ubicación]') in the same language as the user's question")] = "Searching for restaurants..."
) -> dict:
    """
    Find restaurants and dining options in a specific location using Google Local search. Returns both elegant display and interactive map for restaurant discovery.

    Excellent for discovering dining options, specific cuisine types, and restaurant recommendations in any city or area. Provides detailed restaurant information with ratings, reviews, and locations.

    Use when users want dining recommendations, are looking for specific types of food, or need restaurant suggestions for a particular location.
    """
    try:
        return get_restaurants(location, food_query, user_id, status)
    except Exception as e:
        return {"error": f"Restaurant search failed: {str(e)}"}

@mcp.tool(
    name="discover_places_to_visit"
)
def discover_places_to_visit(
    location: Annotated[str, Field(description="The location to search for places to visit (city, neighborhood, or area). Examples: 'Barranquilla', 'Santa Marta', 'Cartagena Centro'")] = "Barranquilla",
    user_id: Annotated[int, Field(description="The ID of the user making the request, used for logging and tracking purposes")] = 1,
    status: Annotated[str, Field(description="A concise description of the search task, using conjugated verbs (e.g., 'Buscando lugares para visitar en [ubicación]') in the same language as the user's question")] = "Searching for places to visit...",
    location_query: Annotated[str, Field(description="Optional query to refine the search for places to visit. If empty, defaults to 'places to visit'. Examples: 'tourist attractions', 'things to do', 'sightseeing spots' or any specific query that helps to retrieve the info that is needed to answer the user question.")] = ""
) -> dict:
    """
    Discover places to visit and tourist attractions in a specific location using Google Local search. Returns both elegant display and interactive guide for place discovery.

    Perfect for finding tourist attractions, museums, parks, landmarks, and interesting places to visit in any city or location. Provides comprehensive information about attractions with images and descriptions.

    Use when users want travel recommendations, are planning visits to specific areas, or need suggestions for sightseeing and tourism activities.
    """
    try:
        return get_location_places(location, user_id, status, location_query)
    except Exception as e:
        return {"error": f"Places search failed: {str(e)}"}

@mcp.tool(
    name="send_information_email"
)
def send_information_email(
    to_email: Annotated[str, Field(description="The email of the user to send the email to. If the user wants to send the email to himself, put on this field the word 'myself' - the function manages it internally. If the user wants to send the email to another person, put the email of that person here.")],
    subject: Annotated[str, Field(description="The subject of the email to send.")],
    body: Annotated[str, Field(description="The body of the email to send.")],
    user_id: Annotated[int, Field(description="The ID of the user requesting the email")] = 1,
    status: Annotated[str, Field(description="A concise description of the email task being performed, using conjugated verbs (e.g., 'Enviando correo a...', 'Sending email about...') in the same language as the user's question")] = "Sending email..."
) -> dict:
    """
    Send an email to the user with the provided information. This function is used to send an email to the user with the information provided by the user.

    Can send emails to the user's own email address (using 'myself') or to specific email addresses. Perfect for sharing information, sending details, or forwarding important content via email.

    Use when users explicitly request to receive information via email or want to send information to someone else.
    """
    try:
        return send_email(to_email, subject, body, status, user_id)
    except Exception as e:
        return {"error": f"Email sending failed: {str(e)}"}

@mcp.tool(
    name="explain_naia_capabilities"
)
def explain_naia_capabilities(
    auto_slide_interval: Annotated[int, Field(description="The interval in milliseconds for auto-advancing the carousel slides. Default is 3000ms (3 seconds).")] = 3000,
    user_id: Annotated[int, Field(description="The ID of the user requesting the role explanation")] = 1,
    status: Annotated[str, Field(description="A concise description of the role explanation task being performed, using conjugated verbs (e.g., 'Explicando los roles de NAIA...', 'Showing NAIA's capabilities...') in the same language as the user's question")] = "Explaining NAIA roles..."
) -> dict:
    """
    Generate a carousel with explanations of all five NAIA roles. ALWAYS use this function when users ask about what roles NAIA has or ask for an explanation of NAIA's capabilities.

    Provides a comprehensive overview of all NAIA's specialized roles including Researcher, Skills Trainer, Personal Assistant, University Guide, and Receptionist. Shows detailed information about each role's capabilities and use cases.

    Perfect for introducing users to NAIA's full potential and helping them understand which role might be most helpful for their specific needs.
    """
    try:
        return explain_naia_roles(auto_slide_interval, user_id, status)
    except Exception as e:
        return {"error": f"NAIA roles explanation failed: {str(e)}"}

@mcp.resource("file://recepcionist/info")
def recepcionist_info():
    """Basic information about NAIA Recepcionist role and available services."""
    return {
        "role": "NAIA Recepcionist",
        "university": "Universidad del Norte",
        "location": "Barranquilla, Colombia",
        "available_services": [
            "University contact search",
            "Campus premises information",
            "Restaurant menu search",
            "Local events discovery",
            "Restaurant recommendations",
            "Places to visit guide",
            "Email services",
            "NAIA capabilities overview"
        ],
        "description": "MCP server providing reception and administrative support services for Universidad del Norte"
    }

@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    return JSONResponse({"status": "ok", "server": "NAIA Recepcionist MCP"})

# REST API Endpoints (optional - for ease of use)
@mcp.custom_route("/api/tools", methods=["GET"])
async def list_tools_endpoint(request):
    """List all available tools in REST format"""
    tools = [
        {"name": "search_university_contacts", "description": "Search university directory for contact information", "endpoint": "/api/contacts"},
        {"name": "get_university_premises_info", "description": "Get information about university facilities", "endpoint": "/api/premises"},
        {"name": "search_restaurant_menus", "description": "Search campus restaurant menus and pricing", "endpoint": "/api/menus"},
        {"name": "find_location_events", "description": "Find events in specified locations", "endpoint": "/api/events"},
        {"name": "find_local_restaurants", "description": "Find restaurants in specified locations", "endpoint": "/api/restaurants"},
        {"name": "discover_places_to_visit", "description": "Discover tourist attractions and places", "endpoint": "/api/places"},
        {"name": "send_information_email", "description": "Send information via email", "endpoint": "/api/email"},
        {"name": "explain_naia_capabilities", "description": "Show all NAIA role capabilities", "endpoint": "/api/capabilities"}
    ]
    return JSONResponse({"tools": tools, "mcp_endpoint": "/mcp/v1", "protocol": "MCP + REST"})

@mcp.custom_route("/api/email", methods=["POST"])
async def send_email_rest(request):
    """REST endpoint for sending emails"""
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

@mcp.custom_route("/api/menus", methods=["POST"])
async def menu_search_rest(request):
    """REST endpoint for menu searches"""
    try:
        data = await request.json()
        result = query_recepcionist_rag(
            user_id=data.get("user_id", 1),
            question=data.get("question", ""),
            k=data.get("k", 3),
            status=data.get("status", "Searching menus..."),
            restaurant_menus=data.get("restaurant_menus", None)
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    print("Starting NAIA Recepcionist MCP Server...")
    print(f"Project root: {project_root}")
    print()
    print("MCP Tools:")
    print("   - search_university_contacts")
    print("   - get_university_premises_info")
    print("   - search_restaurant_menus")
    print("   - find_location_events")
    print("   - find_local_restaurants")
    print("   - discover_places_to_visit")
    print("   - send_information_email")
    print("   - explain_naia_capabilities")
    print()
    print("REST Endpoints:")
    print("   - GET  /api/tools (list all tools)")
    print("   - POST /api/email (send email)")
    print("   - POST /api/menus (menu search)")
    print("   - GET  /health (health check)")
    print()
    print("MCP Protocol: http://localhost:9004/mcp/v1")

    mcp.run(transport="http",
    host="0.0.0.0",
    port=9004)