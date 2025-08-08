import urllib.parse
import requests
from typing import Dict
from apps.users.services import UserService
from apps.status.services import set_status
from services.files import B2FileService
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from openai import OpenAI
import tempfile
import os
from apps.researcher.functions import get_user_info_from_graph
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
import smtplib
from email.mime.text import MIMEText
import requests # no qa
from dotenv import load_dotenv
load_dotenv()

DEFAULT_FROM_EMAIL=os.getenv("DEFAULT_FROM_EMAIL")
EMAIL_HOST_PASSWORD=os.getenv("EMAIL_HOST_PASSWORD")

openai_api_key = os.getenv("open_ai")

client = OpenAI(
    api_key= openai_api_key
)

import json

def create_recepcionist_rag():
    """
    Save documents from B2 cloud storage into a vector database
    """
    try:
        # Get documents from B2
        b2_service = B2FileService()
        document_bytes_list = b2_service.download_recepcionist_documents()
        
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
        persist_dir = "./chromadb_recepcionist"
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
    
def query_recepcionist_rag(user_id: int, question: str, k: int = 3, status: str = "", restaurant_menus: list = None) -> dict:
    """
    Query the information stored in the vector store and generate a response with custom displays for restaurants.
    """
    try:
        set_status(user_id, status, 5)
        persist_dir = "./chromadb_recepcionist"

        if not os.path.exists(persist_dir):
            create_recepcionist_rag()
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
        
        # Generate display based on restaurant_menus parameter
        display_html = None
        if restaurant_menus:
            display_html = generate_restaurant_displays(restaurant_menus)
        
        response = {"resolved_rag": result_text}
        
        # Add display if generated
        if display_html:
            response["display"] = display_html
            
        return response

    except Exception as e:
        print(f"Error retrieving documents: {str(e)}")
        return {"error": str(e)}


def generate_restaurant_displays(restaurant_list: list) -> str:
    """
    Generate displays for the specified restaurants.
    """
    # Define restaurant data with their characteristics and menu links
    restaurants_data = {
        "du nord plaza": {
            "name": "du Nord Plaza - Casa de la Plaza",
            "url": "https://www.uninorte.edu.co/documents/13542542/0/Menu%CC%81+CasadelaPlaza.pdf/79bebb55-0543-fc6d-e15c-5a44a7dc3092?t=1749760705522",
            "specialty": "Variedad gastronómica",
            "description": "Múltiples puntos: Casa de la Plaza, Frida's, Gli Amici y Punto Light",
            "colors": ["#e74c3c", "#f39c12"],  # Rojo a naranja - energético y variado
            "icon": "🍽️",
            "highlights": ["Buffets", "Pizzas", "Comida mexicana", "Italiana", "Saludable"]
        },
        "cafe du nord": {
            "name": "Café du Nord",
            "url": "https://www.uninorte.edu.co/documents/13542542/0/Menu%CC%81+cafe+du+Nord+2025.pdf/4deefcc0-0d44-4d80-9210-e7c228883f2b?t=1749659589814",
            "specialty": "Cocina gourmet francesa",
            "description": "Platos sofisticados al estilo francés con toque caribeño",
            "colors": ["#8e44ad", "#3498db"],  # Púrpura a azul - elegante y sofisticado
            "icon": "☕",
            "highlights": ["Croque Monsieur", "Pasta 4 quesos", "Salmón", "Lomo al Brandy", "Café gourmet"]
        },
        "du nord terrasse": {
            "name": "du Nord Terrasse",
            "url": "https://www.uninorte.edu.co/documents/13542542/0/Menu%CC%81+terrasse+2025.pdf/51c5b9ff-3c6f-17a0-137c-4e01b905ec82?t=1749659752341",
            "specialty": "Cocina árabe auténtica",
            "description": "Sabores del Medio Oriente con ingredientes tradicionales",
            "colors": ["#d4af37", "#cd853f"],  # Dorado a café - colores del desierto
            "icon": "🕌",
            "highlights": ["Hummus", "Shawarma", "Falafel", "Quibbe", "Tahine", "Hojas de parra"]
        },
        "bocas de ceniza": {
            "name": "Restaurante Bocas de Ceniza",
            "url": "https://www.uninorte.edu.co/documents/13542542/35718318/BOCAS+DE+CENIZA+2024.pdf/95ff3d22-046c-d11d-4dd9-db2eb846b85f?t=1737492167298",
            "specialty": "Comida costeña tradicional",
            "description": "Auténticos sabores del Caribe colombiano",
            "colors": ["#2980b9", "#16a085"],  # Azul océano a verde mar
            "icon": "🌊",
            "highlights": ["Pescado frito", "Arroz con coco", "Patacones", "Cazuela de mariscos"]
        },
        "du nord expres": {
            "name": "du Nord Exprès",
            "url": "https://www.uninorte.edu.co/documents/13542542/0/Expre%CC%81s+menu%CC%81.pdf/9a3043a9-d8f8-0d68-54f0-799673343e2f?t=1749825962161",
            "specialty": "Comida rápida gourmet",
            "description": "Opciones rápidas sin sacrificar la calidad",
            "colors": ["#27ae60", "#2ecc71"],  # Naranja vibrante - rápido y energético
            "icon": "⚡",
            "highlights": ["Wraps", "Sandwiches", "Ensaladas", "Smoothies", "Jugos naturales"]
        },
        "restaurante 1966": {
            "name": "Restaurante 1966",
            "url": "https://www.uninorte.edu.co/documents/13542542/25053391/Carta+1966+2023+digital+3+%281%29.pdf/e54394e1-ee01-b77e-6658-2f8451364725?",
            "specialty": "Cocina tradicional de alta calidad",
            "description": "Platos clásicos con ingredientes premium desde 1966",
            "colors": ["#8b4513", "#cd853f"],  # Marrón vintage a dorado - clásico y tradicional
            "icon": "🏛️",
            "highlights": ["Carnes premium", "Platos tradicionales", "Cocina casera", "Recetas familiares"]
        }
    }
    
    # Filter restaurants based on the provided list
    selected_restaurants = []
    for restaurant_key in restaurant_list:
        restaurant_key_lower = restaurant_key.lower().strip()
        if restaurant_key_lower in restaurants_data:
            selected_restaurants.append(restaurants_data[restaurant_key_lower])
    
    if not selected_restaurants:
        return ""
    
    # If only one restaurant, show detailed single display
    if len(selected_restaurants) == 1:
        return generate_single_restaurant_display(selected_restaurants[0])
    
    # If multiple restaurants, show grid display
    return generate_multiple_restaurants_display(selected_restaurants)


def generate_single_restaurant_display(restaurant: dict) -> str:
    """Generate display for a specific restaurant."""
    gradient = f"linear-gradient(135deg, {restaurant['colors'][0]} 0%, {restaurant['colors'][1]} 100%)"
    
    highlights_html = ""
    for highlight in restaurant['highlights']:
        highlights_html += f'<span style="background-color: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 15px; margin: 2px; display: inline-block; font-size: 12px;">{highlight}</span>'
    
    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 650px; margin: 0 auto; padding: 25px; background: {gradient}; border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.2); color: white; text-align: center; position: relative; overflow: hidden;">
        <div style="position: absolute; top: -50%; right: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%); pointer-events: none;"></div>
        
        <div style="position: relative; z-index: 1;">
            <div style="font-size: 48px; margin-bottom: 15px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));">
                {restaurant['icon']}
            </div>
            
            <h2 style="margin: 0 0 10px 0; font-size: 28px; font-weight: 700; text-shadow: 0 3px 6px rgba(0,0,0,0.4); line-height: 1.2;">
                {restaurant['name']}
            </h2>
            
            <div style="background-color: rgba(255,255,255,0.15); padding: 3px 15px; border-radius: 20px; display: inline-block; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <span style="font-size: 14px; font-weight: 600; opacity: 0.9;">{restaurant['specialty']}</span>
            </div>
            
            <p style="margin: 0 0 20px 0; font-size: 16px; opacity: 0.95; line-height: 1.4; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                {restaurant['description']}
            </p>
            
            <div style="margin: 20px 0; text-align: center;">
                <p style="margin-bottom: 10px; font-size: 14px; opacity: 0.9; font-weight: 600;">Especialidades destacadas:</p>
                <div style="line-height: 1.8;">
                    {highlights_html}
                </div>
            </div>
            
            <a href="{restaurant['url']}" target="_blank" rel="noopener noreferrer" 
               style="display: inline-block; background-color: rgba(255,255,255,0.25); color: white; text-decoration: none; padding: 15px 30px; border-radius: 50px; font-weight: 700; font-size: 16px; transition: all 0.3s ease; border: 2px solid rgba(255,255,255,0.3); backdrop-filter: blur(15px); margin-top: 10px;"
               onmouseover="this.style.backgroundColor='rgba(255,255,255,0.35)'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 25px rgba(0,0,0,0.3)'"
               onmouseout="this.style.backgroundColor='rgba(255,255,255,0.25)'; this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14,2 14,8 20,8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10,9 9,9 8,9"></polyline>
                </svg>
                Ver Menú Completo
            </a>
            
            <div style="margin-top: 20px; font-size: 13px; opacity: 0.8; display: flex; align-items: center; justify-content: center;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 5px;">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12,6 12,12 16,14"></polyline>
                </svg>
                Menú actualizado • Universidad del Norte
            </div>
        </div>
    </div>
    """


def generate_multiple_restaurants_display(restaurants: list) -> str:
    """Generate display showing multiple selected restaurants."""
    restaurants_grid = ""
    
    for restaurant in restaurants:
        gradient = f"linear-gradient(135deg, {restaurant['colors'][0]} 0%, {restaurant['colors'][1]} 100%)"
        
        restaurants_grid += f"""
        <div style="background: {gradient}; border-radius: 15px; padding: 20px; text-align: center; color: white; box-shadow: 0 8px 20px rgba(0,0,0,0.15); transition: transform 0.3s ease; position: relative; overflow: hidden;"
             onmouseover="this.style.transform='translateY(-5px)'"
             onmouseout="this.style.transform='translateY(0)'">
            <div style="font-size: 32px; margin-bottom: 10px;">{restaurant['icon']}</div>
            <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                {restaurant['name']}
            </h3>
            <p style="margin: 0 0 15px 0; font-size: 12px; opacity: 0.9; line-height: 1.3;">
                {restaurant['specialty']}
            </p>
            <a href="{restaurant['url']}" target="_blank" rel="noopener noreferrer" 
               style="display: inline-block; background-color: rgba(255,255,255,0.2); color: white; text-decoration: none; padding: 8px 16px; border-radius: 20px; font-weight: 600; font-size: 12px; border: 1px solid rgba(255,255,255,0.3);"
               onmouseover="this.style.backgroundColor='rgba(255,255,255,0.3)'"
               onmouseout="this.style.backgroundColor='rgba(255,255,255,0.2)'">
                Ver Menú
            </a>
        </div>
        """
    
    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 0 auto; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; box-shadow: 0 15px 40px rgba(0,0,0,0.2); color: white;">
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 48px; margin-bottom: 15px;">🍽️</div>
            <h2 style="margin: 0 0 10px 0; font-size: 28px; font-weight: 700; text-shadow: 0 3px 6px rgba(0,0,0,0.4);">
                Menús de Restaurantes
            </h2>
            <p style="margin: 0; font-size: 16px; opacity: 0.9;">
                Opciones gastronómicas seleccionadas en el campus
            </p>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 25px;">
            {restaurants_grid}
        </div>
        
        <div style="text-align: center; margin-top: 25px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);">
            <p style="margin: 0; font-size: 14px; opacity: 0.8;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 5px;">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12,6 12,12 16,14"></polyline>
                </svg>
                Menús actualizados • Universidad del Norte • du Nord
            </p>
        </div>
    </div>
    """


def search_university_staff(name: str, user_id: int, status: str) -> Dict:
    """
    Search for university staff using the EXACT same algorithm as search_contacts.
    This is the working version that successfully finds people.
    """
    set_status(user_id, status, 5)
    
    # Validate required fields
    search_name = name
    if not search_name:
        return {"error": "El nombre es requerido para buscar personal universitario"}
    
    try:
        # Get user's Microsoft Graph token
        user_service = UserService()
        access_token = user_service.get_user_token(user_id)
        
        if not access_token:
            return {"error": "No se encontró token de acceso. Por favor autentícate con Microsoft primero."}
        
        # Set up headers with authentication
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        all_contacts = []
        search_name_lower = search_name.lower()
        
        print(f"Comprehensive staff search for: {name}")
        print(f"Search name lower: {search_name_lower}")
        
        # Enhanced Directory Search (EXACT copy of search_contacts strategy)
        try:
            print("Starting comprehensive directory search...")
            
            # Get name parts for more flexible searching
            name_parts = [part.strip() for part in search_name.split() if part.strip()]
            
            directory_queries = []
            
            # Strategy 1: Get ALL users and filter locally (most reliable)
            directory_queries.append(("https://graph.microsoft.com/v1.0/users?$select=id,displayName,mail,jobTitle,department,userPrincipalName,givenName,surname,usageLocation&$top=999", "all_users"))
            
            # Strategy 2: Search by each name part
            for part in name_parts:
                encoded_part = urllib.parse.quote(part)
                directory_queries.extend([
                    (f"https://graph.microsoft.com/v1.0/users?$filter=startswith(displayName,'{encoded_part}')&$select=id,displayName,mail,jobTitle,department,userPrincipalName,givenName,surname,usageLocation&$top=100", f"startswith_{part}"),
                    (f"https://graph.microsoft.com/v1.0/users?$filter=startswith(givenName,'{encoded_part}')&$select=id,displayName,mail,jobTitle,department,userPrincipalName,givenName,surname,usageLocation&$top=100", f"givenName_{part}"),
                    (f"https://graph.microsoft.com/v1.0/users?$filter=startswith(surname,'{encoded_part}')&$select=id,displayName,mail,jobTitle,department,userPrincipalName,givenName,surname,usageLocation&$top=100", f"surname_{part}")
                ])
            
            for i, (users_url, query_type) in enumerate(directory_queries):
                try:
                    print(f"Trying directory query {i+1} ({query_type}): {users_url}")
                    users_response = requests.get(users_url, headers=headers, timeout=25)
                    print(f"Directory API response status: {users_response.status_code}")
                    
                    if users_response.status_code == 200:
                        users_data = users_response.json()
                        users_found = len(users_data.get('value', []))
                        print(f"Found {users_found} users in directory response {i+1} ({query_type})")
                        
                        for user in users_data.get('value', []):
                            display_name = user.get('displayName', '')
                            email = user.get('mail') or user.get('userPrincipalName', '')
                            job_title = user.get('jobTitle', '')
                            department = user.get('department', '')
                            
                            # Filter for university staff (has jobTitle or department)
                            if not (job_title or department):
                                continue
                            
                            # For "all users" query, filter by name match
                            if query_type == "all_users":
                                # Check if any part of the search name appears in the display name
                                name_match = False
                                for part in name_parts:
                                    if len(part) >= 2 and part.lower() in display_name.lower():
                                        name_match = True
                                        break
                                
                                if not name_match:
                                    continue
                            
                            contact = {
                                "id": f"directory_{user.get('id', '')}",
                                "displayName": display_name,
                                "email": email,
                                "jobTitle": job_title,
                                "department": department,
                                "givenName": user.get('givenName', ''),
                                "surname": user.get('surname', ''),
                                "usageLocation": user.get('usageLocation', ''),
                                "source": "directory",
                                "user_data": user  # Store complete user data
                            }
                            all_contacts.append(contact)
                            print(f"Added directory user: {display_name} ({email})")
                    else:
                        print(f"Directory API error: {users_response.status_code} - {users_response.text}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"Directory query failed: {str(e)}")
                    continue
        
        except Exception as e:
            print(f"Error in directory search: {str(e)}")
        
        print(f"Total contacts found before deduplication: {len(all_contacts)}")
        
        # Remove duplicates and prioritize results (EXACT copy from search_contacts)
        print("Removing duplicates and prioritizing results...")
        
        unique_contacts = []
        seen_emails = set()
        
        for contact in all_contacts:
            email = contact.get('email', '').lower()
            if email and email not in seen_emails:
                seen_emails.add(email)
                unique_contacts.append(contact)
        
        print(f"Unique contacts after deduplication: {len(unique_contacts)}")
        
        # Smart filtering for best matches (EXACT copy from search_contacts logic)
        search_parts_lower = [part.lower() for part in name_parts]
        print(f"Search parts: {search_parts_lower}")
        
        filtered_contacts = []
        
        for contact in unique_contacts:
            display_name_lower = contact.get('displayName', '').lower()
            
            # Check if ALL search parts appear in the display name
            all_parts_found = all(part in display_name_lower for part in search_parts_lower)
            
            if all_parts_found:
                contact['match_score'] = 100  # Full match
                filtered_contacts.append(contact)
                print(f"FULL MATCH (all parts): {contact.get('displayName', '')} (score: 100)")
            else:
                # Partial match - check how many parts are found
                parts_found = sum(1 for part in search_parts_lower if part in display_name_lower)
                match_percentage = (parts_found / len(search_parts_lower)) * 100
                
                if match_percentage >= 50:  # At least 50% of parts found
                    contact['match_score'] = match_percentage
                    filtered_contacts.append(contact)
                    print(f"PARTIAL MATCH: {contact.get('displayName', '')} (score: {match_percentage})")
        
        print(f"Final filtered contacts after strict matching: {len(filtered_contacts)}")
        
        if not filtered_contacts:
            return {
                "display": _generate_no_results_html(search_name),
                "message": f"No se encontró personal universitario con el nombre '{search_name}'. Intenta con variaciones del nombre."
            }
        
        # Sort by match score and limit results
        filtered_contacts.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        final_results = filtered_contacts[:10]
        
        print(f"Found {len(final_results)} relevant contacts matching '{search_name}'")
        
        # Get profile photos for each user (keeping existing photo logic)
        enhanced_results = []
        for contact in final_results:
            enhanced_contact = contact.copy()
            user_data = contact.get('user_data', {})
            
            # Try to get user's profile photo
            try:
                user_id_graph = user_data.get('id')
                if user_id_graph:
                    photo_url = f"https://graph.microsoft.com/v1.0/users/{user_id_graph}/photo/$value"
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
            
            enhanced_results.append(enhanced_contact)
        
        # Generate HTML display
        html_display = _generate_staff_results_html(enhanced_results, search_name)
        
        return {
            "display": html_display,
            "message": f"Se encontraron {len(enhanced_results)} miembros del personal universitario que coinciden con '{search_name}'. Revisa la pantalla para ver los detalles completos."
        }
        
    except Exception as e:
        return {"error": f"Error inesperado al buscar personal universitario: {str(e)}"}


def _generate_staff_results_html(staff_results, search_name):
    """Generate HTML display for university staff search results"""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #1a365d; margin-bottom: 10px; font-size: 28px;">
                🏛️ Personal Universitario
            </h1>
            <p style="color: #4a5568; font-size: 16px; margin: 0;">
                Resultados para: <strong>"{search_name}"</strong> ({len(staff_results)} encontrados)
            </p>
        </div>
        
        <div style="display: grid; gap: 20px;">
    """
    
    for i, staff in enumerate(staff_results, 1):
        # Extract data from contact format
        name = staff.get('displayName', 'Nombre no disponible')
        email = staff.get('email', 'Email no disponible')
        job_title = staff.get('jobTitle', '')
        department = staff.get('department', '')
        given_name = staff.get('givenName', '')
        surname = staff.get('surname', '')
        usage_location = staff.get('usageLocation', '')
        photo_base64 = staff.get('photo_base64')
        match_score = staff.get('match_score', 0)
        
        # Determine match quality indicator
        if match_score >= 100:
            match_indicator = "🎯 Coincidencia Exacta"
            match_color = "#10b981"
        elif match_score >= 75:
            match_indicator = "✅ Muy Relevante"
            match_color = "#3b82f6"
        elif match_score >= 50:
            match_indicator = "⭐ Relevante"
            match_color = "#f59e0b"
        else:
            match_indicator = "📋 Posible Coincidencia"
            match_color = "#6b7280"
        
        # Build department display
        dept_display = ""
        if department:
            dept_display = f"<p><strong>🏫 Departamento:</strong> {department}</p>"
        
        # Build job title display
        job_display = ""
        if job_title:
            job_display = f"<p><strong>💼 Cargo:</strong> {job_title}</p>"
        
        # Build name details
        name_details = ""
        if given_name or surname:
            name_parts = []
            if given_name:
                name_parts.append(f"Nombre: {given_name}")
            if surname:
                name_parts.append(f"Apellido: {surname}")
            if name_parts:
                name_details = f"<p><small><strong>👤 Detalles:</strong> {' | '.join(name_parts)}</small></p>"
        
        # Build location info
        location_display = ""
        if usage_location:
            location_display = f"<p><strong>🌍 Ubicación:</strong> {usage_location}</p>"
        
        # Profile photo section
        photo_section = ""
        if photo_base64:
            photo_section = f"""
                <div style="text-align: center; margin-bottom: 15px;">
                    <img src="{photo_base64}" alt="Foto de perfil de {name}" 
                         style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #3182ce;">
                </div>
            """
        else:
            photo_section = f"""
                <div style="text-align: center; margin-bottom: 15px;">
                    <div style="width: 80px; height: 80px; border-radius: 50%; background-color: #3182ce; display: flex; align-items: center; justify-content: center; margin: 0 auto; color: white; font-size: 24px; font-weight: bold;">
                        {name[0].upper() if name else '?'}
                    </div>
                </div>
            """
        
        html += f"""
            <div style="background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); border-left: 4px solid #3182ce;">
                {photo_section}
                
                <div style="text-align: center; margin-bottom: 15px;">
                    <h2 style="margin: 0 0 5px 0; color: #1a365d; font-size: 22px;">{name}</h2>
                    <p style="margin: 0 0 10px 0; color: #4a5568; font-size: 14px;">
                        <strong>📧 Email:</strong> {email}
                    </p>
                    <span style="background-color: {match_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                        {match_indicator}
                    </span>
                    {name_details}
                </div>
                
                <div style="margin-top: 15px; line-height: 1.6; color: #2d3748;">
                    {job_display}
                    {dept_display}
                    {location_display}
                </div>
                
                <div style="text-align: center; margin-top: 15px; padding-top: 15px; border-top: 1px solid #e2e8f0;">
                    <span style="background-color: #e6fffa; color: #234e52; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                        Resultado #{i} (Coincidencia: {match_score:.0f}%)
                    </span>
                </div>
            </div>
        """
    
    html += """
        </div>
        
        <div style="background-color: #e6fffa; padding: 20px; margin-top: 30px; border-radius: 8px; border-left: 4px solid #38b2ac;">
            <h3 style="margin: 0 0 10px 0; color: #234e52; font-size: 18px;">💡 Información del Resultado</h3>
            <ul style="margin: 0; padding-left: 20px; color: #2d3748; line-height: 1.6;">
                <li>Los resultados están ordenados por porcentaje de coincidencia</li>
                <li>Se muestran personas que contienen todas o la mayoría de las palabras buscadas</li>
                <li>Los datos provienen del directorio oficial de Universidad del Norte</li>
                <li>Para contactar al personal, usa el email institucional proporcionado</li>
            </ul>
        </div>
    </div>
    """
    
    return html


def _generate_no_results_html(search_name):
    """Generate HTML for when no staff results are found"""
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px; text-align: center; background-color: #f8f9fa;">
        <div style="background-color: white; border-radius: 12px; padding: 40px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 64px; margin-bottom: 20px;">🔍</div>
            <h2 style="color: #1a365d; margin-bottom: 15px;">No se encontraron resultados</h2>
            <p style="color: #4a5568; font-size: 16px; margin-bottom: 25px;">
                No se encontró personal universitario con el nombre "<strong>{search_name}</strong>"
            </p>
            
            <div style="background-color: #e6fffa; padding: 20px; border-radius: 8px; text-align: left;">
                <h3 style="margin: 0 0 15px 0; color: #234e52;">💡 Sugerencias:</h3>
                <ul style="margin: 0; padding-left: 20px; color: #2d3748;">
                    <li>Verifica la ortografía del nombre completo</li>
                    <li>Intenta buscar solo por el nombre: "Christian"</li>
                    <li>Intenta buscar solo por el apellido: "Quintero"</li>
                    <li>Prueba con nombres intermedios: "Christian Giovanny"</li>
                    <li>Asegúrate de que la persona es personal activo de la universidad</li>
                </ul>
            </div>
        </div>
    </div>
    """

def answer_question_of_uni_premises(place: str, user_id: int, status: str) -> Dict:
    """
    Answer questions about university premises with information and image carousel.
    Returns structured data with 'info' and 'graph' keys following the investigator pattern.
    """
    try:     
        # Set status
        set_status(user_id, status, 5)
        
        # Dictionary mapping place names to their URLs
        places = {
            "Restaurante Bocas de Ceniza": "https://www.uninorte.edu.co/web/dunord/bocas-de-ceniza",
            "Restaurante du Nord Plaza": "https://www.uninorte.edu.co/web/dunord/du-nord-plaza",
            "Café du Nord": "https://www.uninorte.edu.co/web/dunord/cafe-du-nord",
            "Restaurante 1966": "https://www.uninorte.edu.co/web/dunord/restaurante-1966",
            "du Nord Exprès": "https://www.uninorte.edu.co/web/dunord/du-nord-express",
            "du Nord Terrasse": "https://www.uninorte.edu.co/web/dunord/du-nord-terrasse",
            "Le Petit": "https://www.uninorte.edu.co/web/dunord/le-petit-cafe",
            "La Esquina": "https://www.uninorte.edu.co/web/dunord/la-esquina",
            "El Contenedor": "https://www.uninorte.edu.co/web/dunord/el-contenedor",
            "La Crepería": "https://www.uninorte.edu.co/web/dunord/la-creperia",
            "du Nord H": "https://www.uninorte.edu.co/web/dunord/du-nord-h",
            "Vending Machines": "https://www.uninorte.edu.co/web/dunord/vending-machines",
            "La Gelateria": "https://www.uninorte.edu.co/web/dunord/la-gelateria",
            "Hot Dogs": "https://www.uninorte.edu.co/web/dunord/hot-dogs",
            "Librería y Papelería KM5": "https://www.uninorte.edu.co/web/dunord/libreria-y-papeleria-km5",
            "du Nord Store": "https://www.uninorte.edu.co/web/dunord/du-nord-store",
            "du Nord Graphique": "https://www.uninorte.edu.co/web/dunord/du-nord-graphique",
            "Almacen Mapuka": "https://www.uninorte.edu.co/web/dunord/mapuka",
            "Zonas Digitales": "https://www.uninorte.edu.co/web/dunord/zonas-digitales",
            "Le Salón": "https://www.uninorte.edu.co/web/dunord/le-salon",
            "Gimnasio Uninorte": "https://www.uninorte.edu.co/web/dunord/gimnasio-uninorte",
            "Droguería": "https://www.uninorte.edu.co/web/dunord/drogueria",
            "Coliseo": "https://www.uninorte.edu.co/web/dunord/coliseo",
            "Centro Deportivo Roble Amarillo": "https://www.uninorte.edu.co/web/dunord/centro-deportivo-roble-amarillo"
        }
        
        # Normalize input for matching
        normalized_place = place.strip().lower()
        
        # Find the best match in places dictionary
        matched_place = None
        for key in places.keys():
            if normalized_place in key.lower():
                matched_place = key
                break
        
        if not matched_place:
            # Try partial matching
            for key in places.keys():
                key_parts = key.lower().split()
                if any(normalized_place in part for part in key_parts):
                    matched_place = key
                    break
        
        if not matched_place:
            # No match found
            return {
                "error": f"No se encontró información para el lugar: '{place}'. Verifica el nombre e intenta de nuevo."
            }
        
        # Extract information from the website
        url = places[matched_place]
        
        try:
            # Fetch the content
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove navigation, headers, footers and other non-content elements
            for element in soup.select('nav, header, footer, .navigation, .navbar, .menu, .sidebar, #header, #footer, #navigation, script, style, .advertisement'):
                element.decompose()
            
            # Extract the main content
            content_elements = soup.select('article, .article, section, .content, .main-content, main, .page-content, .entry-content, .portlet-body')
            
            content_text = ""
            if content_elements:
                for element in content_elements:
                    # Extract text from paragraphs, headings, lists
                    for tag in element.select('p, h1, h2, h3, h4, h5, h6, li, .description, .info, .details'):
                        if tag.text.strip():
                            content_text += tag.text.strip() + "\n\n"
            
            # If no content found with specific selectors, try to get any meaningful text
            if not content_text:
                content_text = soup.get_text(separator="\n", strip=True)
                # Clean up the text
                content_text = re.sub(r'\n\s*\n', '\n\n', content_text)
                content_text = re.sub(r'\s{2,}', ' ', content_text)
            
            # Truncate if too long
            max_length = 2000
            if len(content_text) > max_length:
                content_text = content_text[:max_length] + "..."
            
            if not content_text:
                content_text = f"Información sobre {matched_place} disponible en Universidad del Norte."
                
        except requests.RequestException:
            content_text = f"Información sobre {matched_place} - uno de los espacios de la Universidad del Norte."
            
        image_carousel_html = ""
        try:
            api_key = os.getenv("SERPAPI_KEY")
            if api_key:
                # Create search query for images
                search_query = f"{matched_place} Universidad del Norte Uninorte"
                
                params = {
                    "engine": "google_images",
                    "q": search_query,
                    "api_key": api_key,
                    "num": 8,  # Get more images for better selection
                    "safe": "active",
                    "ijn": "0"
                }
                
                search = GoogleSearch(params)
                results = search.get_dict()
                
                if "images_results" in results and results["images_results"]:
                    # Generate carousel HTML using the same structure as the investigator
                    image_carousel_html = generate_image_carousel_html(
                        results["images_results"][:6],  # Limit to 6 best images
                        max_images=6
                    )
                
        except Exception as e:
            print(f"Error searching for images: {str(e)}")
            # Continue without images if search fails
        
        # Prepare the response in the investigator format
        info_content = f"""**Información sobre {matched_place}**

{content_text}

**Enlace oficial:** {url}

**Ubicación:** Universidad del Norte, Barranquilla, Colombia

Esta información proviene del sitio web oficial de Universidad del Norte y está actualizada según la fuente institucional."""

        # Create a simple and elegant display for redirection to the official page
        display_html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); color: white; text-align: center;">
            <div style="margin-bottom: 20px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #ffffff;">
                    <path d="M21 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h6"></path>
                    <path d="m21 3-9 9"></path>
                    <path d="M15 3h6v6"></path>
                </svg>
            </div>
            
            <h2 style="margin: 0 0 15px 0; font-size: 24px; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                {matched_place}
            </h2>
            
            <p style="margin: 0 0 25px 0; font-size: 16px; opacity: 0.9; line-height: 1.5;">
                Consulta toda la información oficial, horarios, servicios y detalles actualizados en la página web de Universidad del Norte.
            </p>
            
            <a href="{url}" target="_blank" rel="noopener noreferrer" style="display: inline-block; background-color: rgba(255,255,255,0.2); color: white; text-decoration: none; padding: 15px 30px; border-radius: 50px; font-weight: 600; font-size: 16px; transition: all 0.3s ease; border: 2px solid rgba(255,255,255,0.3); backdrop-filter: blur(10px);" onmouseover="this.style.backgroundColor='rgba(255,255,255,0.3)'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 25px rgba(0,0,0,0.2)'" onmouseout="this.style.backgroundColor='rgba(255,255,255,0.2)'; this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15,3 21,3 21,9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                </svg>
                Visitar Página Oficial
            </a>
            
            <div style="margin-top: 20px; font-size: 14px; opacity: 0.8;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 5px;">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12,6 12,12 16,14"></polyline>
                </svg>
                Información actualizada • Universidad del Norte
            </div>
        </div>
        """

        result = {
            "info": info_content,
            "display": display_html
        }
        
        # Add carousel if images were found
        if image_carousel_html:
            result["graph"] = image_carousel_html
        
        return result
        
    except Exception as e:
        print(f"Error in answer_question_of_uni_premises: {str(e)}")
        return {
            "error": f"Error inesperado al buscar información sobre {place}: {str(e)}"
        }


def generate_image_carousel_html(search_results, max_images=6):
    """
    Genera HTML para un carrusel de imágenes a partir de los resultados de búsqueda de SerpAPI.
    Usa el mismo estilo que el investigador.
    """
    # Limitar a max_images resultados
    results = search_results[:max_images]
    
    if not results:
        return ""
    
    # Generar HTML para el carrusel
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Galería de Imágenes</title>
        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
                background-color: #f8fafc;
                color: #1e293b;
            }
            
            .carousel-container {
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: white;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }
            
            .carousel-title {
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 16px;
                color: #334155;
                display: flex;
                align-items: center;
            }
            
            .carousel {
                position: relative;
                overflow: hidden;
                border-radius: 8px;
            }
            
            .carousel-inner {
                display: flex;
                transition: transform 0.5s ease;
            }
            
            .carousel-item {
                min-width: 100%;
                position: relative;
            }
            
            .carousel-image {
                width: 100%;
                height: 400px;
                object-fit: cover;
                display: block;
            }
            
            .carousel-caption {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
                color: white;
                padding: 20px;
                font-size: 0.9rem;
                line-height: 1.4;
            }
            
            .carousel-controls {
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                display: flex;
                justify-content: space-between;
                width: 100%;
                padding: 0 10px;
                pointer-events: none;
            }
            
            .carousel-control {
                background-color: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s ease;
                pointer-events: auto;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            }
            
            .carousel-control:hover {
                background-color: white;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            }
            
            .carousel-indicators {
                display: flex;
                justify-content: center;
                gap: 8px;
                margin-top: 16px;
            }
            
            .carousel-indicator {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background-color: #cbd5e1;
                cursor: pointer;
                transition: background-color 0.2s ease;
            }
            
            .carousel-indicator.active {
                background-color: #3b82f6;
            }
            
            .carousel-attribution {
                margin-top: 12px;
                font-size: 0.75rem;
                color: #94a3b8;
                text-align: center;
            }
            
            @media (max-width: 640px) {
                .carousel-container {
                    padding: 12px;
                }
                
                .carousel-image {
                    height: 300px;
                }
            }
        </style>
    </head>
    <body>
        <div class="carousel-container">
            <h2 class="carousel-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                Galería de Imágenes
            </h2>
            <div class="carousel" id="imageCarousel">
                <div class="carousel-inner" id="carouselInner">
    """
    
    # Generar HTML para cada imagen
    for i, image in enumerate(results):
        # Obtener información de la imagen
        title = image.get("title", "").replace('"', "&quot;").replace("'", "&#39;")
        source = image.get("source", "")
        image_url = image.get("original", image.get("thumbnail", ""))
        
        if not image_url:
            continue
            
        html += f"""
                    <div class="carousel-item" id="slide{i}">
                        <img src="{image_url}" alt="{title}" class="carousel-image" />
                        <div class="carousel-caption">
                            {title}
                            <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 4px;">Fuente: {source}</div>
                        </div>
                    </div>
        """
    
    # Añadir controles y indicadores
    html += """
                </div>
                <div class="carousel-controls">
                    <div class="carousel-control" id="prevButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                    </div>
                    <div class="carousel-control" id="nextButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                    </div>
                </div>
                <div class="carousel-indicators" id="indicators">
    """
    
    # Generar indicadores
    for i in range(len(results)):
        active = "active" if i == 0 else ""
        html += f'<div class="carousel-indicator {active}" data-slide="{i}"></div>'
    
    # Cerrar el HTML con JavaScript para el carrusel
    html += """
                </div>
            </div>
            <div class="carousel-attribution">
                Imágenes proporcionadas a través de Google Image Search
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const carousel = document.getElementById('imageCarousel');
                const inner = document.getElementById('carouselInner');
                const indicators = document.querySelectorAll('.carousel-indicator');
                const prevButton = document.getElementById('prevButton');
                const nextButton = document.getElementById('nextButton');
                
                let currentSlide = 0;
                const slideCount = indicators.length;
                
                if (slideCount === 0) return;
                
                function showSlide(index) {
                    if (index < 0) index = slideCount - 1;
                    if (index >= slideCount) index = 0;
                    
                    currentSlide = index;
                    inner.style.transform = `translateX(-${currentSlide * 100}%)`;
                    
                    indicators.forEach((indicator, i) => {
                        if (i === currentSlide) {
                            indicator.classList.add('active');
                        } else {
                            indicator.classList.remove('active');
                        }
                    });
                }
                
                prevButton.addEventListener('click', () => {
                    showSlide(currentSlide - 1);
                });
                
                nextButton.addEventListener('click', () => {
                    showSlide(currentSlide + 1);
                });
                
                indicators.forEach((indicator, index) => {
                    indicator.addEventListener('click', () => {
                        showSlide(index);
                    });
                });
                
                // Auto-advance every 5 seconds
                let autoplayInterval = setInterval(() => {
                    showSlide(currentSlide + 1);
                }, 5000);
                
                // Pause on hover
                carousel.addEventListener('mouseenter', () => {
                    clearInterval(autoplayInterval);
                });
                
                // Resume on leave
                carousel.addEventListener('mouseleave', () => {
                    autoplayInterval = setInterval(() => {
                        showSlide(currentSlide + 1);
                    }, 5000);
                });
                
                // Keyboard navigation
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'ArrowLeft') {
                        showSlide(currentSlide - 1);
                    } else if (e.key === 'ArrowRight') {
                        showSlide(currentSlide + 1);
                    }
                });
                
                showSlide(0);
            });
        </script>
    </body>
    </html>
    """
    
    return html

def get_location_events(location: str = "Barranquilla", user_id: int = 0, status: str = "") -> dict:
    """
    Get events happening in a specific location using SerpAPI.
    Returns both display and graph using real event images.
    """
    try:
        if user_id:
            set_status(user_id, status, 5)

        api_key = os.getenv('SERPAPI_KEY')
        if not api_key:
            raise ValueError("SERPAPI_KEY not found in environment variables")

        params_google = {
            "engine": "google_events",
            "q": f"Events in {location}",
            "hl": "es",
            "gl": "co",
            "api_key": api_key
        }

        search = GoogleSearch(params_google)
        results = search.get_dict()
        
        if "events_results" not in results:
            return {"error": f"No se encontraron eventos para {location}"}
            
        events_results = results["events_results"]
        
        # Generate display and collect real images
        display_html = generate_events_display(events_results, location)
        
        # Extract real images from events results
        event_images = []
        for event in events_results[:8]:
            if 'thumbnail' in event and event['thumbnail']:
                event_images.append({
                    'url': event['thumbnail'],
                    'title': event.get('title', 'Evento'),
                    'venue': event.get('venue', {}).get('name', 'Lugar por confirmar'),
                    'date': event.get('date', {}).get('start_date', 'Fecha por confirmar')
                })
        
        graph_html = generate_functional_carousel(event_images, f"Eventos en {location}", "events")
        
        return {
            "display": display_html,
            "graph": graph_html
        }
        
    except Exception as e:
        print(f"Error in get_location_events: {str(e)}")
        return {"error": f"Error al buscar eventos: {str(e)}"}


def get_restaurants(location: str = "Barranquilla", food_query: str = "restaurants", user_id: int = 0, status: str = "") -> dict:
    """
    Get restaurants in a specific location using SerpAPI.
    Returns both display and graph using real restaurant images.
    """
    try:
        if user_id:
            set_status(user_id, status, 5)

        api_key = os.getenv('SERPAPI_KEY')
        if not api_key:
            raise ValueError("SERPAPI_KEY not found in environment variables")

        params = {
            "engine": "google_local",
            "q": food_query,
            "location": location,
            "api_key": api_key
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "local_results" not in results:
            return {"error": f"No se encontraron restaurantes para {food_query} en {location}"}
            
        local_results = results["local_results"]
        
        # Generate display and collect real images
        display_html = generate_restaurants_display(local_results, location, food_query)
        
        # Extract real images from restaurant results
        restaurant_images = []
        for restaurant in local_results[:8]:
            if 'thumbnail' in restaurant and restaurant['thumbnail']:
                restaurant_images.append({
                    'url': restaurant['thumbnail'],
                    'title': restaurant.get('title', 'Restaurante'),
                    'rating': restaurant.get('rating', 0),
                    'price': restaurant.get('price', ''),
                    'type': restaurant.get('type', '')
                })
        
        graph_html = generate_functional_carousel(restaurant_images, f"Restaurantes en {location}", "restaurants")
        
        return {
            "display": display_html,
            "graph": graph_html
        }
        
    except Exception as e:
        print(f"Error in get_restaurants: {str(e)}")
        return {"error": f"Error al buscar restaurantes: {str(e)}"}


def get_location_places(location: str = "Barranquilla", user_id: int = 0, status: str = "", location_query: str = "") -> dict:
    """
    Get places to visit in a specific location using SerpAPI.
    Returns both display and graph using real place images.
    """
    try:
        if user_id:
            set_status(user_id, status, 5)

        api_key = os.getenv('SERPAPI_KEY')
        if not api_key:
            raise ValueError("SERPAPI_KEY not found in environment variables")

        params = {
            "engine": "google_local",
            "q": location_query or "places to visit",
            "location": location,
            "api_key": api_key
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "local_results" not in results:
            return {"error": f"No se encontraron lugares para visitar en {location}"}
            
        local_results = results["local_results"]
        
        # Generate display and collect real images
        display_html = generate_places_display(local_results, location)
        
        # Extract real images from places results
        place_images = []
        for place in local_results[:8]:
            if 'thumbnail' in place and place['thumbnail']:
                place_images.append({
                    'url': place['thumbnail'],
                    'title': place.get('title', 'Lugar'),
                    'rating': place.get('rating', 0),
                    'type': place.get('type', ''),
                    'address': place.get('address', '')
                })
        
        graph_html = generate_functional_carousel(place_images, f"Lugares en {location}", "places")
        
        return {
            "display": display_html,
            "graph": graph_html
        }
        
    except Exception as e:
        print(f"Error in get_location_places: {str(e)}")
        return {"error": f"Error al buscar lugares: {str(e)}"}


def generate_functional_carousel(images: list, title: str, carousel_type: str) -> str:
    """
    Generate a fully functional image carousel using real images from API results.
    """
    if not images:
        return f"""
        <div style="text-align: center; padding: 40px; color: #666;">
            <div style="font-size: 48px; margin-bottom: 16px;">📷</div>
            <p>No hay imágenes disponibles para mostrar</p>
        </div>
        """
    
    # Generate carousel items HTML
    carousel_items = ""
    indicators = ""
    
    for i, img in enumerate(images):
        # Create caption based on carousel type
        if carousel_type == "events":
            caption = f"""
                <div class="carousel-caption">
                    <h3>{img['title']}</h3>
                    <p>📍 {img['venue']}</p>
                    <p>📅 {img['date']}</p>
                </div>
            """
        elif carousel_type == "restaurants":
            stars = "⭐" * int(img['rating']) if img['rating'] else ""
            caption = f"""
                <div class="carousel-caption">
                    <h3>{img['title']}</h3>
                    <p>{stars} {img['rating']}/5</p>
                    <p>💰 {img['price']} • {img['type']}</p>
                </div>
            """
        else:  # places
            stars = "⭐" * int(img['rating']) if img['rating'] else ""
            caption = f"""
                <div class="carousel-caption">
                    <h3>{img['title']}</h3>
                    <p>{stars} {img['rating']}/5</p>
                    <p>📂 {img['type']}</p>
                </div>
            """
        
        carousel_items += f"""
                    <div class="carousel-item" id="slide{i}">
                        <img src="{img['url']}" alt="{img['title']}" class="carousel-image" />
                        {caption}
                    </div>
        """
        indicators += f'<div class="carousel-indicator" data-slide="{i}"></div>'
    
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
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
            }}
            
            .carousel-inner {{
                display: flex;
                transition: transform 0.5s ease;
            }}
            
            .carousel-item {{
                min-width: 100%;
                position: relative;
            }}
            
            .carousel-image {{
                width: 100%;
                height: 400px;
                object-fit: cover;
                display: block;
            }}
            
            .carousel-caption {{
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
                color: white;
                padding: 20px;
                font-size: 0.9rem;
                line-height: 1.4;
            }}
            
            .carousel-caption h3 {{
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 8px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.5);
            }}
            
            .carousel-caption p {{
                font-size: 14px;
                margin: 4px 0;
                opacity: 0.9;
            }}
            
            .carousel-controls {{
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                display: flex;
                justify-content: space-between;
                width: 100%;
                padding: 0 10px;
                pointer-events: none;
            }}
            
            .carousel-control {{
                background-color: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s ease;
                pointer-events: auto;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            }}
            
            .carousel-control:hover {{
                background-color: white;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            }}
            
            .carousel-indicators {{
                display: flex;
                justify-content: center;
                gap: 8px;
                margin-top: 16px;
            }}
            
            .carousel-indicator {{
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background-color: #cbd5e1;
                cursor: pointer;
                transition: background-color 0.2s ease;
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
                
                .carousel-image {{
                    height: 300px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="carousel-container">
            <h2 class="carousel-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                {title}
            </h2>
            <div class="carousel" id="imageCarousel">
                <div class="carousel-inner" id="carouselInner">
                    {carousel_items}
                </div>
                <div class="carousel-controls">
                    <div class="carousel-control" id="prevButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                    </div>
                    <div class="carousel-control" id="nextButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                    </div>
                </div>
                <div class="carousel-indicators" id="indicators">
                    {indicators}
                </div>
            </div>
            <div class="carousel-attribution">
                Imágenes de resultados de búsqueda
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const carousel = document.getElementById('imageCarousel');
                const inner = document.getElementById('carouselInner');
                const indicators = document.querySelectorAll('.carousel-indicator');
                const prevButton = document.getElementById('prevButton');
                const nextButton = document.getElementById('nextButton');
                
                let currentSlide = 0;
                const slideCount = {len(images)};
                
                if (slideCount === 0) return;
                
                function showSlide(index) {{
                    if (index < 0) index = slideCount - 1;
                    if (index >= slideCount) index = 0;
                    
                    currentSlide = index;
                    inner.style.transform = `translateX(-${{currentSlide * 100}}%)`;
                    
                    indicators.forEach((indicator, i) => {{
                        indicator.classList.toggle('active', i === currentSlide);
                    }});
                }}
                
                prevButton.addEventListener('click', () => {{
                    showSlide(currentSlide - 1);
                }});
                
                nextButton.addEventListener('click', () => {{
                    showSlide(currentSlide + 1);
                }});
                
                indicators.forEach((indicator, index) => {{
                    indicator.addEventListener('click', () => {{
                        showSlide(index);
                    }});
                }});
                
                // Auto-advance every 5 seconds
                let autoplayInterval = setInterval(() => {{
                    showSlide(currentSlide + 1);
                }}, 5000);
                
                // Pause on hover
                carousel.addEventListener('mouseenter', () => {{
                    clearInterval(autoplayInterval);
                }});
                
                // Resume on leave
                carousel.addEventListener('mouseleave', () => {{
                    autoplayInterval = setInterval(() => {{
                        showSlide(currentSlide + 1);
                    }}, 5000);
                }});
                
                // Keyboard navigation
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


# === DISPLAY FUNCTIONS (keeping the existing ones) ===

def generate_events_display(events_results: list, location: str) -> str:
    """Generate elegant display for events."""
    events_cards = ""
    
    for i, event in enumerate(events_results[:6]):  # Limit to 6 events
        title = event.get("title", "Evento sin título")
        date = event.get("date", {})
        venue = event.get("venue", {})
        
        # Format date
        date_str = "Fecha por confirmar"
        if date:
            start_date = date.get("start_date", "")
            if start_date:
                date_str = start_date
        
        # Format venue
        venue_name = venue.get("name", "Lugar por confirmar") if venue else "Lugar por confirmar"
        
        # Format description
        description = event.get("description", "")
        if len(description) > 100:
            description = description[:100] + "..."
        
        events_cards += f"""
        <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; border-left: 4px solid #3498db; transition: transform 0.3s ease;"
             onmouseover="this.style.transform='translateY(-5px)'"
             onmouseout="this.style.transform='translateY(0)'">
            <div style="display: flex; align-items: flex-start; gap: 15px;">
                <div style="background: linear-gradient(135deg, #3498db, #2980b9); color: white; border-radius: 10px; padding: 10px; text-align: center; min-width: 60px;">
                    <div style="font-size: 20px; font-weight: bold;">📅</div>
                    <div style="font-size: 10px; opacity: 0.9;">{i+1}</div>
                </div>
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 18px; font-weight: 600;">{title}</h3>
                    <div style="color: #7f8c8d; font-size: 14px; margin-bottom: 5px;">
                        <strong>📍 Lugar:</strong> {venue_name}
                    </div>
                    <div style="color: #7f8c8d; font-size: 14px; margin-bottom: 8px;">
                        <strong>🗓️ Fecha:</strong> {date_str}
                    </div>
                    {f'<p style="color: #34495e; font-size: 13px; margin: 0; line-height: 1.4;">{description}</p>' if description else ''}
                </div>
            </div>
        </div>
        """
    
    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 700px; margin: 0 auto; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.2); color: white;">
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 48px; margin-bottom: 15px;">🎉</div>
            <h2 style="margin: 0 0 10px 0; font-size: 28px; font-weight: 700; text-shadow: 0 3px 6px rgba(0,0,0,0.4);">
                Eventos en {location}
            </h2>
            <p style="margin: 0; font-size: 16px; opacity: 0.9;">
                Descubre los mejores eventos happening en tu ciudad
            </p>
        </div>
        
        <div style="background: rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; backdrop-filter: blur(10px);">
            {events_cards}
        </div>
        
        <div style="text-align: center; margin-top: 20px; font-size: 14px; opacity: 0.8;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 5px;">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12,6 12,12 16,14"></polyline>
            </svg>
            Información actualizada • Google Events
        </div>
    </div>
    """


def generate_restaurants_display(restaurants: list, location: str, query: str) -> str:
    """Generate elegant display for restaurants."""
    restaurant_cards = ""
    
    for i, restaurant in enumerate(restaurants[:8]):  # Limit to 8 restaurants
        title = restaurant.get("title", "Restaurante")
        rating = restaurant.get("rating", 0)
        price = restaurant.get("price", "")
        type_cuisine = restaurant.get("type", "")
        address = restaurant.get("address", "")
        
        # Generate star rating
        stars = ""
        for j in range(5):
            if j < int(rating):
                stars += "⭐"
            else:
                stars += "☆"
        
        price_display = f"💰 {price}" if price else ""
        type_display = f"🍽️ {type_cuisine}" if type_cuisine else ""
        
        restaurant_cards += f"""
        <div style="background: white; border-radius: 12px; padding: 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 15px; border-left: 4px solid #e74c3c; transition: transform 0.3s ease;"
             onmouseover="this.style.transform='translateY(-3px)'"
             onmouseout="this.style.transform='translateY(0)'">
            <div style="display: flex; align-items: flex-start; gap: 15px;">
                <div style="background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; border-radius: 10px; padding: 10px; text-align: center; min-width: 50px;">
                    <div style="font-size: 18px;">🍴</div>
                    <div style="font-size: 10px; opacity: 0.9;">{i+1}</div>
                </div>
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 16px; font-weight: 600;">{title}</h3>
                    <div style="margin-bottom: 5px;">
                        <span style="color: #f39c12; font-size: 14px;">{stars}</span>
                        <span style="color: #7f8c8d; font-size: 13px; margin-left: 5px;">({rating})</span>
                    </div>
                    <div style="color: #7f8c8d; font-size: 12px; margin-bottom: 5px;">
                        {type_display} {price_display}
                    </div>
                    <div style="color: #95a5a6; font-size: 11px;">📍 {address}</div>
                </div>
            </div>
        </div>
        """
    
    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 750px; margin: 0 auto; padding: 25px; background: linear-gradient(135deg, #fd746c 0%, #ff9068 100%); border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.2); color: white;">
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 48px; margin-bottom: 15px;">🍽️</div>
            <h2 style="margin: 0 0 10px 0; font-size: 28px; font-weight: 700; text-shadow: 0 3px 6px rgba(0,0,0,0.4);">
                Restaurantes en {location}
            </h2>
            <p style="margin: 0; font-size: 16px; opacity: 0.9;">
                {query} - Las mejores opciones gastronómicas
            </p>
        </div>
        
        <div style="background: rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; backdrop-filter: blur(10px); max-height: 500px; overflow-y: auto;">
            {restaurant_cards}
        </div>
        
        <div style="text-align: center; margin-top: 20px; font-size: 14px; opacity: 0.8;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 5px;">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12,6 12,12 16,14"></polyline>
            </svg>
            Información actualizada • Google Local
        </div>
    </div>
    """


def generate_places_display(places: list, location: str) -> str:
    """Generate elegant display for places to visit."""
    places_cards = ""
    
    for i, place in enumerate(places[:6]):  # Limit to 6 places
        title = place.get("title", "Lugar")
        rating = place.get("rating", 0)
        type_place = place.get("type", "")
        address = place.get("address", "")
        description = place.get("description", "")
        
        if len(description) > 120:
            description = description[:120] + "..."
        
        # Generate star rating
        stars = ""
        for j in range(5):
            if j < int(rating):
                stars += "⭐"
            else:
                stars += "☆"
        
        # Choose emoji based on type
        emoji = "📍"
        if "museum" in type_place.lower():
            emoji = "🏛️"
        elif "park" in type_place.lower():
            emoji = "🌳"
        elif "beach" in type_place.lower():
            emoji = "🏖️"
        elif "restaurant" in type_place.lower():
            emoji = "🍽️"
        elif "church" in type_place.lower() or "cathedral" in type_place.lower():
            emoji = "⛪"
        
        places_cards += f"""
        <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; border-left: 4px solid #27ae60; transition: transform 0.3s ease;"
             onmouseover="this.style.transform='translateY(-5px)'"
             onmouseout="this.style.transform='translateY(0)'">
            <div style="display: flex; align-items: flex-start; gap: 15px;">
                <div style="background: linear-gradient(135deg, #27ae60, #2ecc71); color: white; border-radius: 10px; padding: 12px; text-align: center; min-width: 60px;">
                    <div style="font-size: 24px;">{emoji}</div>
                    <div style="font-size: 10px; opacity: 0.9;">{i+1}</div>
                </div>
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 18px; font-weight: 600;">{title}</h3>
                    <div style="margin-bottom: 8px;">
                        <span style="color: #f39c12; font-size: 14px;">{stars}</span>
                        <span style="color: #7f8c8d; font-size: 13px; margin-left: 5px;">({rating})</span>
                    </div>
                    <div style="color: #7f8c8d; font-size: 14px; margin-bottom: 8px;">
                        <strong>📂 Tipo:</strong> {type_place}
                    </div>
                    <div style="color: #95a5a6; font-size: 12px; margin-bottom: 8px;">📍 {address}</div>
                    {f'<p style="color: #34495e; font-size: 13px; margin: 0; line-height: 1.4;">{description}</p>' if description else ''}
                </div>
            </div>
        </div>
        """
    
    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 700px; margin: 0 auto; padding: 25px; background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%); border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.2); color: white;">
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 48px; margin-bottom: 15px;">🗺️</div>
            <h2 style="margin: 0 0 10px 0; font-size: 28px; font-weight: 700; text-shadow: 0 3px 6px rgba(0,0,0,0.4);">
                Lugares en {location}
            </h2>
            <p style="margin: 0; font-size: 16px; opacity: 0.9;">
                Descubre los mejores sitios para visitar y explorar
            </p>
        </div>
        
        <div style="background: rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; backdrop-filter: blur(10px);">
            {places_cards}
        </div>
        
        <div style="text-align: center; margin-top: 20px; font-size: 14px; opacity: 0.8;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 5px;">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12,6 12,12 16,14"></polyline>
            </svg>
            Información actualizada • Google Local
        </div>
    </div>
    """



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
            set_status(user_id, status or "Sending email...", 5)

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