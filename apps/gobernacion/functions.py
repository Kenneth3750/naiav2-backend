from openai import OpenAI
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import List, Dict
import os
from apps.status.services import set_status
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import numpy as np
from bs4 import BeautifulSoup
import time
import os
import re
from apps.recepcionist.functions import generate_functional_carousel, generate_events_display, generate_places_display
from serpapi import GoogleSearch
from redis.commands.search.query import Query
import redis
load_dotenv()


OPENAI_API_KEY = os.getenv("open_ai")
client = OpenAI(api_key=OPENAI_API_KEY)
VSS_MINIMUM_SCORE = 0.3
VSS_DIMENSION = 500

r = redis.Redis(host='localhost', port=6379, db=0)

def make_search_with_radius(input_embedding):
    q = Query("@embedding:[VECTOR_RANGE $radius $vec]=>{$YIELD_DISTANCE_AS: score}").sort_by("score").return_fields("title", "content", "link", "score").dialect(2).paging(0, 4)
    query_params = {
        "vec": input_embedding,
        "radius": VSS_MINIMUM_SCORE
    }
    res = r.ft('gov_idx').search(q, query_params=query_params)
    return res

def frequently_asked_questions(user_id: int, question: str, status: str) -> Dict:
    """
    This functions handles the answers for frequently asked questions.
    """
    set_status(user_id, status, 7)
    start_time = time.time()
    response = client.embeddings.create(
        input=question,
        model="text-embedding-3-small",
        dimensions=VSS_DIMENSION
    )

    embed_time = time.time() - start_time
    print("Time taken to generate embedding:", embed_time)
    input_embedding = np.array(response.data[0].embedding, dtype=np.float32).tobytes()

    search_start_time = time.time()
    res = make_search_with_radius(input_embedding)

    search_time = time.time() - search_start_time
    print("Time taken for search:", search_time)

    answer_divs = []
    link_titles = []
    links = []

    # Procesar resultados de Redis
    if res and res.total > 0:
        print(f"Se encontraron {res.total} resultados:")
        
        for i, doc in enumerate(res.docs):
            print(f"\n--- Resultado {i+1} ---")
            print(f"Título: {doc.title}")
            print(f"Contenido: {doc.content}")
            print(f"Link: {doc.link}")
            print(f"Score: {doc.score}")
            
            answer_divs.append([doc.content])  
            link_titles.append(doc.title)
            links.append(doc.link)
    else:
        print("No se encontraron resultados")
        return {"content_for_answers": ["No se encontró información relevante en la base de datos."], "display": None}

    if links:  # Cambiar array por links
        cards_html = ""
        for link, title in zip(links, link_titles):
            cards_html += f'''
            <a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block; transition: all 0.3s ease; transform: translateY(0);" 
            onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 15px 35px rgba(255,255,255,0.2)'" 
            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 25px rgba(255,255,255,0.1)'">
                
                <div style="background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 12px; padding: 20px; box-shadow: 0 8px 25px rgba(255,255,255,0.1);">
                    
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <div style="background: rgba(255, 255, 255, 0.2); border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; margin-right: 15px;">
                            <span style="font-size: 18px;">🏛️</span>
                        </div>
                        <div style="flex: 1;">
                            <div style="background: rgba(255, 255, 255, 0.2); height: 2px; border-radius: 1px; margin-bottom: 5px;"></div>
                            <div style="background: rgba(255, 255, 255, 0.1); height: 1px; border-radius: 1px; width: 70%;"></div>
                        </div>
                    </div>
                    
                    <h4 style="color: #ffffff; font-size: 16px; font-weight: 600; margin: 0; line-height: 1.4; text-shadow: 0 1px 3px rgba(0,0,0,0.3);">
                        {title}
                    </h4>
                    
                    <div style="display: flex; align-items: center; margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.2);">
                        <span style="color: #e2e8f0; font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">
                            Ver más información
                        </span>
                        <span style="color: #ffffff; margin-left: auto; font-size: 16px; transition: transform 0.3s ease;">→</span>
                    </div>
                </div>
            </a>
            '''
        
        pretty_links = f'''
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 25px; border-radius: 15px; box-shadow: 0 10px 30px rgba(30, 58, 138, 0.3); margin: 20px 0;">
            <div style="text-align: center; margin-bottom: 25px;">
                <h3 style="color: #ffffff; font-size: 24px; font-weight: bold; margin: 0; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                    📚 Enlaces de Interés - Gobernación del Atlántico
                </h3>
                <p style="color: #e2e8f0; margin: 8px 0 0 0; font-size: 14px;">
                    Explora más información oficial sobre tu consulta
                </p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
                {cards_html}
            </div>
            
            <div style="text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255, 255, 255, 0.2);">
                <p style="color: #cbd5e1; font-size: 12px; margin: 0;">
                    🇨🇴 Información oficial de la Gobernación del Atlántico
                </p>
            </div>
        </div>
        '''
    else:
        pretty_links = None

    return {"content_for_answers": answer_divs, "display": pretty_links}

def extraer_informacion_multas_simit(soup):
    """
    Extrae información de multas del HTML de SIMIT
    """
    resultado = {
        "tiene_multas": False,
        "mensaje_principal": "",
        "resumen": {
            "comparendos": 0,
            "multas": 0,
            "acuerdos_pago": 0,
            "total_valor": "$0"
        },
        "multas_detalle": [],
        "servicios_disponibles": [],
        "sin_multas_mensaje": ""
    }
    
    # Verificar si NO tiene multas
    sin_multas_div = soup.find("h3", string=re.compile(r"No tienes comparendos ni multas registradas", re.IGNORECASE))
    if sin_multas_div:
        resultado["tiene_multas"] = False
        resultado["sin_multas_mensaje"] = sin_multas_div.get_text(strip=True)
        siguiente_p = sin_multas_div.find_next("p")
        if siguiente_p:
            resultado["mensaje_principal"] = siguiente_p.get_text(strip=True)
        return resultado
    
    # Verificar si SÍ tiene multas - buscar resumen
    resumen_div = soup.find("div", {"id": "resumenEstadoCuenta"})
    if resumen_div:
        resultado["tiene_multas"] = True
        
        # Extraer resumen de cantidades
        try:
            comparendos_span = resumen_div.find("label", string="Comparendos: ")
            if comparendos_span:
                next_span = comparendos_span.find_next("span")
                if next_span and next_span.find("strong"):
                    resultado["resumen"]["comparendos"] = int(next_span.find("strong").text.strip())
        except:
            pass
            
        try:
            multas_span = resumen_div.find("label", string="Multas: ")
            if multas_span:
                next_span = multas_span.find_next("span")
                if next_span and next_span.find("strong"):
                    resultado["resumen"]["multas"] = int(next_span.find("strong").text.strip())
        except:
            pass
            
        try:
            acuerdos_span = resumen_div.find("label", string="Acuerdos de pago: ")
            if acuerdos_span:
                next_span = acuerdos_span.find_next("span")
                if next_span and next_span.find("strong"):
                    resultado["resumen"]["acuerdos_pago"] = int(next_span.find("strong").text.strip())
        except:
            pass
            
        try:
            total_span = resumen_div.find("label", string="Total: ")
            if total_span:
                next_span = total_span.find_next("span")
                if next_span and next_span.find("strong"):
                    resultado["resumen"]["total_valor"] = next_span.find("strong").text.strip()
        except:
            pass
        
        # Extraer detalles de la tabla de multas
        tabla_multas = soup.find("table", {"id": "multaTable"})
        if tabla_multas:
            tbody = tabla_multas.find("tbody")
            if tbody:
                filas = tbody.find_all("tr", class_="page-row")
                for fila in filas:
                    multa_detalle = {}
                    
                    # Extraer tipo y número
                    tipo_td = fila.find("td", {"data-label": "Tipo"})
                    if tipo_td:
                        numero_link = tipo_td.find("a")
                        if numero_link:
                            multa_detalle["numero"] = numero_link.text.strip()
                        
                        tipo_p = tipo_td.find("p", class_="text-muted")
                        if tipo_p:
                            multa_detalle["tipo"] = tipo_p.text.strip()
                        
                        fecha_span = tipo_td.find("span", string=re.compile(r"Fecha"))
                        if fecha_span:
                            multa_detalle["fecha"] = fecha_span.text.strip()
                    
                    # Extraer placa
                    placa_td = fila.find("td", {"data-label": "Placa"})
                    if placa_td:
                        multa_detalle["placa"] = placa_td.text.strip()
                    
                    # Extraer secretaría
                    secretaria_td = fila.find("td", {"data-label": "Secretaría"})
                    if secretaria_td:
                        multa_detalle["secretaria"] = secretaria_td.text.strip()
                    
                    # Extraer estado
                    estado_td = fila.find("td", {"data-label": "Estado"})
                    if estado_td:
                        estado_text = estado_td.get_text(separator=" ", strip=True)
                        multa_detalle["estado"] = estado_text
                    
                    # Extraer valor
                    valor_td = fila.find("td", {"data-label": "Valor"})
                    if valor_td:
                        valor_text = valor_td.get_text(separator=" ", strip=True)
                        multa_detalle["valor"] = valor_text
                    
                    # Extraer valor a pagar
                    valor_pagar_td = fila.find("td", {"data-label": "Valor a pagar"})
                    if valor_pagar_td:
                        valor_pagar_text = valor_pagar_td.get_text(separator=" ", strip=True)
                        multa_detalle["valor_a_pagar"] = valor_pagar_text
                    
                    if multa_detalle:
                        resultado["multas_detalle"].append(multa_detalle)
        
        # Mensaje principal para casos con multas
        total_items = resultado["resumen"]["comparendos"] + resultado["resumen"]["multas"]
        if total_items > 0:
            resultado["mensaje_principal"] = f"Se encontraron {total_items} registro(s): {resultado['resumen']['comparendos']} comparendo(s) y {resultado['resumen']['multas']} multa(s) por un total de {resultado['resumen']['total_valor']}"
    
    return resultado

def consultar_multas_simit(documento_placa):
    """
    Consulta multas en el portal SIMIT
    """
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-images')
    options.add_argument('--disable-plugins')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = None
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(2)
        
        url = "https://www.fcm.org.co/simit/#/home-public"
        print(f"🌐 Navegando a SIMIT: {url}")
        driver.get(url)
        
        wait = WebDriverWait(driver, 15)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        print("✅ Página SIMIT cargada")
        
        time.sleep(4)  # Esperar JavaScript/Angular
        
        # Esperar formulario
        form_element = wait.until(
            EC.presence_of_element_located((By.ID, "formGetEstadoCuenta"))
        )
        print("✅ Formulario SIMIT encontrado")
        
        time.sleep(2)
        
        # Cerrar overlays
        try:
            overlays = driver.find_elements(By.CSS_SELECTOR, ".modal, .overlay, .popup")
            for overlay in overlays:
                if overlay.is_displayed():
                    driver.execute_script("arguments[0].style.display = 'none';", overlay)
        except:
            pass
        
        # Buscar campo de input
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "txtBusqueda"))
        )
        print("✅ Campo de búsqueda SIMIT encontrado")
        
        # Escribir en el campo
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", input_field)
        time.sleep(1)
        driver.execute_script("arguments[0].focus();", input_field)
        time.sleep(0.5)
        
        try:
            input_field.clear()
            input_field.send_keys(documento_placa)
            print(f"✅ Documento/placa ingresado en SIMIT: {documento_placa}")
        except:
            driver.execute_script("arguments[0].value = '';", input_field)
            driver.execute_script("arguments[0].value = arguments[1];", input_field, documento_placa)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", input_field)
            print(f"✅ Documento/placa ingresado con JS: {documento_placa}")
        
        # Buscar y hacer clic en botón
        search_button = wait.until(
            EC.element_to_be_clickable((By.ID, "consultar"))
        )
        print("✅ Botón de búsqueda SIMIT encontrado")
        
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", search_button)
        time.sleep(1)
        
        try:
            search_button.click()
            print("✅ Botón SIMIT clickeado")
        except:
            driver.execute_script("arguments[0].click();", search_button)
            print("✅ Botón SIMIT clickeado con JS")
        
        # Esperar resultados
        print("⏳ Esperando resultados SIMIT...")
        time.sleep(5)
        
        max_wait = 8
        waited = 0
        while waited < max_wait:
            page_source_check = driver.page_source
            if ("No tienes comparendos ni multas" in page_source_check or 
                "resumenEstadoCuenta" in page_source_check or
                "multaTable" in page_source_check):
                print(f"✅ Resultados SIMIT detectados después de {waited + 5} segundos")
                break
            time.sleep(1)
            waited += 1
        
        time.sleep(2)  # Espera final
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        info_multas = extraer_informacion_multas_simit(soup)
        
        print(f"✅ Información SIMIT extraída - Tiene multas: {info_multas['tiene_multas']}")
        
        return {
            "status": "success",
            "documento_placa": documento_placa,
            "tiene_multas": info_multas["tiene_multas"],
            "mensaje_principal": info_multas["mensaje_principal"],
            "resumen": info_multas["resumen"],
            "multas_detalle": info_multas["multas_detalle"],
            "servicios_disponibles": info_multas["servicios_disponibles"],
            "sin_multas_mensaje": info_multas["sin_multas_mensaje"],
            "mensaje": "Consulta SIMIT realizada exitosamente"
        }
        
    except Exception as e:
        error_detail = f"Error SIMIT: {str(e)}"
        if "element not interactable" in str(e).lower():
            error_detail += " - Elemento no interactuable (overlay/animación)"
        print(f"❌ {error_detail}")
        
        return {
            "status": "error",
            "documento_placa": documento_placa,
            "tiene_multas": False,
            "mensaje_principal": "",
            "resumen": {"comparendos": 0, "multas": 0, "acuerdos_pago": 0, "total_valor": "$0"},
            "multas_detalle": [],
            "servicios_disponibles": [],
            "sin_multas_mensaje": "",
            "error": error_detail,
            "mensaje": "Error en consulta SIMIT"
        }
        
    finally:
        if driver:
            try:
                print(f"[CALENDAR] Closing Chrome driver...")
                driver.quit()
                print(f"[CALENDAR] ✅ Chrome driver closed successfully")
            except Exception as driver_error:
                print(f"[CALENDAR] ❌ Error closing driver: {str(driver_error)}")


def generar_html_respuesta_simit(resultado):
    """
    Genera HTML compacto para SIMIT que se ajusta al contenedor del frontend
    """
    if resultado['status'] != 'success':
        return f"""
        <div class="alert alert-danger" style="border-radius: 8px; margin: 10px; padding: 15px; font-size: 14px;">
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle text-danger me-2" style="font-size: 20px;"></i>
                <div>
                    <h6 class="mb-1 text-danger">Error en consulta SIMIT</h6>
                    <p class="mb-0 small">No fue posible consultar: <strong>{resultado['documento_placa']}</strong></p>
                    <small class="text-muted">{resultado.get('error', 'Error desconocido')}</small>
                </div>
            </div>
        </div>
        """
    
    if resultado['tiene_multas']:
        alert_class = "alert-warning"
        icon = "🚨"
        title = "Multas encontradas"
        status_text = "SÍ tiene multas pendientes"
        bg_color = "#fff3cd"
    else:
        alert_class = "alert-success"
        icon = "✅"
        title = "Sin multas"
        status_text = "NO tiene multas pendientes"
        bg_color = "#d1edff"
    
    html = f"""
    <div class="simit-container" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        
        <!-- Header compacto -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 8px 8px 0 0; text-align: center;">
            <h5 style="margin: 0; font-size: 16px; font-weight: 600;">
                <i class="fas fa-search" style="margin-right: 8px;"></i>
                Consulta SIMIT
            </h5>
            <p style="margin: 5px 0 0 0; font-size: 13px; opacity: 0.9;">
                {resultado['documento_placa']}
            </p>
        </div>
        
        <!-- Resultado principal compacto -->
        <div style="padding: 15px;">
            <div class="{alert_class}" style="border-radius: 6px; margin: 0 0 15px 0; padding: 12px; background-color: {bg_color}; border: 1px solid #dee2e6;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 20px; margin-right: 10px;">{icon}</span>
                    <div>
                        <h6 style="margin: 0 0 3px 0; font-size: 14px; font-weight: 600;">{title}</h6>
                        <p style="margin: 0; font-size: 13px; font-weight: 500;">{status_text}</p>
                    </div>
                </div>
            </div>
    """
    
    if not resultado['tiene_multas']:
        # Caso sin multas - versión compacta
        html += f"""
            <div style="background: #f8f9fa; border-radius: 6px; padding: 15px; text-align: center; border-left: 4px solid #28a745;">
                <h6 style="color: #28a745; margin: 0 0 8px 0; font-size: 14px;">
                    <i class="fas fa-thumbs-up" style="margin-right: 6px;"></i>
                    ¡Excelente!
                </h6>
                <p style="margin: 0; font-size: 13px; color: #6c757d;">
                    {resultado.get('sin_multas_mensaje', 'No se encontraron multas en SIMIT')}
                </p>
                {f'<p style="margin: 8px 0 0 0; font-size: 12px; color: #6c757d;">{resultado["mensaje_principal"]}</p>' if resultado.get('mensaje_principal') else ''}
            </div>
        """
    else:
        # Caso con multas - resumen compacto
        resumen = resultado['resumen']
        html += f"""
            <div style="background: #f8f9fa; border-radius: 6px; padding: 12px; margin-bottom: 15px;">
                <h6 style="margin: 0 0 10px 0; font-size: 14px; color: #495057; font-weight: 600;">
                    <i class="fas fa-chart-bar" style="margin-right: 6px;"></i>
                    Resumen
                </h6>
                <div class="simit-grid" style="font-size: 12px;">
                    <div style="background: #17a2b8; color: white; padding: 8px; border-radius: 4px; text-align: center;">
                        <div style="font-weight: bold; font-size: 16px;">{resumen['comparendos']}</div>
                        <div>Comparendos</div>
                    </div>
                    <div style="background: #ffc107; color: #212529; padding: 8px; border-radius: 4px; text-align: center;">
                        <div style="font-weight: bold; font-size: 16px;">{resumen['multas']}</div>
                        <div>Multas</div>
                    </div>
                    <div style="background: #6c757d; color: white; padding: 8px; border-radius: 4px; text-align: center;">
                        <div style="font-weight: bold; font-size: 16px;">{resumen['acuerdos_pago']}</div>
                        <div>Acuerdos</div>
                    </div>
                    <div style="background: #dc3545; color: white; padding: 8px; border-radius: 4px; text-align: center;">
                        <div style="font-weight: bold; font-size: 14px;">{resumen['total_valor']}</div>
                        <div>Total</div>
                    </div>
                </div>
            </div>
        """
        
        # Mostrar detalles compactos de multas
        if resultado['multas_detalle']:
            html += """
                <div style="background: white; border: 1px solid #dee2e6; border-radius: 6px; overflow: hidden;">
                    <div style="background: #343a40; color: white; padding: 10px;">
                        <h6 style="margin: 0; font-size: 13px; font-weight: 600;">
                            <i class="fas fa-list" style="margin-right: 6px;"></i>
                            Detalle de Multas
                        </h6>
                    </div>
                    <div style="max-height: 300px; overflow-y: auto;">
            """
            
            for i, multa in enumerate(resultado['multas_detalle']):
                tipo_color = "#17a2b8" if multa.get('tipo') == "Comparendo" else "#ffc107"
                tipo_text_color = "white" if multa.get('tipo') == "Comparendo" else "#212529"
                
                html += f"""
                    <div style="padding: 12px; border-bottom: 1px solid #e9ecef; {'' if i < len(resultado['multas_detalle'])-1 else 'border-bottom: none;'}">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                            <div style="flex: 1; min-width: 0;">
                                <div style="font-weight: bold; font-size: 12px; color: #495057; margin-bottom: 2px;" class="simit-text-ellipsis">
                                    {multa.get('numero', 'N/A')}
                                </div>
                                <div style="font-size: 11px; color: #6c757d;" class="simit-text-ellipsis">
                                    {multa.get('fecha', '')}
                                </div>
                            </div>
                            <span style="background: {tipo_color}; color: {tipo_text_color}; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: 500; margin-left: 8px; white-space: nowrap;">
                                {multa.get('tipo', 'N/A')}
                            </span>
                        </div>
                        
                        <div style="display: flex; justify-content: space-between; gap: 8px; font-size: 11px; color: #6c757d; flex-wrap: wrap;">
                            <div style="flex: 1; min-width: 120px;">
                                <strong>Placa:</strong> {multa.get('placa', 'N/A')}
                            </div>
                            <div style="flex: 1; min-width: 120px;" class="simit-text-ellipsis">
                                <strong>Secretaría:</strong> {multa.get('secretaria', 'N/A')}
                            </div>
                        </div>
                        
                        <div style="margin-top: 6px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                            <div style="font-size: 11px; color: #6c757d; flex: 1; min-width: 100px;" class="simit-text-ellipsis">
                                <strong>Estado:</strong> {multa.get('estado', 'N/A')}
                            </div>
                            <div style="font-weight: bold; color: #dc3545; font-size: 12px; white-space: nowrap;">
                                {multa.get('valor_a_pagar', 'N/A')}
                            </div>
                        </div>
                    </div>
                """
            
            html += """
                    </div>
                </div>
            """
    
    # Footer compacto
    html += f"""
        </div>
        
        <!-- Footer compacto -->
        <div style="background: #f8f9fa; padding: 12px; text-align: center; border-top: 1px solid #dee2e6; border-radius: 0 0 8px 8px;">
            <a href="https://www.fcm.org.co/simit/#/home-public" 
               target="_blank" 
               style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 6px 12px; border-radius: 15px; text-decoration: none; font-size: 12px; font-weight: 500;">
                <i class="fas fa-external-link-alt" style="margin-right: 4px;"></i>
                Portal SIMIT
            </a>
            <div style="margin-top: 6px;">
                <small style="color: #6c757d; font-size: 10px;">
                    <i class="fas fa-info-circle" style="margin-right: 3px;"></i>
                    Consulta: {time.strftime('%d/%m/%Y %H:%M', time.localtime())}
                </small>
            </div>
        </div>
    </div>
    """
    
    # CSS separado como string normal (sin f-string)
    css_styles = """
    <style>
        /* Estilos específicos para el contenedor SIMIT */
        .simit-container {
            max-width: 100%;
            overflow-x: hidden;
            box-sizing: border-box;
        }
        
        .simit-container * {
            box-sizing: border-box;
        }
        
        /* Grid responsive para resumen */
        .simit-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }
        
        @media (max-width: 480px) {
            .simit-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Prevenir texto largo */
        .simit-text-ellipsis {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
    </style>
    """
    
    return html + css_styles


def search_traffic_fines(documento_placa: str, user_id: int, status: str) -> Dict:
    """
    Función principal para NAIA - ACTUALIZADA PARA SIMIT
    """
    try:
        set_status(user_id, status, 7)
    
        
        if not documento_placa:
            return {
                "error": "No se entregó ningún documento o placa al realizar la búsqueda. Solicita al usuario que proporcione alguna de estas opciones."
            }



        resultado = consultar_multas_simit(documento_placa)
        
        # USAR EL NUEVO GENERADOR HTML SIMIT
        html_display = generar_html_respuesta_simit(resultado)
        
        return {
            "display": html_display,
            "status": resultado['status'],
            "tiene_multas": resultado.get('tiene_multas', False),
            "documento_placa": documento_placa,
            "resumen": resultado.get('resumen', {}),
            "total_multas": len(resultado.get('multas_detalle', []))
        }
        
    except Exception as e:
        error_html = f"""
        <div class="alert alert-danger border-danger" style="border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle text-danger me-3" style="font-size: 24px;"></i>
                <div>
                    <h5 class="mb-1 text-danger">❌ Error en consulta SIMIT</h5>
                    <p class="mb-0">No fue posible consultar las multas para <strong>{documento_placa}</strong></p>
                    <small class="text-muted">Error: {str(e)}</small>
                </div>
            </div>
        </div>
        """
        
        return {
            "display": error_html,
            "status": "error",
            "tiene_multas": False,
            "documento_placa": documento_placa,
            "error": str(e)
        }
  
def explain_passport_process(user_id: int, status: str, auto_slide_interval: int = 4000) -> Dict:
    """
    Explica el proceso completo para sacar pasaporte en la Gobernación del Atlántico
    con display informativo y carrusel visual de los pasos
    
    Args:
        user_id (int): ID del usuario
        status (str): Estado de la operación
        auto_slide_interval (int): Intervalo de auto-avance del carrusel en ms
        
    Returns:
        dict: JSON con display HTML y carrusel de pasos
    """
    try:
        # Establecer estado
        set_status(user_id, status, 7)
        
        # Información del proceso de pasaporte
        passport_info = {
            "primer_pago": {
                "ordinario": 139068,
                "ejecutivo": 139068,
                "metodo": "PSE (Place to Pay)"
            },
            "segundo_pago": {
                "ordinario": 111000,
                "ejecutivo": 244000,
                "tiempo_limite": "24 horas desde entrega de número de solicitud"
            },
            "entrega": {
                "tiempo": "48 horas hábiles después del segundo pago",
                "horario": "Lunes a Jueves: 9 a.m - 4 p.m, Viernes: 9 a.m - 3 p.m"
            }
        }
        
        # Pasos del proceso
        process_steps = [
            {
                "numero": 1,
                "titulo": "Verificar Requisitos",
                "descripcion": "Revisar todos los documentos necesarios para la expedición del pasaporte",
                "url": "https://pasaportesatlantico.gov.co/publicaciones/2/requisitos-para-expedicion-de-pasaporte/",
                "imagen": "http://127.0.0.1:8000/api/v1/gov_images/step1_requisitos.png",
                "detalles": "Confirme que cuenta con todos los documentos en buen estado y perfectamente legibles"
            },
            {
                "numero": 2,
                "titulo": "Realizar Primer Pago",
                "descripcion": "Efectuar el primer pago correspondiente al tipo de pasaporte solicitado",
                "url": "https://pasaportesatlantico.gov.co/pasaporte/",
                "imagen": "http://127.0.0.1:8000/api/v1/gov_images/step2_primer_pago.png",
                "detalles": f"Pasaporte Ordinario: ${passport_info['primer_pago']['ordinario']:,} | Pasaporte Ejecutivo: ${passport_info['primer_pago']['ejecutivo']:,}"
            },
            {
                "numero": 3,
                "titulo": "Agendar Cita",
                "descripcion": "Solicitar cita únicamente después de que el primer pago haya sido aceptado",
                "url": "https://pasaportesatlantico.gov.co/pasaporte/cita/datos-usuario/",
                "imagen": "http://127.0.0.1:8000/api/v1/gov_images/step3_agendar_cita.png",
                "detalles": "Para casos especiales, se recomienda agendar en jornada de mañana"
            },
            {
                "numero": 4,
                "titulo": "Realizar Segundo Pago",
                "descripcion": "Efectuar el segundo pago después de la formalización en la oficina",
                "url": "https://tramites.cancilleria.gov.co/ApostillaLegalizacion/pago/inicioPagoTC.aspx",
                "imagen": "http://127.0.0.1:8000/api/v1/gov_images/step4_segundo_pago.png",
                "detalles": f"Pasaporte Ordinario: ${passport_info['segundo_pago']['ordinario']:,} | Pasaporte Ejecutivo: ${passport_info['segundo_pago']['ejecutivo']:,}"
            }
        ]
        
        # Generar HTML del display informativo
        display_html = f"""
        <div class="passport-process-container" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);">
            <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2d3748; margin: 0; font-size: 28px; font-weight: 700;">
                        🛂 Proceso de Expedición de Pasaporte
                    </h1>
                    <p style="color: #718096; margin: 10px 0 0 0; font-size: 16px;">
                        Gobernación del Atlántico - Guía Completa
                    </p>
                </div>
                
                <div style="display: grid; gap: 20px; margin-bottom: 30px;">
                    <div style="background: #f7fafc; border-left: 4px solid #4299e1; padding: 20px; border-radius: 8px;">
                        <h3 style="color: #2d3748; margin: 0 0 15px 0; font-size: 18px; display: flex; align-items: center;">
                            💳 <span style="margin-left: 10px;">Costos del Trámite</span>
                        </h3>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
                                <h4 style="color: #4299e1; margin: 0 0 10px 0; font-size: 16px;">Primer Pago</h4>
                                <p style="margin: 5px 0; color: #2d3748;"><strong>Ambos tipos:</strong> ${passport_info['primer_pago']['ordinario']:,}</p>
                                <p style="margin: 5px 0; color: #718096; font-size: 14px;">Via PSE (Place to Pay)</p>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
                                <h4 style="color: #48bb78; margin: 0 0 10px 0; font-size: 16px;">Segundo Pago</h4>
                                <p style="margin: 5px 0; color: #2d3748;"><strong>Ordinario:</strong> ${passport_info['segundo_pago']['ordinario']:,}</p>
                                <p style="margin: 5px 0; color: #2d3748;"><strong>Ejecutivo:</strong> ${passport_info['segundo_pago']['ejecutivo']:,}</p>
                            </div>
                        </div>
                    </div>
                    
                    <div style="background: #fff5f5; border-left: 4px solid #f56565; padding: 20px; border-radius: 8px;">
                        <h3 style="color: #2d3748; margin: 0 0 15px 0; font-size: 18px; display: flex; align-items: center;">
                            ⚠️ <span style="margin-left: 10px;">Información Importante</span>
                        </h3>
                        <ul style="margin: 0; padding-left: 20px; color: #2d3748; line-height: 1.6;">
                            <li style="margin-bottom: 8px;">Los datos del formulario de pago deben ser del titular del pasaporte</li>
                            <li style="margin-bottom: 8px;">El segundo pago está habilitado por <strong>24 horas</strong> después de la cita</li>
                            <li style="margin-bottom: 8px;">Si no realiza el trámite en 2025, debe solicitar devolución del dinero</li>
                            <li style="margin-bottom: 8px;">Entrega en <strong>48 horas hábiles</strong> después del segundo pago</li>
                        </ul>
                    </div>
                    
                    <div style="background: #f0fff4; border-left: 4px solid #48bb78; padding: 20px; border-radius: 8px;">
                        <h3 style="color: #2d3748; margin: 0 0 15px 0; font-size: 18px; display: flex; align-items: center;">
                            🕒 <span style="margin-left: 10px;">Horarios de Entrega</span>
                        </h3>
                        <div style="color: #2d3748; line-height: 1.6;">
                            <p style="margin: 5px 0;"><strong>Lunes a Jueves:</strong> 9:00 a.m - 4:00 p.m</p>
                            <p style="margin: 5px 0;"><strong>Viernes:</strong> 9:00 a.m - 3:00 p.m</p>
                            <p style="margin: 10px 0 5px 0; font-size: 14px; color: #718096;">Ubicación: Entrada principal de la Gobernación</p>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 25px;">
                    <div style="display: inline-flex; align-items: center; background: #edf2f7; padding: 15px 25px; border-radius: 25px; color: #2d3748;">
                        <span style="font-size: 16px; font-weight: 600;">📋 Consulta el proceso completo en:</span>
                        <a href="https://pasaportesatlantico.gov.co/#" target="_blank" 
                           style="margin-left: 10px; color: #4299e1; text-decoration: none; font-weight: 600; 
                                  transition: color 0.3s ease;">
                            pasaportesatlantico.gov.co
                        </a>
                    </div>
                </div>
            </div>
        </div>
        """
        
        # Generar HTML del carrusel
        carousel_html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Proceso de Pasaporte - Pasos Visuales</title>
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                
                .passport-carousel-container {{
                    width: 90%;
                    max-width: 900px;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 25px 50px rgba(0,0,0,0.15);
                    overflow: hidden;
                    position: relative;
                }}
                
                .carousel-header {{
                    background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
                    color: white;
                    padding: 25px;
                    text-align: center;
                }}
                
                .carousel-header h2 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 600;
                }}
                
                .carousel-header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                    font-size: 16px;
                }}
                
                .carousel-wrapper {{
                    position: relative;
                    overflow: hidden;
                    height: 500px;
                }}
                
                .carousel-inner {{
                    display: flex;
                    transition: transform 0.5s ease-in-out;
                    height: 100%;
                }}
                
                .carousel-slide {{
                    min-width: 100%;
                    display: flex;
                    position: relative;
                    background: #f8fafc;
                }}
                
                .slide-image {{
                    flex: 1;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                    background: #ffffff;
                }}
                
                .slide-image img {{
                    max-width: 100%;
                    max-height: 100%;
                    border-radius: 10px;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                    object-fit: contain;
                }}
                
                .slide-content {{
                    flex: 1;
                    padding: 30px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    background: white;
                }}
                
                .step-number {{
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 40px;
                    height: 40px;
                    background: linear-gradient(135deg, #4299e1, #3182ce);
                    color: white;
                    border-radius: 50%;
                    font-weight: bold;
                    font-size: 18px;
                    margin-bottom: 15px;
                }}
                
                .slide-title {{
                    color: #2d3748;
                    font-size: 22px;
                    font-weight: 600;
                    margin: 0 0 15px 0;
                    line-height: 1.3;
                }}
                
                .slide-description {{
                    color: #4a5568;
                    font-size: 16px;
                    line-height: 1.5;
                    margin-bottom: 20px;
                }}
                
                .slide-details {{
                    background: #edf2f7;
                    padding: 15px;
                    border-radius: 8px;
                    color: #2d3748;
                    font-size: 14px;
                    margin-bottom: 20px;
                    line-height: 1.4;
                }}
                
                .slide-link {{
                    display: inline-flex;
                    align-items: center;
                    background: linear-gradient(135deg, #48bb78, #38a169);
                    color: white;
                    text-decoration: none;
                    padding: 12px 20px;
                    border-radius: 25px;
                    font-weight: 600;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                    align-self: flex-start;
                }}
                
                .slide-link:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 8px 20px rgba(72, 187, 120, 0.3);
                }}
                
                .carousel-controls {{
                    position: absolute;
                    top: 50%;
                    transform: translateY(-50%);
                    background: rgba(255,255,255,0.9);
                    border: none;
                    width: 50px;
                    height: 50px;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.3s ease;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }}
                
                .carousel-controls:hover {{
                    background: white;
                    transform: translateY(-50%) scale(1.1);
                }}
                
                .carousel-control-prev {{
                    left: 20px;
                }}
                
                .carousel-control-next {{
                    right: 20px;
                }}
                
                .carousel-indicators {{
                    display: flex;
                    justify-content: center;
                    padding: 25px;
                    background: #f8fafc;
                    gap: 12px;
                }}
                
                .carousel-indicator {{
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    background: #cbd5e1;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }}
                
                .carousel-indicator.active {{
                    background: #4299e1;
                    transform: scale(1.3);
                }}
                
                .carousel-indicator:hover {{
                    background: #94a3b8;
                    transform: scale(1.2);
                }}
                
                .carousel-footer {{
                    text-align: center;
                    padding: 20px;
                    background: #f8fafc;
                    border-top: 1px solid #e2e8f0;
                }}
                
                .carousel-footer p {{
                    margin: 0;
                    color: #718096;
                    font-size: 14px;
                }}
                
                @media (max-width: 768px) {{
                    .carousel-slide {{
                        flex-direction: column;
                    }}
                    
                    .slide-image, .slide-content {{
                        flex: none;
                    }}
                    
                    .slide-image {{
                        height: 200px;
                    }}
                    
                    .carousel-wrapper {{
                        height: auto;
                        min-height: 600px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="passport-carousel-container">
                <div class="carousel-header">
                    <h2>🛂 Proceso de Expedición de Pasaporte</h2>
                    <p>Siga estos pasos para obtener su pasaporte en la Gobernación del Atlántico</p>
                </div>
                
                <div class="carousel-wrapper">
                    <div class="carousel-inner" id="carouselInner">
        """
        
        # Agregar slides para cada paso
        for i, step in enumerate(process_steps):
            carousel_html += f"""
                        <div class="carousel-slide">
                            <div class="slide-image">
                                <img src="{step['imagen']}" alt="Paso {step['numero']}: {step['titulo']}" />
                            </div>
                            <div class="slide-content">
                                <div class="step-number">{step['numero']}</div>
                                <h3 class="slide-title">{step['titulo']}</h3>
                                <p class="slide-description">{step['descripcion']}</p>
                                <div class="slide-details">{step['detalles']}</div>
                                <a href="{step['url']}" target="_blank" class="slide-link">
                                    🔗 Ir al paso {step['numero']}
                                </a>
                            </div>
                        </div>
            """
        
        # Completar el HTML del carrusel
        carousel_html += f"""
                    </div>
                    
                    <button class="carousel-controls carousel-control-prev" id="prevBtn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="15 18 9 12 15 6"></polyline>
                        </svg>
                    </button>
                    
                    <button class="carousel-controls carousel-control-next" id="nextBtn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                    </button>
                </div>
                
                <div class="carousel-indicators" id="indicators">
        """
        
        # Agregar indicadores
        for i in range(len(process_steps)):
            active_class = "active" if i == 0 else ""
            carousel_html += f'<div class="carousel-indicator {active_class}" data-slide="{i}"></div>'
        
        # JavaScript del carrusel
        carousel_html += f"""
                </div>
                
                <div class="carousel-footer">
                    <p>💡 Use las flechas o haga clic en los indicadores para navegar entre los pasos</p>
                </div>
            </div>
            
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    const carousel = document.querySelector('.carousel-inner');
                    const slides = document.querySelectorAll('.carousel-slide');
                    const indicators = document.querySelectorAll('.carousel-indicator');
                    const prevBtn = document.getElementById('prevBtn');
                    const nextBtn = document.getElementById('nextBtn');
                    
                    let currentSlide = 0;
                    const totalSlides = slides.length;
                    
                    function updateCarousel() {{
                        const translateX = -currentSlide * 100;
                        carousel.style.transform = `translateX(${{translateX}}%)`;
                        
                        // Actualizar indicadores
                        indicators.forEach((indicator, index) => {{
                            indicator.classList.toggle('active', index === currentSlide);
                        }});
                    }}
                    
                    function nextSlide() {{
                        currentSlide = (currentSlide + 1) % totalSlides;
                        updateCarousel();
                    }}
                    
                    function prevSlide() {{
                        currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
                        updateCarousel();
                    }}
                    
                    function goToSlide(index) {{
                        currentSlide = index;
                        updateCarousel();
                    }}
                    
                    // Event listeners
                    nextBtn.addEventListener('click', nextSlide);
                    prevBtn.addEventListener('click', prevSlide);
                    
                    indicators.forEach((indicator, index) => {{
                        indicator.addEventListener('click', () => goToSlide(index));
                    }});
                    
                    // Auto-advance carousel
                    let autoplayInterval = setInterval(nextSlide, {auto_slide_interval});
                    
                    // Pause autoplay on hover
                    const container = document.querySelector('.passport-carousel-container');
                    container.addEventListener('mouseenter', () => {{
                        clearInterval(autoplayInterval);
                    }});
                    
                    container.addEventListener('mouseleave', () => {{
                        autoplayInterval = setInterval(nextSlide, {auto_slide_interval});
                    }});
                    
                    // Keyboard navigation
                    document.addEventListener('keydown', (e) => {{
                        if (e.key === 'ArrowLeft') prevSlide();
                        if (e.key === 'ArrowRight') nextSlide();
                    }});
                    
                    // Initialize
                    updateCarousel();
                }});
            </script>
        </body>
        </html>
        """
        
        return {
            "display": display_html,
            "graph": carousel_html,
            "status": "success",
            "proceso": "pasaporte",
            "pasos_totales": len(process_steps),
            "costos": passport_info
        }
        
    except Exception as e:
        error_html = f"""
        <div class="alert alert-danger" style="border-radius: 10px; padding: 20px; background: #fee; border: 1px solid #fcc;">
            <h5 style="color: #c53030; margin: 0 0 10px 0;">❌ Error al cargar información del pasaporte</h5>
            <p style="color: #742a2a; margin: 0;">No fue posible cargar la información del proceso de pasaporte</p>
            <small style="color: #a0aec0;">Error: {str(e)}</small>
        </div>
        """
        
        return {
            "display": error_html,
            "graph": "",
            "status": "error",
            "proceso": "pasaporte",
            "error": str(e)
        }
    



def get_location_events(location: str = "Barranquilla", user_id: int = 0, status: str = "", event_query: str = "") -> dict:
    """
    Get events happening in a specific location using SerpAPI.
    Returns both display and graph using real event images.
    """
    try:
        if user_id:
            set_status(user_id, status, 7)

        api_key = os.getenv('SERPAPI_KEY')
        if not api_key:
            raise ValueError("SERPAPI_KEY not found in environment variables")

        params_google = {
            "engine": "google_events",
            "q": f"{event_query} en {location}, Atlántico",
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

def get_location_places(location: str = "Barranquilla", user_id: int = 0, status: str = "", location_query: str = "") -> dict:
    """
    Get places to visit in a specific location using SerpAPI.
    Returns both display and graph using real place images.
    """
    try:
        if user_id:
            set_status(user_id, status, 7)

        api_key = os.getenv('SERPAPI_KEY')
        if not api_key:
            raise ValueError("SERPAPI_KEY not found in environment variables")

        params = {
            "engine": "google_local",
            "q": f"{location_query} en {location}, Atlántico",
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
