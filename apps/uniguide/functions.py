from email.mime.text import MIMEText
from apps.status.services import set_status
import smtplib
import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from services.files import B2FileService
from datetime import datetime, timezone, timedelta
import json
load_dotenv()

DEFAULT_FROM_EMAIL=os.getenv("DEFAULT_FROM_EMAIL")
EMAIL_HOST_PASSWORD=os.getenv("EMAIL_HOST_PASSWORD")

openai_api_key = os.getenv("open_ai")

client = OpenAI(
    api_key= openai_api_key
)

def send_email(to_email: str, subject: str, body: str, status: str = "", user_id: int = 0) -> dict:
    """
    Sends an email using Gmail SMTP server.
    
    Args:
        to_email (str): The recipient's email address
        subject (str): The subject of the email
        body (str): The body content of the email
        status (str, optional): Status message for tracking. Defaults to "".
        user_id (int, optional): User ID for status updates. Defaults to 0.
        
    Returns:
        dict: A dictionary containing either success message or error details
        
    Raises:
        ValueError: If email credentials are not set or if required fields are empty
        SMTPAuthenticationError: If email authentication fails
        SMTPException: For other SMTP-related errors
    """
    # Validate required fields
    if not to_email or not subject or not body:
        return {"error": "Email, subject, and body are required"}
        
    # Basic email format validation
    if '@' not in to_email or '.' not in to_email:
        return {"error": "Invalid email format"}
    
    try:
        if user_id:
            set_status(user_id, status or "Sending email...", 2)

        if not all([DEFAULT_FROM_EMAIL, EMAIL_HOST_PASSWORD]):
            raise ValueError("DEFAULT_FROM_EMAIL and EMAIL_HOST_PASSWORD must be set in the environment variables")
        
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = DEFAULT_FROM_EMAIL
        msg["To"] = to_email

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


def create_rag():
    """
    Save documents from B2 cloud storage into a vector database
    """
    try:
        # Get documents from B2
        b2_service = B2FileService()
        document_bytes_list = b2_service.download_uniguide_documents()
        
        if not document_bytes_list:
            raise ValueError("No documents found in B2 storage.")
            
        all_documents = []
        
        # Process each document from B2
        for i, file_info in enumerate(document_bytes_list):
            # Extract file bytes and filename from the returned data
            if isinstance(file_info, dict) and 'bytes' in file_info and 'filename' in file_info:
                file_bytes = file_info['bytes']
                file_name = file_info['filename']
            else:
                # If not in expected format, use the old behavior
                file_bytes = file_info
                file_name = ""
            
            # Determine appropriate file extension for temp file
            if file_name and file_name.lower().endswith('.docx'):
                suffix = '.docx'
            elif file_name and file_name.lower().endswith('.txt'):
                suffix = '.txt'
            else:
                suffix = '.pdf'  # Default to PDF
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_path = temp_file.name
                temp_file.write(file_bytes)
            
            try:
                if suffix == '.pdf':
                    # Process as PDF
                    loader = PyPDFLoader(temp_path)
                    docs = loader.load()
                    all_documents.extend(docs)
                    print(f"Processed PDF document #{i+1}")
                elif suffix == '.docx':
                    # Process as DOCX
                    loader = Docx2txtLoader(temp_path)
                    docs = loader.load()
                    all_documents.extend(docs)
                    print(f"Processed DOCX document #{i+1}")
                else:
                    # Process as text
                    loader = TextLoader(temp_path)
                    docs = loader.load()
                    all_documents.extend(docs)
                    print(f"Processed TXT document #{i+1}")
            except Exception as e:
                print(f"Failed to process document #{i+1}: {str(e)}")
                try:
                    # Fallback: try as plain text if original processing fails
                    loader = TextLoader(temp_path, encoding='utf-8', autodetect_encoding=True)
                    docs = loader.load()
                    all_documents.extend(docs)
                    print(f"Processed document #{i+1} as fallback text")
                except Exception as inner_e:
                    print(f"All processing methods failed for document #{i+1}: {str(inner_e)}")
            
            # Clean up temp file
            os.unlink(temp_path)

        if not all_documents:
            raise ValueError("No documents could be successfully processed.")
        
        # Create embeddings and store in Chroma
        persist_dir = "./chromadb_uniguide"
        os.makedirs(persist_dir, exist_ok=True)

        embeddings = OpenAIEmbeddings(
            api_key=openai_api_key,
            model="text-embedding-3-large"
        )

        # Create text splitter
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=1000,
            chunk_overlap=200
        )

        # Split documents into chunks
        chunks = text_splitter.split_documents(all_documents)

        # Create and persist vector store
        vector_store = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings
        )
        
        vector_store.add_documents(chunks)
        vector_store.persist()

        return f"Successfully processed {len(document_bytes_list)} documents from B2 storage"

    except Exception as e:
        print(f"Error processing documents: {str(e)}")
        return {"error": str(e)}

def query_university_rag(user_id: int, question: str, k: int = 3, status:str = "") -> dict:
    """
    Query the information stored in the vector store and generate a response.
    """
    try:
        set_status(user_id, status, 2)
        persist_dir = "./chromadb_uniguide"

        if not os.path.exists(persist_dir):
            create_rag()
            raise FileNotFoundError("No documents have been indexed yet.")

        embeddings = OpenAIEmbeddings(
            api_key=openai_api_key,
            model="text-embedding-3-large"
        )
        
        vector_store = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings
        )

        results = vector_store.similarity_search(question, k=k)

        if not results:
            return {"response": "No relevant documents found for your question."}
        
        rag_results = []
        for i, doc in enumerate(results, 1):
            rag_results.append(f"Document {i}: {doc.page_content}")

        result_text = "\n\n".join(rag_results)

        print(f"RAG results: {result_text}")
        return {"resolved_rag": result_text}

    except Exception as e:
        print(f"Error retrieving documents: {str(e)}")
        return {"error": str(e)}


def get_current_month_uni_calendar(user_id: int, status: str) -> str:
    """ Scrape the current month's events from the Universidad del Norte calendar.
    Returns:
        str: Formatted string of events with their names and dates.
    """
    driver = None
    try: 
        set_status(user_id, status, 2)
        url = 'https://outlook.office365.com/calendar/published/82dc57e4303e46d490fec6d6df9e41c6@uninorte.edu.co/ca0af55ded00488eb89bac6079a9675a7730392440685253853/calendar.html'


        gmt_minus_5 = timezone(timedelta(hours=-5))

        current_bogota_time = datetime.now(gmt_minus_5)
        current_day = current_bogota_time.strftime('%Y-%m-%d')
        print(f"Current day in GMT-5: {current_day}")

        # Configuración más robusta de Chrome
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--remote-debugging-port=0') 
        options.add_argument('--disable-logging')
        options.add_argument('--disable-gpu-logging')
        

        driver = webdriver.Chrome(options=options)
        

        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)

        driver.get(url)
        time.sleep(2)  

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        divs = soup.find_all('div', role='button')
        print(f"Found {len(divs)} events.")

        formatted_events = ""
        for div in divs:
            if div.get('aria-label') is not None:
                title = div.get("aria-label").strip().replace('\n', ' ').split(",")
                formatted_events += f"EVENT NAME: {title[0].strip()}, DATE: {title[2].strip()}\n"
            elif div.get('title') is not None:
                title = div.get("title").strip().replace('\n', ' ').split(",")
                formatted_events += f"EVENT NAME: {title[0].strip()}, DATE: {title[1].strip()}\n"
            else:
                print("No title or aria-label found for a div.")

        print("number of formatted events:", len(formatted_events.split('\n')) - 1)
        formatted_events += f"\n\nCurrent day in GMT-5: {current_day}, Use this date to compare with the events above.\n"
        
        return {"current_month_calendar": formatted_events}
    
    except Exception as e:
        print(f"Error scraping calendar: {str(e)}")
        return {"error": str(e)}
    
    finally:
        if driver is not None:
            try:
                driver.quit()
                print("WebDriver cerrado correctamente")
            except Exception as cleanup_error:
                print(f"Error cerrando WebDriver: {cleanup_error}")
                try:
                    import psutil
                    import os
                    
                    # Buscar y matar procesos de Chrome/ChromeDriver
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            if 'chrome' in proc.info['name'].lower() or 'chromedriver' in proc.info['name'].lower():
                                proc.kill()
                                print(f"Proceso {proc.info['name']} (PID: {proc.info['pid']}) terminado forzadamente")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except ImportError:
                    print("psutil no disponible para cleanup manual")
                except Exception as manual_cleanup_error:
                    print(f"Error en cleanup manual: {manual_cleanup_error}")

def get_virtual_campus_tour(area_filter: str = None, place_name: str = None, language: str = "Spanish", user_id: int = 0, status: str = "") -> dict:
    """
    Generates an interactive virtual campus tour with intelligent place matching.
    
    Args:
        area_filter (str): Filter by category ("academic", "recreational", "services") or None for all
        place_name (str): Specific place name or None for category/all places
        language (str): Language for the tour interface
        user_id (int): User ID for status tracking
        status (str): Status message for tracking
        
    Returns:
        dict: Dictionary with HTML tour interface split between "display" and "graph"
    """
    try:
        set_status(user_id, status, 2)  # 2 = uniguide role
        
        # Get tour data from B2
        b2_service = B2FileService()
        tour_data = b2_service.download_virtual_tour_data()
        
        if not tour_data or not tour_data.get('tour_info'):
            return {"error": "No se pudo cargar la información del tour virtual"}
        
        tour_info = tour_data['tour_info']
        available_images = tour_data.get('images', {})
        is_spanish = language.lower().startswith('es') or 'spanish' in language.lower()
        
        # Use intelligent matching if place_name is provided
        if place_name:
            print(f"Using intelligent matching for: {place_name}")
            match_result = intelligent_place_matcher(place_name, tour_info, language)
            
            if match_result.get("matches") and len(match_result["matches"]) > 0:
                # Found specific place(s)
                best_match = match_result["matches"][0]
                matched_place_key = best_match["place_key"]
                
                # Find the place data
                for category_key, category_data in tour_info.get('categories', {}).items():
                    if matched_place_key in category_data.get('places', {}):
                        place_data = category_data['places'][matched_place_key]
                        place_data['category'] = category_data.get('name', category_key)
                        place_data['place_key'] = matched_place_key
                        
                        # Generate single place view
                        display_content, graph_content = generate_single_place_html_split(
                            place_data, available_images, b2_service, is_spanish
                        )
                        
                        return {
                            "display": display_content,
                            "graph": graph_content,
                            "match_info": {
                                "found": True,
                                "place": matched_place_key,
                                "confidence": best_match.get("confidence", 0),
                                "interpretation": match_result.get("interpretation", "")
                            }
                        }
            
            elif match_result.get("suggested_category"):
                # Redirect to category view
                area_filter = match_result["suggested_category"]
                place_name = None  # Clear place_name to show category
            
            else:
                # No matches found, show general tour with search info
                area_filter = None
                place_name = None
        
        # Filter data based on area_filter or show all categories
        categories_to_show = []
        
        if area_filter:
            # Filter by specific category
            if area_filter in tour_info.get('categories', {}):
                category_data = tour_info['categories'][area_filter]
                categories_to_show.append({
                    'key': area_filter,
                    'name': category_data.get('name', area_filter),
                    'description': category_data.get('description', ''),
                    'places': category_data.get('places', {})
                })
            else:
                # Invalid category, show all
                for category_key, category_data in tour_info.get('categories', {}).items():
                    categories_to_show.append({
                        'key': category_key,
                        'name': category_data.get('name', category_key),
                        'description': category_data.get('description', ''),
                        'places': category_data.get('places', {})
                    })
        else:
            # Show all categories
            for category_key, category_data in tour_info.get('categories', {}).items():
                categories_to_show.append({
                    'key': category_key,
                    'name': category_data.get('name', category_key),
                    'description': category_data.get('description', ''),
                    'places': category_data.get('places', {})
                })
        
        # Generate overview/category view
        display_content, graph_content = generate_tour_overview_html_split(
            categories_to_show, available_images, b2_service, is_spanish
        )
        
        result = {
            "display": display_content,
            "graph": graph_content
        }
        
        # Add search info if there was a search attempt
        if place_name:
            result["match_info"] = {
                "found": False,
                "search_term": place_name,
                "interpretation": match_result.get("interpretation", "") if 'match_result' in locals() else "",
                "fallback": "overview"
            }
        
        return result
        
    except Exception as e:
        print(f"Error generating virtual campus tour: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

def generate_single_place_html_split(place_data: dict, available_images: dict, b2_service: B2FileService, is_spanish: bool = True) -> tuple:
    """Generate split HTML for a single place: (info_content, image_carousel)"""
    
    place_name = place_data.get('name', 'Lugar')
    description = place_data.get('description', '')
    services = place_data.get('services', [])
    contact = place_data.get('contact', {})
    hours = place_data.get('hours', {})
    highlights = place_data.get('highlights', [])
    images = place_data.get('images', [])
    
    # Generate information content (display)
    contact_html = ""
    if contact:
        contact_title = "Información de Contacto" if is_spanish else "Contact Information"
        contact_html = f'<h3 class="section-title">{contact_title}</h3><div class="contact-grid">'
        
        if contact.get('email'):
            email_label = "Correo electrónico" if is_spanish else "Email"
            contact_html += f'''
            <div class="contact-item">
                <span class="contact-icon">📧</span>
                <div>
                    <div class="contact-label">{email_label}</div>
                    <div class="contact-value">{contact['email']}</div>
                </div>
            </div>
            '''
        
        if contact.get('phone'):
            phone_label = "Teléfono" if is_spanish else "Phone"
            contact_html += f'''
            <div class="contact-item">
                <span class="contact-icon">📞</span>
                <div>
                    <div class="contact-label">{phone_label}</div>
                    <div class="contact-value">{contact['phone']}</div>
                </div>
            </div>
            '''
        
        if contact.get('website'):
            website_label = "Sitio web" if is_spanish else "Website"
            contact_html += f'''
            <div class="contact-item">
                <span class="contact-icon">🌐</span>
                <div>
                    <div class="contact-label">{website_label}</div>
                    <div class="contact-value"><a href="{contact['website']}" target="_blank">Visitar sitio web</a></div>
                </div>
            </div>
            '''
        
        contact_html += '</div>'
    
    # Generate services
    services_html = ""
    if services:
        services_title = "Servicios Disponibles" if is_spanish else "Available Services"
        services_html = f'<h3 class="section-title">{services_title}</h3><div class="services-grid">'
        for service in services:
            services_html += f'<div class="service-item">✓ {service}</div>'
        services_html += '</div>'
    
    # Generate hours
    hours_html = ""
    if hours:
        hours_title = "Horarios de Atención" if is_spanish else "Operating Hours"
        hours_html = f'<h3 class="section-title">{hours_title}</h3><div class="hours-grid">'
        for hour_type, hour_info in hours.items():
            hour_type_display = hour_type.replace('_', ' ').title()
            hours_html += f'''
            <div class="hours-item">
                <div class="hours-type">{hour_type_display}</div>
                <div class="hours-time">{hour_info}</div>
            </div>
            '''
        hours_html += '</div>'
    
    # Generate highlights
    highlights_html = ""
    if highlights:
        highlights_title = "Puntos Destacados" if is_spanish else "Highlights"
        highlights_html = f'<h3 class="section-title">{highlights_title}</h3><div class="highlights-grid">'
        for highlight in highlights:
            highlights_html += f'<div class="highlight-item">⭐ {highlight}</div>'
        highlights_html += '</div>'
    
    # Information content (display)
    display_content = f"""
    <div class="tour-info-container">
        <div class="tour-header">
            <h1 class="place-title">🏛️ {place_name}</h1>
            <p class="place-description">{description}</p>
        </div>
        
        <div class="tour-content">
            {contact_html}
            {services_html}
            {hours_html}
            {highlights_html}
        </div>
    </div>
    
    {get_info_styles()}
    """
    
    # Generate image carousel (graph)
    image_carousel = ""
    if images:
        carousel_title = f"Galería - {place_name}" if is_spanish else f"Gallery - {place_name}"
        image_carousel = f"""
        <div class="image-carousel-container">
            <div class="carousel-header">
                <h2 class="carousel-title">📸 {carousel_title}</h2>
            </div>
            <div class="image-carousel">
        """
        
        for i, img_name in enumerate(images):
            if img_name in available_images:
                img_url = b2_service.get_virtual_tour_image_url(img_name)
                if img_url:
                    active_class = "active" if i == 0 else ""
                    image_carousel += f'''
                    <div class="carousel-slide {active_class}">
                        <img src="{img_url}" alt="{place_name} - Imagen {i+1}" class="carousel-image">
                        <div class="slide-caption">
                            <span class="slide-number">{i+1} / {len(images)}</span>
                        </div>
                    </div>
                    '''
        
        # Add navigation controls
        if len(images) > 1:
            image_carousel += '''
                <button class="carousel-btn prev-btn" onclick="changeSlide(-1)">‹</button>
                <button class="carousel-btn next-btn" onclick="changeSlide(1)">›</button>
                <div class="carousel-dots">
            '''
            for i in range(len(images)):
                active_dot = "active" if i == 0 else ""
                image_carousel += f'<span class="dot {active_dot}" onclick="currentSlide({i+1})"></span>'
            image_carousel += '</div>'
        
        image_carousel += f'''
            </div>
        </div>
        
        {get_carousel_styles()}
        
        <script>
        let slideIndex = 1;
        
        function changeSlide(n) {{
            showSlide(slideIndex += n);
        }}
        
        function currentSlide(n) {{
            showSlide(slideIndex = n);
        }}
        
        function showSlide(n) {{
            let slides = document.getElementsByClassName("carousel-slide");
            let dots = document.getElementsByClassName("dot");
            if (n > slides.length) {{ slideIndex = 1; }}
            if (n < 1) {{ slideIndex = slides.length; }}
            
            for (let i = 0; i < slides.length; i++) {{
                slides[i].classList.remove("active");
            }}
            for (let i = 0; i < dots.length; i++) {{
                dots[i].classList.remove("active");
            }}
            
            if (slides[slideIndex-1]) slides[slideIndex-1].classList.add("active");
            if (dots[slideIndex-1]) dots[slideIndex-1].classList.add("active");
        }}
        </script>
        '''
    
    return display_content, image_carousel


def generate_tour_overview_html_split(categories: list, available_images: dict, b2_service: B2FileService, is_spanish: bool = True) -> tuple:
    """Generate split HTML for tour overview: (info_content, campus_carousel)"""
    
    title = "Tour Virtual - Universidad del Norte" if is_spanish else "Virtual Tour - Universidad del Norte"
    
    # Information content (display) - Esta parte se mantiene igual
    places_html = ""
    for category in categories:
        category_name = category.get('name', '')
        category_desc = category.get('description', '')
        places = category.get('places', {})
        
        if places:
            places_html += f'''
            <div class="category-section">
                <h2 class="category-title">{category_name}</h2>
                <p class="category-description">{category_desc}</p>
                <div class="places-list">
            '''
            
            for place_key, place_data in places.items():
                place_name = place_data.get('name', place_key)
                place_desc = place_data.get('description', '')[:150] + "..."
                services = place_data.get('services', [])
                
                services_preview = ""
                if services:
                    services_preview = f"<div class='services-preview'>Servicios: {', '.join(services[:3])}</div>"
                
                places_html += f'''
                <div class="place-overview-card">
                    <h3 class="place-name">{place_name}</h3>
                    <p class="place-description">{place_desc}</p>
                    {services_preview}
                </div>
                '''
            
            places_html += '</div></div>'
    
    display_content = f"""
    <div class="tour-overview-container">
        <div class="tour-header">
            <h1 class="main-title">🎓 {title}</h1>
            <p class="tour-intro">{"Explora las principales instalaciones de nuestro campus" if is_spanish else "Explore the main facilities of our campus"}</p>
        </div>
        
        {places_html}
    </div>
    
    {get_info_styles()}
    """
    
    # NUEVA IMPLEMENTACIÓN: Carrusel optimizado con todas las imágenes del campus
    carousel_title = "Galería del Campus" if is_spanish else "Campus Gallery"
    
    # Recopilar TODAS las imágenes de todos los lugares
    all_images = []
    for category in categories:
        places = category.get('places', {})
        for place_key, place_data in places.items():
            place_name = place_data.get('name', place_key)
            images = place_data.get('images', [])
            
            # Agregar todas las imágenes de este lugar
            for img_name in images:
                if img_name in available_images:
                    img_url = b2_service.get_virtual_tour_image_url(img_name)
                    if img_url:
                        all_images.append({
                            'url': img_url,
                            'name': img_name,
                            'place': place_name,
                            'alt': f"{place_name} - {img_name}"
                        })
    
    # Generar carrusel con las mismas dimensiones que el que funciona bien
    campus_carousel = ""
    if all_images:
        campus_carousel = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{carousel_title}</title>
            <style>
                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
                    background-color: #f8fafc;
                    color: #1e293b;
                }}
                
                .carousel-container {{
                    width: 100%;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: white;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                }}
                
                .carousel-title {{
                    font-size: 1.25rem;
                    font-weight: 600;
                    margin-bottom: 16px;
                    color: #334155;
                    display: flex;
                    align-items: center;
                }}
                
                .carousel-title svg {{
                    margin-right: 8px;
                }}
                
                .carousel {{
                    position: relative;
                    overflow: hidden;
                    border-radius: 8px;
                    height: 400px;
                    background-color: #f1f5f9;
                }}
                
                .carousel-inner {{
                    display: flex;
                    transition: transform 0.5s ease;
                    height: 100%;
                }}
                
                .carousel-item {{
                    min-width: 100%;
                    height: 100%;
                    position: relative;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                
                .carousel-image {{
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    border-radius: 8px;
                }}
                
                .place-title {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    background: linear-gradient(to bottom, rgba(0,0,0,0.8), transparent);
                    color: white;
                    padding: 16px 20px 30px;
                    text-align: center;
                    z-index: 5;
                }}
                
                .place-name {{
                    font-size: 1.1rem;
                    font-weight: 600;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.5);
                }}
                
                .image-counter {{
                    position: absolute;
                    bottom: 12px;
                    right: 12px;
                    background: rgba(0,0,0,0.7);
                    color: white;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 0.75rem;
                    font-weight: 500;
                    z-index: 5;
                }}
                
                .carousel-controls {{
                    position: absolute;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 40px;
                    height: 40px;
                    background: rgba(255, 255, 255, 0.9);
                    border: none;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s ease;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    z-index: 10;
                }}
                
                .carousel-control:hover {{
                    background-color: white;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                }}
                
                .carousel-control.prev {{
                    left: 12px;
                }}
                
                .carousel-control.next {{
                    right: 12px;
                }}
                
                .carousel-indicators {{
                    display: flex;
                    justify-content: center;
                    gap: 6px;
                    margin-top: 12px;
                    flex-wrap: wrap;
                    max-height: 60px;
                    overflow-y: auto;
                }}
                
                .carousel-indicator {{
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background-color: #cbd5e1;
                    cursor: pointer;
                    transition: background-color 0.2s ease;
                    margin: 2px;
                }}
                
                .carousel-indicator.active {{
                    background-color: #3b82f6;
                }}
                
                .carousel-attribution {{
                    margin-top: 12px;
                    font-size: 0.75rem;
                    color: #94a3b8;
                    text-align: center;
                }}
                
                @media (max-width: 640px) {{
                    .carousel-container {{
                        padding: 12px;
                    }}
                    
                    .carousel {{
                        height: 300px;
                    }}
                    
                    .carousel-indicators {{
                        gap: 4px;
                        max-height: 40px;
                    }}
                    
                    .carousel-indicator {{
                        width: 6px;
                        height: 6px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="carousel-container">
                <h2 class="carousel-title">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                    {carousel_title}
                </h2>
                <div class="carousel" id="campusCarousel">
                    <div class="carousel-inner" id="carouselInner">
        """
        
        # Generar HTML para cada imagen
        for i, img_data in enumerate(all_images):
            campus_carousel += f"""
                        <div class="carousel-item" id="slide{i}">
                            <img src="{img_data['url']}" alt="{img_data['alt']}" class="carousel-image" />
                            <div class="place-title">
                                <div class="place-name">{img_data['place']}</div>
                            </div>
                            <div class="image-counter">{i+1} / {len(all_images)}</div>
                        </div>
            """
        
        # Añadir controles y indicadores
        campus_carousel += """
                    </div>
                    <button class="carousel-controls carousel-control prev" id="prevButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                    </button>
                    <button class="carousel-controls carousel-control next" id="nextButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                    </button>
                </div>
                <div class="carousel-indicators" id="indicators">
        """
        
        # Generar indicadores (limitados si hay muchas imágenes)
        for i in range(len(all_images)):
            active = "active" if i == 0 else ""
            campus_carousel += f'<div class="carousel-indicator {active}" data-slide="{i}"></div>'
        
        # JavaScript para el carrusel
        campus_carousel += f"""
                </div>
                <div class="carousel-attribution">
                    Campus Universidad del Norte - {len(all_images)} imágenes
                </div>
            </div>
            
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    const carousel = document.getElementById('campusCarousel');
                    const inner = document.getElementById('carouselInner');
                    const items = document.querySelectorAll('.carousel-item');
                    const indicators = document.querySelectorAll('.carousel-indicator');
                    const prevButton = document.getElementById('prevButton');
                    const nextButton = document.getElementById('nextButton');
                    
                    let currentSlide = 0;
                    const totalSlides = items.length;
                    
                    function showSlide(index) {{
                        if (index >= totalSlides) {{
                            currentSlide = 0;
                        }} else if (index < 0) {{
                            currentSlide = totalSlides - 1;
                        }} else {{
                            currentSlide = index;
                        }}
                        
                        const offset = -currentSlide * 100;
                        inner.style.transform = `translateX(${{offset}}%)`;
                        
                        // Update indicators
                        indicators.forEach((indicator, i) => {{
                            indicator.classList.toggle('active', i === currentSlide);
                        }});
                    }}
                    
                    // Navigation buttons
                    prevButton.addEventListener('click', () => {{
                        showSlide(currentSlide - 1);
                    }});
                    
                    nextButton.addEventListener('click', () => {{
                        showSlide(currentSlide + 1);
                    }});
                    
                    // Indicator clicks
                    indicators.forEach((indicator, i) => {{
                        indicator.addEventListener('click', () => {{
                            showSlide(i);
                        }});
                    }});
                    
                    // Auto-advance carousel every 4 seconds (más rápido porque hay más imágenes)
                    let autoplayInterval = setInterval(() => {{
                        showSlide(currentSlide + 1);
                    }}, 4000);
                    
                    // Pause autoplay when hovering over carousel
                    carousel.addEventListener('mouseenter', () => {{
                        clearInterval(autoplayInterval);
                    }});
                    
                    // Resume autoplay when mouse leaves
                    carousel.addEventListener('mouseleave', () => {{
                        autoplayInterval = setInterval(() => {{
                            showSlide(currentSlide + 1);
                        }}, 4000);
                    }});
                    
                    // Handle keyboard navigation
                    document.addEventListener('keydown', (e) => {{
                        if (e.key === 'ArrowLeft') {{
                            showSlide(currentSlide - 1);
                        }} else if (e.key === 'ArrowRight') {{
                            showSlide(currentSlide + 1);
                        }}
                    }});
                    
                    // Initialize first slide
                    showSlide(0);
                }});
            </script>
        </body>
        </html>
        """
    else:
        # Fallback si no hay imágenes
        campus_carousel = f"""
        <div style="text-align: center; padding: 40px; color: #64748b;">
            <p>No hay imágenes disponibles para mostrar</p>
        </div>
        """
    
    return display_content, campus_carousel

def get_info_styles() -> str:
    """Return CSS styles for information content"""
    return """
    <style>
        .tour-info-container, .tour-overview-container {
            max-width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            padding: 20px;
            color: #1e293b;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
        }
        
        .tour-header {
            text-align: center;
            margin-bottom: 25px;
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 12px;
        }
        
        .main-title, .place-title {
            font-size: 2rem;
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 15px;
        }
        
        .tour-intro, .place-description {
            font-size: 1rem;
            color: #4a5568;
            line-height: 1.6;
        }
        
        .tour-content {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 25px;
        }
        
        .section-title {
            font-size: 1.3rem;
            color: #2d3748;
            margin: 20px 0 15px 0;
            border-bottom: 2px solid #667eea;
            padding-bottom: 8px;
        }
        
        .contact-grid, .services-grid, .hours-grid, .highlights-grid {
            display: grid;
            gap: 12px;
            margin-bottom: 20px;
        }
        
        .contact-item, .service-item, .highlight-item, .hours-item {
            padding: 12px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .contact-item {
            display: flex;
            align-items: center;
            gap: 12px;
            background: #f7fafc;
        }
        
        .service-item, .highlight-item {
            background: #f0fff4;
            border-left-color: #48bb78;
        }
        
        .hours-item {
            display: flex;
            justify-content: space-between;
            background: #fff5f5;
            border-left-color: #f56565;
        }
        
        .category-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .category-title {
            font-size: 1.5rem;
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .places-list {
            display: grid;
            gap: 15px;
        }
        
        .place-overview-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .place-name {
            font-size: 1.2rem;
            color: #2d3748;
            margin-bottom: 8px;
        }
        
        @media (max-width: 768px) {
            .tour-info-container, .tour-overview-container {
                padding: 15px;
            }
            .main-title, .place-title {
                font-size: 1.6rem;
            }
        }
    </style>
    """

def get_carousel_styles() -> str:
    """Return CSS styles for image carousel and gallery"""
    return """
<style>
.image-carousel-container {
    max-width: 100%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 20px;
    padding: 25px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
    box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}

.carousel-header {
    text-align: center;
    margin-bottom: 25px;
}

.carousel-title {
    font-size: 2rem;
    font-weight: 800;
    color: white;
    text-shadow: 0 3px 6px rgba(0,0,0,0.4);
    background: linear-gradient(45deg, #fff, #f0f8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.image-carousel {
    position: relative;
    background: rgba(255, 255, 255, 0.98);
    border-radius: 16px;
    overflow: hidden;
    height: 450px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.1);
    backdrop-filter: blur(10px);
}

.carousel-slide {
    position: absolute;
    width: 100%;
    height: 100%;
    opacity: 0.7;
    transition: all 0.8s cubic-bezier(0.4, 0.0, 0.2, 1);
}

.carousel-slide.active {
    opacity: 1;
}

.carousel-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.8s cubic-bezier(0.4, 0.0, 0.2, 1);
    filter: brightness(0.9) saturate(1.1);
}

.slide-caption {
    position: absolute;
    bottom: 20px;
    left: 20px;
    right: 20px;
    background: linear-gradient(135deg, rgba(0,0,0,0.8), rgba(0,0,0,0.6));
    color: white;
    padding: 15px 20px;
    border-radius: 12px;
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255,255,255,0.2);
    transform: translateY(100px);
    opacity: 0;
    transition: all 0.6s cubic-bezier(0.4, 0.0, 0.2, 1);
}

.carousel-slide.active .slide-caption {
    transform: translateY(0);
    opacity: 1;
}

.slide-number {
    font-size: 0.9rem;
    font-weight: 600;
    letter-spacing: 1px;
}

.carousel-btn {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7));
    color: #333;
    border: none;
    width: 50px;
    height: 50px;
    cursor: pointer;
    font-size: 20px;
    border-radius: 50%;
    transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.3);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    z-index: 10;
}

.carousel-btn:hover {
    background: linear-gradient(135deg, #ffffff, #f8f9fa);
    transform: translateY(-50%) scale(1.1);
    box-shadow: 0 12px 35px rgba(0,0,0,0.25);
}

.carousel-btn:active {
    transform: translateY(-50%) scale(0.95);
}

.prev-btn {
    left: 20px;
}

.next-btn {
    right: 20px;
}

.carousel-dots {
    position: absolute;
    bottom: 30px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 10px;
    background: rgba(0,0,0,0.4);
    padding: 10px 15px;
    border-radius: 25px;
    backdrop-filter: blur(10px);
}

.dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: rgba(255,255,255,0.5);
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
    position: relative;
}

.dot:hover {
    background: rgba(255,255,255,0.8);
    transform: scale(1.2);
}

.dot.active {
    background: linear-gradient(135deg, #667eea, #764ba2);
    transform: scale(1.3);
    box-shadow: 0 0 20px rgba(102, 126, 234, 0.6);
}

.dot.active::after {
    content: '';
    position: absolute;
    top: -3px;
    left: -3px;
    right: -3px;
    bottom: -3px;
    border: 2px solid rgba(255,255,255,0.6);
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.1); }
}

.carousel-progress-container {
    position: absolute;
    top: 15px;
    left: 20px;
    right: 20px;
    display: flex;
    align-items: center;
    gap: 15px;
    z-index: 10;
}

.carousel-progress-bar {
    flex: 1;
    height: 4px;
    background: rgba(255,255,255,0.3);
    border-radius: 2px;
    overflow: hidden;
}

.carousel-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea, #764ba2);
    border-radius: 2px;
    transition: width 0.3s ease;
    box-shadow: 0 0 10px rgba(102, 126, 234, 0.6);
}

.carousel-counter {
    color: white;
    font-size: 0.9rem;
    font-weight: 600;
    background: rgba(0,0,0,0.4);
    padding: 5px 12px;
    border-radius: 15px;
    backdrop-filter: blur(10px);
    text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

/* Efectos de loading elegantes */
@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

.carousel-slide::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    transition: left 0.8s cubic-bezier(0.4, 0.0, 0.2, 1);
    z-index: 1;
}

.carousel-slide.active::before {
    left: 100%;
}

/* Responsive */
@media (max-width: 768px) {
    .image-carousel {
        height: 300px;
    }
    
    .carousel-btn {
        width: 40px;
        height: 40px;
        font-size: 16px;
    }
    
    .prev-btn {
        left: 10px;
    }
    
    .next-btn {
        right: 10px;
    }
    
    .carousel-title {
        font-size: 1.5rem;
    }
}
</style>
 <script>
class ModernCarousel {
    constructor() {
        this.currentSlide = 0;
        this.slides = [];
        this.totalSlides = 0;
        this.autoSlideInterval = null;
        this.touchStartX = 0;
        this.touchEndX = 0;
        this.isTransitioning = false;
        
        this.init();
    }
    
    init() {
        this.slides = document.querySelectorAll('.carousel-slide');
        this.totalSlides = this.slides.length;
        
        if (this.totalSlides <= 1) return;
        
        this.setupSlides();
        this.createProgressBar();
        this.addEventListeners();
        this.startAutoSlide();
        this.showSlide(0, false);
    }
    
    setupSlides() {
        this.slides.forEach((slide, index) => {
            slide.style.transform = `translateX(${index * 100}%)`;
            slide.style.transition = 'all 0.8s cubic-bezier(0.4, 0.0, 0.2, 1)';
        });
    }
    
    createProgressBar() {
        const progressContainer = document.createElement('div');
        progressContainer.className = 'carousel-progress-container';
        progressContainer.innerHTML = `
            <div class="carousel-progress-bar">
                <div class="carousel-progress-fill"></div>
            </div>
            <span class="carousel-counter">${this.currentSlide + 1} / ${this.totalSlides}</span>
        `;
        
        const carousel = document.querySelector('.image-carousel');
        carousel.appendChild(progressContainer);
    }
    
    showSlide(index, animate = true) {
        if (this.isTransitioning && animate) return;
        if (animate) this.isTransitioning = true;
        
        this.currentSlide = index;
        if (this.currentSlide >= this.totalSlides) this.currentSlide = 0;
        if (this.currentSlide < 0) this.currentSlide = this.totalSlides - 1;
        
        // Actualizar slides con efectos parallax
        this.slides.forEach((slide, i) => {
            const offset = (i - this.currentSlide) * 100;
            const img = slide.querySelector('.carousel-image');
            
            if (animate) {
                slide.style.transform = `translateX(${offset}%)`;
                
                // Efecto parallax en las imágenes
                if (i === this.currentSlide) {
                    img.style.transform = 'scale(1.05)';
                    slide.style.opacity = '1';
                    slide.style.filter = 'brightness(1) saturate(1.1)';
                } else {
                    img.style.transform = 'scale(1)';
                    slide.style.opacity = '0.7';
                    slide.style.filter = 'brightness(0.8) saturate(0.8)';
                }
            }
        });
        
        this.updateDots();
        this.updateProgressBar();
        this.updateCounter();
        
        if (animate) {
            setTimeout(() => {
                this.isTransitioning = false;
            }, 800);
        }
    }
    
    updateDots() {
        const dots = document.querySelectorAll('.dot');
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === this.currentSlide);
        });
    }
    
    updateProgressBar() {
        const progressFill = document.querySelector('.carousel-progress-fill');
        if (progressFill) {
            const percentage = ((this.currentSlide + 1) / this.totalSlides) * 100;
            progressFill.style.width = `${percentage}%`;
        }
    }
    
    updateCounter() {
        const counter = document.querySelector('.carousel-counter');
        if (counter) {
            counter.textContent = `${this.currentSlide + 1} / ${this.totalSlides}`;
        }
    }
    
    nextSlide() {
        this.showSlide(this.currentSlide + 1);
    }
    
    prevSlide() {
        this.showSlide(this.currentSlide - 1);
    }
    
    goToSlide(index) {
        this.showSlide(index);
    }
    
    startAutoSlide() {
        this.stopAutoSlide();
        this.autoSlideInterval = setInterval(() => {
            this.nextSlide();
        }, 5000);
        
        // Animación del progress bar
        this.startProgressAnimation();
    }
    
    stopAutoSlide() {
        if (this.autoSlideInterval) {
            clearInterval(this.autoSlideInterval);
            this.autoSlideInterval = null;
        }
        this.stopProgressAnimation();
    }
    
    startProgressAnimation() {
        const progressFill = document.querySelector('.carousel-progress-fill');
        if (progressFill) {
            progressFill.style.transition = 'width 5s linear';
        }
    }
    
    stopProgressAnimation() {
        const progressFill = document.querySelector('.carousel-progress-fill');
        if (progressFill) {
            progressFill.style.transition = 'width 0.3s ease';
        }
    }
    
    addEventListeners() {
        const carousel = document.querySelector('.image-carousel');
        
        // Hover events
        carousel.addEventListener('mouseenter', () => this.stopAutoSlide());
        carousel.addEventListener('mouseleave', () => this.startAutoSlide());
        
        // Touch events para móvil
        carousel.addEventListener('touchstart', (e) => {
            this.touchStartX = e.changedTouches[0].screenX;
            this.stopAutoSlide();
        });
        
        carousel.addEventListener('touchend', (e) => {
            this.touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe();
            this.startAutoSlide();
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') this.prevSlide();
            if (e.key === 'ArrowRight') this.nextSlide();
        });
        
        // Button events
        const prevBtn = document.querySelector('.prev-btn');
        const nextBtn = document.querySelector('.next-btn');
        
        if (prevBtn) prevBtn.addEventListener('click', () => {
            this.stopAutoSlide();
            this.prevSlide();
            setTimeout(() => this.startAutoSlide(), 3000);
        });
        
        if (nextBtn) nextBtn.addEventListener('click', () => {
            this.stopAutoSlide();
            this.nextSlide();
            setTimeout(() => this.startAutoSlide(), 3000);
        });
        
        // Dot events
        const dots = document.querySelectorAll('.dot');
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                this.stopAutoSlide();
                this.goToSlide(index);
                setTimeout(() => this.startAutoSlide(), 3000);
            });
        });
    }
    
    handleSwipe() {
        const swipeThreshold = 50;
        const diff = this.touchStartX - this.touchEndX;
        
        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                this.nextSlide(); // Swipe left
            } else {
                this.prevSlide(); // Swipe right
            }
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new ModernCarousel();
});

// Funciones globales para compatibilidad
function changeSlide(n) {
    if (window.carousel) {
        if (n > 0) window.carousel.nextSlide();
        else window.carousel.prevSlide();
    }
}

function currentSlide(n) {
    if (window.carousel) {
        window.carousel.goToSlide(n - 1);
    }
}
</script>
    """



def intelligent_place_matcher(user_query: str, tour_info: dict, language: str = "Spanish") -> dict:
    """
    Usa un agente LLM para hacer matching inteligente de lugares
    
    Args:
        user_query (str): Lo que busca el usuario
        tour_info (dict): Información completa del tour
        language (str): Idioma de la consulta
        
    Returns:
        dict: Resultado del matching con lugares encontrados
    """
    try:
        # Extraer solo los nombres y IDs de lugares disponibles
        available_places = {}
        for category_key, category_data in tour_info.get('categories', {}).items():
            for place_key, place_data in category_data.get('places', {}).items():
                available_places[place_key] = {
                    "name": place_data.get('name', ''),
                    "category": category_data.get('name', ''),
                    "description": place_data.get('description', '')[:100] + "...",
                    "services": place_data.get('services', [])[:3]  
                }
        
        system_prompt = """You are an intelligent location matching agent for Universidad del Norte's virtual tour system. Your job is to analyze user queries and match them to available campus locations.

CRITICAL INSTRUCTIONS:
1. Return ONLY a valid JSON response with the exact structure specified
2. Use ONLY the place_key IDs exactly as provided in the available places list
3. Be very flexible with user queries - handle typos, synonyms, partial names, and different languages
4. Consider context and user intent, not just literal matches

AVAILABLE PLACES:
""" + json.dumps(available_places, indent=2, ensure_ascii=False) + """

RESPONSE FORMAT (return ONLY this JSON structure):
{
  "matches": [
    {
      "place_key": "exact_key_from_available_places",
      "confidence": 0.95,
      "reason": "Brief explanation of why this matches"
    }
  ],
  "query_type": "specific_place|category|general_tour",
  "suggested_category": "academic|recreational|services|null",
  "interpretation": "What you understood from the user's query"
}

MATCHING RULES:
- For specific places: Return exact place_key matches
- For categories: Return suggested_category and empty matches
- For general tours: Return query_type "general_tour"
- Handle multiple languages (Spanish/English)
- Consider synonyms, abbreviations, and common misspellings
- Match based on services offered if place name isn't clear

EXAMPLES:
User: "biblioteca" → match "biblioteca" place_key
User: "library" → match "biblioteca" place_key  
User: "gimnasio" → match "polideportivo" place_key
User: "lugares académicos" → category "academic"
User: "tour completo" → query_type "general_tour"
User: "karl parrish" → match "biblioteca" place_key
User: "donde estudiar" → match "biblioteca" place_key based on services"""

        user_prompt = f"""User query: "{user_query}"
Language: {language}

Analyze this query and return the appropriate JSON response. Be intelligent about matching - consider:
- Synonyms and alternative names
- Purpose/function (if they want to study → biblioteca)
- Services offered by locations
- Partial names or abbreviations
- Common misspellings
- Different languages

Return ONLY the JSON response."""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        
        # Parse JSON response
        try:
            result = json.loads(response.choices[0].message.content)
            print(f"Matching agent result: {result}")
            return result
        except json.JSONDecodeError:
            print(f"JSON decode error. Raw response: {response.choices[0].message.content}")
            return {
                "matches": [],
                "query_type": "general_tour",
                "suggested_category": None,
                "interpretation": "Error parsing response"
            }
        
    except Exception as e:
        print(f"Error in intelligent place matcher: {str(e)}")
        return {
            "matches": [],
            "query_type": "general_tour", 
            "suggested_category": None,
            "interpretation": f"Error: {str(e)}"
        }
    

def search_internet_for_uni_answers(query: str, status: str, user_id: int):
    """"
    Use LLM with internet connectivity to search for answers about Universidad del Norte
    """
    try:
        set_status(user_id, status, 2)
        system_prompt = """ """
        user_prompt = f"""The user has asked the following question about Universidad del Norte: '{query}'   """

        response = client.chat.completions.create(
            model="gpt-4o-search-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        )

        answer = response.choices[0].message.content
        print(f"Search result: {answer}")

        return {"answer": answer}
    except Exception as e:
        print(f"Error in search_internet_for_uni_answers: {str(e)}")
        return {"error": str(e), "answer": None}
