from dotenv import load_dotenv
import os
from typing import Dict
from apps.status.services import set_status
from serpapi import GoogleSearch
from html import escape
from apps.users.services import UserService
import requests 
import json
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
    

def send_email_on_behalf_of_user(to_email_or_name: str, subject: str, body: str, user_id: int, status: str = "Enviando correo...") -> dict:
    """
    Sends an email on behalf of the user using Microsoft Graph API with their OAuth token.
    Can accept either an email address or a contact name. If a name is provided and multiple
    contacts are found, returns the options for the user to choose.
    
    Args:
        to_email_or_name (str): The recipient's email address or name
        subject (str): The email subject
        body (str): The email body content
        user_id (int): The ID of the user sending the email
        status (str): Status message for tracking. Defaults to "Enviando correo..."
        
    Returns:
        dict: A dictionary containing either success message, contact options, or error details
    """
    # Validate required fields
    if not to_email_or_name or not subject or not body:
        return {"error": "Recipient, subject, and body are required"}
        
    if not user_id:
        return {"error": "User ID is required"}
    
    try:
        # Set status for tracking
        if user_id:
            set_status(user_id, status, 3)  # role_id 3 for Personal Assistant
        
        recipient_input = to_email_or_name.strip()
        
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
    Searches for contacts by name using Microsoft Graph API.
    Searches in people, contacts, and organizational directory.
    
    Args:
        name (str): The name to search for
        user_id (int): The ID of the user making the search
        status (str): Status message for tracking. Defaults to "Buscando contactos..."
        
    Returns:
        dict: A dictionary containing either contact results or error details
        Format: {
            "contacts": [
                {
                    "id": "unique_id",
                    "displayName": "Full Name",
                    "email": "email@domain.com",
                    "jobTitle": "Position",
                    "department": "Department",
                    "source": "people|contacts|directory"
                }
            ],
            "count": number_of_results
        }
    """
    # Validate required fields
    if not name or not name.strip():
        return {"error": "Name is required for contact search"}
        
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
        
        # Set up headers with authentication
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        all_contacts = []
        search_name = name.strip().lower()
        
        print(f"Searching contacts for: {name}")
        
        # 1. Search in People (frequent contacts and suggestions)
        try:
            people_url = f"https://graph.microsoft.com/v1.0/me/people?$search=\"{name}\""
            people_response = requests.get(people_url, headers=headers, timeout=15)
            
            if people_response.status_code == 200:
                people_data = people_response.json()
                for person in people_data.get('value', []):
                    # Extract primary email
                    email_addresses = person.get('emailAddresses', [])
                    if email_addresses and email_addresses[0].get('address'):
                        contact = {
                            "id": f"people_{person.get('id', '')}",
                            "displayName": person.get('displayName', ''),
                            "email": email_addresses[0].get('address', ''),
                            "jobTitle": person.get('jobTitle', ''),
                            "department": person.get('department', ''),
                            "source": "people"
                        }
                        all_contacts.append(contact)
            else:
                print(f"People search failed: {people_response.status_code}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error searching people: {str(e)}")
        
        # 2. Search in Contacts
        try:
            contacts_url = f"https://graph.microsoft.com/v1.0/me/contacts?$filter=contains(displayName,'{name}') or contains(givenName,'{name}') or contains(surname,'{name}')"
            contacts_response = requests.get(contacts_url, headers=headers, timeout=15)
            
            if contacts_response.status_code == 200:
                contacts_data = contacts_response.json()
                for contact_item in contacts_data.get('value', []):
                    # Extract primary email
                    email_addresses = contact_item.get('emailAddresses', [])
                    if email_addresses and email_addresses[0].get('address'):
                        contact = {
                            "id": f"contact_{contact_item.get('id', '')}",
                            "displayName": contact_item.get('displayName', ''),
                            "email": email_addresses[0].get('address', ''),
                            "jobTitle": contact_item.get('jobTitle', ''),
                            "department": contact_item.get('department', ''),
                            "source": "contacts"
                        }
                        all_contacts.append(contact)
            else:
                print(f"Contacts search failed: {contacts_response.status_code}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error searching contacts: {str(e)}")
        
        # 3. Search in Organization Directory (if permissions allow)
        try:
            # Search for users in the organization
            users_url = f"https://graph.microsoft.com/v1.0/users?$filter=startswith(displayName,'{name}') or startswith(givenName,'{name}') or startswith(surname,'{name}')&$select=id,displayName,mail,jobTitle,department,userPrincipalName"
            users_response = requests.get(users_url, headers=headers, timeout=15)
            
            if users_response.status_code == 200:
                users_data = users_response.json()
                for user in users_data.get('value', []):
                    # Use mail or userPrincipalName
                    email = user.get('mail') or user.get('userPrincipalName', '')
                    if email:
                        contact = {
                            "id": f"user_{user.get('id', '')}",
                            "displayName": user.get('displayName', ''),
                            "email": email,
                            "jobTitle": user.get('jobTitle', ''),
                            "department": user.get('department', ''),
                            "source": "directory"
                        }
                        all_contacts.append(contact)
            else:
                print(f"Directory search failed: {users_response.status_code}")
                # Don't treat directory search failure as fatal error
        
        except requests.exceptions.RequestException as e:
            print(f"Error searching directory: {str(e)}")
            # Don't treat directory search failure as fatal error
        
        # Remove duplicates based on email address
        unique_contacts = {}
        for contact in all_contacts:
            email = contact['email'].lower()
            if email not in unique_contacts:
                unique_contacts[email] = contact
            else:
                # Keep the one from the most reliable source
                existing_source = unique_contacts[email]['source']
                current_source = contact['source']
                # Priority: people > contacts > directory
                if (current_source == 'people' and existing_source != 'people') or \
                   (current_source == 'contacts' and existing_source == 'directory'):
                    unique_contacts[email] = contact
        
        # Convert back to list and sort by name
        final_contacts = list(unique_contacts.values())
        final_contacts.sort(key=lambda x: x['displayName'].lower())
        
        # Filter results to ensure they actually match the search term
        # This helps with false positives from broad API searches
        filtered_contacts = []
        for contact in final_contacts:
            display_name_lower = contact['displayName'].lower()
            if search_name in display_name_lower or \
               any(search_name in part.lower() for part in contact['displayName'].split()):
                filtered_contacts.append(contact)
        
        print(f"Found {len(filtered_contacts)} unique contacts matching '{name}'")
        
        return {
            "contacts": filtered_contacts,
            "count": len(filtered_contacts)
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