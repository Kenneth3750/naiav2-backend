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
import json
from bs4 import BeautifulSoup
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

def query_recepcionist_rag(user_id: int, question: str, k: int = 3, status:str = "") -> dict:
    """
    Query the information stored in the vector store and generate a response.
    """
    try:
        set_status(user_id, status, 2)
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
        return {"resolved_rag": result_text}

    except Exception as e:
        print(f"Error retrieving documents: {str(e)}")
        return {"error": str(e)}



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
    Answer questions about university premises by scraping relevant content from the official website.
    """
    set_status(user_id, status, 5)
    
    if not place:
        return {"error": "El lugar es requerido para responder preguntas sobre las instalaciones universitarias"}
    
    try:
        places = {
            "Restaurante Bocas de Ceniza": "https://www.uninorte.edu.co/web/dunord/bocas-de-ceniza",
            "Restaurante du Nord Plaza": "https://www.uninorte.edu.co/web/dunord/du-nord-plaza",
            "Café du Nord": "https://www.uninorte.edu.co/web/dunord/cafe-du-nord",
            "Restaurante 1966": "https://www.uninorte.edu.co/web/dunord/restarurante-1966",
            "du Nord Exprès": "https://www.uninorte.edu.co/web/dunord/du-nord-expres",
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
        
        if matched_place:
            url = places[matched_place]
            
            # Fetch the content
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove navigation, headers, footers and other non-content elements
            for element in soup.select('nav, header, footer, .navigation, .navbar, .menu, .sidebar, #header, #footer, #navigation, script, style, .advertisement'):
                element.decompose()
            
            # Extract the main content - focus on article, section or main content div
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
                
                # Clean up the text by removing consecutive newlines and whitespace
                content_text = re.sub(r'\n\s*\n', '\n\n', content_text)
                content_text = re.sub(r'\s{2,}', ' ', content_text)
            
            if content_text:
                # Truncate if too long (keeping it under a reasonable size)
                max_length = 3000
                if len(content_text) > max_length:
                    content_text = content_text[:max_length] + "... [Contenido truncado]"
                
                return {
                    "display": f"""
                    <div style="font-family: Arial, sans-serif; padding: 15px; background-color: #f9f9f9; border-radius: 8px; margin-top: 10px;">
                        <h2 style="color: #1a365d;">Información sobre: {matched_place}</h2>
                        <div style="white-space: pre-wrap; line-height: 1.5;">{content_text}</div>
                        <p style="margin-top: 20px; font-size: 0.9em;">
                            <a href="{url}" target="_blank" style="color: #3182ce;">Ver información completa en el sitio web</a>
                        </p>
                    </div>
                    """,
                    "message": f"He encontrado información sobre {matched_place}. La información se muestra en pantalla."
                }
            else:
                return {
                    "display": f"""
                    <div style="font-family: Arial, sans-serif; padding: 15px; background-color: #f9f9f9; border-radius: 8px;">
                        <h2 style="color: #1a365d;">Información sobre: {matched_place}</h2>
                        <p>La página existe pero no se pudo extraer el contenido relevante.</p>
                        <p>
                            <a href="{url}" target="_blank" style="color: #3182ce;">Visitar la página directamente</a>
                        </p>
                    </div>
                    """,
                    "message": f"La página de {matched_place} existe, pero no pude extraer la información. He proporcionado un enlace directo."
                }
        else:
            return {
                "display": f"""
                <div style="font-family: Arial, sans-serif; padding: 15px; background-color: #f9f9f9; border-radius: 8px;">
                    <h2 style="color: #1a365d;">Lugar no encontrado</h2>
                    <p>No se encontró información específica para el lugar: <strong>{place}</strong>.</p>
                    <p>Lugares disponibles:</p>
                    <ul style="columns: 2; column-gap: 20px;">
                        {' '.join([f'<li>{p}</li>' for p in sorted(places.keys())])}
                    </ul>
                </div>
                """,
                "message": f"No se encontró información para '{place}'. Intenta con otro lugar o revisa la lista de lugares disponibles."
            }
        
    except requests.RequestException as e:
        return {
            "display": f"<p>Error al acceder al sitio web: {str(e)}</p>",
            "message": "No pude acceder al sitio web de la universidad. Verifica la conexión a internet."
        }
    except Exception as e:
        return {
            "error": f"Error inesperado al responder preguntas sobre las instalaciones universitarias: {str(e)}"
        }
