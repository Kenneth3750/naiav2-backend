from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, List
import os
from apps.status.services import set_status
import time
import requests
from bs4 import BeautifulSoup
import json
import re

load_dotenv()

OPENAI_API_KEY = os.getenv("open_ai")
client = OpenAI(api_key=OPENAI_API_KEY)

VIDEO_MOMPOX = "https://video.wixstatic.com/video/669154_b8b37ed3a2cb4d818b4c054e812803f7/1080p/mp4/file.mp4"


def about_mompox_inteligente(user_id: int, status: str) -> Dict:
    """
    Explica qué es Mompox Inteligente con video y contenido visual.
    """
    set_status(user_id, status, 8)

    graph_html = f'''
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 100%; margin: 0 auto;">
        <div style="border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <video
                autoplay
                muted
                loop
                playsinline
                style="width: 100%; display: block;"
            >
                <source src="{VIDEO_MOMPOX}" type="video/mp4">
            </video>
        </div>
    </div>
    '''

    display_html = '''
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 100%; margin: 0 auto;">

        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1a3a5c 0%, #2e7d6e 100%); padding: 20px; border-radius: 12px; margin-bottom: 16px; text-align: center;">
            <h3 style="color: #ffffff; font-size: 20px; font-weight: 700; margin: 0 0 6px 0;">
                Mompox Inteligente
            </h3>
            <p style="color: #d4edda; font-size: 14px; margin: 0; font-style: italic;">
                Tradición + Innovación
            </p>
        </div>

        <!-- Qué es -->
        <div style="background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #1a1a1a; font-size: 15px; margin: 0 0 8px 0;">¿Qué es?</h4>
            <p style="color: #2d2d2d; font-size: 13px; line-height: 1.6; margin: 0;">
                Estrategia impulsada por la Gobernación de Bolívar y el Ministerio TIC para transformar a Santa Cruz de Mompox en un territorio inteligente, donde la tecnología se pone al servicio de las personas, la cultura y el medio ambiente.
            </p>
        </div>

        <!-- Premio -->
        <div style="background: #fffbeb; border: 1px solid #f59e0b; border-radius: 12px; padding: 16px; margin-bottom: 12px; text-align: center;">
            <span style="font-size: 28px;">🏆</span>
            <p style="color: #92400e; font-size: 13px; font-weight: 600; margin: 8px 0 4px 0;">
                Smart City Expo Awards 2025
            </p>
            <p style="color: #78350f; font-size: 12px; margin: 0;">
                Mejor Iniciativa del Sector Público
            </p>
        </div>

        <!-- Por qué Mompox -->
        <div style="background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #1a1a1a; font-size: 15px; margin: 0 0 8px 0;">¿Por qué Mompox?</h4>
            <p style="color: #2d2d2d; font-size: 13px; line-height: 1.6; margin: 0;">
                Patrimonio de la Humanidad por la UNESCO desde 1995, cuna de historia, tradiciones y riqueza cultural. Un laboratorio vivo para innovar con sentido social, sin romper con sus raíces. Territorio resiliente frente a desafíos de conectividad, riesgos ambientales y brechas digitales.
            </p>
        </div>

        <!-- Qué buscamos -->
        <div style="background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #1a1a1a; font-size: 15px; margin: 0 0 8px 0;">¿Qué buscamos?</h4>
            <p style="color: #2d2d2d; font-size: 13px; line-height: 1.6; margin: 0;">
                Acercar la tecnología a la vida cotidiana de momposinos y visitantes, conectando el pasado con el futuro. Una ciudad más participativa, conectada y sostenible, donde la innovación se traduce en bienestar colectivo.
            </p>
        </div>

        <!-- Diferenciadores -->
        <div style="background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #1a1a1a; font-size: 15px; margin: 0 0 10px 0;">¿Qué nos hace diferentes?</h4>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="background: #2e7d6e; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 13px;">🔄</span>
                    <span style="color: #2d2d2d; font-size: 13px;">Modelo replicable para otros territorios intermedios</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="background: #2e7d6e; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 13px;">🤝</span>
                    <span style="color: #2d2d2d; font-size: 13px;">Transformación digital con enfoque humano</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="background: #2e7d6e; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 13px;">🌿</span>
                    <span style="color: #2d2d2d; font-size: 13px;">Fusión de tradición, innovación y sostenibilidad</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="background: #2e7d6e; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 13px;">👥</span>
                    <span style="color: #2d2d2d; font-size: 13px;">Comunidad involucrada activamente en cada paso</span>
                </div>
            </div>
        </div>

        <!-- Aliados -->
        <div style="background: linear-gradient(135deg, #1a3a5c 0%, #2e7d6e 100%); border-radius: 12px; padding: 18px; text-align: center;">
            <h4 style="color: #ffffff; font-size: 15px; margin: 0 0 12px 0;">Aliados Clave</h4>
            <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 8px;">
                <span style="background: rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 14px; color: #e2e8f0; font-size: 12px;">Ministerio TIC</span>
                <span style="background: rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 14px; color: #e2e8f0; font-size: 12px;">Gobernación de Bolívar</span>
                <span style="background: rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 14px; color: #e2e8f0; font-size: 12px;">Alcaldía de Mompox</span>
                <span style="background: rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 14px; color: #e2e8f0; font-size: 12px;">Policía Nacional</span>
                <span style="background: rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 14px; color: #e2e8f0; font-size: 12px;">Ciudadanía momposina</span>
            </div>
        </div>

    </div>
    '''

    return {
        "graph": graph_html,
        "display": display_html,
        "content_for_answers": [
            "Mompox Inteligente es una estrategia de la Gobernación de Bolívar y el Ministerio TIC para transformar a Santa Cruz de Mompox en un territorio inteligente. Fue reconocido como la mejor iniciativa del sector público en los Smart City Expo Awards 2025."
        ]
    }


BLOG_SITEMAP_URL = "https://mompoxinteligente.bolivar.gov.co/blog-posts-sitemap.xml"
MOMPOX_BASE_URL = "https://mompoxinteligente.bolivar.gov.co"


def _fetch_post_urls_from_sitemap(limit: int = 10) -> List[str]:
    """
    Fetches blog post URLs from the sitemap.
    """
    resp = requests.get(BLOG_SITEMAP_URL, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "xml")
    urls_with_dates = []
    for url_tag in soup.find_all("url"):
        loc = url_tag.find("loc")
        lastmod = url_tag.find("lastmod")
        if loc:
            urls_with_dates.append({
                "url": loc.text.strip(),
                "lastmod": lastmod.text.strip() if lastmod else "1970-01-01"
            })
    urls_with_dates.sort(key=lambda x: x["lastmod"], reverse=True)
    return [item["url"] for item in urls_with_dates[:limit]]


def _scrape_post(url: str) -> Dict:
    """
    Scrapes a single blog post page extracting data from schema markup.
    """
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    post = {
        "title": "",
        "date": "",
        "author": "",
        "excerpt": "",
        "image": "",
        "url": url,
    }

    schema_tag = soup.find("script", type="application/ld+json")
    if schema_tag:
        try:
            data = json.loads(schema_tag.string)
            post["title"] = data.get("headline", "")
            post["date"] = data.get("datePublished", "")
            post["excerpt"] = data.get("description", "")
            author = data.get("author", {})
            if isinstance(author, dict):
                post["author"] = author.get("name", "")
            elif isinstance(author, list) and author:
                post["author"] = author[0].get("name", "")
            image = data.get("image", "")
            if isinstance(image, list) and image:
                post["image"] = image[0]
            elif isinstance(image, str):
                post["image"] = image
        except (json.JSONDecodeError, TypeError):
            pass

    if not post["title"]:
        og_title = soup.find("meta", property="og:title")
        if og_title:
            post["title"] = og_title.get("content", "")

    if not post["image"]:
        og_image = soup.find("meta", property="og:image")
        if og_image:
            post["image"] = og_image.get("content", "")

    if not post["excerpt"]:
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            post["excerpt"] = og_desc.get("content", "")

    return post


def _format_date_spanish(date_str: str) -> str:
    """
    Formats an ISO date string to Spanish readable format.
    """
    months = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
    }
    try:
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return f"{day} {months.get(month, '')} {year}"
    except Exception:
        pass
    return date_str


def get_mompox_news(user_id: int, status: str, limit: int = 6) -> Dict:
    """
    Fetches latest news from Mompox Inteligente blog.
    """
    set_status(user_id, status, 8)

    try:
        post_urls = _fetch_post_urls_from_sitemap(limit=limit)

        posts = []
        for url in post_urls:
            try:
                post = _scrape_post(url)
                if post["title"]:
                    posts.append(post)
            except Exception:
                continue

        if not posts:
            return {
                "display": '<div style="padding: 20px; text-align: center; color: #2d2d2d;">No se encontraron noticias disponibles.</div>',
                "content_for_answers": ["No se encontraron noticias de Mompox Inteligente en este momento."]
            }

        # Build news cards HTML
        cards_html = ""
        for post in posts:
            image_section = ""
            if post["image"]:
                image_section = f'''
                <div style="width: 100%; height: 160px; overflow: hidden; border-radius: 10px 10px 0 0;">
                    <img src="{post['image']}" alt="{post['title']}" style="width: 100%; height: 100%; object-fit: cover;" />
                </div>
                '''

            date_display = _format_date_spanish(post["date"]) if post["date"] else ""
            date_section = f'<span style="color: #6b7280; font-size: 11px;">{date_display}</span>' if date_display else ""

            excerpt = post["excerpt"]
            if len(excerpt) > 120:
                excerpt = excerpt[:120] + "..."

            cards_html += f'''
            <a href="{post['url']}" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block;">
                <div style="background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); transition: transform 0.2s ease, box-shadow 0.2s ease;"
                     onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(0,0,0,0.12)'"
                     onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0,0,0,0.06)'">
                    {image_section}
                    <div style="padding: 14px;">
                        {date_section}
                        <h4 style="color: #1a1a1a; font-size: 14px; font-weight: 600; margin: 6px 0 8px 0; line-height: 1.4;">
                            {post['title']}
                        </h4>
                        <p style="color: #4b5563; font-size: 12px; line-height: 1.5; margin: 0;">
                            {excerpt}
                        </p>
                        <div style="display: flex; align-items: center; margin-top: 10px; padding-top: 10px; border-top: 1px solid #f3f4f6;">
                            <span style="color: #2e7d6e; font-size: 12px; font-weight: 500;">Leer más</span>
                            <span style="color: #2e7d6e; margin-left: auto; font-size: 14px;">→</span>
                        </div>
                    </div>
                </div>
            </a>
            '''

        display_html = f'''
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 100%; margin: 0 auto;">

            <!-- Header -->
            <div style="background: linear-gradient(135deg, #1a3a5c 0%, #2e7d6e 100%); padding: 18px; border-radius: 12px; margin-bottom: 16px; text-align: center;">
                <h3 style="color: #ffffff; font-size: 18px; font-weight: 700; margin: 0 0 4px 0;">
                    Noticias de Mompox Inteligente
                </h3>
                <p style="color: #d4edda; font-size: 13px; margin: 0;">
                    Últimas novedades del proyecto
                </p>
            </div>

            <!-- News grid -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px;">
                {cards_html}
            </div>

        </div>
        '''

        # Build content for TTS
        titles_summary = ". ".join([p["title"] for p in posts[:3]])
        content_for_answers = [
            f"Estas son las últimas noticias de Mompox Inteligente. Entre las más recientes: {titles_summary}."
        ]

        return {
            "display": display_html,
            "content_for_answers": content_for_answers
        }

    except Exception as e:
        return {
            "display": f'<div style="padding: 20px; text-align: center; color: #dc2626;">Error al obtener noticias: {str(e)}</div>',
            "content_for_answers": ["Hubo un error al obtener las noticias de Mompox Inteligente. Por favor intenta de nuevo."]
        }
