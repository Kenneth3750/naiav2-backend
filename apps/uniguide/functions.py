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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from services.files import B2FileService
import json
from serpapi import GoogleSearch
from typing import Dict
from apps.researcher.functions import generate_image_carousel_html
from apps.researcher.functions import get_user_info_from_graph
import smtplib
from email.mime.text import MIMEText
import requests
from apps.personal.functions import generate_contacts_html_enhanced
from apps.users.services import UserService
from services.files import B2FileService
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.redis import RedisVectorStore
import redis
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import StorageContext, Document
import tempfile
from dotenv import load_dotenv
from tqdm import tqdm
from redisvl.schema import IndexSchema
from llama_index.core.settings import Settings
import io
from PyPDF2 import PdfReader


load_dotenv()

DEFAULT_FROM_EMAIL=os.getenv("DEFAULT_FROM_EMAIL")
EMAIL_HOST_PASSWORD=os.getenv("EMAIL_HOST_PASSWORD")

openai_api_key = os.getenv("open_ai")
r = redis.Redis(host='localhost', port=6379, db=0)
embedded_model = OpenAIEmbedding(model="text-embedding-3-small", dimensions=800, api_key=openai_api_key)

Settings.embed_model = embedded_model
client = OpenAI(
    api_key= openai_api_key
)

def create_rag():
    b2_service = B2FileService()
    document_bytes_list = b2_service.download_uniguide_documents()

    if not document_bytes_list:
        raise ValueError("No documents found in B2 storage.")

    documents = []
    for i, file_info in tqdm(enumerate(document_bytes_list)):
        if isinstance(file_info, dict) and 'bytes' in file_info and 'filename' in file_info:
            file_bytes = file_info['bytes']
            file_name = file_info['filename']
        else:
            file_bytes = file_info
            file_name = ""

        # Check if it's a PDF by content, not just filename
        is_pdf = file_bytes.startswith(b'%PDF')
        
        if file_name and file_name.lower().endswith('.txt'):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
                temp_file.write(file_bytes)
                temp_path = temp_file.name
            with open(temp_path, 'r', encoding='utf-8') as f:
                text = f.read()
            documents.append(Document(text=text))
            os.unlink(temp_path)
        elif (file_name and file_name.lower().endswith('.pdf')) or is_pdf:
            # Process PDF files (either by extension or by content detection)
            try:
                pdf_stream = io.BytesIO(file_bytes)
                reader = PdfReader(pdf_stream)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                if text.strip():  # Only add if we extracted some text
                    documents.append(Document(text=text))
                else:
                    print(f"Warning: No text extracted from PDF: {file_name or 'unknown'}")
            except Exception as e:
                print(f"Error processing PDF {file_name or 'unknown'}: {e}")
        else:
            # fallback: try decode as utf-8 text only if not a PDF
            try:
                text = file_bytes.decode('utf-8')
                documents.append(Document(text=text))
            except Exception as e:
                print(f"Error decoding {file_name or 'unknown'}: {e}")

    print(f"Documents processed: {len(documents)}")
    custom_schema = IndexSchema.from_dict(
        {
            # customize basic index specs
            "index": {
                "name": "university",
                "prefix": "rag:university",
                "key_separator": ":",
            },
            # customize fields that are indexed
            "fields": [
                # required fields for llamaindex
                {"type": "tag", "name": "id"},
                {"type": "tag", "name": "doc_id"},
                {"type": "text", "name": "text"},
                # custom metadata fields
                {"type": "tag", "name": "file_name"},
                # custom vector field definition for cohere embeddings
                {
                    "type": "vector",
                    "name": "vector",
                    "attrs": {
                        "dims": 800,
                        "algorithm": "hnsw",
                        "distance_metric": "cosine",
                    },
                },
            ],
        }
    )

    vector_store = RedisVectorStore(
        redis_client=r, 
        overwrite=True,
        schema=custom_schema
    )

    # Crear el contexto de almacenamiento
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Construir el índice
    index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context
    )
    
    custom_schema.to_yaml("university_schema.yaml")

def query_university_rag(user_id: int, question: str, k: int = 3, status:str = "") -> dict:
    """
    Query the information stored in the vector store and generate a response.
    """
    try:
        start_time = time.time()
        set_status(user_id, status, 2)
        os.environ["OPENAI_API_KEY"] = openai_api_key
        vector_store = RedisVectorStore(
            schema=IndexSchema.from_yaml("university_schema.yaml"),
            redis_client=r,
        )
        search_index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        retriever = search_index.as_retriever(
            similarity_top_k=3
        )
        result_nodes = retriever.retrieve(question)
        rag_info = ""
        for node in result_nodes:
            print(f"Info: {node.text}")
            print("-" * 80)
            rag_info += f"{node.text}\n"
        print(f"Time taken for RAG query: {time.time() - start_time:.2f} seconds")
        print(f"RAG results: {rag_info}")
        return {"resolved_rag": rag_info}

    except Exception as e:
        print(f"Error retrieving documents: {str(e)}")
        return {"error": str(e)}
    

def get_university_calendar_multi_month(user_id: int, months_to_search: list, status: str) -> dict:
    """
    Get university calendar events for multiple months to find specific events
    Enhanced with detailed logging for debugging
    """
    driver = None
    temp_dir = None
    
    try:
        print(f"[CALENDAR] Starting calendar function for user {user_id}")
        print(f"[CALENDAR] Months to search: {months_to_search}")
        
        set_status(user_id, status, 2)
        
        # Create unique temporary directory
        import tempfile
        import uuid
        temp_dir = tempfile.mkdtemp(prefix='chrome-', suffix=f'-{uuid.uuid4().hex[:8]}')
        print(f"[CALENDAR] Created temp directory: {temp_dir}")
        
        # Enhanced Chrome options for server stability
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
        options.add_argument(f'--user-data-dir={temp_dir}')
        
        # Additional stability options for servers
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-component-extensions-with-background-pages')
        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-sync')
        
        print(f"[CALENDAR] Chrome options configured: {len(options.arguments)} arguments")
        
        # Initialize Chrome driver
        print(f"[CALENDAR] Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(options=options)
        print(f"[CALENDAR] ✅ Chrome driver initialized successfully")
        
        # Set timeouts
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(20)
        print(f"[CALENDAR] Timeouts set: page_load=60s, implicit_wait=20s")
        
        # Navigate to calendar URL
        url = 'https://outlook.office365.com/calendar/published/82dc57e4303e46d490fec6d6df9e41c6@uninorte.edu.co/ca0af55ded00488eb89bac6079a9675a7730392440685253853/calendar.html'
        print(f"[CALENDAR] Loading URL: {url}")
        
        driver.get(url)
        print(f"[CALENDAR] ✅ Page loaded successfully")
        
        # Wait for calendar to load
        print(f"[CALENDAR] Waiting for calendar elements to load...")
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ms-CommandBar"))
            )
            print(f"[CALENDAR] ✅ Calendar elements found and loaded")
        except Exception as wait_error:
            print(f"[CALENDAR] ❌ Error waiting for calendar elements: {str(wait_error)}")
            # Try alternative selectors
            print(f"[CALENDAR] Trying alternative element selectors...")
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print(f"[CALENDAR] ✅ Page body loaded as fallback")
            except Exception as fallback_error:
                print(f"[CALENDAR] ❌ Complete page load failure: {str(fallback_error)}")
                raise wait_error
        
        all_events = {}
        from datetime import datetime, timezone, timedelta
        gmt_minus_5 = timezone(timedelta(hours=-5))
        current_date = datetime.now(gmt_minus_5)
        current_month = current_date.month
        current_year = current_date.year
        
        print(f"[CALENDAR] Current date: {current_date}, Month: {current_month}, Year: {current_year}")
        
        month_names = ["", "January", "February", "March", "April", "May", "June", 
                      "July", "August", "September", "October", "November", "December"]
        
        # Process each month
        for i, target_month in enumerate(months_to_search):
            print(f"[CALENDAR] Processing month {i+1}/{len(months_to_search)}: {month_names[target_month]} (month {target_month})")
            
            months_diff = target_month - current_month
            print(f"[CALENDAR] Month difference: {months_diff} (from {current_month} to {target_month})")
            
            # Navigate to target month
            if months_diff != 0:
                print(f"[CALENDAR] Navigating {abs(months_diff)} months {'forward' if months_diff > 0 else 'backward'}")
                
                for j in range(abs(months_diff)):
                    try:
                        if months_diff > 0:
                            print(f"[CALENDAR] Clicking next button (step {j+1}/{abs(months_diff)})")
                            next_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title*='siguiente']"))
                            )
                            next_button.click()
                        else:
                            print(f"[CALENDAR] Clicking previous button (step {j+1}/{abs(months_diff)})")
                            prev_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title*='anterior']"))
                            )
                            prev_button.click()
                        
                        time.sleep(2)  # Wait for navigation
                        print(f"[CALENDAR] ✅ Navigation step {j+1} completed")
                        
                    except Exception as nav_error:
                        print(f"[CALENDAR] ❌ Navigation error at step {j+1}: {str(nav_error)}")
                        # Try alternative navigation selectors
                        try:
                            print(f"[CALENDAR] Trying alternative navigation...")
                            if months_diff > 0:
                                alt_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'next') or contains(@aria-label, 'siguiente')]")
                            else:
                                alt_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'previous') or contains(@aria-label, 'anterior')]")
                            alt_button.click()
                            time.sleep(2)
                            print(f"[CALENDAR] ✅ Alternative navigation successful")
                        except Exception as alt_nav_error:
                            print(f"[CALENDAR] ❌ Alternative navigation also failed: {str(alt_nav_error)}")
                            raise nav_error
            else:
                print(f"[CALENDAR] Already on target month, no navigation needed")
            
            # Extract events from current month
            print(f"[CALENDAR] Extracting events for {month_names[target_month]}...")
            time.sleep(3)  # Wait for month to fully load
            
            try:
                page_source = driver.page_source
                print(f"[CALENDAR] Page source length: {len(page_source)} characters")
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(page_source, 'html.parser')
                print(f"[CALENDAR] BeautifulSoup parsing completed")
                
                month_events = []
                
                # Method 1: Original method with role='button'
                print(f"[CALENDAR] Method 1: Searching for divs with role='button'")
                divs_role_button = soup.find_all('div', role='button')
                print(f"[CALENDAR] Found {len(divs_role_button)} divs with role='button'")
                
                method1_events = 0
                for div in divs_role_button:
                    if div.get('aria-label') is not None:
                        try:
                            title = div.get("aria-label").strip().replace('\n', ' ').split(",")
                            event_text = f"EVENT: {title[0].strip()}, DATE: {title[2].strip()}"
                            if event_text not in month_events:
                                month_events.append(event_text)
                                method1_events += 1
                        except Exception as parse_error:
                            print(f"[CALENDAR] Error parsing aria-label: {str(parse_error)}")
                    elif div.get('title') is not None:
                        try:
                            title = div.get("title").strip().replace('\n', ' ').split(",")
                            event_text = f"EVENT: {title[0].strip()}, DATE: {title[1].strip()}"
                            if event_text not in month_events:
                                month_events.append(event_text)
                                method1_events += 1
                        except Exception as parse_error:
                            print(f"[CALENDAR] Error parsing title: {str(parse_error)}")
                
                print(f"[CALENDAR] Method 1 found {method1_events} events")
                
                # Method 2: Look for divs with data-calitemid
                print(f"[CALENDAR] Method 2: Searching for divs with data-calitemid")
                event_containers = soup.find_all('div', {'data-calitemid': True})
                print(f"[CALENDAR] Found {len(event_containers)} event containers")
                
                method2_events = 0
                for container in event_containers:
                    try:
                        inner_div = container.find('div', {'title': True})
                        if inner_div and inner_div.get('title'):
                            title = inner_div.get('title').strip().replace('\n', ' ').split(",")
                            event_text = f"EVENT: {title[0].strip()}, DATE: {title[1].strip()}"
                            if event_text not in month_events:
                                month_events.append(event_text)
                                method2_events += 1
                        
                        inner_div_aria = container.find('div', {'aria-label': True})
                        if inner_div_aria and inner_div_aria.get('aria-label'):
                            title = inner_div_aria.get('aria-label').strip().replace('\n', ' ').split(",")
                            event_text = f"EVENT: {title[0].strip()}, DATE: {title[2].strip()}"
                            if event_text not in month_events:
                                month_events.append(event_text)
                                method2_events += 1
                    except Exception as parse_error:
                        print(f"[CALENDAR] Error in method 2 parsing: {str(parse_error)}")
                
                print(f"[CALENDAR] Method 2 found {method2_events} additional events")
                
                # Method 3: Look for spans with class 'xWbuA'
                print(f"[CALENDAR] Method 3: Searching for spans with class 'xWbuA'")
                event_spans = soup.find_all('span', class_='xWbuA')
                print(f"[CALENDAR] Found {len(event_spans)} event spans")
                
                method3_events = 0
                for span in event_spans:
                    try:
                        parent_container = span.find_parent('div', {'data-calitemid': True})
                        if parent_container:
                            title_div = parent_container.find('div', {'title': True})
                            aria_div = parent_container.find('div', {'aria-label': True})
                            
                            if title_div:
                                title = title_div.get('title').strip().replace('\n', ' ').split(",")
                                event_text = f"EVENT: {span.get_text().strip()}, DATE: {title[1].strip()}"
                                if event_text not in month_events:
                                    month_events.append(event_text)
                                    method3_events += 1
                            elif aria_div:
                                title = aria_div.get('aria-label').strip().replace('\n', ' ').split(",")
                                event_text = f"EVENT: {span.get_text().strip()}, DATE: {title[2].strip()}"
                                if event_text not in month_events:
                                    month_events.append(event_text)
                                    method3_events += 1
                    except Exception as parse_error:
                        print(f"[CALENDAR] Error in method 3 parsing: {str(parse_error)}")
                
                print(f"[CALENDAR] Method 3 found {method3_events} additional events")
                
                print(f"[CALENDAR] Total events found for {month_names[target_month]}: {len(month_events)}")
                for event in month_events[:3]:  # Log first 3 events as sample
                    print(f"[CALENDAR] Sample event: {event}")
                
                all_events[month_names[target_month]] = month_events
                
                # Reset to current month for next iteration
                current_month = target_month
                
            except Exception as extraction_error:
                print(f"[CALENDAR] ❌ Error extracting events for {month_names[target_month]}: {str(extraction_error)}")
                all_events[month_names[target_month]] = []
        
        # Format results
        print(f"[CALENDAR] Formatting results...")
        formatted_events = f"UNIVERSITY EVENTS FOR {current_year}:\n\n"
        total_events = 0
        for month_name, events in all_events.items():
            formatted_events += f"{month_name.upper()}:\n"
            for event in events:
                formatted_events += f"  {event}\n"
            formatted_events += "\n"
            total_events += len(events)
        
        print(f"[CALENDAR] ✅ Calendar extraction completed successfully")
        print(f"[CALENDAR] Total events across all months: {total_events}")
        
        # Generate HTML (assuming this function exists)
        try:
            caldendar_html = generate_calendar_html(all_events, current_year)
            print(f"[CALENDAR] ✅ HTML generation completed")
        except Exception as html_error:
            print(f"[CALENDAR] ❌ HTML generation error: {str(html_error)}")
            caldendar_html = "<p>Error generating calendar display</p>"

        return {"calendar_events": formatted_events, "graph": caldendar_html}
        
    except Exception as e:
        print(f"[CALENDAR] ❌ MAJOR ERROR in calendar function: {str(e)}")
        print(f"[CALENDAR] Error type: {type(e).__name__}")
        import traceback
        print(f"[CALENDAR] Full traceback: {traceback.format_exc()}")
        return {"error": str(e)}
    
    finally:
        print(f"[CALENDAR] Starting cleanup process...")
        
        # Cleanup driver
        if driver:
            try:
                print(f"[CALENDAR] Closing Chrome driver...")
                driver.quit()
                print(f"[CALENDAR] ✅ Chrome driver closed successfully")
            except Exception as driver_error:
                print(f"[CALENDAR] ❌ Error closing driver: {str(driver_error)}")
        
        # Cleanup temporary directory
        if temp_dir:
            try:
                print(f"[CALENDAR] Cleaning up temp directory: {temp_dir}")
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"[CALENDAR] ✅ Temp directory cleaned up")
            except Exception as cleanup_error:
                print(f"[CALENDAR] ❌ Error cleaning temp directory: {str(cleanup_error)}")
        
        print(f"[CALENDAR] Cleanup process completed")


def get_virtual_campus_tour(area_filter: str = None, place_name: str = None, language: str = "Spanish", user_id: int = 0, status: str = "") -> dict:
    """
    Generates an interactive virtual campus tour with intelligent place matching.
    Optimized to download only necessary images based on the specific request.
    
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
        
        # Step 1: Get only tour JSON data from B2 (fast)
        b2_service = B2FileService()
        tour_info = b2_service.download_virtual_tour_json_only()
        
        if not tour_info:
            return {"error": "No se pudo cargar la información del tour virtual"}
        
        is_spanish = language.lower().startswith('es') or 'spanish' in language.lower()
        
        # Step 2: Determine what places we need to show
        places_to_show = []
        match_result = None
        
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
                        places_to_show.append(place_data)
                        break
            
            elif match_result.get("suggested_category"):
                # Redirect to category view
                area_filter = match_result["suggested_category"]
                place_name = None  # Clear place_name to show category
        
        # If no specific place found or showing categories
        if not places_to_show:
            # Filter data based on area_filter or show all categories
            if area_filter:
                # Filter by specific category
                if area_filter in tour_info.get('categories', {}):
                    category_data = tour_info['categories'][area_filter]
                    for place_key, place_data in category_data.get('places', {}).items():
                        place_data['category'] = category_data.get('name', area_filter)
                        place_data['place_key'] = place_key
                        places_to_show.append(place_data)
                else:
                    # Invalid category, show all
                    for category_key, category_data in tour_info.get('categories', {}).items():
                        for place_key, place_data in category_data.get('places', {}).items():
                            place_data['category'] = category_data.get('name', category_key)
                            place_data['place_key'] = place_key
                            places_to_show.append(place_data)
            else:
                # Show all categories
                for category_key, category_data in tour_info.get('categories', {}).items():
                    for place_key, place_data in category_data.get('places', {}).items():
                        place_data['category'] = category_data.get('name', category_key)
                        place_data['place_key'] = place_key
                        places_to_show.append(place_data)
        
        # Step 3: Extract image names only from places we need to show
        required_images = set()
        for place in places_to_show:
            images = place.get('images', [])
            if images:
                required_images.update(images)
        
        print(f"Required images: {len(required_images)} out of potentially many more")
        
        # Step 4: Get only the required images info
        available_images = b2_service.get_virtual_tour_images_info(list(required_images))
        
        # Step 5: Generate the appropriate view
        if place_name and match_result and match_result.get("matches") and len(places_to_show) == 1:
            # Single place view
            place_data = places_to_show[0]
            display_content, graph_content = generate_single_place_html_split(
                place_data, available_images, b2_service, is_spanish
            )
            
            return {
                "display": display_content,
                "graph": graph_content,
                "match_info": {
                    "found": True,
                    "place": place_data['place_key'],
                    "confidence": match_result["matches"][0].get("confidence", 0),
                    "interpretation": match_result.get("interpretation", "")
                }
            }
        else:
            # Overview/category view - need to organize places back into categories
            categories_to_show = []
            
            if area_filter:
                # Single category view
                if area_filter in tour_info.get('categories', {}):
                    category_data = tour_info['categories'][area_filter]
                    category_places = {}
                    for place in places_to_show:
                        if place.get('category') == category_data.get('name', area_filter):
                            category_places[place['place_key']] = place
                    
                    categories_to_show.append({
                        'key': area_filter,
                        'name': category_data.get('name', area_filter),
                        'description': category_data.get('description', ''),
                        'places': category_places
                    })
                else:
                    # Invalid category, organize all places by their categories
                    category_map = {}
                    for place in places_to_show:
                        cat_name = place.get('category', 'unknown')
                        if cat_name not in category_map:
                            category_map[cat_name] = {'places': {}}
                        category_map[cat_name]['places'][place['place_key']] = place
                    
                    for cat_key, cat_data in tour_info.get('categories', {}).items():
                        cat_display_name = cat_data.get('name', cat_key)
                        if cat_display_name in category_map:
                            categories_to_show.append({
                                'key': cat_key,
                                'name': cat_display_name,
                                'description': cat_data.get('description', ''),
                                'places': category_map[cat_display_name]['places']
                            })
            else:
                # All categories view
                category_map = {}
                for place in places_to_show:
                    cat_name = place.get('category', 'unknown')
                    if cat_name not in category_map:
                        category_map[cat_name] = {'places': {}}
                    category_map[cat_name]['places'][place['place_key']] = place
                
                for cat_key, cat_data in tour_info.get('categories', {}).items():
                    cat_display_name = cat_data.get('name', cat_key)
                    if cat_display_name in category_map:
                        categories_to_show.append({
                            'key': cat_key,
                            'name': cat_display_name,
                            'description': cat_data.get('description', ''),
                            'places': category_map[cat_display_name]['places']
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
                    "interpretation": match_result.get("interpretation", "") if match_result else "",
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
    
    # Generate image carousel (graph) - CORREGIDO
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
                # CORREGIDO: Usar directamente la URL del diccionario
                img_url = available_images[img_name].get('url')
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
    
    # CORREGIDO: Carrusel optimizado con imágenes disponibles
    carousel_title = "Galería del Campus" if is_spanish else "Campus Gallery"
    
    # Recopilar imágenes usando el diccionario optimizado
    all_images = []
    for category in categories:
        places = category.get('places', {})
        for place_key, place_data in places.items():
            place_name = place_data.get('name', place_key)
            images = place_data.get('images', [])
            
            # CORREGIDO: Usar directamente available_images que ya tiene las URLs
            for img_name in images:
                if img_name in available_images:
                    img_url = available_images[img_name].get('url')
                    if img_url:
                        all_images.append({
                            'url': img_url,
                            'name': img_name,
                            'place': place_name,
                            'alt': f"{place_name} - {img_name}"
                        })
    
    # Generar carrusel
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
        
        # Generar indicadores
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
                    
                    // Auto-advance carousel every 4 seconds
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
User: "gimnasio" → match "gimnasio" place_key
User: "lugares académicos" → category "academic"
User: "tour completo" → query_type "general_tour"
User: "karl parrish" → match "biblioteca" place_key
User: "donde estudiar" → match "biblioteca" place_key based on services

Specific situation:
- Never select the Centro deportivo roble amarillo as the gym location, it does not matter if there is a gym inside.
- The main gym of the university is the one clearly named Gimnasio Uninorte. You must always select this as the gym location."""

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
    

def search_internet_for_uni_answers(query: str, status: str, user_id: int, image_query: str ) -> Dict:
    """"
    Use LLM with internet connectivity to search for answers about Universidad del Norte
    """
    try:
        set_status(user_id, status, 2)
        api_key = os.getenv("SERPAPI_KEY")
        if not api_key:
            raise ValueError("SERPAPI_KEY not found in .env file")
        system_prompt = """You are an assistant specialized in searching for specific information about Universidad del Norte (UniNorte) in Barranquilla, Colombia via the internet.

        MAIN OBJECTIVE:
        Your only function is to search for VERY SPECIFIC information about UniNorte that is NOT found in the university's official administrative documents. This function is used only when the institutional RAG cannot answer very detailed or obscure questions.

        TYPES OF QUERIES YOU SHOULD ADDRESS:
        1. Specific architectural details: "How many floors does building J have?", "How tall is the administrative tower?"
        2. Very specific physical information: "How many classrooms are in building K?", "What color are the benches in the central park?"
        3. Curious facts or very detailed information about facilities: "How many windows does the library have?"
        4. Recent information about constructions or renovations
        5. Very specific details about locations on campus
        6. Obscure questions that require direct observation of the campus

        IMPORTANT RESTRICTIONS:
        - ONLY search for information about Universidad del Norte in Barranquilla, Colombia
        - DO NOT answer questions about academic policies, administrative procedures, scholarships, certificates, or official processes (that's for the RAG)
        - DO NOT search for information about other universities
        - Focus solely on physical data, architectural details, or very specific details about the campus

        RESPONSE FORMAT:
        - Provide clear and specific information
        - If you cannot find the exact information, indicate that the information might not be publicly available
        - Keep answers concise but informative
        - Always mention that the information comes from internet searches

        IMPORTANT:
        This function is used when questions are so specific that they are unlikely to be in official administrative documents. The system will have already tried to search in the institutional RAG before coming here."""
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


        image_params = {
            "engine": "google_images",
            "q": image_query,
            "api_key": api_key,
        }

        search_results = GoogleSearch(image_params)
        image_html = generate_image_carousel_html(search_results.get_dict().get("images_results", []))

        return {"answer": answer, "graph": image_html}
    except Exception as e:
        print(f"Error in search_internet_for_uni_answers: {str(e)}")
        return {"error": str(e), "answer": None}

def generate_calendar_html(all_events, year):
    from datetime import datetime
    import re
    
    def parse_event_date(date_str):
        """Parse various date formats and return a datetime object for sorting"""
        try:
            # Remove extra spaces and normalize
            date_str = re.sub(r'\s+', ' ', date_str.strip())
            
            # Common Spanish date patterns
            spanish_months = {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
                'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
            }
            
            # Pattern: "15 de septiembre de 2024" or "15 de septiembre"
            pattern1 = r'(\d{1,2})\s+de\s+(\w+)(?:\s+de\s+(\d{4}))?'
            match = re.search(pattern1, date_str.lower())
            if match:
                day = int(match.group(1))
                month_name = match.group(2)
                year_val = int(match.group(3)) if match.group(3) else year
                
                if month_name in spanish_months:
                    month = spanish_months[month_name]
                    return datetime(year_val, month, day)
            
            # Pattern: "2024-09-15" or "15/09/2024" or "15-09-2024"
            date_patterns = [
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
                r'(\d{1,2})-(\d{1,2})-(\d{4})'   # DD-MM-YYYY
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_str)
                if match:
                    if 'yyyy' in pattern.lower():  # YYYY-MM-DD
                        year_val, month, day = map(int, match.groups())
                    else:  # DD/MM/YYYY or DD-MM-YYYY
                        day, month, year_val = map(int, match.groups())
                    
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        return datetime(year_val, month, day)
            
            # If all else fails, return a default date for sorting purposes
            return datetime(year, 1, 1)
            
        except:
            # Return a default date if parsing fails
            return datetime(year, 1, 1)
    
    html = f"""
    <div style="max-height: 600px; overflow-y: auto; font-family: Arial, sans-serif;">
        <h2 style="color: #124072; text-align: center; margin-bottom: 20px;">
            📅 Eventos Universitarios {year}
        </h2>
    """
    
    for i, (month_name, events) in enumerate(all_events.items()):
        # Sort events by date within each month
        events_with_dates = []
        for event in events:
            # Parse event text: "EVENT: name, DATE: date"
            parts = event.split(", DATE: ")
            event_name = parts[0].replace("EVENT: ", "")
            event_date_str = parts[1] if len(parts) > 1 else "Fecha TBD"
            
            # Parse date for sorting
            parsed_date = parse_event_date(event_date_str)
            
            events_with_dates.append({
                'name': event_name,
                'date_str': event_date_str,
                'parsed_date': parsed_date,
                'original': event
            })
        
        # Sort by parsed date
        events_with_dates.sort(key=lambda x: x['parsed_date'])
        
        is_first = i == 0
        html += f"""
        <details {"open" if is_first else ""} style="margin-bottom: 15px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
            <summary style="background: #124072; color: white; padding: 15px; cursor: pointer; font-weight: bold;">
                📅 {month_name} ({len(events_with_dates)} eventos)
            </summary>
            <div style="padding: 15px; background: #f9fafb;">
        """
        
        for event_data in events_with_dates:
            # Format date for display (keep original if it's already formatted nicely)
            display_date = event_data['date_str']
            
            # Try to format date nicely if it was successfully parsed
            if event_data['parsed_date'].year != year or event_data['parsed_date'] != datetime(year, 1, 1):
                try:
                    # Format as "Lunes, 15 de septiembre"
                    spanish_days = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
                    spanish_months_full = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                                         'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
                    
                    weekday = spanish_days[event_data['parsed_date'].weekday()]
                    day = event_data['parsed_date'].day
                    month = spanish_months_full[event_data['parsed_date'].month - 1]
                    
                    display_date = f"{weekday.capitalize()}, {day} de {month}"
                except:
                    # Keep original date string if formatting fails
                    pass
            
            html += f"""
            <div style="background: white; padding: 12px; margin-bottom: 8px; border-radius: 6px; border-left: 4px solid #00aeda; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-weight: 600; color: #124072; margin-bottom: 4px;">{event_data['name']}</div>
                <div style="color: #6b7280; font-size: 14px;">🗓️ {display_date}</div>
            </div>
            """
        
        html += """
            </div>
        </details>
        """
    
    html += "</div>"
    return html


def send_email(to_email: str, subject: str, body: str, status: str = "", user_id: int = 0) -> dict:
    """
    Sends an email using Gmail SMTP server.
    Can automatically detect when to use the authenticated user's email address.
    Includes a footer with the sender's information for traceability.
    
    Args:
        to_email (str): The recipient's email address or indicators like "mi correo", "my email"
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
    if not subject or not body:
        return {"error": "Subject and body are required"}
    
    # Check if we need to get the user's email automatically
    user_email_indicators = [
        "mi correo", "my email", "mi email", "my mail", 
        "mi dirección", "my address", "mío", "mine", "me", "yo", "I", "myself"
    ]
    
    # Determine if we need to fetch user's email
    should_get_user_email = (
        not to_email or 
        to_email.strip().lower() in user_email_indicators or
        (to_email and '@' not in to_email and '.' not in to_email)
    )
    
    # Get user information for footer (always when user_id is provided)
    user_info = None
    if user_id:
        user_info_result = get_user_info_from_graph(user_id)
        if "error" not in user_info_result:
            user_info = user_info_result
        
        # If we need to get user's email for the recipient
        if should_get_user_email:
            if "error" in user_info_result:
                return user_info_result
            to_email = user_info["email"]
            print(f"Using user's email address: {to_email}")
    
    # If we still need to get user email but don't have user_id
    if should_get_user_email and not user_id:
        return {"error": "User ID is required to get your email address"}
    
    # Validate final email
    if not to_email:
        return {"error": "Email address is required"}
        
    # Basic email format validation
    if '@' not in to_email or '.' not in to_email:
        return {"error": "Invalid email format"}
    
    # Add footer with user information for traceability
    footer = "\n\n" + "─" * 50 + "\n"
    if user_info:
        footer += f"Este email fue enviado por: {user_info['name']} ({user_info['email']})\n"
    else:
        footer += "Este email fue enviado a través de la plataforma NAIA\n"
    footer += "Universidad del Norte - NAIA Assistant\n"
    footer += "Para soporte técnico, contacta: naia@uninorte.edu.co"
    
    # Add footer to the body
    final_body = body + footer
    
    try:
        if user_id:
            set_status(user_id, status or "Sending email...", 2)

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
            if user_info:
                print(f"Email ejecutado por: {user_info['name']} ({user_info['email']})")
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
            set_status(user_id, status, 2) 

        # Get user's Microsoft Graph token
        user_service = UserService()
        access_token = user_service.get_user_token(user_id)

        print(f"Using access token: {access_token[:10]}...")  # Print only first 10 chars for security
        
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
            set_status(user_id, status, 2)
        
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
    