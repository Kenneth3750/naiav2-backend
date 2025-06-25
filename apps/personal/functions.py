from dotenv import load_dotenv
import os
from typing import Dict
from apps.status.services import set_status
from serpapi import GoogleSearch
import json
from html import escape

load_dotenv()

def get_current_news(location: str, user_id: int, status: str) -> Dict:
    """
    Obtiene las últimas noticias de una ubicación específica con visualización moderna y atractiva.
    
    Args:
        location (str): La ubicación para obtener noticias
        user_id (int): ID del usuario
        status (str): Mensaje de estado
        
    Returns:
        dict: Diccionario con HTML visual de noticias
    """
    try:
        set_status(user_id, status, 3)  # 3 = role_id del asistente personal
        
        params = {
            "engine": "google_news",
            "q": location,
            "gl": "co",  # Colombia
            "hl": "es",  # Español
            "api_key": os.getenv("SERPAPI_KEY")
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        news_results = results.get("news_results", [])
        
        if not news_results:
            return {"error": "No se encontraron noticias para esta ubicación"}
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Noticias de {location}</title>
            <style>
                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                
                .news-container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    color: white;
                }}
                
                .header h1 {{
                    font-size: 2.5rem;
                    font-weight: 700;
                    margin-bottom: 10px;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }}
                
                .header p {{
                    font-size: 1.2rem;
                    opacity: 0.9;
                }}
                
                .news-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                    gap: 25px;
                    margin-top: 30px;
                }}
                
                .news-card {{
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    transition: all 0.3s ease;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255,255,255,0.2);
                }}
                
                .news-card:hover {{
                    transform: translateY(-10px);
                    box-shadow: 0 30px 60px rgba(0,0,0,0.2);
                }}
                
                .news-image {{
                    width: 100%;
                    height: 200px;
                    background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                    overflow: hidden;
                }}
                
                .news-image img {{
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }}
                
                .news-image .placeholder {{
                    font-size: 3rem;
                    color: white;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }}
                
                .news-content {{
                    padding: 25px;
                }}
                
                .news-title {{
                    font-size: 1.3rem;
                    font-weight: 700;
                    color: #2d3748;
                    margin-bottom: 15px;
                    line-height: 1.4;
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                }}
                
                .news-meta {{
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    margin-bottom: 15px;
                    font-size: 0.9rem;
                    color: #718096;
                }}
                
                .news-source {{
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    color: white;
                    padding: 5px 12px;
                    border-radius: 15px;
                    font-weight: 600;
                    font-size: 0.8rem;
                }}
                
                .news-date {{
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }}
                
                .news-snippet {{
                    color: #4a5568;
                    line-height: 1.6;
                    margin-bottom: 20px;
                    display: -webkit-box;
                    -webkit-line-clamp: 3;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                }}
                
                .news-link {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    color: #667eea;
                    text-decoration: none;
                    font-weight: 600;
                    transition: all 0.3s ease;
                    padding: 10px 20px;
                    background: rgba(102, 126, 234, 0.1);
                    border-radius: 25px;
                    border: 2px solid transparent;
                }}
                
                .news-link:hover {{
                    background: #667eea;
                    color: white;
                    transform: translateX(5px);
                }}
                
                .stats-bar {{
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 20px;
                    margin-bottom: 30px;
                    display: flex;
                    justify-content: space-around;
                    text-align: center;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }}
                
                .stat-item {{
                    display: flex;
                    flex-direction: column;
                    gap: 5px;
                }}
                
                .stat-number {{
                    font-size: 2rem;
                    font-weight: 700;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                
                .stat-label {{
                    color: #718096;
                    font-size: 0.9rem;
                    font-weight: 500;
                }}
                
                .breaking-badge {{
                    position: absolute;
                    top: 15px;
                    right: 15px;
                    background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                    color: white;
                    padding: 5px 12px;
                    border-radius: 15px;
                    font-size: 0.8rem;
                    font-weight: 700;
                    animation: pulse 2s infinite;
                }}
                
                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; }}
                    50% {{ opacity: 0.7; }}
                }}
                
                @media (max-width: 768px) {{
                    .header h1 {{
                        font-size: 2rem;
                    }}
                    
                    .news-grid {{
                        grid-template-columns: 1fr;
                        gap: 20px;
                    }}
                    
                    .stats-bar {{
                        flex-direction: column;
                        gap: 15px;
                    }}
                }}
            </style>
        </head>
        <body>
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
            
            # Determinar si es noticia destacada (primeras 3)
            is_breaking = i < 3
            
            # Preparar contenido de imagen
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
        </body>
        </html>
        """
        with open("news.html", "w", encoding="utf-8") as file:
            file.write(html_content)
        
        return {"display": html_content}
        
    except Exception as e:
        print(f"Error obteniendo noticias: {str(e)}")
        return {"error": str(e)}


def get_weather(location: str, user_id: int, status: str) -> Dict:
    """
    Obtiene información del clima con una visualización moderna y atractiva.
    
    Args:
        location (str): La ubicación para obtener el clima
        user_id (int): ID del usuario
        status (str): Mensaje de estado
        
    Returns:
        dict: Diccionario con HTML visual del clima
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
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Clima en {location}</title>
            <style>
                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
                    background: linear-gradient(135deg, #74b9ff 0%, #0984e3 50%, #00b894 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                
                .weather-container {{
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 30px;
                    padding: 40px;
                    max-width: 500px;
                    width: 100%;
                    text-align: center;
                    box-shadow: 0 30px 60px rgba(0,0,0,0.2);
                    backdrop-filter: blur(20px);
                    border: 1px solid rgba(255,255,255,0.3);
                    position: relative;
                    overflow: hidden;
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
                
                .location-header {{
                    margin-bottom: 30px;
                }}
                
                .location-name {{
                    font-size: 1.8rem;
                    font-weight: 700;
                    color: #2d3748;
                    margin-bottom: 5px;
                }}
                
                .update-time {{
                    color: #718096;
                    font-size: 0.9rem;
                }}
                
                .main-weather {{
                    margin-bottom: 40px;
                }}
                
                .weather-icon {{
                    font-size: 6rem;
                    margin-bottom: 20px;
                    animation: float 3s ease-in-out infinite;
                }}
                
                @keyframes float {{
                    0%, 100% {{ transform: translateY(0px); }}
                    50% {{ transform: translateY(-10px); }}
                }}
                
                .temperature {{
                    font-size: 4rem;
                    font-weight: 700;
                    background: linear-gradient(45deg, #74b9ff, #0984e3);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                }}
                
                .weather-condition {{
                    font-size: 1.3rem;
                    color: #4a5568;
                    font-weight: 500;
                    text-transform: capitalize;
                }}
                
                .weather-details {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-top: 30px;
                }}
                
                .detail-card {{
                    background: linear-gradient(135deg, rgba(116, 185, 255, 0.1), rgba(0, 184, 148, 0.1));
                    border-radius: 15px;
                    padding: 20px;
                    border: 1px solid rgba(116, 185, 255, 0.2);
                    transition: all 0.3s ease;
                }}
                
                .detail-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                }}
                
                .detail-icon {{
                    font-size: 2rem;
                    margin-bottom: 10px;
                }}
                
                .detail-label {{
                    color: #718096;
                    font-size: 0.9rem;
                    margin-bottom: 5px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                
                .detail-value {{
                    color: #2d3748;
                    font-size: 1.2rem;
                    font-weight: 600;
                }}
                
                .weather-advice {{
                    background: linear-gradient(135deg, #ffeaa7, #fdcb6e);
                    border-radius: 15px;
                    padding: 20px;
                    margin-top: 30px;
                    border: 1px solid rgba(253, 203, 110, 0.3);
                }}
                
                .advice-icon {{
                    font-size: 1.5rem;
                    margin-bottom: 10px;
                }}
                
                .advice-text {{
                    color: #8b4513;
                    font-weight: 500;
                    line-height: 1.4;
                }}
                
                @media (max-width: 480px) {{
                    .weather-container {{
                        padding: 30px 20px;
                    }}
                    
                    .temperature {{
                        font-size: 3rem;
                    }}
                    
                    .weather-icon {{
                        font-size: 4rem;
                    }}
                    
                    .weather-details {{
                        grid-template-columns: 1fr;
                        gap: 15px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="weather-container">
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
        </body>
        </html>
        """

        with open("weather.html", "w", encoding="utf-8") as file:
            file.write(html_content)
        
        return {"display": html_content}
        
    except Exception as e:
        print(f"Error obteniendo clima: {str(e)}")
        return {"error": str(e)}