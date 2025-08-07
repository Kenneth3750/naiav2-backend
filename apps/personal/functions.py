from dotenv import load_dotenv
import os
from typing import Dict
from apps.status.services import set_status
from serpapi import GoogleSearch
from html import escape
from apps.users.services import UserService
import requests 
import json
import re
load_dotenv()

def get_current_news(location: str, user_id: int, status: str, query: str, language: str) -> Dict:
    """
    Obtiene las últimas noticias de una ubicación específica con visualización moderna y responsive.
    
    Args:
        location (str): La ubicación para obtener noticias
        user_id (int): ID del usuario
        status (str): Mensaje de estado
        
    Returns:
        dict: Diccionario con HTML visual de noticias responsive
    """
    try:
        set_status(user_id, status, 3) 
        
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
        
        for i, article in enumerate(news_results[:12]):  # Limitar a 12 noticias
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
                <div class="placeholder" style="{placeholder_style}">
                    📰
                </div>
                {breaking_badge}
            </div>
            <div class="news-content">
                <h3 class="news-title">{title}</h3>
                <div class="news-meta">
                    <span class="news-source">{source}</span>
                    <span class="news-date">
                        🕐 {date}
                    </span>
                </div>
                <p class="news-snippet">{snippet}</p>
                <a href="{link}" target="_blank" class="news-link">
                    Leer más
                    <span>→</span>
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
    
    /* Media Queries para pantallas más grandes */
    @media (min-width: 768px) {
        .news-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header h1 {
            font-size: 2.2rem;
        }
        
        .header p {
            font-size: 1.2rem;
        }
        
        .stats-bar {
            flex-direction: row;
            justify-content: space-around;
        }
        
        .stat-number {
            font-size: 2rem;
        }
        
        .news-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .news-image {
            height: 200px;
        }
        
        .news-title {
            font-size: 1.2rem;
        }
        
        .news-meta {
            flex-direction: row;
            align-items: center;
            gap: 12px;
        }
    }
    
    @media (min-width: 1024px) {
        .news-grid {
            grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
            gap: 25px;
        }
    }
    
    /* Optimización para landscape en móviles */
    @media (orientation: landscape) and (max-height: 600px) {
        .header h1 {
            font-size: 1.5rem;
            margin-bottom: 4px;
        }
        
        .header p {
            font-size: 0.9rem;
        }
        
        .stats-bar {
            padding: 12px;
            flex-direction: row;
            justify-content: space-around;
        }
        
        .news-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
        }
        
        .news-image {
            height: 120px;
        }
    }
</style>
        """
        
        return {"display": html_content}
        
    except Exception as e:
        print(f"Error obteniendo noticias: {str(e)}")
        return {"error": str(e)}


def get_weather(location: str, user_id: int, status: str) -> Dict:
    """
    Obtiene información del clima con una visualización moderna, responsive y atractiva.
    
    Args:
        location (str): La ubicación para obtener el clima
        user_id (int): ID del usuario
        status (str): Mensaje de estado
        
    Returns:
        dict: Diccionario con HTML visual del clima responsive
    """
    try:
        set_status(user_id, status, 3)  # 3 = role_id del asistente personal
        
        params = {
            "q": f"clima en {location}",
            "hl": "es",
            "gl": "co",
            "api_key": os.getenv("SERPAPI_KEY")
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        weather_data = results.get("answer_box", {})
        
        if not weather_data:
            return {"error": "No se pudo obtener información del clima"}
        
        # Extraer datos del clima
        temperature = weather_data.get("temperature", "N/A")
        weather_condition = weather_data.get("weather", "N/A")
        precipitation = weather_data.get("precipitation", "0%")
        humidity = weather_data.get("humidity", "N/A")
        wind = weather_data.get("wind", "N/A")
        date = weather_data.get("date", "N/A")
        
        # Determinar ícono del clima
        weather_icon = "☀️"
        if "lluvia" in weather_condition.lower() or "rain" in weather_condition.lower():
            weather_icon = "🌧️"
        elif "nublado" in weather_condition.lower() or "cloud" in weather_condition.lower():
            weather_icon = "☁️"
        elif "sol" in weather_condition.lower() or "sun" in weather_condition.lower():
            weather_icon = "☀️"
        elif "tormenta" in weather_condition.lower() or "storm" in weather_condition.lower():
            weather_icon = "⛈️"
        
        html_content = f"""
<div class="weather-container">
    <div class="weather-content">
        <div class="location-header">
            <h1 class="location-name">📍 {escape(location)}</h1>
            <p class="update-time">Actualizado: {escape(date)}</p>
        </div>
        
        <div class="main-weather">
            <div class="weather-icon">{weather_icon}</div>
            <div class="temperature">{escape(str(temperature))}</div>
            <div class="weather-condition">{escape(weather_condition)}</div>
        </div>
        
        <div class="weather-details">
            <div class="detail-card">
                <div class="detail-icon">💧</div>
                <div class="detail-label">Precipitación</div>
                <div class="detail-value">{escape(precipitation)}</div>
            </div>
            
            <div class="detail-card">
                <div class="detail-icon">💨</div>
                <div class="detail-label">Humedad</div>
                <div class="detail-value">{escape(humidity)}</div>
            </div>
            
            <div class="detail-card">
                <div class="detail-icon">🌪️</div>
                <div class="detail-label">Viento</div>
                <div class="detail-value">{escape(wind)}</div>
            </div>
            
            <div class="detail-card">
                <div class="detail-icon">🌡️</div>
                <div class="detail-label">Sensación</div>
                <div class="detail-value">Agradable</div>
            </div>
        </div>
        
        <div class="weather-advice">
            <div class="advice-icon">💡</div>
            <div class="advice-text">
                {'¡Perfecto para actividades al aire libre!' if 'sol' in weather_condition.lower() else 
                 '¡No olvides el paraguas!' if 'lluvia' in weather_condition.lower() else 
                 '¡Ideal para una caminata!'}
            </div>
        </div>
    </div>
</div>
<style>
    .weather-container {{
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 50%, #00b894 100%);
        border-radius: 24px;
        padding: 4px;
        max-width: 100%;
        width: 100%;
        text-align: center;
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.3);
        position: relative;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        gap: 20px;
        box-sizing: border-box;
        margin: 0 auto;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
    }}
    
    .weather-container::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        animation: shine 3s infinite;
    }}
    
    @keyframes shine {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    .weather-content {{
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 20px;
        box-sizing: border-box;
    }}
    
    .location-header {{
        margin-bottom: 16px;
    }}
    
    .location-name {{
        font-size: 1.5rem;
        font-weight: 700;
        color: #2d3748;
        margin-bottom: 5px;
    }}
    
    .update-time {{
        color: #718096;
        font-size: 0.85rem;
    }}
    
    .main-weather {{
        margin-bottom: 20px;
    }}
    
    .weather-icon {{
        font-size: 4rem;
        margin-bottom: 16px;
        animation: float 3s ease-in-out infinite;
    }}
    
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-8px); }}
    }}
    
    .temperature {{
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(45deg, #74b9ff, #0984e3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }}
    
    .weather-condition {{
        font-size: 1.1rem;
        color: #4a5568;
        font-weight: 500;
        text-transform: capitalize;
    }}
    
    .weather-details {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
    }}
    
    .detail-card {{
        background: linear-gradient(135deg, rgba(116, 185, 255, 0.1), rgba(0, 184, 148, 0.1));
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(116, 185, 255, 0.2);
        transition: all 0.3s ease;
    }}
    
    .detail-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }}
    
    .detail-icon {{
        font-size: 1.5rem;
        margin-bottom: 8px;
    }}
    
    .detail-label {{
        color: #718096;
        font-size: 0.8rem;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .detail-value {{
        color: #2d3748;
        font-size: 1rem;
        font-weight: 600;
    }}
    
    .weather-advice {{
        background: linear-gradient(135deg, #ffeaa7, #fdcb6e);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(253, 203, 110, 0.3);
    }}
    
    .advice-icon {{
        font-size: 1.2rem;
        margin-bottom: 8px;
    }}
    
    .advice-text {{
        color: #8b4513;
        font-weight: 500;
        line-height: 1.4;
        font-size: 0.9rem;
    }}
    
    /* Media Queries para pantallas más grandes */
    @media (min-width: 768px) {{
        .weather-container {{
            max-width: 500px;
            padding: 6px;
        }}
        
        .weather-content {{
            padding: 28px;
            gap: 24px;
        }}
        
        .location-name {{
            font-size: 1.8rem;
        }}
        
        .weather-icon {{
            font-size: 5rem;
            margin-bottom: 20px;
        }}
        
        .temperature {{
            font-size: 4rem;
            margin-bottom: 10px;
        }}
        
        .weather-condition {{
            font-size: 1.3rem;
        }}
        
        .weather-details {{
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }}
        
        .detail-card {{
            padding: 20px;
        }}
        
        .detail-icon {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        
        .detail-value {{
            font-size: 1.2rem;
        }}
        
        .weather-advice {{
            padding: 20px;
        }}
        
        .advice-text {{
            font-size: 1rem;
        }}
    }}
    
    /* Optimización para landscape en móviles */
    @media (orientation: landscape) and (max-height: 600px) {{
        .weather-container {{
            padding: 3px;
        }}
        
        .weather-content {{
            padding: 14px;
            gap: 10px;
        }}
        
        .location-name {{
            font-size: 1.3rem;
        }}
        
        .weather-icon {{
            font-size: 3rem;
            margin-bottom: 8px;
        }}
        
        .temperature {{
            font-size: 2.5rem;
            margin-bottom: 6px;
        }}
        
        .weather-condition {{
            font-size: 1rem;
        }}
        
        .weather-details {{
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
        }}
        
        .detail-card {{
            padding: 12px;
        }}
        
        .detail-icon {{
            font-size: 1.2rem;
            margin-bottom: 4px;
        }}
        
        .detail-label {{
            font-size: 0.7rem;
        }}
        
        .detail-value {{
            font-size: 0.9rem;
        }}
        
        .weather-advice {{
            padding: 12px;
        }}
    }}
</style>
        """
        
        return {"display": html_content}
        
    except Exception as e:
        print(f"Error obteniendo clima: {str(e)}")
        return {"error": str(e)}
    

def get_user_email_from_graph(user_id: int) -> dict:
    """
    Gets the authenticated user's email address using Microsoft Graph API.
    
    Args:
        user_id (int): The ID of the user
        
    Returns:
        dict: Contains either the email address or error information
    """
    try:
        # Get user's Microsoft Graph token
        user_service = UserService()
        access_token = user_service.get_user_token(user_id)
        
        if not access_token:
            return {"error": "No access token found for user. Please authenticate with Microsoft first."}
        
        # Microsoft Graph API endpoint for user profile
        graph_url = "https://graph.microsoft.com/v1.0/me"
        
        # Set up headers with authentication
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Make the API call to get user profile
        response = requests.get(graph_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            user_data = response.json()
            email = user_data.get('mail') or user_data.get('userPrincipalName')
            
            if email:
                return {"email": email}
            else:
                return {"error": "No email address found in user profile"}
                
        elif response.status_code == 401:
            return {"error": "Authentication failed. Please refresh your Microsoft login."}
        elif response.status_code == 403:
            return {"error": "Insufficient permissions to read user profile."}
        else:
            return {"error": f"Failed to get user email: {response.text}"}
            
    except requests.exceptions.Timeout:
        return {"error": "Request timeout while getting user email"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error while getting user email: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error while getting user email: {str(e)}"}

def send_email_on_behalf_of_user(to_email_or_name: str, subject: str, body: str, user_id: int, status: str = "Enviando correo...") -> dict:
    """
    Sends an email on behalf of the user using Microsoft Graph API with their OAuth token.
    Can accept either an email address, a contact name, or user indicators like "mi correo".
    If user indicators are detected, automatically uses the authenticated user's email.
    If a name is provided and multiple contacts are found, returns the options for the user to choose.
    
    Args:
        to_email_or_name (str): The recipient's email address, name, or user indicators like "mi correo"
        subject (str): The email subject
        body (str): The email body content
        user_id (int): The ID of the user sending the email
        status (str): Status message for tracking. Defaults to "Enviando correo..."
        
    Returns:
        dict: A dictionary containing either success message, contact options, or error details
    """
    # Validate required fields
    if not subject or not body:
        return {"error": "Subject and body are required"}
        
    if not user_id:
        return {"error": "User ID is required"}
    
    try:
        # Set status for tracking
        if user_id:
            set_status(user_id, status, 3)  # role_id 3 for Personal Assistant
        
        # Check if we need to get the user's email automatically
        user_email_indicators = [
            "mi correo", "my email", "mi email", "my mail", 
            "mi dirección", "my address", "mío", "mine", "me", "yo", "I", "myself"
        ]
        
        recipient_input = to_email_or_name.strip() if to_email_or_name else ""
        
        # Determine if we need to fetch user's email
        should_get_user_email = (
            not recipient_input or 
            recipient_input.lower() in user_email_indicators or
            (recipient_input and '@' not in recipient_input and '.' not in recipient_input and len(recipient_input.split()) <= 2 and any(indicator in recipient_input.lower() for indicator in user_email_indicators))
        )
        
        if should_get_user_email:
            # Get user's email from Microsoft Graph
            email_result = get_user_email_from_graph(user_id)
            
            if "error" in email_result:
                return email_result
                
            user_email = email_result["email"]
            print(f"Using user's email address: {user_email}")
            return _send_email_direct(user_email, subject, body, user_id, "yourself")
        
        # Validate recipient input
        if not recipient_input:
            return {"error": "Recipient is required"}
        
        # Check if input is already an email address
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, recipient_input):
            # Direct email - send immediately
            return _send_email_direct(recipient_input, subject, body, user_id)
        
        # Input is a name - search for contacts
        print(f"Searching contacts for name: {recipient_input}")
        search_result = search_contacts_by_name(recipient_input, user_id, "Buscando contacto...")
        
        if "error" in search_result:
            return search_result
        
        contacts = search_result.get("contacts", [])
        
        if len(contacts) == 0:
            return {
                "error": f"No se encontraron contactos que coincidan con '{recipient_input}'. Por favor verifica el nombre o usa el email directo."
            }
        
        elif len(contacts) == 1:
            # Single contact found - send directly
            contact = contacts[0]
            print(f"Single contact found: {contact['displayName']} - {contact['email']}")
            return _send_email_direct(contact['email'], subject, body, user_id, contact['displayName'])
        
        else:
            # Multiple contacts found - return options for user selection
            contact_display = display_contact_options(contacts, recipient_input)
            return {
                "multiple_contacts": True,
                "contacts": contacts,
                "display": contact_display,
                "message": f"Encontré {len(contacts)} contactos que coinciden con '{recipient_input}'. Por favor selecciona uno para continuar con el envío del correo.",
                "subject": subject, 
                "body": body
            }
    
    except Exception as e:
        error_msg = f"Unexpected error while processing email request: {str(e)}"
        print(f"Unexpected error: {error_msg}")
        return {"error": error_msg}


def _send_email_direct(email: str, subject: str, body: str, user_id: int, recipient_name: str = None) -> dict:
    """
    Internal function to send email directly to a specific email address.
    
    Args:
        email (str): The recipient's email address
        subject (str): The email subject
        body (str): The email body content
        user_id (int): The ID of the user sending the email
        recipient_name (str): Optional recipient name for logging
        
    Returns:
        dict: A dictionary containing either success message or error details
    """
    try:
        # Get user's Microsoft Graph token
        user_service = UserService()
        access_token = user_service.get_user_token(user_id)
        
        if not access_token:
            return {"error": "No access token found for user. Please authenticate with Microsoft first."}
        
        # Microsoft Graph API endpoint for sending emails
        graph_url = "https://graph.microsoft.com/v1.0/me/sendMail"
        
        # Prepare the email payload according to Microsoft Graph API format
        email_payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": body
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": email,
                            "name": recipient_name if recipient_name else ""
                        }
                    }
                ]
            },
            "saveToSentItems": True
        }
        
        # Set up headers with authentication
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        recipient_display = f"{recipient_name} ({email})" if recipient_name else email
        print(f"Sending email to {recipient_display} on behalf of user {user_id}")
        print(f"Subject: {subject}")
        
        # Make the API call to Microsoft Graph
        response = requests.post(
            graph_url,
            headers=headers,
            data=json.dumps(email_payload),
            timeout=30
        )
        
        # Check response status
        if response.status_code == 202:
            # 202 Accepted - Email queued successfully
            print(f"Email sent successfully to {recipient_display}")
            success_message = f"Correo enviado exitosamente a {recipient_display}"
            return {"success": success_message}
        
        elif response.status_code == 401:
            # Unauthorized - Token might be expired or invalid
            error_msg = "Authentication failed. Please refresh your Microsoft login."
            print(f"Authentication error: {response.text}")
            return {"error": error_msg}
        
        elif response.status_code == 403:
            # Forbidden - Insufficient permissions
            error_msg = "Insufficient permissions to send email. Please check your Microsoft account permissions."
            print(f"Permission error: {response.text}")
            return {"error": error_msg}
        
        else:
            # Other errors
            error_detail = ""
            try:
                error_response = response.json()
                error_detail = error_response.get('error', {}).get('message', response.text)
            except:
                error_detail = response.text
            
            error_msg = f"Failed to send email: {error_detail}"
            print(f"Microsoft Graph API error: {response.status_code} - {error_detail}")
            return {"error": error_msg}
    
    except requests.exceptions.Timeout:
        error_msg = "Request timeout while sending email"
        print(f"Timeout error: {error_msg}")
        return {"error": error_msg}
    
    except requests.exceptions.RequestException as e:
        error_msg = "Network error while sending email"
        print(f"Request error: {str(e)}")
        return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error while sending email: {str(e)}"
        print(f"Unexpected error: {error_msg}")
        return {"error": error_msg}

def search_contacts_by_name(name: str, user_id: int, status: str = "Buscando contactos...") -> dict:
    """
    Simplified contact search using Microsoft Graph native search.
    Uses Microsoft's intelligent search algorithms instead of manual filtering.
    
    Args:
        name (str): The complete name to search for
        user_id (int): The ID of the user making the search
        status (str): Status message for tracking. Defaults to "Buscando contactos..."
        
    Returns:
        dict: A dictionary containing contact results, count, and HTML display
        Format: {
            "contacts": [list of contacts],
            "count": number_of_results,
            "display": "HTML formatted results"
        }
    """
    # Validate required fields
    if not name or not name.strip():
        return {"error": "Name is required for contact search"}
        
    if not user_id:
        return {"error": "User ID is required"}
    
    try:
        # Import required modules
        import urllib.parse
        import time
        import base64
        
        # Set status for tracking
        if user_id:
            set_status(user_id, status, 3)  # role_id 3 for Personal Assistant
        
        # Get user's Microsoft Graph token
        user_service = UserService()
        access_token = user_service.get_user_token(user_id)
        
        if not access_token:
            return {"error": "No access token found for user. Please authenticate with Microsoft first."}
        
        # Set up headers with authentication and required consistency level
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "ConsistencyLevel": "eventual"  # Required for $search queries
        }
        
        all_contacts = []
        search_name = name.strip()
        
        # URL encode the complete search term
        encoded_name = urllib.parse.quote(search_name)
        
        print(f"Native Microsoft Graph search for: {name}")
        print(f"Encoded search term: {encoded_name}")
        
        # 1. People Search - Native Microsoft search
        try:
            people_queries = [
                f"https://graph.microsoft.com/v1.0/me/people?$search=\"{encoded_name}\"&$top=50",
                f"https://graph.microsoft.com/v1.0/me/people?$search=\"displayName:{encoded_name}\"&$top=50"
            ]
            
            for i, people_url in enumerate(people_queries):
                try:
                    print(f"People search {i+1}: {people_url}")
                    people_response = requests.get(people_url, headers=headers, timeout=20)
                    print(f"People API response status: {people_response.status_code}")
                    
                    if people_response.status_code == 200:
                        people_data = people_response.json()
                        people_found = len(people_data.get('value', []))
                        print(f"Found {people_found} people in query {i+1}")
                        
                        for person in people_data.get('value', []):
                            display_name = person.get('displayName', '')
                            email_addresses = person.get('emailAddresses', [])
                            
                            if email_addresses and email_addresses[0].get('address'):
                                contact = {
                                    "id": f"people_{person.get('id', '')}",
                                    "displayName": display_name,
                                    "email": email_addresses[0].get('address', ''),
                                    "jobTitle": person.get('jobTitle', ''),
                                    "department": person.get('department', ''),
                                    "companyName": person.get('companyName', ''),
                                    "source": "people",
                                    "relevanceScore": person.get('relevanceScore', 0),
                                    "graph_id": person.get('id', '')
                                }
                                all_contacts.append(contact)
                                print(f"Added people contact: {display_name}")
                        
                        if people_found > 0:
                            break  # Stop if we got results from first query
                            
                    else:
                        print(f"People API error: {people_response.status_code} - {people_response.text}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"People query {i+1} failed: {str(e)}")
                    continue
        
        except Exception as e:
            print(f"Error in people search: {str(e)}")
        
        # 2. Directory Search - Native Microsoft Graph search
        try:
            print("Starting native Microsoft Graph directory search...")
            
            directory_queries = [
                # Primary search: exact name
                f"https://graph.microsoft.com/v1.0/users?$search=\"displayName:{encoded_name}\"&$select=id,displayName,mail,jobTitle,department,userPrincipalName,companyName,officeLocation&$top=50&$count=true",
                # Secondary search: broader search
                f"https://graph.microsoft.com/v1.0/users?$search=\"displayName:{encoded_name}\" OR \"mail:{encoded_name}\"&$select=id,displayName,mail,jobTitle,department,userPrincipalName,companyName,officeLocation&$top=100&$count=true"
            ]
            
            for i, users_url in enumerate(directory_queries):
                try:
                    print(f"Directory search {i+1}: {users_url}")
                    users_response = requests.get(users_url, headers=headers, timeout=25)
                    print(f"Directory API response status: {users_response.status_code}")
                    
                    if users_response.status_code == 200:
                        users_data = users_response.json()
                        users_found = len(users_data.get('value', []))
                        total_count = users_data.get('@odata.count', users_found)
                        print(f"Found {users_found} users (total: {total_count}) in directory search {i+1}")
                        
                        for user in users_data.get('value', []):
                            display_name = user.get('displayName', '')
                            email = user.get('mail') or user.get('userPrincipalName', '')
                            
                            if email and display_name:
                                contact = {
                                    "id": f"user_{user.get('id', '')}",
                                    "displayName": display_name,
                                    "email": email,
                                    "jobTitle": user.get('jobTitle', ''),
                                    "department": user.get('department', ''),
                                    "companyName": user.get('companyName', ''),
                                    "officeLocation": user.get('officeLocation', ''),
                                    "source": "directory",
                                    "relevanceScore": 0,
                                    "graph_id": user.get('id', '')
                                }
                                all_contacts.append(contact)
                                print(f"Added directory user: {display_name} ({email})")
                        
                        # If first query gave good results, don't run second
                        if i == 0 and users_found > 0:
                            break
                                
                    elif users_response.status_code == 400:
                        print(f"Directory search bad request (400): {users_response.text}")
                    elif users_response.status_code == 403:
                        print(f"Directory search forbidden (403) - insufficient permissions")
                    else:
                        print(f"Directory API error: {users_response.status_code} - {users_response.text}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"Directory search {i+1} failed: {str(e)}")
                    continue
                    
                # Small delay between requests
                time.sleep(0.2)
        
        except Exception as e:
            print(f"Error in directory search: {str(e)}")
        
        # 3. Contacts Search - Simple local search
        try:
            print("Searching local contacts...")
            contacts_url = f"https://graph.microsoft.com/v1.0/me/contacts?$top=100"
            
            contacts_response = requests.get(contacts_url, headers=headers, timeout=20)
            print(f"Contacts API response status: {contacts_response.status_code}")
            
            if contacts_response.status_code == 200:
                contacts_data = contacts_response.json()
                contacts_found = len(contacts_data.get('value', []))
                print(f"Found {contacts_found} total contacts, filtering for matches")
                
                search_name_lower = search_name.lower()
                matches = 0
                
                for contact_item in contacts_data.get('value', []):
                    display_name = contact_item.get('displayName', '')
                    email_addresses = contact_item.get('emailAddresses', [])
                    
                    # Simple check: if search name appears in display name
                    if search_name_lower in display_name.lower():
                        if email_addresses and email_addresses[0].get('address'):
                            contact = {
                                "id": f"contact_{contact_item.get('id', '')}",
                                "displayName": display_name,
                                "email": email_addresses[0].get('address', ''),
                                "jobTitle": contact_item.get('jobTitle', ''),
                                "department": contact_item.get('department', ''),
                                "companyName": contact_item.get('companyName', ''),
                                "source": "contacts",
                                "relevanceScore": 0,
                                "graph_id": contact_item.get('id', '')
                            }
                            all_contacts.append(contact)
                            matches += 1
                            print(f"Added contact: {display_name}")
                
                print(f"Found {matches} matching contacts")
            else:
                print(f"Contacts API error: {contacts_response.status_code} - {contacts_response.text}")
        
        except Exception as e:
            print(f"Error in contacts search: {str(e)}")
        
        print(f"Total contacts found before deduplication: {len(all_contacts)}")
        
        # Simple deduplication by email
        unique_contacts = {}
        for contact in all_contacts:
            email = contact['email'].lower()
            if email not in unique_contacts:
                unique_contacts[email] = contact
            else:
                # Keep the one from the most reliable source
                existing = unique_contacts[email]
                current = contact
                
                # Priority: people > directory > contacts (People API usually has better relevance)
                source_priority = {'people': 3, 'directory': 2, 'contacts': 1}
                
                current_priority = source_priority.get(current['source'], 0)
                existing_priority = source_priority.get(existing['source'], 0)
                
                if current_priority > existing_priority:
                    unique_contacts[email] = current
                elif current_priority == existing_priority and current.get('relevanceScore', 0) > existing.get('relevanceScore', 0):
                    unique_contacts[email] = current
        
        # Convert back to list and sort by source priority and relevance
        final_contacts = list(unique_contacts.values())
        
        def sort_key(contact):
            source_priority = {'people': 3, 'directory': 2, 'contacts': 1}
            source_score = source_priority.get(contact['source'], 0)
            relevance_score = contact.get('relevanceScore', 0)
            
            return (
                -source_score,  # Better sources first
                -relevance_score,  # Higher relevance first
                contact['displayName'].lower()  # Alphabetical
            )
        
        final_contacts.sort(key=sort_key)
        
        print(f"Final unique contacts after deduplication: {len(final_contacts)}")
        
        # Get profile photos for each contact
        enhanced_contacts = []
        for contact in final_contacts:
            enhanced_contact = contact.copy()
            
            # Try to get user's profile photo
            try:
                graph_id = contact.get('graph_id')
                if graph_id and contact['source'] in ['directory', 'people']:
                    # For directory users and people, use users/{id}/photo
                    photo_url = f"https://graph.microsoft.com/v1.0/users/{graph_id}/photo/$value"
                elif graph_id and contact['source'] == 'contacts':
                    # For contacts, try contacts approach
                    photo_url = f"https://graph.microsoft.com/v1.0/me/contacts/{graph_id}/photo/$value"
                else:
                    photo_url = None
                
                if photo_url:
                    photo_response = requests.get(photo_url, headers=headers, timeout=10)
                    if photo_response.status_code == 200:
                        photo_base64 = base64.b64encode(photo_response.content).decode('utf-8')
                        enhanced_contact['photo_base64'] = f"data:image/jpeg;base64,{photo_base64}"
                        print(f"✅ Photo found for {contact.get('displayName', 'Unknown')}")
                    else:
                        enhanced_contact['photo_base64'] = None
                        print(f"❌ No photo for {contact.get('displayName', 'Unknown')} - Status: {photo_response.status_code}")
                else:
                    enhanced_contact['photo_base64'] = None
                    
            except Exception as e:
                print(f"❌ Error getting photo for {contact.get('displayName', 'Unknown')}: {str(e)}")
                enhanced_contact['photo_base64'] = None
            
            enhanced_contacts.append(enhanced_contact)
        
        print(f"Found {len(enhanced_contacts)} relevant contacts matching '{name}'")
        
        # Generate HTML display
        html_display = generate_contacts_html_enhanced(enhanced_contacts, search_name)
        
        return {
            "contacts": enhanced_contacts,
            "count": len(enhanced_contacts),
            "display": html_display
        }
    
    except requests.exceptions.Timeout:
        error_msg = "Request timeout while searching contacts"
        print(f"Timeout error: {error_msg}")
        return {"error": error_msg}
    
    except requests.exceptions.RequestException as e:
        error_msg = "Network error while searching contacts"
        print(f"Request error: {str(e)}")
        return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error while searching contacts: {str(e)}"
        print(f"Unexpected error: {error_msg}")
        return {"error": error_msg}

def generate_contacts_html_enhanced(contacts, search_term):
    """Generate enhanced HTML display for contact search results with photos and beautiful styling"""
    
    if not contacts:
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px; text-align: center; background-color: #f8f9fa;">
            <div style="background-color: white; border-radius: 12px; padding: 40px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <div style="font-size: 64px; margin-bottom: 20px;">🔍</div>
                <h2 style="color: #1a365d; margin-bottom: 15px;">No se encontraron contactos</h2>
                <p style="color: #4a5568; font-size: 16px; margin-bottom: 25px;">
                    No se encontraron contactos para "<strong>{search_term}</strong>"
                </p>
                
                <div style="background-color: #e6fffa; padding: 20px; border-radius: 8px; text-align: left;">
                    <h3 style="margin: 0 0 15px 0; color: #234e52;">💡 Sugerencias:</h3>
                    <ul style="margin: 0; padding-left: 20px; color: #2d3748;">
                        <li>Verifica la ortografía del nombre completo</li>
                        <li>Intenta buscar solo por el nombre o apellido</li>
                        <li>Prueba con variaciones del nombre</li>
                        <li>Asegúrate de que la persona esté en tu directorio</li>
                    </ul>
                </div>
            </div>
        </div>
        """
    
    # Generate HTML for results
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #1a365d; margin-bottom: 10px; font-size: 28px;">
                📞 Contactos Encontrados
            </h1>
            <p style="color: #4a5568; font-size: 16px; margin: 0;">
                Resultados para: <strong>"{search_term}"</strong> ({len(contacts)} encontrados)
            </p>
        </div>
        
        <div style="display: grid; gap: 20px;">
    """
    
    source_icons = {
        'people': '👥',
        'contacts': '📞', 
        'directory': '🏢',
        'directory_fuzzy': '🔍'
    }
    
    source_names = {
        'people': 'Contactos Frecuentes',
        'contacts': 'Contactos Guardados',
        'directory': 'Directorio Organizacional',
        'directory_fuzzy': 'Búsqueda Expandida'
    }
    
    for i, contact in enumerate(contacts, 1):
        # Extract contact data
        name = contact.get('displayName', 'Nombre no disponible')
        email = contact.get('email', 'Email no disponible')
        job_title = contact.get('jobTitle', '')
        department = contact.get('department', '')
        company_name = contact.get('companyName', '')
        office_location = contact.get('officeLocation', '')
        photo_base64 = contact.get('photo_base64')
        match_score = contact.get('match_score', 0)
        source = contact.get('source', 'unknown')
        relevance_score = contact.get('relevanceScore', 0)
        
        # Determine match quality indicator
        if match_score >= 100:
            match_indicator = "🎯 Coincidencia Exacta"
            match_color = "#10b981"
        elif match_score >= 85:
            match_indicator = "✅ Muy Relevante"
            match_color = "#3b82f6"
        elif match_score >= 70:
            match_indicator = "⭐ Relevante"
            match_color = "#f59e0b"
        else:
            match_indicator = "📋 Posible Coincidencia"
            match_color = "#6b7280"
        
        # Build additional info
        additional_info = []
        if job_title:
            additional_info.append(f"<p><strong>💼 Cargo:</strong> {job_title}</p>")
        if department:
            additional_info.append(f"<p><strong>🏫 Departamento:</strong> {department}</p>")
        if company_name:
            additional_info.append(f"<p><strong>🏢 Empresa:</strong> {company_name}</p>")
        if office_location:
            additional_info.append(f"<p><strong>📍 Oficina:</strong> {office_location}</p>")
        
        additional_info_html = "".join(additional_info) if additional_info else "<p style='color: #888; font-style: italic;'>No hay información adicional disponible</p>"
        
        # Source info
        source_icon = source_icons.get(source, '📋')
        source_name = source_names.get(source, 'Fuente Desconocida')
        
        # Profile photo section
        photo_section = ""
        if photo_base64:
            photo_section = f"""
                <div style="text-align: center; margin-bottom: 15px;">
                    <img src="{photo_base64}" alt="Foto de perfil de {name}" 
                         style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #667eea;">
                </div>
            """
        else:
            photo_section = f"""
                <div style="text-align: center; margin-bottom: 15px;">
                    <div style="width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; margin: 0 auto; color: white; font-size: 24px; font-weight: bold;">
                        {name[0].upper() if name else '?'}
                    </div>
                </div>
            """
        
        html += f"""
            <div style="background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); border-left: 4px solid #667eea;">
                {photo_section}
                
                <div style="text-align: center; margin-bottom: 15px;">
                    <h2 style="margin: 0 0 5px 0; color: #1a365d; font-size: 22px;">{name}</h2>
                    <p style="margin: 0 0 10px 0; color: #4a5568; font-size: 14px;">
                        <strong>📧 Email:</strong> 
                        <a href="mailto:{email}" style="color: #667eea; text-decoration: none; font-weight: 500;">{email}</a>
                    </p>
                    <span style="background-color: {match_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                        {match_indicator}
                    </span>
                </div>
                
                <div style="margin-top: 15px; line-height: 1.6; color: #2d3748;">
                    {additional_info_html}
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px; padding-top: 15px; border-top: 1px solid #e2e8f0;">
                    <span style="background-color: #e6fffa; color: #234e52; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                        #{i} • {source_icon} {source_name}
                    </span>
                    <span style="background-color: #f0f4f8; color: #2d3748; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                        Coincidencia: {match_score:.0f}%
                    </span>
                </div>
                
                <div style="text-align: center; margin-top: 10px;">
                    <span style="font-size: 12px; color: #888; font-style: italic;">
                        💡 Para usar este contacto, menciona el <strong>número {i}</strong> en tu mensaje
                    </span>
                </div>
            </div>
        """
    
    html += """
        </div>
        
        <div style="background-color: #e6fffa; padding: 20px; margin-top: 30px; border-radius: 8px; border-left: 4px solid #38b2ac;">
            <h3 style="margin: 0 0 10px 0; color: #234e52; font-size: 18px;">💡 Cómo usar los resultados</h3>
            <ul style="margin: 0; padding-left: 20px; color: #2d3748; line-height: 1.6;">
                <li>Los resultados están ordenados por relevancia y calidad de coincidencia</li>
                <li>Para seleccionar un contacto, menciona su número: "usar el contacto número 2"</li>
                <li>Los contactos incluyen información del directorio y contactos guardados</li>
                <li>Las fotos de perfil se obtienen automáticamente cuando están disponibles</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 20px; padding: 15px; background: white; border-radius: 10px; border: 2px dashed #667eea;">
            <p style="margin: 0; color: #667eea; font-weight: 600; font-size: 14px;">
                💬 Para usar cualquiera de estos contactos, simplemente menciona su número (ej: "enviar email al contacto número 1")
            </p>
        </div>
    </div>
    """
    
    return html

def generate_contacts_html(contacts, search_term):
    """Generate HTML display for contact search results"""
    
    if not contacts:
        return f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
            <div style="text-align: center; color: white;">
                <h2 style="margin: 0 0 10px 0; font-size: 24px;">🔍 Búsqueda de Contactos</h2>
                <p style="margin: 0; font-size: 16px; opacity: 0.9;">No se encontraron contactos para "<strong>{search_term}</strong>"</p>
            </div>
        </div>
        """
    
    source_icons = {
        'people': '👥',
        'contacts': '📞', 
        'directory': '🏢',
        'directory_partial': '🔍'
    }
    
    source_names = {
        'people': 'Contactos Frecuentes',
        'contacts': 'Contactos Guardados',
        'directory': 'Directorio Universitario',
        'directory_partial': 'Búsqueda Ampliada'
    }
    
    contacts_html = ""
    for i, contact in enumerate(contacts, 1):
        source_icon = source_icons.get(contact['source'], '📧')
        source_name = source_names.get(contact['source'], contact['source'].title())
        
        # Build additional info
        additional_info = []
        if contact.get('jobTitle'):
            additional_info.append(f"📋 {contact['jobTitle']}")
        if contact.get('department'):
            additional_info.append(f"🏛️ {contact['department']}")
        if contact.get('companyName'):
            additional_info.append(f"🏢 {contact['companyName']}")
        if contact.get('officeLocation'):
            additional_info.append(f"📍 {contact['officeLocation']}")
        
        additional_info_html = "<br>".join(additional_info) if additional_info else "<em style='color: #888;'>Sin información adicional</em>"
        
        contacts_html += f"""
        <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-left: 5px solid #667eea; transition: transform 0.2s ease;">
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 15px; font-size: 18px;">
                    {i}
                </div>
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 5px 0; color: #333; font-size: 20px; font-weight: 600;">{contact['displayName']}</h3>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="background: #f0f8ff; color: #667eea; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 500;">
                            {source_icon} {source_name}
                        </span>
                    </div>
                </div>
            </div>
            
            <div style="margin-left: 50px;">
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <span style="color: #667eea; font-weight: 600; margin-right: 8px;">📧 Email:</span>
                        <a href="mailto:{contact['email']}" style="color: #667eea; text-decoration: none; font-weight: 500; font-size: 16px;">{contact['email']}</a>
                    </div>
                    <div style="color: #555; font-size: 14px; line-height: 1.6;">
                        {additional_info_html}
                    </div>
                </div>
                
                <div style="font-size: 12px; color: #888; font-style: italic;">
                    💡 Para seleccionar este contacto, menciona el <strong>número {i}</strong> en tu mensaje
                </div>
            </div>
        </div>
        """
    
    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 900px; margin: 20px auto; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; box-shadow: 0 15px 35px rgba(0,0,0,0.2);">
        <!-- Header -->
        <div style="text-align: center; color: white; padding: 25px 20px;">
            <h2 style="margin: 0 0 10px 0; font-size: 28px; font-weight: 700;">🔍 Resultados de Búsqueda</h2>
            <p style="margin: 0; font-size: 16px; opacity: 0.9;">Se encontraron <strong>{len(contacts)} contactos</strong> para "<strong>{search_term}</strong>"</p>
        </div>
        
        <!-- Results -->
        <div style="padding: 20px; background: #f5f7fa; border-radius: 0 0 15px 15px;">
            {contacts_html}
            
            <!-- Footer -->
            <div style="text-align: center; margin-top: 20px; padding: 15px; background: white; border-radius: 10px; border: 2px dashed #667eea;">
                <p style="margin: 0; color: #667eea; font-weight: 600; font-size: 14px;">
                    💬 Para usar cualquiera de estos contactos, simplemente menciona su número (ej: "el contacto número 3")
                </p>
            </div>
        </div>
    </div>
    """

def display_contact_options(contacts: list, search_name: str) -> str:
    """
    Creates a formatted display of contact options for the user to choose from.
    
    Args:
        contacts (list): List of contact dictionaries
        search_name (str): The original search name
        
    Returns:
        str: Formatted HTML string with contact options
    """
    if not contacts:
        return f"<p>No se encontraron contactos que coincidan con '{search_name}'</p>"
    
    if len(contacts) == 1:
        contact = contacts[0]
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 20px auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <h3 style="color: #9333ea; margin-bottom: 15px;">✓ Contacto encontrado</h3>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #9333ea;">
                <strong>{contact['displayName']}</strong><br>
                <span style="color: #666;">{contact['email']}</span><br>
                {f"<small style='color: #888;'>{contact['jobTitle']}</small>" if contact['jobTitle'] else ""}
                {f"<small style='color: #888;'> - {contact['department']}</small>" if contact['department'] else ""}
            </div>
            <p style="margin-top: 15px; color: #666;">Puedes proceder con el envío del correo.</p>
        </div>
        """
    
    # Multiple contacts found
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 20px auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h3 style="color: #9333ea; margin-bottom: 15px;">📧 Contactos encontrados para "{search_name}"</h3>
        <p style="margin-bottom: 20px; color: #666;">Encontré {len(contacts)} contactos. Selecciona uno:</p>
        <div style="space-y: 10px;">
    """
    
    for i, contact in enumerate(contacts, 1):
        # Extract username from email for easier reference
        username = contact['email'].split('@')[0] if '@' in contact['email'] else ''
        
        html += f"""
        <div style="background-color: #f8f9fa; padding: 15px; margin-bottom: 10px; border-radius: 6px; border-left: 4px solid #9333ea;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <strong style="font-size: 16px; color: #333;">#{i}. {contact['displayName']}</strong><br>
                    <span style="color: #666; font-size: 14px;">{contact['email']}</span><br>
                    {f"<small style='color: #888;'>{contact['jobTitle']}</small>" if contact['jobTitle'] else ""}
                    {f"<small style='color: #888;'> - {contact['department']}</small>" if contact['department'] else ""}
                </div>
                <div style="text-align: right; font-size: 12px; color: #9333ea;">
                    <div>Opción {i}</div>
                    {f"<div>@{username}</div>" if username else ""}
                </div>
            </div>
        </div>
        """
    
    html += """
        </div>
        <div style="background-color: #e8f4fd; padding: 15px; margin-top: 20px; border-radius: 6px;">
            <h4 style="margin: 0 0 10px 0; color: #1d4ed8;">💡 Formas de seleccionar:</h4>
            <ul style="margin: 0; padding-left: 20px; color: #333;">
                <li><strong>Por número:</strong> "el segundo", "opción 3", "número 1"</li>
                <li><strong>Por nombre completo:</strong> usar el nombre exacto mostrado</li>
                <li><strong>Por username:</strong> usar solo la parte antes del @</li>
            </ul>
        </div>
    </div>
    """
    
    return html


def read_calendar_events(start_date: str, end_date: str, user_id: int, status: str = "Consultando calendario...") -> dict:
    """
    Reads calendar events for the specified date range using Microsoft Graph API.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        user_id (int): The ID of the user requesting calendar information
        status (str): Status message for tracking. Defaults to "Consultando calendario..."
        
    Returns:
        dict: A dictionary containing calendar events and HTML display
    """
    # Validate required fields
    if not start_date or not end_date:
        return {"error": "Start date and end date are required"}
        
    if not user_id:
        return {"error": "User ID is required"}
    
    try:
        # Set status for tracking
        if user_id:
            set_status(user_id, status, 3)  # role_id 3 for Personal Assistant
        
        # Get user's Microsoft Graph token
        user_service = UserService()
        access_token = user_service.get_user_token(user_id)
        
        if not access_token:
            return {"error": "No access token found for user. Please authenticate with Microsoft first."}
        
        # Format dates for Microsoft Graph API
        start_iso = f"{start_date}T00:00:00"
        end_iso = f"{end_date}T23:59:59"
        
        # Set up headers with authentication
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Microsoft Graph API endpoint for calendar events
        calendar_url = f"https://graph.microsoft.com/v1.0/me/events?$filter=start/dateTime ge '{start_iso}' and end/dateTime le '{end_iso}'&$orderby=start/dateTime&$select=id,subject,start,end,location,body,attendees,importance,isAllDay,webLink"
        
        print(f"Fetching calendar events from {start_date} to {end_date}")
        
        response = requests.get(calendar_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            events_data = response.json()
            events = events_data.get('value', [])
            
            # Generate HTML display
            html_display = _generate_calendar_html(events, start_date, end_date)
            
            print(f"Found {len(events)} events")
            
            return {
                "events": events,
                "display": html_display,
                "total_events": len(events),
                "start_date": start_date,
                "end_date": end_date,
                "success": "Calendar events retrieved successfully"
            }
        
        elif response.status_code == 401:
            error_msg = "Authentication failed. Please refresh your Microsoft login."
            print(f"Authentication error: {response.text}")
            return {"error": error_msg}
        
        elif response.status_code == 403:
            error_msg = "Insufficient permissions to read calendar. Please check your Microsoft account permissions."
            print(f"Permission error: {response.text}")
            return {"error": error_msg}
        
        else:
            error_detail = ""
            try:
                error_response = response.json()
                error_detail = error_response.get('error', {}).get('message', response.text)
            except:
                error_detail = response.text
            
            error_msg = f"Failed to read calendar: {error_detail}"
            print(f"Microsoft Graph API error: {response.status_code} - {error_detail}")
            return {"error": error_msg}
    
    except requests.exceptions.Timeout:
        error_msg = "Request timeout while reading calendar"
        print(f"Timeout error: {error_msg}")
        return {"error": error_msg}
    
    except requests.exceptions.RequestException as e:
        error_msg = "Network error while reading calendar"
        print(f"Request error: {str(e)}")
        return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error while reading calendar: {str(e)}"
        print(f"Unexpected error: {error_msg}")
        return {"error": error_msg}


def _generate_calendar_html(events: list, start_date: str, end_date: str) -> str:
    """Generate HTML display for calendar events."""
    
    if not events:
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 20px auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <h3 style="color: #9333ea; margin-bottom: 15px;">📅 Calendario</h3>
            <p style="color: #666; text-align: center; padding: 40px 20px;">No tienes eventos programados del {start_date} al {end_date}</p>
        </div>
        """
    
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 20px auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h3 style="color: #9333ea; margin-bottom: 20px;">📅 Tu Calendario</h3>
        <p style="margin-bottom: 20px; color: #666;">Del {start_date} al {end_date} - {len(events)} eventos</p>
        <div style="space-y: 15px;">
    """
    
    current_date = None
    
    for event in events:
        # Parse event date and time  
        start_str = event.get('start', {}).get('dateTime', '')
        end_str = event.get('end', {}).get('dateTime', '')
        
        print(f"DEBUG - Raw datetime string: {start_str}")
        
        try:
            from datetime import datetime, timedelta
            # Microsoft Graph returns UTC time, convert to Colombia (UTC-5)
            if 'T' in start_str:
                # Clean the string and parse
                clean_start = start_str.split('.')[0]  # Remove microseconds
                clean_end = end_str.split('.')[0]      # Remove microseconds
                
                start_utc = datetime.fromisoformat(clean_start)
                end_utc = datetime.fromisoformat(clean_end)
                
                # Convert UTC to Colombia time (subtract 5 hours)
                start_local = start_utc - timedelta(hours=5)
                end_local = end_utc - timedelta(hours=5)
            else:
                start_local = datetime.now()
                end_local = datetime.now()
        except Exception as e:
            print(f"Error parsing datetime: {e}, start_str: {start_str}")
            from datetime import datetime
            start_local = datetime.now()
            end_local = datetime.now()
        
        event_date = start_local.strftime('%Y-%m-%d')
        
        # Add date separator if new day
        if current_date != event_date:
            current_date = event_date
            formatted_date = start_local.strftime('%A, %d de %B')
            html += f"""
            <div style="background-color: #f1f5f9; padding: 10px; margin: 20px 0 10px 0; border-radius: 6px; font-weight: bold; color: #475569;">
                {formatted_date}
            </div>
            """
        
        # Format time
        if event.get('isAllDay', False):
            time_str = "Todo el día"
        else:
            start_time_str = start_local.strftime('%H:%M')
            end_time_str = end_local.strftime('%H:%M')
            time_str = f"{start_time_str} - {end_time_str}"
        
        # Get location
        location = event.get('location', {}).get('displayName', '') if isinstance(event.get('location'), dict) else event.get('location', '')
        
        # Get attendees count
        attendees_count = len(event.get('attendees', []))
        
        html += f"""
        <div style="background-color: #f8f9fa; padding: 15px; margin-bottom: 15px; border-radius: 6px; border-left: 4px solid #9333ea;">
            <div style="margin-bottom: 8px;">
                <strong style="font-size: 16px; color: #333;">{event.get('subject', 'Sin título')}</strong>
            </div>
            <div style="color: #666; font-size: 14px; margin-bottom: 5px;">
                🕒 {time_str}
            </div>
            {f'<div style="color: #666; font-size: 14px; margin-bottom: 5px;">📍 {location}</div>' if location else ''}
            {f'<div style="color: #666; font-size: 14px;">👥 {attendees_count} asistentes</div>' if attendees_count > 0 else ''}
        </div>
        """
    
    html += """
        </div>
    </div>
    """
    
    return html


def create_calendar_event(title: str, start_datetime: str, end_datetime: str, user_id: int, description: str = "", status: str = "Creando recordatorio...") -> dict:
    """
    Creates a calendar event/reminder using Microsoft Graph API.
    
    Args:
        title (str): Title of the event/reminder
        start_datetime (str): Start date and time in YYYY-MM-DDTHH:MM format (Colombia time)
        end_datetime (str): End date and time in YYYY-MM-DDTHH:MM format (Colombia time)
        user_id (int): The ID of the user creating the event
        description (str): Optional description for the event. Defaults to ""
        status (str): Status message for tracking. Defaults to "Creando recordatorio..."
        
    Returns:
        dict: A dictionary containing either success message or error details
    """
    # Validate required fields
    if not title or not start_datetime or not end_datetime:
        return {"error": "Title, start datetime, and end datetime are required"}
        
    if not user_id:
        return {"error": "User ID is required"}
    
    try:
        # Set status for tracking
        if user_id:
            set_status(user_id, status, 3)  # role_id 3 for Personal Assistant
        
        # Get user's Microsoft Graph token
        user_service = UserService()
        access_token = user_service.get_user_token(user_id)
        
        if not access_token:
            return {"error": "No access token found for user. Please authenticate with Microsoft first."}
        
        # Validate datetime format
        try:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_datetime)
            end_dt = datetime.fromisoformat(end_datetime)
            
            # Ensure end time is after start time
            if end_dt <= start_dt:
                return {"error": "End time must be after start time"}
        except:
            return {"error": "Invalid datetime format. Use YYYY-MM-DDTHH:MM format"}
        
        # Prepare the event payload for Microsoft Graph API
        event_payload = {
            "subject": title,
            "start": {
                "dateTime": start_datetime,
                "timeZone": "America/Bogota"
            },
            "end": {
                "dateTime": end_datetime,
                "timeZone": "America/Bogota"
            },
            "body": {
                "contentType": "text",
                "content": description if description else ""
            },
            "isReminderOn": True,
            "reminderMinutesBeforeStart": 15
        }
        
        # Set up headers with authentication
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Microsoft Graph API endpoint for creating events
        events_url = "https://graph.microsoft.com/v1.0/me/events"
        
        print(f"Creating calendar event: {title} from {start_datetime} to {end_datetime}")
        
        # Make the API call to Microsoft Graph
        response = requests.post(
            events_url,
            headers=headers,
            data=json.dumps(event_payload),
            timeout=30
        )
        
        # Check response status
        if response.status_code == 201:
            # 201 Created - Event created successfully
            event_data = response.json()
            event_id = event_data.get('id', '')
            web_link = event_data.get('webLink', '')
            
            print(f"Event created successfully with ID: {event_id}")
            
            # Format success message
            start_formatted = start_dt.strftime('%d de %B a las %H:%M')
            success_message = f"Recordatorio '{title}' creado exitosamente para el {start_formatted}"
            
            return {
                "success": success_message,
                "event_id": event_id,
                "title": title,
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
                "web_link": web_link,
                "message": "Event created successfully"
            }
        
        elif response.status_code == 401:
            # Unauthorized - Token might be expired or invalid
            error_msg = "Authentication failed. Please refresh your Microsoft login."
            print(f"Authentication error: {response.text}")
            return {"error": error_msg}
        
        elif response.status_code == 403:
            # Forbidden - Insufficient permissions
            error_msg = "Insufficient permissions to create calendar events. Please check your Microsoft account permissions."
            print(f"Permission error: {response.text}")
            return {"error": error_msg}
        
        elif response.status_code == 400:
            # Bad Request - Invalid data
            try:
                error_response = response.json()
                error_detail = error_response.get('error', {}).get('message', 'Invalid event data')
            except:
                error_detail = "Invalid event data"
            
            error_msg = f"Cannot create event: {error_detail}"
            print(f"Bad request error: {response.text}")
            return {"error": error_msg}
        
        else:
            # Other errors
            error_detail = ""
            try:
                error_response = response.json()
                error_detail = error_response.get('error', {}).get('message', response.text)
            except:
                error_detail = response.text
            
            error_msg = f"Failed to create event: {error_detail}"
            print(f"Microsoft Graph API error: {response.status_code} - {error_detail}")
            return {"error": error_msg}
    
    except requests.exceptions.Timeout:
        error_msg = "Request timeout while creating event"
        print(f"Timeout error: {error_msg}")
        return {"error": error_msg}
    
    except requests.exceptions.RequestException as e:
        error_msg = "Network error while creating event"
        print(f"Request error: {str(e)}")
        return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error while creating event: {str(e)}"
        print(f"Unexpected error: {error_msg}")
        return {"error": error_msg}
    

def read_user_emails(user_id: int, max_emails: int = 10, unread_only: bool = False, search_query: str = None, status: str = "Consultando emails...") -> dict:
    """
    Reads user emails using Microsoft Graph API without marking them as read.
    
    Args:
        user_id (int): The ID of the user requesting email information
        max_emails (int): Maximum number of emails to retrieve (default: 10, max: 50)
        unread_only (bool): If True, only returns unread emails (default: False)
        search_query (str): Search query for subject, sender, or content (optional)
        status (str): Status message for tracking. Defaults to "Consultando emails..."
        
    Returns:
        dict: A dictionary containing emails and HTML display or error information
    """
    # Validate required fields
    if not user_id:
        return {"error": "User ID is required"}
    
    # Limit max_emails to prevent performance issues
    if max_emails > 50:
        max_emails = 50
    elif max_emails < 1:
        max_emails = 10
    
    try:
        # Set status for tracking
        if user_id:
            set_status(user_id, status, 3)  # role_id 3 for Personal Assistant
        
        # Get user's Microsoft Graph token
        user_service = UserService()
        access_token = user_service.get_user_token(user_id)
        
        if not access_token:
            return {"error": "No access token found for user. Please authenticate with Microsoft first."}
        
        # Build Microsoft Graph API URL for emails
        graph_url = "https://graph.microsoft.com/v1.0/me/messages"
        
        # Build query parameters
        params = {
            "$top": max_emails,
            "$select": "id,subject,from,receivedDateTime,bodyPreview,isRead,hasAttachments,importance,webLink"
        }
        
        # Add unread filter if requested
        filters = []
        if unread_only:
            filters.append("isRead eq false")
        
        # Add search query if provided
        if search_query and search_query.strip():
            params["$search"] = f'"{search_query.strip()}"'
            # NOTE: Microsoft Graph API doesn't allow $filter or $orderBy with $search
            # So we'll filter unread emails locally and results won't be sorted by date
        else:
            # Only use $filter and $orderBy when there's no search query
            params["$orderby"] = "receivedDateTime desc"  # Most recent first
            if filters:
                params["$filter"] = " and ".join(filters)
        
        # Set up headers with authentication
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        print(f"Fetching emails for user {user_id}")
        if unread_only:
            print("Filtering for unread emails only")
        if search_query:
            print(f"Searching for: {search_query}")
        
        # Make the API call to Microsoft Graph
        response = requests.get(
            graph_url,
            headers=headers,
            params=params,
            timeout=30
        )
        
        # Check response status
        if response.status_code == 200:
            # Success - process emails
            emails_data = response.json()
            emails = emails_data.get('value', [])
            if search_query and unread_only:
                emails = [email for email in emails if not email.get('isRead', True)]
            
            print(f"Retrieved {len(emails)} emails")
            
            if not emails:
                # No emails found
                message = "No hay emails"
                if unread_only:
                    message += " no leídos"
                if search_query:
                    message += f" que coincidan con '{search_query}'"
                message += " en este momento."
                
                return {
                    "emails": [],
                    "count": 0,
                    "display": f'<div style="padding: 20px; text-align: center; color: #666;"><p>{message}</p></div>'
                }
            
            # Generate HTML display
            html_display = _generate_emails_html(emails, unread_only, search_query, max_emails)
            
            return {
                "emails": emails,
                "count": len(emails),
                "display": html_display
            }
        
        elif response.status_code == 401:
            # Unauthorized - Token might be expired or invalid
            error_msg = "Authentication failed. Please refresh your Microsoft login."
            print(f"Authentication error: {response.text}")
            return {"error": error_msg}
        
        elif response.status_code == 403:
            error_msg = "Insufficient permissions to read emails. Please check your Microsoft account permissions."
            print(f"Permission error: {response.text}")
            return {"error": error_msg}
        
        else:
            # Other errors
            error_detail = ""
            try:
                error_response = response.json()
                error_detail = error_response.get('error', {}).get('message', response.text)
            except:
                error_detail = response.text
            
            error_msg = f"Failed to read emails: {error_detail}"
            print(f"Microsoft Graph API error: {response.status_code} - {error_detail}")
            return {"error": error_msg}
    
    except requests.exceptions.Timeout:
        error_msg = "Request timeout while reading emails"
        print(f"Timeout error: {error_msg}")
        return {"error": error_msg}
    
    except requests.exceptions.RequestException as e:
        error_msg = "Network error while reading emails"
        print(f"Request error: {str(e)}")
        return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error while reading emails: {str(e)}"
        print(f"Unexpected error: {error_msg}")
        return {"error": error_msg}


def _generate_emails_html(emails: list, unread_only: bool, search_query: str, max_emails: int) -> str:
    """Generate HTML display for emails."""
    
    # Create header based on filters applied
    header_parts = []
    if unread_only:
        header_parts.append("No Leídos")
    if search_query:
        header_parts.append(f"Búsqueda: '{search_query}'")
    
    header_title = "📧 Emails"
    if header_parts:
        header_title += f" ({', '.join(header_parts)})"
    
    html = f"""
    <div style="max-width: 800px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px 12px 0 0; text-align: center;">
            <h2 style="margin: 0; font-size: 1.4rem; font-weight: 600;">{header_title}</h2>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 0.9rem;">
                Mostrando {len(emails)} de {max_emails} emails máximo
            </p>
        </div>
        
        <div style="background: white; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
    """
    
    for i, email in enumerate(emails):
        # Extract sender information
        sender_info = email.get('from', {})
        sender_email_addr = sender_info.get('emailAddress', {})
        sender_name = sender_email_addr.get('name', 'Remitente desconocido')
        sender_email = sender_email_addr.get('address', '')
        
        # Format date
        received_date = email.get('receivedDateTime', '')
        formatted_date = ""
        if received_date:
            try:
                from datetime import datetime
                # Parse ISO 8601 date
                date_obj = datetime.fromisoformat(received_date.replace('Z', '+00:00'))
                # Format for display
                formatted_date = date_obj.strftime("%d/%m/%Y %H:%M")
            except:
                formatted_date = received_date[:16]  # Fallback
        
        # Email properties
        subject = email.get('subject', 'Sin asunto')
        body_preview = email.get('bodyPreview', '')[:150] + '...' if email.get('bodyPreview', '') else 'Sin contenido'
        is_read = email.get('isRead', True)
        has_attachments = email.get('hasAttachments', False)
        importance = email.get('importance', 'normal')
        web_link = email.get('webLink', '')
        
        # Styling based on read status
        email_bg = "#f8fafc" if is_read else "#fef3c7"
        border_left = "4px solid #e5e7eb" if is_read else "4px solid #f59e0b"
        subject_weight = "500" if is_read else "600"
        
        # Importance indicator
        importance_icon = ""
        if importance == "high":
            importance_icon = "🔴 "
        elif importance == "low":
            importance_icon = "🔵 "
        
        # Attachment indicator
        attachment_icon = "📎 " if has_attachments else ""
        
        # Unread indicator
        unread_indicator = ""
        if not is_read:
            unread_indicator = '<span style="display: inline-block; width: 8px; height: 8px; background: #f59e0b; border-radius: 50%; margin-left: 8px;"></span>'
        
        html += f"""
            <div style="border-left: {border_left}; background: {email_bg}; padding: 16px 20px; {'' if i == len(emails) - 1 else 'border-bottom: 1px solid #e5e7eb;'}">
                <div style="display: flex; justify-content: between; align-items: flex-start; margin-bottom: 8px;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; margin-bottom: 4px;">
                            <h4 style="margin: 0; font-size: 1rem; font-weight: {subject_weight}; color: #1f2937; line-height: 1.3;">
                                {importance_icon}{attachment_icon}{subject[:80] + '...' if len(subject) > 80 else subject}
                            </h4>
                            {unread_indicator}
                        </div>
                        <div style="display: flex; align-items: center; margin-bottom: 8px; font-size: 0.875rem; color: #6b7280;">
                            <span style="font-weight: 500;">{sender_name}</span>
                            {f' <span style="color: #9ca3af;">({sender_email})</span>' if sender_email and sender_email != sender_name else ''}
                            <span style="margin: 0 8px; color: #d1d5db;">•</span>
                            <span>{formatted_date}</span>
                        </div>
                    </div>
                </div>
                
                <div style="color: #4b5563; font-size: 0.875rem; line-height: 1.4; margin-bottom: 12px;">
                    {body_preview}
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; gap: 12px; font-size: 0.75rem; color: #6b7280;">
                        <span>{'✉️ No leído' if not is_read else '📖 Leído'}</span>
                        {f'<span>📎 {attachment_icon.strip()}</span>' if has_attachments else ''}
                        {f'<span>⚠️ {importance.title()}</span>' if importance != 'normal' else ''}
                    </div>
                    {f'<a href="{web_link}" target="_blank" style="font-size: 0.75rem; color: #3b82f6; text-decoration: none; padding: 4px 8px; background: #eff6ff; border-radius: 4px; border: 1px solid #bfdbfe;">Ver en Outlook</a>' if web_link else ''}
                </div>
            </div>
        """
    
    html += """
        </div>
        
        <div style="background-color: #f1f5f9; padding: 15px; margin-top: 16px; border-radius: 8px; font-size: 0.875rem;">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">💡</span>
                <strong style="color: #334155;">Información importante:</strong>
            </div>
            <ul style="margin: 0; padding-left: 20px; color: #475569; line-height: 1.5;">
                <li><strong>Los emails NO se marcan como leídos</strong> automáticamente</li>
                <li>Usa el enlace "Ver en Outlook" para abrir y responder emails</li>
                <li>Los emails no leídos aparecen con fondo amarillo y punto naranja</li>
                <li>Puedes buscar por asunto, remitente o contenido</li>
            </ul>
        </div>
    </div>
    """
    
    return html
