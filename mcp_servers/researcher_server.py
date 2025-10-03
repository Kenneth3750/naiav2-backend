import sys
import os
import django
from pathlib import Path
from fastmcp import FastMCP, Client
from starlette.responses import JSONResponse
from typing import Annotated
from pydantic import Field
from dotenv import load_dotenv

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

# Load environment variables
load_dotenv()

# Now import the functions from apps.researcher.functions (after Django is set up)
try:
    from apps.researcher.functions import (
        scholar_search,
        write_document,
        answer_from_user_rag,
        factual_web_query,
        create_graph,
        send_email,
        get_current_news,
        explain_naia_roles,
        deep_content_analysis_for_specific_information
    )
    print("✓ Successfully imported researcher functions")
except ImportError as e:
    print(f"✗ Error importing functions: {e}")
    sys.exit(1)

# Initialize MCP server
mcp = FastMCP(
    name="NAIAResearcherMCPServer"
)

@mcp.tool(
    name="scholar_search",
    description="EXCLUSIVELY for finding academic articles and research papers. Never use for general internet searches. Call this function any time the user wants academic references, citations, or scholarly information.",
    tags={"academic", "research", "scholar"},
    meta={"version": "1.0", "author": "NAIA-team"}
)
def search_academic_papers(
    query: Annotated[str, Field(description="Simple and clean search query optimized for Google Scholar. RULES: 1) For author searches: Use ONLY 'Author Full Name University Name' (keep university names in their original form, never translate them). 2) For topic searches: Use only the main keywords/topics. 3) NEVER include language specifications like 'artículos en inglés', 'English articles', 'papers in', etc. 4) NEVER include words like 'artículos', 'papers', 'research', 'estudios'. 5) Keep it simple as if typing directly in Google Scholar search box. Example: 'Cristian Quintero Monroy Universidad del Norte' NOT 'artículos de Cristian Quintero Monroy Universidad del Norte en inglés'")],
    query_2: Annotated[str, Field(description="Alternative search query in English following the same rules as 'query'. RULES: 1) For author searches: Use ONLY 'Author Full Name University Name' (keep university names exactly as provided by user, never translate). 2) For topic searches: Translate only the topic keywords to English. 3) NEVER include 'English articles', 'papers in English', etc. 4) If original query was already in English, make this slightly different by reordering terms or using synonyms. Example: 'Cristian Quintero Monroy Universidad del Norte' or for topics 'wastewater treatment neural networks' NOT 'English articles about wastewater treatment'")] = "",
    num_results: Annotated[int, Field(description="The number of results to return")] = 3,
    status: Annotated[str, Field(description="A concise description of the search task being performed, using conjugated verbs (e.g., 'Buscando artículos sobre...', 'Searching for papers about...') in the same language as the user's question")] = "Searching for academic papers...",
    user_id: Annotated[int, Field(description="The ID of the user who is performing the search. Look at the first developer prompt to get the user_id")] = 1,
    language1: Annotated[str, Field(description="The language of the search query. For example, 'es' for Spanish or 'en' for English")] = "en",
    language2: Annotated[str, Field(description="The language of the search query in English. For example, 'es' for Spanish or 'en' for English. This default value is 'en'")] = "en"
) -> dict:
    """
    This function searches for academic papers using Google Scholar API.
    It retrieves the title, authors, snippet, and link of the papers.

    Use this function EXCLUSIVELY for academic literature and scholarly information.
    NEVER use for general internet searches - use factual_web_query for that.

    Returns HTML display with search results.
    """
    try:
        return scholar_search(query, query_2, num_results, status, user_id, language1, language2)
    except Exception as e:
        return {"error": f"Scholar search failed: {str(e)}"}

@mcp.tool(
    name="write_document",
    description="Creates written documents of any length or complexity. Use for essays, objectives, reports, or any text content. NEVER use for visual content like graphs, charts, or diagrams. This function generates a well-structured academic document in markdown format.",
    tags={"document", "writing", "academic"},
    meta={"version": "1.0", "author": "NAIA-team"}
)
def create_document(
    query: Annotated[str, Field(description="The content to write about")],
    user_id: Annotated[int, Field(description="The ID of the user who is writing the document. Look at the first developer prompt to get the user_id")],
    status: Annotated[str, Field(description="A concise description of what is being written, using conjugated verbs (e.g., 'Redactando documento sobre...', 'Writing report about...') in the same language as the user's question")],
    document_type: Annotated[str, Field(description="The type of document to create. Options: 'academic' (default, formal academic paper), 'report' (technical report), 'essay' (thoughtful essay), 'brief' (concise document), 'creative' (creative writing), 'notes' (study notes), 'presentation' (content for slides). Choose based on user's request or writing purpose.")],
    use_internet: Annotated[bool, Field(description="Whether to search the internet for current information on the topic. Default is FALSE. Set to TRUE for comprehensive, up-to-date content when needed.")],
    use_rag: Annotated[bool, Field(description="Whether to search the user's personal documents for relevant information. Default is FALSE. Set to TRUE when the topic might relate to the user's uploaded files.")],
    context: Annotated[str, Field(description="The context or background information for the document, for default it is empty. Put here references provided by scholar_search or any info provided by the user in order to write the document")] = "",
    query_for_references: Annotated[str, Field(description="Query to search for academic references. Set to 'None' if the document doesn't require academic references (like simple objectives or basic texts). Only use real references found via scholar_search. Default is 'None'.")] = "None",
    num_results: Annotated[int, Field(description="The number of results to return. Default is 5, if the user does not specify a number of results, put 5 here, if the user specifies a number of results, put it here")] = 5,
    language_for_references: Annotated[str, Field(description="The language of the search query. For example, 'es' for Spanish or 'en' for English")] = "en",
    specific_documents: Annotated[list[str], Field(description="Optional list of specific document names to search in the user's library. Leave empty to search all documents.")] = []
) -> dict:
    """
    Creates comprehensive documents based on the user's topic with ability to leverage multiple
    information sources including internet search and user's own documents.

    This function generates high-quality content on the requested topic using multiple sources:
    - Academic references (if requested)
    - Internet search results (if use_internet=True)
    - User's uploaded documents (if use_rag=True)

    Returns PDF-ready markdown content.
    """
    try:
        return write_document(
            query=query,
            context=context,
            user_id=user_id,
            status=status,
            query_for_references=query_for_references,
            language_for_references=language_for_references,
            num_results=num_results,
            document_type=document_type,
            use_internet=use_internet,
            use_rag=use_rag,
            specific_documents=specific_documents
        )
    except Exception as e:
        return {"error": f"Document creation failed: {str(e)}"}

@mcp.tool(
    name="answer_from_user_rag",
    description="Searches ONLY within the user's uploaded PDF documents. Call this function whenever the user asks about content that might be in their documents. The document titles are visible to you - call this function when users mention topics similar to these titles.",
    tags={"rag", "documents", "search"},
    meta={"version": "1.0", "author": "NAIA-team"}
)
def search_user_documents(
    user_id: Annotated[int, Field(description="The ID of the user whose documents to search")],
    pregunta: Annotated[str, Field(description="The question to search for in the user's documents")],
    status: Annotated[str, Field(description="A concise description of what is being searched for, using conjugated verbs (e.g., 'Buscando en tus documentos...', 'Searching through your files for...') in the same language as the user's question")],
    k: Annotated[int, Field(description="The number of most relevant results to return (default: 3)")] = 3
) -> dict:
    """
    Query the information stored in the user's vector database and generate a response.

    CRITICAL FUNCTION - Use this to search through the user's uploaded PDF documents.
    This is the RAG (Retrieval Augmented Generation) function for user documents.

    Use when:
    - User asks what their documents contain or say about a topic
    - User wants information that might be in their documents
    - User mentions wanting to know about content in their files

    Returns relevant information extracted from user's documents.
    """
    try:
        return answer_from_user_rag(user_id, pregunta, k, status)
    except Exception as e:
        return {"error": f"RAG search failed: {str(e)}"}

@mcp.tool(
    name="factual_web_query",
    description="For real-time information from the internet. DO NOT use for finding academic papers (use scholar_search instead). This function is for current events, factual information, or getting specific content from web sources. Only use when other functions cannot provide the answer.",
    tags={"web", "search", "factual"},
    meta={"version": "1.0", "author": "NAIA-team"}
)
def search_web(
    query: Annotated[str, Field(description="Natural and concise search query optimized for web search engines like Google. RULES: 1) Write queries as a normal person would type them in Google. 2) Keep it between 3-8 words maximum. 3) Focus on the main topic/entity being searched. 4) Use natural language, not keyword stuffing. 5) Be specific but concise. EXAMPLES: CORRECT: 'Ingeniería Biomédica Universidad del Norte', 'programa Ingeniería Biomédica Uninorte'. WRONG: 'Universidad del Norte Ingeniería Biomédica programa descripción plan de estudios laboratorios Uninorte Barranquilla Colombia'")],
    user_id: Annotated[int, Field(description="The ID of the user who is performing the search. Look at the first developer prompt to get the user_id")],
    status: Annotated[str, Field(description="A concise description of the search task being performed, using conjugated verbs (e.g., 'Investigando en la web sobre...', 'Searching the web for...') in the same language as the user's question")] = "Searching the web..."
) -> dict:
    """
    Searches the internet for factual information using Google search.

    Use for real-time info, facts about specific entities, or knowledge beyond your training.
    Returns search results with HTML display on the left side and image results on the right side.

    CRITICAL: Default to this for any specific information request about entities, places, or events.
    """
    try:
        return factual_web_query(query, status, user_id)
    except Exception as e:
        return {"error": f"Web search failed: {str(e)}"}

@mcp.tool(
    name="create_graph",
    description="Creates academic graphs and visualizations. This function has BUILT-IN internet search capability - NEVER use factual_web_query before calling this function as it's redundant. Always use this function directly for any visualization request.",
    tags={"graph", "visualization", "data"},
    meta={"version": "1.0", "author": "NAIA-team"}
)
def generate_graph(
    user_query: Annotated[str, Field(description="The user's specific request for what type of graph to create and how it should look")],
    information_for_graph: Annotated[str, Field(description="The numerical data or structured information to visualize. Use real values only, never fabricate data points. When data is provided: Use exactly as given by user without modification. When data needs to be sourced: Specify a clear search query (e.g., 'Find Colombia's GDP 2015-2025 from World Bank') with needed time periods, regions, and preferred sources. All online data must be properly cited within the visualization itself.")],
    user_id: Annotated[int, Field(description="The ID of the user requesting the graph. Look at the first developer prompt to get the user_id")],
    status: Annotated[str, Field(description="A concise description of the graph creation task being performed, using conjugated verbs (e.g., 'Creando gráfico sobre...', 'Generating visualization of...') in the same language as the user's question")],
    internet_is_required: Annotated[bool, Field(description="Set to TRUE if data needs to be sourced from the internet. Set to FALSE if user provides the data directly. This parameter controls the function's own internal internet search - never use factual_web_query separately.")]
) -> dict:
    """
    Creates data visualizations with built-in internet search capability.

    Use for any request for visual representation of data (charts, graphs, visualizations).
    Has its own internet search - DO NOT use factual_web_query before this.

    Returns interactive HTML visualization.
    """
    try:
        return create_graph(user_query, information_for_graph, user_id, status, internet_is_required)
    except Exception as e:
        return {"error": f"Graph creation failed: {str(e)}"}

@mcp.tool(
    name="send_email",
    description="Send an email to the user. This function is used to send an email to the user with the information provided by the user.",
    tags={"email", "communication"},
    meta={"version": "1.0", "author": "NAIA-team"}
)
def send_user_email(
    to_email: Annotated[str, Field(description="The email of the user to send the email to. If the user wants to send the email to himself, put on this field the word 'myself' the function manages it internally. If the user wants to send the email to another person, put the email of that person here.")],
    subject: Annotated[str, Field(description="The subject of the email to send.")],
    body: Annotated[str, Field(description="The body of the email to send.")],
    user_id: Annotated[int, Field(description="The ID of the user requesting the email. Look at the first developer prompt to get the user_id")],
    status: Annotated[str, Field(description="A concise description of the email task being performed, using conjugated verbs (e.g., 'Enviando correo a...', 'Sending email about...') in the same language as the user's question")] = "Sending email..."
) -> dict:
    """
    Sends an email using Gmail SMTP server.
    Can automatically detect when to use the authenticated user's email address.

    Use when users request to send information via email.
    Always confirm with the user before sending emails, and verify recipient addresses.

    Returns success confirmation or error message.
    """
    try:
        return send_email(to_email, subject, body, status, user_id)
    except Exception as e:
        return {"error": f"Email sending failed: {str(e)}"}

@mcp.tool(
    name="get_current_news",
    description="Gets the latest news from a specific location with modern and attractive visualization.",
    tags={"news", "current", "location"},
    meta={"version": "1.0", "author": "NAIA-team"}
)
def fetch_current_news(
    location: Annotated[str, Field(description="The location to get news from (city, country, or region). Example: 'Barranquilla', 'Colombia', 'Atlántico'")],
    user_id: Annotated[int, Field(description="The ID of the user requesting the news. Look in the first developer prompt to get the user_id")],
    status: Annotated[str, Field(description="A concise description of the task being performed, using conjugated verbs (e.g., 'Getting news from...', 'Searching news about...') in the same language as the user's question")],
    query: Annotated[str, Field(description="Specific query to search for news. Example: 'latest news from Barranquilla', 'breaking news Colombia', 'recent news Atlántico', written in the same language as the user's question")],
    language: Annotated[str, Field(description="The language in which the news should be retrieved. Example: 'es' for Spanish, 'en' for English, always use the two letter ISO 639-1 code")]
) -> dict:
    """
    Obtiene las últimas noticias de una ubicación específica con visualización moderna.

    Use when users want current events, news updates, or information about recent developments.
    Returns modern HTML visualization with news articles.
    """
    try:
        return get_current_news(location, user_id, status, query, language)
    except Exception as e:
        return {"error": f"News fetch failed: {str(e)}"}

@mcp.tool(
    name="explain_naia_roles",
    description="Generate a carousel with explanations of all five NAIA roles. ALWAYS use this function when users ask about what roles NAIA has or ask for an explanation of NAIA's capabilities.",
    tags={"naia", "roles", "capabilities"},
    meta={"version": "1.0", "author": "NAIA-team"}
)
def show_naia_roles(
    user_id: Annotated[int, Field(description="The ID of the user requesting the role explanation. Look at the first developer prompt to get the user_id")],
    status: Annotated[str, Field(description="A concise description of the role explanation task being performed, using conjugated verbs (e.g., 'Explicando los roles de NAIA...', 'Showing NAIA's capabilities...') in the same language as the user's question")],
    auto_slide_interval: Annotated[int, Field(description="The interval in milliseconds for auto-advancing the carousel slides. Default is 3000ms (3 seconds).")] = 3000
) -> dict:
    """
    Generates a visual carousel with explanations of all NAIA roles.

    Use when users ask about NAIA's roles, capabilities, or what NAIA can do.
    Returns interactive HTML carousel with role descriptions.
    """
    try:
        return explain_naia_roles(user_id, status, auto_slide_interval)
    except Exception as e:
        return {"error": f"Role explanation failed: {str(e)}"}

@mcp.tool(
    name="deep_content_analysis",
    description="Performs an in-depth search and information retrieval on specific topics. Use for comprehensive research that requires deep analysis and synthesis of multiple sources.",
    tags={"research", "analysis", "deep"},
    meta={"version": "1.0", "author": "NAIA-team"}
)
def deep_analysis(
    query: Annotated[str, Field(description="The required search query")],
    user_id: Annotated[int, Field(description="User ID for status updates")],
    status: Annotated[str, Field(description="Status message")] = "Performing deep content analysis...",
    url: Annotated[str | None, Field(description="Optional URL to focus the search")] = None
) -> dict:
    """
    Performs an in-depth search and information retrieval on specific topics.

    Use for complex research needs requiring synthesis and comprehensive analysis.
    Can optionally focus on a specific URL for targeted research.

    Returns comprehensive research results with detailed analysis.
    """
    try:
        return deep_content_analysis_for_specific_information(query, url, user_id, status)
    except Exception as e:
        return {"error": f"Deep analysis failed: {str(e)}"}

@mcp.resource("file://researcher/info")
def researcher_info():
    """Basic information about the NAIA Researcher role and available services."""
    return {
        "role": "NAIA Researcher",
        "description": "Advanced academic research assistant specializing in scholarly work, literature searches, document creation, and comprehensive analysis",
        "available_functions": [
            "scholar_search - Academic paper and scholarly information search",
            "write_document - Comprehensive document creation",
            "answer_from_user_rag - Search user's uploaded documents",
            "factual_web_query - Real-time internet information search",
            "create_graph - Data visualization creation",
            "send_email - Email composition and sending",
            "get_current_news - Current news retrieval",
            "explain_naia_roles - NAIA roles explanation",
            "deep_content_analysis - Comprehensive research analysis"
        ],
        "specializations": [
            "Literature Reviews",
            "Data Analysis",
            "Document Creation",
            "Research Methodology",
            "Citation Management"
        ]
    }

@mcp.custom_route("/", methods=["GET"])
async def root(request):
    return JSONResponse({
        "name": "NAIA Researcher MCP Server",
        "version": "2.0.0",
        "description": "Complete researcher MCP server with all 9 functions",
        "tools": [
            "scholar_search",
            "write_document",
            "answer_from_user_rag",
            "factual_web_query",
            "create_graph",
            "send_email",
            "get_current_news",
            "explain_naia_roles",
            "deep_content_analysis"
        ],
        "status": "All functions operational"
    })

@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    return JSONResponse({"status": "ok", "server": "NAIA Researcher MCP"})

# REST API Endpoints (opcional - para facilidad de uso)
@mcp.custom_route("/api/tools", methods=["GET"])
async def list_tools_endpoint(request):
    """Lista todas las herramientas disponibles en formato REST"""
    tools = [
        {"name": "scholar_search", "description": "Search academic papers and scholarly information", "endpoint": "/api/scholar"},
        {"name": "write_document", "description": "Create comprehensive documents", "endpoint": "/api/write"},
        {"name": "answer_from_user_rag", "description": "Search user's uploaded documents", "endpoint": "/api/rag"},
        {"name": "factual_web_query", "description": "Search internet for factual information", "endpoint": "/api/web"},
        {"name": "create_graph", "description": "Create data visualizations", "endpoint": "/api/graph"},
        {"name": "send_email", "description": "Send emails", "endpoint": "/api/email"},
        {"name": "get_current_news", "description": "Get current news from location", "endpoint": "/api/news"},
        {"name": "explain_naia_roles", "description": "Show NAIA roles explanation", "endpoint": "/api/roles"},
        {"name": "deep_content_analysis", "description": "Perform deep research analysis", "endpoint": "/api/deep"}
    ]
    return JSONResponse({"tools": tools, "mcp_endpoint": "/mcp/v1", "protocol": "MCP + REST"})

if __name__ == "__main__":
    print("Starting NAIA Researcher MCP Server...")
    print(f"Project root: {project_root}")
    print()
    print("MCP Tools (9 functions):")
    print("   1. scholar_search - Academic paper search")
    print("   2. write_document - Document creation")
    print("   3. answer_from_user_rag - User document search (RAG)")
    print("   4. factual_web_query - Web search")
    print("   5. create_graph - Data visualization")
    print("   6. send_email - Email sending")
    print("   7. get_current_news - News retrieval")
    print("   8. explain_naia_roles - NAIA roles explanation")
    print("   9. deep_content_analysis - Deep research analysis")
    print()
    print("REST Endpoints:")
    print("   - GET  /api/tools (list all tools)")
    print("   - GET  /health (health check)")
    print()
    print("MCP Protocol: http://localhost:9000/mcp/v1")

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=9000
    )
