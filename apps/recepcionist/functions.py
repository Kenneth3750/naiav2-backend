import urllib.parse
import requests
from typing import Dict
from apps.users.services import UserService
from apps.status.services import set_status

def search_university_staff(name: str, user_id: int, status: str) -> Dict:
    """
    Search for university staff and faculty using Microsoft Graph API.
    Returns detailed information with photos in HTML format.
    
    Args:
        params (dict): Parameters containing 'name' for search
        user_id (int): The ID of the user making the search
        role_id (int): Role ID for tracking
        
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
        
        # Prepare search strategies similar to existing contact search
        name_parts = [part.strip() for part in search_name.split() if part.strip()]
        all_results = []
        seen_ids = set()
        
        # Strategy 1: Search by display name parts
        for part in name_parts:
            encoded_part = urllib.parse.quote(part)
            search_queries = [
                f"https://graph.microsoft.com/v1.0/users?$filter=startswith(displayName,'{encoded_part}')&$select=id,displayName,mail,jobTitle,department,officeLocation,businessPhones,userPrincipalName,companyName&$top=50",
                f"https://graph.microsoft.com/v1.0/users?$filter=contains(displayName,'{encoded_part}')&$select=id,displayName,mail,jobTitle,department,officeLocation,businessPhones,userPrincipalName,companyName&$top=50"
            ]
            
            for query_url in search_queries:
                try:
                    response = requests.get(query_url, headers=headers, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        users = data.get('value', [])
                        for user in users:
                            user_id_graph = user.get('id')
                            if user_id_graph and user_id_graph not in seen_ids:
                                # Filter for university staff (has jobTitle or department)
                                if user.get('jobTitle') or user.get('department'):
                                    seen_ids.add(user_id_graph)
                                    all_results.append(user)
                except Exception as e:
                    print(f"Error in search query: {str(e)}")
                    continue
        
        # Strategy 2: Try full name search
        encoded_full_name = urllib.parse.quote(search_name)
        full_name_queries = [
            f"https://graph.microsoft.com/v1.0/users?$filter=contains(displayName,'{encoded_full_name}')&$select=id,displayName,mail,jobTitle,department,officeLocation,businessPhones,userPrincipalName,companyName&$top=20"
        ]
        
        for query_url in full_name_queries:
            try:
                response = requests.get(query_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    users = data.get('value', [])
                    for user in users:
                        user_id_graph = user.get('id')
                        if user_id_graph and user_id_graph not in seen_ids:
                            if user.get('jobTitle') or user.get('department'):
                                seen_ids.add(user_id_graph)
                                all_results.append(user)
            except Exception as e:
                print(f"Error in full name search: {str(e)}")
                continue
        
        # Remove duplicates and sort by relevance
        unique_results = []
        for user in all_results:
            if user not in unique_results:
                unique_results.append(user)
        
        # Sort by name relevance and limit results
        def calculate_relevance(user):
            display_name = user.get('displayName', '').lower()
            search_lower = search_name.lower()
            if search_lower in display_name:
                return 0  # Exact match has highest priority
            elif any(part.lower() in display_name for part in name_parts):
                return 1  # Partial match
            else:
                return 2  # Other matches
        
        unique_results.sort(key=calculate_relevance)
        final_results = unique_results[:10]  # Limit to 10 results
        
        print(f"Found {len(final_results)} university staff members")
        
        if not final_results:
            return {
                "display": _generate_no_results_html(search_name),
                "message": f"No se encontró personal universitario con el nombre '{search_name}'"
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
                else:
                    enhanced_user['photo_base64'] = None
            except Exception as e:
                print(f"Error getting photo for user {user.get('displayName', 'Unknown')}: {str(e)}")
                enhanced_user['photo_base64'] = None
            
            enhanced_results.append(enhanced_user)
        
        # Generate HTML display
        html_display = _generate_staff_search_html(enhanced_results, search_name)
        
        return {
            "display": html_display,
            "message": f"Se encontraron {len(enhanced_results)} miembros del personal universitario. Revisa la pantalla para ver los detalles completos."
        }
        
    except requests.exceptions.Timeout:
        return {"error": "Tiempo de espera agotado al buscar personal universitario"}
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Error de red al buscar personal universitario: {str(e)}"}
    
    except Exception as e:
        return {"error": f"Error inesperado al buscar personal universitario: {str(e)}"}


def _generate_staff_search_html(staff_results, search_name):
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
        # Extract and clean data
        name = staff.get('displayName', 'Nombre no disponible')
        email = staff.get('mail', staff.get('userPrincipalName', 'Email no disponible'))
        job_title = staff.get('jobTitle', '')
        department = staff.get('department', '')
        office = staff.get('officeLocation', '')
        phones = staff.get('businessPhones', [])
        company = staff.get('companyName', '')
        photo_base64 = staff.get('photo_base64')
        
        # Build phone display
        phone_display = ""
        if phones and len(phones) > 0:
            phone_display = f"<p><strong>📞 Teléfono:</strong> {phones[0]}</p>"
        
        # Build office display
        office_display = ""
        if office:
            office_display = f"<p><strong>🏢 Oficina:</strong> {office}</p>"
        
        # Build department display
        dept_display = ""
        if department:
            dept_display = f"<p><strong>🏫 Departamento:</strong> {department}</p>"
        
        # Build job title display
        job_display = ""
        if job_title:
            job_display = f"<p><strong>💼 Cargo:</strong> {job_title}</p>"
        
        # Build company display
        company_display = ""
        if company and company.lower() not in ['uninorte', 'universidad del norte']:
            company_display = f"<p><strong>🏛️ Institución:</strong> {company}</p>"
        
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
                    <p style="margin: 0; color: #4a5568; font-size: 14px;">
                        <strong>📧 Email:</strong> {email}
                    </p>
                </div>
                
                <div style="margin-top: 15px; line-height: 1.6; color: #2d3748;">
                    {job_display}
                    {dept_display}
                    {office_display}
                    {phone_display}
                    {company_display}
                </div>
                
                <div style="text-align: center; margin-top: 15px; padding-top: 15px; border-top: 1px solid #e2e8f0;">
                    <span style="background-color: #e6fffa; color: #234e52; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                        Resultado #{i}
                    </span>
                </div>
            </div>
        """
    
    html += """
        </div>
        
        <div style="background-color: #e6fffa; padding: 20px; margin-top: 30px; border-radius: 8px; border-left: 4px solid #38b2ac;">
            <h3 style="margin: 0 0 10px 0; color: #234e52; font-size: 18px;">💡 Información Adicional</h3>
            <ul style="margin: 0; padding-left: 20px; color: #2d3748; line-height: 1.6;">
                <li>Los datos mostrados provienen del directorio oficial de la universidad</li>
                <li>Si no aparece la información de contacto, es posible que no esté disponible públicamente</li>
                <li>Para contactar al personal, puedes usar el email institucional proporcionado</li>
                <li>Los horarios de atención pueden variar - se recomienda contactar previamente</li>
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
                    <li>Verifica la ortografía del nombre</li>
                    <li>Intenta con solo el nombre o solo el apellido</li>
                    <li>Busca usando nombres parciales (ej: "Juan" en lugar de "Juan Carlos")</li>
                    <li>Asegúrate de que la persona forma parte del personal universitario</li>
                </ul>
            </div>
        </div>
    </div>
    """