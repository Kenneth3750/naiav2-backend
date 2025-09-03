import os
from fastmcp import FastMCP, Client
from dotenv import load_dotenv
from openai import OpenAI
from serpapi import GoogleSearch
from typing import List, Dict
import tempfile
import json
import smtplib
from email.mime.text import MIMEText
import requests
import datetime
from datetime import timedelta, timezone
from starlette.responses import JSONResponse
# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP(
    name="NAIAResearcherMCPServer"
)

# Environment variables
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
openai_api_key = os.getenv("open_ai")

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

def escape(text):
    """Escape HTML special characters"""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")

@mcp.tool(
    name="scholar_search",
    description="EXCLUSIVELY for finding academic articles and research papers. Never use for general internet searches. Call this function any time the user wants academic references, citations, or scholarly information.",
    tags={"academic", "research", "scholar"},
    meta={"version": "1.0", "author": "NAIA-team"}
)
def scholar_search(query: str = "", query_2: str = "", num_results: int = 3, status: str = "", user_id: int = 0, language1: str = "", language2: str = "en"):
    """
    This function searches for academic papers using Google Scholar API.
    It retrieves the title, authors, snippet, and link of the papers.
    """
    load_dotenv()
    api_key = os.getenv("SERPAPI_KEY")

    if not api_key:
        print("Error: SERPAPI_KEY not found in .env file")
        return {"error": "SERPAPI_KEY not found"}

    # Configure search parameters
    params_1 = {
        "engine": "google_scholar",
        "q": query,
        "api_key": api_key,
        "num": num_results,
        "hl": language1,
    }
    
    params_2 = {
        "engine": "google_scholar",
        "q": query_2,
        "api_key": api_key, 
        "num": num_results,
        "hl": language2,
    }

    try:
        # Combined search result object
        combined_results = {"query": f"{query} & {query_2}", "results": []}
        
        # First query
        if query:
            search1 = GoogleSearch(params_1)
            results1 = search1.get_dict()
            
            print(f"\n=== Search Results for: {query} ===\n")
            for i, result in enumerate(results1.get("organic_results", []), 1):
                research_information = {
                    "result_number": i,
                    "query_source": "query_1",
                    "title": result.get("title", "N/A"),
                    "authors": [
                        author.get("name", "N/A")
                        for author in result.get("publication_info", {})
                        .get("authors", [])
                    ],
                    "snippet": result.get("snippet", "N/A"),
                    "link": result.get("link", "N/A"),
                }
                combined_results["results"].append(research_information)
                print(f"Result {i} from query 1")
                print(f"Title: {result.get('title', 'N/A')}")
        
        if query_2:
            search2 = GoogleSearch(params_2)
            results2 = search2.get_dict()
            
            print(f"\n=== Search Results for: {query_2} ===\n")
            offset = len(combined_results["results"])
            for i, result in enumerate(results2.get("organic_results", []), 1):
                research_information = {
                    "result_number": i + offset,
                    "query_source": "query_2",
                    "title": result.get("title", "N/A"),
                    "authors": [
                        author.get("name", "N/A")
                        for author in result.get("publication_info", {})
                        .get("authors", [])
                    ],
                    "snippet": result.get("snippet", "N/A"),
                    "link": result.get("link", "N/A"),
                }
                combined_results["results"].append(research_information)
                print(f"Result {i} from query 2")
                print(f"Title: {result.get('title', 'N/A')}")
                
        return convert_to_html(combined_results)

    except (ValueError, TypeError, KeyError) as e:
        print(f"Error during search: {str(e)}")
        raise ValueError(f"Error during search: {str(e)}") from e
    except ConnectionError as e:
        print(f"Connection error during search: {str(e)}")
        error_msg = f"Connection error during search: {str(e)}"
        raise ConnectionError(error_msg) from e

def convert_to_html(search_result):
    """Convert search results to HTML format"""
    html = f"""
    <div class="search-results">
        <h2>Search Results for: {search_result['query']}</h2>
        <div class="results-container">
    """

    for result in search_result["results"]:
        html += f"""
            <div class="result-card">
                <h3>Result {result['result_number']}</h3>
                <h4 class="title">{result['title']}</h4>
                <p class="authors"><strong>Authors:</strong> {', '.join(result['authors'])}</p>
                <p class="snippet">{result['snippet']}</p>
                <a href="{result['link']}" class="read-more" target="_blank">Read More</a>
            </div>
        """

    html += """
        </div>
    </div>
    <style>
        .search-results {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .result-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .title {
            color: #0B3954;
            margin: 10px 0;
        }
        .authors {
            color: #006621;
        }
        .read-more {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            background-color: #1f2937;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 6px;
            border: none;
            margin-top: 12px;
            font-family: inherit;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .read-more:hover {
            background-color: #111827;
        }
        .read-more:active {
            background-color: #374151
        }
    </style>
    """
    return {"display": html}

@mcp.tool(
    name="factual_web_query",
    description="For real-time information from the internet. DO NOT use for finding academic papers (use scholar_search instead). This function is for current events, factual information, or getting specific content from web sources. Only use when other functions cannot provide the answer.",
    tags={"web", "search", "factual"},
    meta={"version": "1.0", "author": "NAIA-team"}
)
def factual_web_query(query: str, status: str = "", user_id: int = 0):
    """
    This function searches the internet for information using the SerpAPI.
    """
    try:
        api_key = os.getenv("SERPAPI_KEY")
        if not api_key:
            raise ValueError("SERPAPI_KEY not found in .env file")
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "output": "json",
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])
        
        html_output = f"""
        <div class="naia-search-container">
            <h2 class="search-title">Resultados de búsqueda</h2>
            <div class="search-query-box">
              <span class="search-icon">🔍</span>
              <span class="query-text">{query}</span>
            </div>
            <div class="results-container">
        """
        
        for i, result in enumerate(organic_results[:10], 1):
            title = escape(result.get("title", "No Title Available"))
            link = result.get("link", "#")
            snippet = escape(result.get("snippet", "No description available."))
            
            html_output += f"""
            <div class="result-card">
                <div class="result-number">{i}</div>
                <div class="result-content">
                  <a href="{link}" class="result-title" target="_blank">{title}</a>
                  <div class="result-url">{link}</div>
                  <p class="result-snippet">{snippet}</p>
                </div>
            </div>
            """
        
        html_output += """
            </div>
        </div>
        <style>
            .naia-search-container {
              font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
              width: 100%;
              max-width: 100%;
              margin: 0;
              padding: 12px;
              background: rgba(255, 255, 255, 0.7);
              border-radius: 10px;
              box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
            }
            .search-title {
              color: #0c2461;
              font-size: 20px;
              margin-bottom: 12px;
              text-align: center;
              font-weight: 600;
            }
            .search-query-box {
              background: rgba(240, 249, 255, 0.8);
              padding: 10px 12px;
              border-radius: 8px;
              margin-bottom: 16px;
              display: flex;
              align-items: center;
              border-left: 3px solid #0284c7;
            }
            .search-icon {
              font-size: 16px;
              margin-right: 10px;
            }
            .query-text {
              font-size: 14px;
              color: #333;
              font-weight: 500;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            }
            .results-container {
              display: flex;
              flex-direction: column;
              gap: 12px;
            }
            .result-card {
              display: flex;
              background: white;
              border-radius: 8px;
              padding: 12px;
              box-shadow: 0 2px 8px rgba(0,0,0,0.03);
              transition: transform 0.2s, box-shadow 0.2s;
              position: relative;
              overflow: hidden;
              border-left: 2px solid transparent;
            }
            .result-card:hover {
              transform: translateY(-2px);
              box-shadow: 0 4px 12px rgba(0,0,0,0.08);
              border-left-color: #0284c7;
            }
            .result-number {
              background: #0c2461;
              color: white;
              width: 24px;
              height: 24px;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              font-weight: bold;
              margin-right: 12px;
              flex-shrink: 0;
              font-size: 12px;
            }
            .result-content {
              flex-grow: 1;
              min-width: 0;
            }
            .result-title {
              font-size: 15px;
              color: #0c2461;
              text-decoration: none;
              font-weight: 600;
              margin-bottom: 4px;
              display: block;
              line-height: 1.3;
              overflow: hidden;
              text-overflow: ellipsis;
              display: -webkit-box;
              -webkit-line-clamp: 2;
              -webkit-box-orient: vertical;
            }
            .result-title:hover {
              text-decoration: underline;
            }
            .result-url {
              font-size: 12px;
              color: #0284c7;
              margin-bottom: 6px;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
              max-width: 100%;
            }
            .result-snippet {
              font-size: 13px;
              color: #555;
              line-height: 1.4;
              margin: 0;
              overflow: hidden;
              text-overflow: ellipsis;
              display: -webkit-box;
              -webkit-line-clamp: 3;
              -webkit-box-orient: vertical;
            }
        </style>
        """
        
        # Generate image carousel
        image_params = {
            "engine": "google_images",
            "q": query,
            "api_key": api_key,
        }

        search_results = GoogleSearch(image_params)
        image_html = generate_image_carousel_html(search_results.get_dict().get("images_results", []))
        
        return {"search_results": html_output, "graph": image_html}
    except Exception as e:
        print(f"Error during search: {str(e)}")
        return {"error": str(e)}

def generate_image_carousel_html(search_results, max_images=4):
    """Generate HTML for image carousel from SerpAPI search results."""
    results = search_results[:max_images]
    
    if not results:
        return "<div class='no-results'>No se encontraron imágenes para esta búsqueda.</div>"
    
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Resultados de Búsqueda de Imágenes</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto; }
            .carousel-container { 
                width: 100%; max-width: 800px; margin: 0 auto; padding: 20px;
                background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }
            .carousel-title { font-size: 1.25rem; font-weight: 600; margin-bottom: 16px; }
            .carousel { position: relative; overflow: hidden; border-radius: 8px; }
            .carousel-inner { display: flex; transition: transform 0.5s ease; }
            .carousel-item { min-width: 100%; display: flex; flex-direction: column; align-items: center; }
            .carousel-image { width: 100%; max-height: 400px; object-fit: contain; border-radius: 8px; }
            .carousel-caption { padding: 12px; text-align: center; font-size: 0.875rem; color: #64748b; }
        </style>
    </head>
    <body>
        <div class="carousel-container">
            <h2 class="carousel-title">Resultados de imágenes</h2>
            <div class="carousel">
                <div class="carousel-inner">
    """
    
    for i, image in enumerate(results):
        title = image.get("title", "").replace('"', "&quot;").replace("'", "&#39;")
        source = image.get("source_name", image.get("source", ""))
        image_url = image.get("original", image.get("thumbnail", ""))
        
        html += f"""
            <div class="carousel-item">
                <img src="{image_url}" alt="{title}" class="carousel-image" />
                <div class="carousel-caption">{title}<br><small>Fuente: {source}</small></div>
            </div>
        """
    
    html += """
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

@mcp.tool(
    name="send_email",
    description="Send an email to the user. This function is used to send an email to the user with the information provided by the user.",
    tags={"email", "communication"},
    meta={"version": "1.0", "author": "NAIA-team"}
)
def send_email(to_email: str, subject: str, body: str, status: str = "", user_id: int = 0):
    """
    Sends an email using Gmail SMTP server.
    Can automatically detect when to use the authenticated user's email address.
    """
    if not subject or not body:
        return {"error": "Subject and body are required"}
    
    # Basic email format validation
    if '@' not in to_email or '.' not in to_email:
        return {"error": "Invalid email format"}
    
    # Add footer with user information for traceability
    footer = "\n\n" + "─" * 50 + "\n"
    footer += "Este email fue enviado a través de la plataforma NAIA\n"
    footer += "Universidad del Norte - NAIA Assistant\n"
    footer += "Para soporte técnico, contacta: naia@uninorte.edu.co"
    
    final_body = body + footer
    
    try:
        if not all([DEFAULT_FROM_EMAIL, EMAIL_HOST_PASSWORD]):
            raise ValueError("DEFAULT_FROM_EMAIL and EMAIL_HOST_PASSWORD must be set in the environment variables")
        
        msg = MIMEText(final_body)
        msg["Subject"] = subject
        msg["From"] = f"NAIA Uninorte <{DEFAULT_FROM_EMAIL}>"
        msg["To"] = to_email
        msg["Reply-To"] = "naia@uninorte.edu.co"

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            print("Iniciando conexión con el servidor de correo")
            server.login(DEFAULT_FROM_EMAIL, EMAIL_HOST_PASSWORD)
            print("Login exitoso")
            server.send_message(msg)
            print(f"Email enviado a {to_email}")
        
        return {"success": 'Email enviado correctamente'}
    
    except smtplib.SMTPAuthenticationError as e:
        error_msg = "Error de autenticación del correo"
        print(f"{error_msg}: {str(e)}")
        return {"error": error_msg}
    except smtplib.SMTPException as e:
        error_msg = "Error en el servidor de correo"
        print(f"{error_msg}: {str(e)}")
        return {"error": error_msg}
    except Exception as e:
        print(f"Error al enviar el email: {str(e)}")
        return {"error": str(e)}

@mcp.tool(
    name="get_current_news",
    description="Gets the latest news from a specific location with modern and attractive visualization.",
    tags={"news", "current", "location"},
    meta={"version": "1.0", "author": "NAIA-team"}
)
def get_current_news(location: str, user_id: int, status: str, query: str, language: str):
    """
    Obtiene las últimas noticias de una ubicación específica con visualización moderna y responsive.
    """
    try:
        params = {
            "engine": "google_news",
            "q": f"{query} {location}",
            "hl": language, 
            "api_key": os.getenv("SERPAPI_KEY")
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        news_results = results.get("news_results", [])
        
        if not news_results:
            return {"error": "No se encontraron noticias para esta ubicación"}
        
        html_content = f"""
<div class="news-container">
    <div class="header">
        <h1>📰 Últimas Noticias</h1>
        <p>Mantente informado sobre {escape(location)}</p>
    </div>
    
    <div class="stats-bar">
        <div class="stat-item">
            <div class="stat-number">{len(news_results)}</div>
            <div class="stat-label">Noticias Encontradas</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">🔥</div>
            <div class="stat-label">Actualizadas</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">📍</div>
            <div class="stat-label">{escape(location)}</div>
        </div>
    </div>
    
    <div class="news-grid">
        """
        
        for i, article in enumerate(news_results[:12]):
            title = escape(article.get("title", "Sin título"))
            snippet = escape(article.get("snippet", "Sin descripción disponible"))
            link = article.get("link", "#")
            source = escape(article.get("source", {}).get("name", "Fuente desconocida"))
            date = escape(article.get("date", "Fecha no disponible"))
            thumbnail = article.get("thumbnail")

            is_breaking = i < 3
            
            if thumbnail:
                img_html = f'<img src="{thumbnail}" alt="{title}" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\'">'
                placeholder_style = "display: none"
            else:
                img_html = ""
                placeholder_style = "display: flex"
            
            breaking_badge = '<div class="breaking-badge">🔥 DESTACADA</div>' if is_breaking else ''
            
            html_content += f"""
        <div class="news-card">
            <div class="news-image">
                {img_html}
                <div class="placeholder" style="{placeholder_style}">📰</div>
                {breaking_badge}
            </div>
            <div class="news-content">
                <h3 class="news-title">{title}</h3>
                <div class="news-meta">
                    <span class="news-source">{source}</span>
                    <span class="news-date">🕐 {date}</span>
                </div>
                <p class="news-snippet">{snippet}</p>
                <a href="{link}" target="_blank" class="news-link">
                    Leer más <span>→</span>
                </a>
            </div>
        </div>
            """
        
        html_content += """
    </div>
</div>
<style>
    .news-container {
        max-width: 100%;
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 16px;
        box-sizing: border-box;
        color: #1e293b;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
    }
    
    .header {
        text-align: center;
        color: white;
        margin-bottom: 16px;
    }
    
    .header h1 {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 8px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .header p {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    .stats-bar {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        text-align: center;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .stat-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    
    .stat-number {
        font-size: 1.5rem;
        font-weight: 700;
        background: linear-gradient(45deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stat-label {
        color: #718096;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .news-grid {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    
    .news-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .news-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }
    
    .news-image {
        width: 100%;
        height: 160px;
        background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }
    
    .news-image img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    .news-image .placeholder {
        font-size: 2.5rem;
        color: white;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .news-content {
        padding: 20px;
    }
    
    .news-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2d3748;
        margin-bottom: 12px;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    .news-meta {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 12px;
        font-size: 0.85rem;
        color: #718096;
    }
    
    .news-source {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.75rem;
        align-self: flex-start;
    }
    
    .news-date {
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    .news-snippet {
        color: #4a5568;
        line-height: 1.5;
        margin-bottom: 16px;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        font-size: 0.9rem;
    }
    
    .news-link {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: #667eea;
        text-decoration: none;
        font-weight: 600;
        transition: all 0.3s ease;
        padding: 8px 16px;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 20px;
        border: 2px solid transparent;
        font-size: 0.9rem;
    }
    
    .news-link:hover {
        background: #667eea;
        color: white;
        transform: translateX(3px);
    }
    
    .breaking-badge {
        position: absolute;
        top: 12px;
        right: 12px;
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 700;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
</style>
        """
        
        return {"display": html_content}
        
    except Exception as e:
        print(f"Error obteniendo noticias: {str(e)}")
        return {"error": str(e)}
    

@mcp.custom_route("/", methods=["GET"])
async def root(request):
    return JSONResponse({
        "name": "NAIA Researcher MCP Server",
        "version": "1.0.0",
        "tools": ["scholar_search", "factual_web_query", "send_email", "get_current_news"]
    })

@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    return JSONResponse({"status": "ok", "server": "NAIA Researcher MCP"})

@mcp.tool
def say_hello(name: str):
    return f"Hello, {name}!"

if __name__ == "__main__":
    import uvicorn
    app = mcp.http_app()
    uvicorn.run(app, host="0.0.0.0", port=9000)