import urllib.parse
import requests
from typing import Dict
from apps.users.services import UserService
from apps.status.services import set_status
import json

def search_university_staff(name: str, user_id: int, status: str) -> Dict:
    """
    Search for university staff and faculty using Microsoft Graph API with improved search strategy.
    Returns detailed information with photos in HTML format.
    
    Args:
        name (str): The name to search for
        user_id (int): The ID of the user making the search
        status (str): Status message for tracking
        
    Returns:
        dict: Contains 'display' key with HTML formatted results
    """
    set_status(user_id, status, 5)
    
    # Validate required fields
    search_name = name
    if not search_name:
        return {"error": "El nombre es requerido para buscar personal universitario"}
    
    try:
        # Get user's Microsoft Graph token using existing UserService
        user_service = UserService()
        access_token = user_service.get_user_token(user_id)
        
        if not access_token:
            return {"error": "No se encontró token de acceso. Por favor autentícate con Microsoft primero."}
        
        # Set up headers with authentication
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        print(f"Searching university staff for: {search_name}")
        
        all_results = []
        seen_ids = set()
        name_parts = [part.strip() for part in search_name.split() if part.strip()]
        search_name_lower = search_name.lower()
        
        print(f"Name parts to search: {name_parts}")
        
        # URL encode the search term properly
        encoded_name = urllib.parse.quote(search_name)
        
        # Strategy 1: Get ALL users and filter locally (most reliable like in search_contacts)
        try:
            print("Strategy 1: Getting ALL users and filtering locally...")
            all_users_url = "https://graph.microsoft.com/v1.0/users?$select=id,displayName,mail,jobTitle,department,userPrincipalName,givenName,surname,usageLocation&$top=999"
            
            print(f"Executing query: {all_users_url}")
            response = requests.get(all_users_url, headers=headers, timeout=30)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('value', [])
                print(f"Found {len(users)} total users to filter")
                
                for user in users:
                    user_id_graph = user.get('id')
                    display_name = user.get('displayName', '')
                    
                    if user_id_graph and user_id_graph not in seen_ids:
                        # Filter for university staff (has jobTitle or department)
                        if user.get('jobTitle') or user.get('department'):
                            # Check if any part of the search name appears in the display name
                            name_match = False
                            for part in name_parts:
                                if len(part) >= 2 and part.lower() in display_name.lower():
                                    name_match = True
                                    break
                            
                            if name_match:
                                seen_ids.add(user_id_graph)
                                all_results.append(user)
                                
                                # DEBUG: Print detailed user information
                                print("="*80)
                                print(f"MATCH FOUND: {display_name}")
                                print("="*80)
                                print("COMPLETE USER DATA:")
                                print(json.dumps(user, indent=2, ensure_ascii=False))
                                print("="*80)
                
                print(f"Strategy 1 found {len(all_results)} matching users")
                
            else:
                print(f"Strategy 1 failed with status: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error in Strategy 1: {str(e)}")
        
        # Strategy 2: Use $search (if we don't have enough results)
        if len(all_results) < 5:
            try:
                print("Strategy 2: Using $search...")
                search_queries = [
                    f"https://graph.microsoft.com/v1.0/users?$search=\"{encoded_name}\"&$select=id,displayName,mail,jobTitle,department,userPrincipalName,givenName,surname,usageLocation&$top=100"
                ]
                
                for query_url in search_queries:
                    try:
                        print(f"Executing search query: {query_url}")
                        response = requests.get(query_url, headers=headers, timeout=15)
                        print(f"Search response status: {response.status_code}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            users = data.get('value', [])
                            print(f"Search found {len(users)} users")
                            
                            for user in users:
                                user_id_graph = user.get('id')
                                if user_id_graph and user_id_graph not in seen_ids:
                                    if user.get('jobTitle') or user.get('department'):
                                        seen_ids.add(user_id_graph)
                                        all_results.append(user)
                                        print(f"Search added: {user.get('displayName', 'Unknown')}")
                        else:
                            print(f"Search API Error: {response.status_code} - {response.text}")
                            
                    except Exception as e:
                        print(f"Error in search query: {str(e)}")
                        continue
                        
            except Exception as e:
                print(f"Error in Strategy 2: {str(e)}")
        
        # Strategy 3: Search by givenName and surname (if still not enough results)
        if len(all_results) < 5:
            try:
                print("Strategy 3: Searching by givenName and surname...")
                for part in name_parts:
                    encoded_part = urllib.parse.quote(part)
                    name_field_queries = [
                        f"https://graph.microsoft.com/v1.0/users?$filter=startswith(givenName,'{encoded_part}')&$select=id,displayName,mail,jobTitle,department,userPrincipalName,givenName,surname,usageLocation&$top=50",
                        f"https://graph.microsoft.com/v1.0/users?$filter=startswith(surname,'{encoded_part}')&$select=id,displayName,mail,jobTitle,department,userPrincipalName,givenName,surname,usageLocation&$top=50"
                    ]
                    
                    for query_url in name_field_queries:
                        try:
                            print(f"Executing name field query: {query_url}")
                            response = requests.get(query_url, headers=headers, timeout=15)
                            print(f"Name field response status: {response.status_code}")
                            
                            if response.status_code == 200:
                                data = response.json()
                                users = data.get('value', [])
                                print(f"Name field search found {len(users)} users")
                                
                                for user in users:
                                    user_id_graph = user.get('id')
                                    if user_id_graph and user_id_graph not in seen_ids:
                                        if user.get('jobTitle') or user.get('department'):
                                            seen_ids.add(user_id_graph)
                                            all_results.append(user)
                                            print(f"Name field added: {user.get('displayName', 'Unknown')}")
                            else:
                                print(f"Name field API Error: {response.status_code} - {response.text}")
                                
                        except Exception as e:
                            print(f"Error in name field query: {str(e)}")
                            continue
                            
            except Exception as e:
                print(f"Error in Strategy 3: {str(e)}")
        
        # Enhanced relevance scoring
        def calculate_relevance_score(user):
            display_name = user.get('displayName', '').lower()
            given_name = user.get('givenName', '').lower()
            surname = user.get('surname', '').lower()
            job_title = user.get('jobTitle', '').lower()
            department = user.get('department', '').lower()
            
            score = 0
            
            # Exact name match gets highest score
            if search_name_lower == display_name:
                score += 1000
            
            # Check if all name parts are present in display name
            all_parts_in_display = all(part.lower() in display_name for part in name_parts)
            if all_parts_in_display:
                score += 500
                
            # Check individual name parts
            for part in name_parts:
                part_lower = part.lower()
                if part_lower in display_name:
                    score += 100
                if part_lower in given_name:
                    score += 80
                if part_lower in surname:
                    score += 80
            
            # Prioritize actual staff/faculty over students/graduates
            if 'profesor' in job_title or 'professor' in job_title:
                score += 200
            elif 'funcionario' in job_title or 'funcionario' in department:
                score += 150
            elif 'coordinador' in job_title or 'director' in job_title:
                score += 180
            elif 'estudiante' in job_title or 'student' in job_title or department == 'estudiantes':
                score -= 100
            elif 'egresado' in job_title or 'graduate' in job_title or department == 'egresados':
                score -= 200
                
            return score
        
        # Apply scoring and sort
        for user in all_results:
            user['relevance_score'] = calculate_relevance_score(user)
        
        # Sort by relevance and limit results
        all_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        final_results = all_results[:10]  # Limit to 10 results
        
        # Filter out very low relevance results
        final_results = [user for user in final_results if user['relevance_score'] > 50]
        
        print(f"Final results count: {len(final_results)}")
        print("FINAL RESULTS SUMMARY:")
        for i, user in enumerate(final_results, 1):
            print(f"{i}. {user.get('displayName', 'N/A')} - {user.get('jobTitle', 'N/A')} - {user.get('department', 'N/A')} (Score: {user.get('relevance_score', 0)})")
        
        if not final_results:
            return {
                "display": _generate_no_results_html(search_name),
                "message": f"No se encontró personal universitario con el nombre '{search_name}'. Intenta con variaciones del nombre o verifica la ortografía."
            }
        
        # Get profile photos for each user
        enhanced_results = []
        for user in final_results:
            enhanced_user = user.copy()
            
            # Try to get user's profile photo
            try:
                photo_url = f"https://graph.microsoft.com/v1.0/users/{user['id']}/photo/$value"
                photo_response = requests.get(photo_url, headers=headers, timeout=10)
                if photo_response.status_code == 200:
                    import base64
                    photo_base64 = base64.b64encode(photo_response.content).decode('utf-8')
                    enhanced_user['photo_base64'] = f"data:image/jpeg;base64,{photo_base64}"
                    print(f"✅ Photo found for {user.get('displayName', 'Unknown')}")
                else:
                    enhanced_user['photo_base64'] = None
                    print(f"❌ No photo for {user.get('displayName', 'Unknown')} - Status: {photo_response.status_code}")
            except Exception as e:
                print(f"❌ Error getting photo for user {user.get('displayName', 'Unknown')}: {str(e)}")
                enhanced_user['photo_base64'] = None
            
            enhanced_results.append(enhanced_user)
        
        # Generate HTML display
        html_display = _generate_staff_search_html(enhanced_results, search_name)
        
        return {
            "display": html_display,
            "message": f"Se encontraron {len(enhanced_results)} miembros del personal universitario que coinciden con '{search_name}'. Revisa la pantalla para ver los detalles completos."
        }
        
    except requests.exceptions.Timeout:
        return {"error": "Tiempo de espera agotado al buscar personal universitario"}
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Error de red al buscar personal universitario: {str(e)}"}
    
    except Exception as e:
        return {"error": f"Error inesperado al buscar personal universitario: {str(e)}"}


def _generate_staff_search_html(staff_results, search_name):
    """Generate HTML display for university staff search results with relevance indicators"""
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
        # Extract and clean data (only use available fields based on the logs)
        name = staff.get('displayName', 'Nombre no disponible')
        email = staff.get('mail', staff.get('userPrincipalName', 'Email no disponible'))
        job_title = staff.get('jobTitle', '')
        department = staff.get('department', '')
        given_name = staff.get('givenName', '')
        surname = staff.get('surname', '')
        usage_location = staff.get('usageLocation', '')
        photo_base64 = staff.get('photo_base64')
        relevance_score = staff.get('relevance_score', 0)
        
        # Determine relevance indicator
        if relevance_score >= 500:
            relevance_indicator = "🎯 Coincidencia Exacta"
            relevance_color = "#10b981"
        elif relevance_score >= 200:
            relevance_indicator = "✅ Muy Relevante"
            relevance_color = "#3b82f6"
        elif relevance_score >= 100:
            relevance_indicator = "⭐ Relevante"
            relevance_color = "#f59e0b"
        else:
            relevance_indicator = "📋 Posible Coincidencia"
            relevance_color = "#6b7280"
        
        # Build department display
        dept_display = ""
        if department:
            dept_display = f"<p><strong>🏫 Departamento:</strong> {department}</p>"
        
        # Build job title display
        job_display = ""
        if job_title:
            job_display = f"<p><strong>💼 Cargo:</strong> {job_title}</p>"
        
        # Build name details if different from displayName
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
                    <span style="background-color: {relevance_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                        {relevance_indicator}
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
                        Resultado #{i} (Puntuación: {relevance_score})
                    </span>
                </div>
            </div>
        """
    
    html += """
        </div>
        
        <div style="background-color: #e6fffa; padding: 20px; margin-top: 30px; border-radius: 8px; border-left: 4px solid #38b2ac;">
            <h3 style="margin: 0 0 10px 0; color: #234e52; font-size: 18px;">💡 Consejos de Búsqueda</h3>
            <ul style="margin: 0; padding-left: 20px; color: #2d3748; line-height: 1.6;">
                <li>Los resultados están ordenados por relevancia con tu búsqueda</li>
                <li>Si no encuentras a quien buscas, intenta con variaciones del nombre</li>
                <li>Puedes buscar por nombre, apellido, o nombre completo</li>
                <li>Los datos mostrados provienen del directorio oficial de la universidad</li>
                <li>Se priorizan profesores y funcionarios sobre estudiantes y egresados</li>
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
                    <li>Prueba con variaciones como "Chris" o apellidos compuestos</li>
                    <li>Asegúrate de que la persona es personal activo de la universidad</li>
                </ul>
            </div>
        </div>
    </div>
    """