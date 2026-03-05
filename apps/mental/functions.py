from dotenv import load_dotenv
import os
from typing import Dict
from apps.status.services import set_status
from openai import OpenAI
from serpapi import GoogleSearch
from apps.chat.repositories import redis_pool
from apps.uniguide.functions import get_virtual_campus_tour
from apps.recepcionist.functions import send_email
from apps.personal.functions import search_contacts_by_name, create_calendar_event
import redis
load_dotenv()

openai_api_key = os.getenv("open_ai")
serpapi_key = os.getenv("SERPAPI_KEY")

client = OpenAI(
    api_key= openai_api_key
)

def cae_info_for_user(user_id: int, status: str, language: str) -> Dict:
    """
    This function generates a html format with information about CAE (Centro de Acompañamiento Estudiantil) from Universidad del Norte.
    Args:
        user_id (int): The ID of the user
        status (str): The status message for tracking
        language (str): The language of the information to be generated
    Returns:
        dict: A dictionary containing the HTML format with information about CAE
    """
    try:
        set_status(user_id, status, 6)
        
        # CAE image URL
        cae_image_url = "https://www.uninorte.edu.co/documents/26405488/0/Estudiante+Centro+de+Acompa%C3%B1amiento+Estudiantil+%281%29.png"
        
        # Content based on language
        if language.lower() == "english":
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>CAE - Student Support Center</title>
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
                    
                    .container {{
                        width: 100%;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: white;
                        border-radius: 12px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                    }}
                    
                    .title {{
                        font-size: 1.5rem;
                        font-weight: 600;
                        margin-bottom: 16px;
                        color: #124072;
                        display: flex;
                        align-items: center;
                        border-bottom: 2px solid #00aeda;
                        padding-bottom: 10px;
                    }}
                    
                    .title svg {{
                        margin-right: 8px;
                    }}
                    
                    .image-container {{
                        position: relative;
                        width: 100%;
                        height: 300px;
                        overflow: hidden;
                        background-color: #f1f5f9;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 8px;
                        margin-bottom: 20px;
                    }}
                    
                    .image {{
                        max-width: 100%;
                        max-height: 100%;
                        width: auto;
                        height: auto;
                        object-fit: contain;
                        border-radius: 8px;
                    }}
                    
                    .info-section {{
                        margin-bottom: 24px;
                    }}
                    
                    .info-section h3 {{
                        font-size: 1.25rem;
                        color: #124072;
                        margin-bottom: 12px;
                    }}
                    
                    .info-card {{
                        background-color: #f8fafc;
                        border-left: 4px solid #00aeda;
                        padding: 15px;
                        margin-bottom: 15px;
                        border-radius: 6px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }}
                    
                    .info-card h4 {{
                        font-size: 1.1rem;
                        color: #124072;
                        margin-bottom: 8px;
                    }}
                    
                    .info-card p {{
                        margin-bottom: 10px;
                    }}
                    
                    .info-card ul {{
                        padding-left: 20px;
                        margin-bottom: 10px;
                    }}
                    
                    .info-card li {{
                        margin-bottom: 5px;
                    }}
                    
                    .emergency {{
                        background-color: #fef2f2;
                        border-left: 4px solid #dc2626;
                        padding: 15px;
                        margin-bottom: 15px;
                        border-radius: 6px;
                    }}
                    
                    .emergency h4 {{
                        color: #dc2626;
                    }}
                    
                    .support-network {{
                        text-align: center;
                        font-size: 1.5rem;
                        font-weight: bold;
                        color: #124072;
                        margin: 30px 0;
                    }}
                    
                    .contact-button {{
                        display: block;
                        width: 100%;
                        padding: 12px;
                        background: linear-gradient(90deg, #124072 60%, #00aeda 100%);
                        color: white;
                        text-align: center;
                        border-radius: 8px;
                        font-weight: 600;
                        text-decoration: none;
                        margin-top: 20px;
                        transition: all 0.3s ease;
                    }}
                    
                    .contact-button:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(18, 64, 114, 0.4);
                    }}
                    
                    @media (max-width: 640px) {{
                        .container {{
                            padding: 12px;
                        }}
                        
                        .image-container {{
                            height: 200px;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="title">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                        CAE - Student Support Center
                    </h1>
                    
                    <div class="image-container">
                        <img src="{cae_image_url}" alt="CAE - We are your support network" class="image">
                    </div>
                    
                    <p class="support-network">WE ARE YOUR SUPPORT NETWORK</p>
                    
                    <div class="info-section">
                        <h3>About CAE</h3>
                        <div class="info-card">
                            <p>The Student Support Center (CAE) at Universidad del Norte offers professional support for your mental health and wellbeing. Our team of qualified psychologists is ready to help you with any challenges you might encounter during your academic life.</p>
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <h3>Our Services</h3>
                        <div class="info-card">
                            <h4>Psychological Support</h4>
                            <ul>
                                <li>Individual psychological counseling</li>
                                <li>Crisis intervention</li>
                                <li>Emotional support</li>
                                <li>Academic stress management</li>
                                <li>Personal development guidance</li>
                            </ul>
                        </div>
                        
                        <div class="info-card">
                            <h4>When to Seek Help</h4>
                            <ul>
                                <li>Difficulties with self-acceptance</li>
                                <li>Anger management issues</li>
                                <li>Family problems affecting your wellbeing</li>
                                <li>Conflicts with professors, classmates, friends, or family</li>
                                <li>Grief or loss experiences</li>
                                <li>Substance use concerns</li>
                                <li>Experiences of abuse or mistreatment</li>
                                <li>Persistent worry, tension, anxiety, or stress</li>
                                <li>Sleep disturbances</li>
                                <li>Academic performance decline</li>
                                <li>Loss of interest in activities</li>
                                <li>Loss of will to live</li>
                                <li>Persistent sadness, lack of energy or motivation</li>
                                <li>Irritability or social isolation</li>
                                <li>Frequent crying</li>
                                <li>Changes in eating habits</li>
                                <li>Restlessness or hyperactivity</li>
                                <li>Self-harm behaviors</li>
                                <li>Thoughts of death or suicide</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <h3>Contact Information</h3>
                        <div class="info-card">
                            <h4>Regular Hours</h4>
                            <p>Monday to Friday: 8:00 am to 12:30 pm and 2:00 pm to 6:30 pm</p>
                            <h4>Team</h4>
                            <p>Professional psychologists available ALWAYS</p>
                        </div>
                        
                        <div class="emergency">
                            <h4>Emergency Crisis Line (24 hours)</h4>
                            <p>3793333 – 3399999 (outside campus)</p>
                            <p><strong>Important:</strong> If you are experiencing a mental health crisis, don't hesitate to call.</p>
                        </div>
                    </div>
                    
                    <a href="#" class="contact-button">SCHEDULE AN APPOINTMENT</a>
                </div>
            </body>
            </html>
            """
        else:  # Spanish by default
            html_content = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>CAE - Centro de Acompañamiento Estudiantil</title>
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
                    
                    .container {{
                        width: 100%;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: white;
                        border-radius: 12px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                    }}
                    
                    .title {{
                        font-size: 1.5rem;
                        font-weight: 600;
                        margin-bottom: 16px;
                        color: #124072;
                        display: flex;
                        align-items: center;
                        border-bottom: 2px solid #00aeda;
                        padding-bottom: 10px;
                    }}
                    
                    .title svg {{
                        margin-right: 8px;
                    }}
                    
                    .image-container {{
                        position: relative;
                        width: 100%;
                        height: 300px;
                        overflow: hidden;
                        background-color: #f1f5f9;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 8px;
                        margin-bottom: 20px;
                    }}
                    
                    .image {{
                        max-width: 100%;
                        max-height: 100%;
                        width: auto;
                        height: auto;
                        object-fit: contain;
                        border-radius: 8px;
                    }}
                    
                    .info-section {{
                        margin-bottom: 24px;
                    }}
                    
                    .info-section h3 {{
                        font-size: 1.25rem;
                        color: #124072;
                        margin-bottom: 12px;
                    }}
                    
                    .info-card {{
                        background-color: #f8fafc;
                        border-left: 4px solid #00aeda;
                        padding: 15px;
                        margin-bottom: 15px;
                        border-radius: 6px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }}
                    
                    .info-card h4 {{
                        font-size: 1.1rem;
                        color: #124072;
                        margin-bottom: 8px;
                    }}
                    
                    .info-card p {{
                        margin-bottom: 10px;
                    }}
                    
                    .info-card ul {{
                        padding-left: 20px;
                        margin-bottom: 10px;
                    }}
                    
                    .info-card li {{
                        margin-bottom: 5px;
                    }}
                    
                    .emergency {{
                        background-color: #fef2f2;
                        border-left: 4px solid #dc2626;
                        padding: 15px;
                        margin-bottom: 15px;
                        border-radius: 6px;
                    }}
                    
                    .emergency h4 {{
                        color: #dc2626;
                    }}
                    
                    .support-network {{
                        text-align: center;
                        font-size: 1.5rem;
                        font-weight: bold;
                        color: #124072;
                        margin: 30px 0;
                    }}
                    
                    .contact-button {{
                        display: block;
                        width: 100%;
                        padding: 12px;
                        background: linear-gradient(90deg, #124072 60%, #00aeda 100%);
                        color: white;
                        text-align: center;
                        border-radius: 8px;
                        font-weight: 600;
                        text-decoration: none;
                        margin-top: 20px;
                        transition: all 0.3s ease;
                    }}
                    
                    .contact-button:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(18, 64, 114, 0.4);
                    }}
                    
                    @media (max-width: 640px) {{
                        .container {{
                            padding: 12px;
                        }}
                        
                        .image-container {{
                            height: 200px;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="title">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                        CAE - Centro de Acompañamiento Estudiantil
                    </h1>
                    
                    <div class="image-container">
                        <img src="{cae_image_url}" alt="CAE - Somos tu red de apoyo" class="image">
                    </div>
                    
                    <p class="support-network">SOMOS TU RED DE APOYO</p>
                    
                    <div class="info-section">
                        <h3>Acerca del CAE</h3>
                        <div class="info-card">
                            <p>El Centro de Acompañamiento Estudiantil (CAE) de la Universidad del Norte ofrece apoyo profesional para tu salud mental y bienestar. Nuestro equipo de psicólogos calificados está listo para ayudarte con cualquier desafío que puedas encontrar durante tu vida académica.</p>
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <h3>Nuestros Servicios</h3>
                        <div class="info-card">
                            <h4>Apoyo Psicológico</h4>
                            <ul>
                                <li>Asesoría psicológica individual</li>
                                <li>Intervención en crisis</li>
                                <li>Apoyo emocional</li>
                                <li>Manejo del estrés académico</li>
                                <li>Orientación para desarrollo personal</li>
                            </ul>
                        </div>
                        
                        <div class="info-card">
                            <h4>Cuándo Buscar Ayuda</h4>
                            <ul>
                                <li>No te gustas, te cuesta aceptarte</li>
                                <li>Te resulta muy difícil controlarte cuando te enojas</li>
                                <li>Tienes problemas familiares que te están afectando demasiado</li>
                                <li>Tienes conflictos con alguien cercano (Profesor, compañero, amigo, pareja, familia)</li>
                                <li>Estás atravesando un duelo por la pérdida de alguien o algo</li>
                                <li>Tienes dificultades con el consumo de alcohol y/o sustancias psicoactivas</li>
                                <li>Estás viviendo o has vivido recientemente una situación de abuso o maltrato</li>
                                <li>Te mantienes muy preocupado, tenso, ansioso, estresado</li>
                                <li>Se ha vuelto frecuente que no duermas, duermas muy poco, tu sueño sea intranquilo</li>
                                <li>Te dan ganas de no ir a clases, estudiar y tu rendimiento académico ha bajado</li>
                                <li>Has dejado de disfrutar lo que te gustaba o era divertido para ti</li>
                                <li>Sientes que pierdes las ganas de vivir</li>
                                <li>Sientes mucho desánimo, tristeza, sin energía o motivación para nada</li>
                                <li>Te has vuelto más irritable o te has aislado más de lo habitual</li>
                                <li>Lloras con frecuencia y muy fácilmente</li>
                                <li>Has cambiado tus hábitos alimentarios</li>
                                <li>Inquietud, hiperactividad, hablas rápido o confusamente</li>
                                <li>Te estás haciendo daño físicamente</li>
                                <li>A veces deseas morir o piensas que sería lo mejor ahora mismo</li>
                                <li>Te gustaría acabar con tu vida</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <h3>Información de Contacto</h3>
                        <div class="info-card">
                            <h4>Horario Regular</h4>
                            <p>Lunes a Viernes: 8:00 am a 12:30 pm y 2:00 pm a 6:30 pm</p>
                            <h4>Equipo</h4>
                            <p>Psicólogos profesionales disponibles SIEMPRE</p>
                        </div>
                        
                        <div class="emergency">
                            <h4>Línea de Crisis de Emergencia (24 horas)</h4>
                            <p>3793333 – 3399999 (fuera del campus)</p>
                            <p><strong>Importante:</strong> Si estás experimentando una crisis de salud mental, no dudes en llamar.</p>
                        </div>
                    </div>
                    
                    <a href="#" class="contact-button">AGENDAR UNA CITA</a>
                </div>
            </body>
            </html>
            """
        
        return {"display": html_content}
        
    except Exception as e:
        print(f"Error generating CAE information: {str(e)}")
        return {"error": str(e)}


def mental_health_screening_tool(user_id: int, status: str, user_specific_situation: str, language: str) -> Dict:
    """
    This function generates a conversational guide for NAIA to conduct a mental health screening 
    based on CAE (Centro de Acompañamiento Estudiantil) guidelines. Instead of creating an HTML form,
    it provides a structured conversation guide for natural, spoken assessment.

    Args:
        user_id (int): The ID of the user
        status (str): The status message for tracking
        user_specific_situation (str): Detailed description of the user's specific emotional or psychological situation
        language (str): The language for the screening guide
    Returns:
        dict: A dictionary containing the conversational screening guide
    """
    try:
        set_status(user_id, status, 6)
        update_questionnaire_status(user_id)
        
        # Agent specialized in creating conversational mental health guides
        agent_prompt = """You are a specialized mental health conversation guide generator for Universidad del Norte's NAIA assistant. Your task is to create a structured conversational guide that allows NAIA to conduct a professional, empathetic mental health screening based on CAE (Centro de Acompañamiento Estudiantil) guidelines.

        CRITICAL: You are creating a CONVERSATION GUIDE for NAIA, not conducting the assessment yourself.

        YOUR OUTPUT MUST BE A STRUCTURED STRING that includes:

        1. **CONVERSATION APPROACH** - How NAIA should approach the conversation
        2. **KEY QUESTIONS** - 5-7 essential questions to ask (brief but effective)
        3. **CONVERSATION FLOW** - How to transition between topics naturally
        4. **RED FLAGS TO WATCH** - Critical responses that require immediate CAE referral
        5. **SUPPORTIVE RESPONSES** - How to respond empathetically to different types of answers
        6. **LANGUAGE TO AVOID** - Expressions and words that should not be used
        7. **CLOSING GUIDANCE** - How to conclude the screening and next steps

        CAE MENTAL HEALTH INDICATORS (Base questions on these):
        - Self-acceptance difficulties
        - Anger control problems
        - Family problems affecting wellbeing
        - Interpersonal conflicts
        - Grief and loss
        - Substance use issues
        - Abuse or mistreatment experiences
        - Persistent anxiety, stress, worry
        - Sleep disturbances
        - Academic performance decline
        - Loss of interest in activities
        - Loss of will to live
        - Persistent sadness, lack of energy
        - Irritability or social isolation
        - Frequent crying
        - Changes in eating habits
        - Restlessness or hyperactivity
        - Self-harm behaviors
        - Thoughts of death or suicide

        CONVERSATION GUIDELINES:
        - Keep questions short and natural (as if spoken)
        - Use empathetic, non-judgmental language
        - Allow for natural follow-up questions
        - Validate emotions throughout
        - Maintain professional but warm tone
        - Be culturally sensitive
        - Focus on recent changes and current state

        CAE EMERGENCY CONTACT: 3793333 – 3399999 (24 hours)
        CAE HOURS: Monday to Friday, 8:00 am to 12:30 pm and 2:00 pm to 6:30 pm

        PERSONALIZATION: Adapt the guide based on the user's specific situation while maintaining professional standards.

        OUTPUT FORMAT: Return a clear, structured string guide that NAIA can follow naturally in conversation."""

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": agent_prompt},
                {"role": "user", "content": f"Create a conversational mental health screening guide for NAIA. The user's specific situation is: {user_specific_situation}. Language: {language}. This should be a professional but natural conversation guide that NAIA can follow to assess the user's mental health needs and determine if CAE referral is necessary."}
            ],
        )
        
        conversation_guide = response.choices[0].message.content
        
        return {"conversation_guide": conversation_guide}
        
    except Exception as e:
        print(f"Error generating mental health screening guide: {str(e)}")
        return {"error": str(e)}
    

def personalized_wellness_plan(user_id: int, status: str, user_specific_situation: str, observations: str, language: str, query: str = "") -> Dict:
    try:
        set_status(user_id, status, 6)
        if query:
            params = {
                "engine": "google",
                "q": query,
                "api_key": serpapi_key,
                "outpuyt": "json",
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            organic_results = results.get("organic_results", [])

        system_prompt = """You are a specialized wellness plan generator for Universidad del Norte's mental health support system. Your task is to create comprehensive, personalized wellness plans in HTML format based on mental health assessments and observations.

        CRITICAL HTML REQUIREMENTS:
        1. Generate ONLY clean HTML code - no DOCTYPE, no explanation text
        2. Use Universidad del Norte colors: #124072 (dark blue), #00aeda (light blue), whites and light grays
        3. Create a professional, calming design suitable for mental health content
        4. Make it responsive and print-friendly
        5. Include proper styling with embedded CSS

        WELLNESS PLAN STRUCTURE:
        1. **Header Section**: Title with Universidad del Norte branding
        2. **Assessment Summary**: Brief, non-clinical summary of current situation
        3. **Personal Objectives**: 3-4 specific, achievable goals
        4. **Daily Strategies**: Practical techniques adapted to their specific needs
        5. **Weekly Recommendations**: Structured activities and practices
        6. **University Resources**: Specific CAE and campus resources
        7. **Emergency Contacts**: CAE crisis line and support information
        8. **Progress Tracking**: Simple indicators to monitor wellbeing

        DESIGN PRINCIPLES:
        - Use calming, professional aesthetics
        - Clear visual hierarchy with sections
        - Icons or visual elements (no images, use CSS/Unicode symbols)
        - Adequate white space for readability
        - Soft color palette that promotes wellbeing
        - Print-friendly layout

        CONTENT GUIDELINES:
        - Use supportive, encouraging language
        - Avoid clinical terminology
        - Make recommendations specific and actionable
        - Include time-based suggestions (daily, weekly, monthly)
        - Emphasize self-care and gradual progress
        - Connect strategies to university life context

        CAE INFORMATION TO INCLUDE:
        - Schedule: Monday to Friday, 8:00 am to 12:30 pm and 2:00 pm to 6:30 pm
        - Emergency Crisis Line (24 hours): 3793333 – 3399999
        - Team: Professional psychologists at Centro de Acompañamiento Estudiantil

        PERSONALIZATION REQUIREMENTS:
        - Adapt all recommendations to the user's specific situation
        - Consider their expressed concerns and symptoms
        - Include relevant coping strategies for their particular challenges
        - Suggest realistic goals based on their current state
        - Reference observations to make plan feel personalized

        OUTPUT: Return ONLY clean HTML code with embedded CSS styling. No explanations or additional text."""

        user_prompt = f"""Create a comprehensive personalized wellness plan based on the following information:

        USER SITUATION: {user_specific_situation}

        OBSERVATIONS FROM ASSESSMENT: {observations}

        LANGUAGE: {language}

        {"ADDITIONAL CONTEXT FROM WEB SEARCH: " + str(organic_results[:3]) if query else ""}

        Generate a professional HTML wellness plan that:
        1. Addresses their specific mental health concerns
        2. Provides actionable daily and weekly strategies
        3. Includes relevant university resources
        4. Offers hope and practical next steps
        5. Maintains a supportive, encouraging tone
        6. Uses Universidad del Norte branding and colors

        Focus on creating a plan that feels personally crafted for this individual's situation while maintaining professional mental health support standards."""

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        )

        response_content = response.choices[0].message.content

        # Clean any markdown code block markers from the response
        if response_content.startswith("```html"):
            response_content = response_content.replace("```html", "", 1)
        elif response_content.startswith("```"):
            response_content = response_content.replace("```", "", 1)
        
        # Always check for and remove trailing code block markers
        if response_content.endswith("```"):
            response_content = response_content[:-3]
        
        # Trim any extra whitespace
        response_content = response_content.strip()

        with open(f"wellness_plan_{user_id}.html", "w", encoding="utf-8") as file:
            file.write(response_content)

        return {"graph": response_content}
    
    except Exception as e:
        print(f"Error generating personalized wellness plan: {str(e)}")
        return {"error": str(e)}


def update_questionnaire_status(user_id: int) -> str:
    try:
        r = redis.Redis(connection_pool=redis_pool)
        key = f"questionnaire_status_{user_id}"
        status = r.set(key, 1, ex=1800)
        return status
    except Exception as e:
        print(f"Error updating questionnaire status: {str(e)}")
        return f"Error: {str(e)}"

def get_current_questionnaire_status(user_id: int) -> bool:
    try:
        r = redis.Redis(connection_pool=redis_pool)
        key = f"questionnaire_status_{user_id}"
        status = r.get(key)
        if status is None:
            return False
        return True
    except Exception as e:
        print(f"Error retrieving questionnaire status: {str(e)}")
        return f"Error: {str(e)}"


# ==========================================
# Bienestar Organizacional Functions (role 6 Realtime)
# ==========================================

ACTIVIDADES_BIENESTAR = [
    {
        "name": "Clase de Voleibol",
        "icon": "🏐",
        "target": "Colaboradores y cónyuges",
        "schedule": "Lunes y miércoles, 6:30-8:30 PM",
        "location": "Colegio Buen Consejo",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.51.39+PM.jpeg/aa07ce6a-7f6e-9920-47b7-7d6c4de8d624",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUM1FEV0tFNVZBTkQ4RzJIMzJJRTY2RUtWQi4u",
    },
    {
        "name": "Yoga",
        "icon": "🧘",
        "target": "Colaboradores y cónyuges",
        "schedule": "Lunes y miércoles, 6:00-7:00 PM",
        "location": "Salón de Danza - Coliseo",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.49.49+PM+%281%29.jpeg/6a16809b-3c71-df91-816c-d9550234467f",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUQ0FGT05FN0pTSk1DSUE4VEsxQU1ZR0xXUC4u",
    },
    {
        "name": "Tenis Adulto - Principiante",
        "icon": "🎾",
        "target": "Colaboradores y cónyuges",
        "schedule": "Martes y jueves, 6:00-8:00 PM",
        "location": "Cancha de tenis interna",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/Tenis-adulto.jpg/7c28badd-ae75-2b9f-f8fa-bc72c88eda2b",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUN1JCTFRLSjJTMFpYQTQzMFJBRlROTDlDRS4u",
    },
    {
        "name": "Tenis Adulto - Avanzado",
        "icon": "🎾",
        "target": "Colaboradores y cónyuges",
        "schedule": "Lunes y miércoles, 6:00-8:00 PM",
        "location": "Cancha de tenis interna",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/Tenis-adulto.jpg/7c28badd-ae75-2b9f-f8fa-bc72c88eda2b",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUNE1EWElWVk80SzI4OU9CMlJVVEVGMU85Ry4u",
    },
    {
        "name": "Iniciación al Deporte (3-4 años)",
        "icon": "👶",
        "target": "Hijos, sobrinos, nietos, hermanos",
        "schedule": "Sábados 9:00-10:00 AM",
        "location": "Cancha de Raqueta",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.45.32+PM+%281%29.jpeg/3b61c3a1-5f8e-6f79-615c-ccd883226f6d",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUNUZYQUNMMVJZSUQzUjdXS01EVUpZU08zMC4u",
    },
    {
        "name": "Iniciación al Deporte (2 años)",
        "icon": "👶",
        "target": "Hijos, sobrinos, nietos, hermanos",
        "schedule": "Sábados 8:00-9:00 AM",
        "location": "Cancha de Raqueta",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.45.32+PM+%281%29.jpeg/3b61c3a1-5f8e-6f79-615c-ccd883226f6d",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUOUU1UzE2TkM3MkpBUUw4S00xSE8zSUQ5Ny4u",
    },
    {
        "name": "Percusión Folclórica",
        "icon": "🥁",
        "target": "Colaboradores y cónyuges",
        "schedule": "Viernes, 12:00-2:00 PM",
        "location": "Salón de Música BO",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-09-04+at+5.53.59+PM.jpeg/c2aa34ed-e288-ec73-1592-aa97e41e4ec4",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUNlkxQTcwVTdNSkRZMURDTVRKN0NNR1c0UC4u",
    },
    {
        "name": "Orquesta",
        "icon": "🎵",
        "target": "Colaboradores",
        "schedule": "Martes y jueves, 12:00-2:00 PM",
        "location": "Salón de Música BO",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/orquesta.jpg/ec7c6f08-476c-8e7f-995c-68a4d9791dc6",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUMVRJRkpTQ1VPSjJKWk1UNzI5RE9WMEpYWC4u",
    },
    {
        "name": "Ritmos Latinos",
        "icon": "💃",
        "target": "Colaboradores y cónyuges",
        "schedule": "Miércoles, 12:00-2:00 PM",
        "location": "Salón de Música BO",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/Ritmos-latinos.jpg/47cd6418-ea5e-27bf-859c-e43bae6322e3",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUOVNJUFhWOVFBSUhDQzhTUzBKUEhJUlhFRy4u",
    },
    {
        "name": "Taekwondo Adultos",
        "icon": "🥋",
        "target": "Colaboradores y cónyuges",
        "schedule": "Martes, 6:00-8:00 PM",
        "location": "Salón de Danza (Coliseo, Piso 2)",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.50.18+PM.jpeg/c09685b2-650d-24ad-3212-ed405e45b27a",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUQzAzTVNKMFA3TVY5OTcwV05aQ0tJTEdRTy4u",
    },
    {
        "name": "Running",
        "icon": "🏃",
        "target": "Colaboradores y cónyuges",
        "schedule": "Jueves, 6:00-8:00 PM",
        "location": "Cancha Alterna No. 2",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.48.17+PM.jpeg/ad513539-1baa-53df-9423-e9e1a3a32321",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUN0UwSVkyU1FUMlQxMzBXSVJVRzBJSjJLNi4u",
    },
    {
        "name": "Patinaje Infantil (+4 años)",
        "icon": "⛸️",
        "target": "Hijos y familiares",
        "schedule": "Mar, Jue, Sáb 4:00-5:00 PM",
        "location": "Club Mario Durán - Skate Park",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/patinaje.png/3052cf7b-6685-cb88-deec-91ae0b70b511",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUQzRJVTFQNVhSRTVDR1JQOVg5MTJRTkFOVS4u",
    },
    {
        "name": "Tenis Infantil (5-9 años)",
        "icon": "🎾",
        "target": "Hijos y familiares",
        "schedule": "Sábados 7:00-8:30 AM",
        "location": "Cancha de tenis interna",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/tenis-infantil.png/ddc7cf09-11c6-2b9b-c6e5-2ea0e5b76774",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUQzNFTEJDT1RSQVZJVzJIMlQ1V0JZTEkzWC4u",
    },
    {
        "name": "Tenis Juvenil (+10 años)",
        "icon": "🎾",
        "target": "Hijos y familiares",
        "schedule": "Sábados 8:30-10:00 AM",
        "location": "Cancha de tenis interna",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/tenis-infantil.png/ddc7cf09-11c6-2b9b-c6e5-2ea0e5b76774",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpURVQxNVBMQVZDOFI0VjlTMlNQQlgzR1JFMy4u",
    },
    {
        "name": "Fútbol Infantil (5-9 años)",
        "icon": "⚽",
        "target": "Hijos y familiares",
        "schedule": "Sábados 9:00-10:30 AM",
        "location": "Cancha sintética",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.47.08+PM.jpeg/e5996c6f-d05f-100d-f5cc-980f40d1d0af",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUN1VZTzdEOVNYVzBRSzhLUjNOUEUyVDFVNC4u",
    },
    {
        "name": "Fútbol Juvenil (+10 años)",
        "icon": "⚽",
        "target": "Hijos y familiares",
        "schedule": "Sábados 10:30 AM-12:00 PM",
        "location": "Cancha sintética",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.47.08+PM.jpeg/e5996c6f-d05f-100d-f5cc-980f40d1d0af",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUOEc3NzdOSk5TM0U0MEJTOTRPUEtIUFZHTS4u",
    },
    {
        "name": "Taekwondo Infantil (6-8 años)",
        "icon": "🥋",
        "target": "Hijos y familiares",
        "schedule": "Sábados 8:30-10:00 AM",
        "location": "Coliseo Piso 2 Lobby Sur",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.52.29+PM.jpeg/3e4ab27e-df96-0a79-6846-2ba4aedc56ec",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUNTNCMTYzNk1DVUZKWkpTMzFZSThXR1Y1Uy4u",
    },
    {
        "name": "Taekwondo Junior (9-10 años)",
        "icon": "🥋",
        "target": "Hijos y familiares",
        "schedule": "Sábados 10:00-11:30 AM",
        "location": "Coliseo Piso 2 Lobby Sur",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.52.29+PM.jpeg/3e4ab27e-df96-0a79-6846-2ba4aedc56ec",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUQ0pWTVBJUElSREM0VkczSUNJOUw1TFRPQi4u",
    },
    {
        "name": "Taekwondo Juvenil (+11 años)",
        "icon": "🥋",
        "target": "Hijos y familiares",
        "schedule": "Sábados 11:30 AM-1:00 PM",
        "location": "Coliseo Piso 2 Lobby Sur",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.52.29+PM.jpeg/3e4ab27e-df96-0a79-6846-2ba4aedc56ec",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUNEhFVkY0R1g5MzhVQzFORlpYUk5WUU9YUy4u",
    },
    {
        "name": "Estimulación Musical (6-23 meses)",
        "icon": "🎶",
        "target": "Hijos",
        "schedule": "Sábados 10:00-11:00 AM",
        "location": "C.C. Villa Country Piso 1",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/estimulaci%C3%B3n.jpg/66e59290-f9d1-2b24-60be-d7fe531cdafb",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUM0tZSDE1QjRPN1A3OTVBMkpPQ0pENEk2UC4u",
    },
    {
        "name": "Estimulación Musical (2-4 años)",
        "icon": "🎶",
        "target": "Hijos",
        "schedule": "Sábados 11:00 AM-12:00 PM",
        "location": "C.C. Villa Country Piso 1",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/estimulaci%C3%B3n.jpg/66e59290-f9d1-2b24-60be-d7fe531cdafb",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUNjFRV01ZQjJUS01UUVVMS0FGOElWTldJMC4u",
    },
    {
        "name": "Rumba",
        "icon": "🕺",
        "target": "Colaboradores, cónyuges, hijos (+14 años)",
        "schedule": "Jueves 6:00-7:00 PM / Sábados 7:00-8:00 AM",
        "location": "Salón de Danza - Coliseo",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.49.27+PM.jpeg/b4b16d35-e322-7b84-b4dc-8bea94d6ec1e",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUQVpLMUJZWUNSUUtRTFIyVEdUSU9XVExJNi4u",
    },
    {
        "name": "Fútbol Masculino",
        "icon": "⚽",
        "target": "Colaboradores",
        "schedule": "Martes y jueves, 6:00-8:00 PM",
        "location": "Cancha sintética",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.47.26+PM.jpeg/530b2e2e-ed7e-c3b1-8757-0a6af0b8e735",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpURDhFSEczVEY4QVFMWTBQUjlZREdVR0FTTC4u",
    },
    {
        "name": "Natación Adultos",
        "icon": "🏊",
        "target": "Colaboradores y cónyuges",
        "schedule": "Sábados 8:00-10:00 AM (dos sesiones)",
        "location": "Piscina Uninorte",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/Nataci%C3%B3n1.jpeg.png/17ca814b-5310-d940-e239-43e26ccfa1e4",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUNUROMTVNSjZPSTBTUFVPM1FaUVlENDNGMi4u",
    },
    {
        "name": "Natación Infantil (4-12 años)",
        "icon": "🏊",
        "target": "Hijos",
        "schedule": "Sábados 8:00-10:00 AM (dos sesiones)",
        "location": "Piscina Uninorte",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/Nataci%C3%B3n1.jpeg.png/17ca814b-5310-d940-e239-43e26ccfa1e4",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUQU1GVzIyQ0QzUkxWWkIzU1dVR0dPRlo1NS4u",
    },
    {
        "name": "Música Infantil (5-8 años)",
        "icon": "🎸",
        "target": "Hijos (+5 años)",
        "schedule": "Sábados 10:00-11:00 AM",
        "location": "Salón de Música BO",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/musica-ecuador1.jpg/6af91a56-6b6f-2ba0-4680-7749f6f30673",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpURDFCRVRZSFZCNTAxN1o1WFNSNDJURUtJUC4u",
    },
    {
        "name": "Música Infantil (9-12 años)",
        "icon": "🎸",
        "target": "Hijos (+5 años)",
        "schedule": "Sábados 11:00 AM-12:00 PM",
        "location": "Salón de Música BO",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/musica-ecuador1.jpg/6af91a56-6b6f-2ba0-4680-7749f6f30673",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpURDFCRVRZSFZCNTAxN1o1WFNSNDJURUtJUC4u",
    },
    {
        "name": "Danza Infantil (4-6 años)",
        "icon": "💃",
        "target": "Hijos y familiares",
        "schedule": "Sábados 8:00-9:00 AM",
        "location": "Salón de Danza",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.48.35+PM.jpeg/2f1a9e9e-ff99-601f-8485-56be1c1ccddd",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUM0o4R1NCM0JTNzM3REpOUjQ3Q1ZKMEZaUC4u",
    },
    {
        "name": "Danza Juvenil (7-12 años)",
        "icon": "💃",
        "target": "Hijos y familiares",
        "schedule": "Sábados 9:00-10:00 AM",
        "location": "Salón de Danza",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/WhatsApp+Image+2024-03-06+at+3.48.35+PM.jpeg/2f1a9e9e-ff99-601f-8485-56be1c1ccddd",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUMkhVUVpIUUwwM0FJVkJLOE9ZVkdNS0RKVS4u",
    },
    {
        "name": "Gimnasia Infantil",
        "icon": "🤸",
        "target": "Hijos",
        "schedule": "Sábados 8:00-9:00 AM",
        "location": "Av. Las Dunas - Parque Comercial Las Dunas Open Local C9-C10",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/viga-equilibrio-gimnasia-infantil-atleta-gimnasta-chica-barra-horizontal-ejercicio-competiciones-gimnasia-entrenador-nino.jpg/0356ee69-3753-3a2b-6e3b-819aebabec03",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUOUtONUdKMldUUDRRU1pFM1RHTUZEQkZMWC4u",
    },
    {
        "name": "Fútbol Adolescentes (+12 años)",
        "icon": "⚽",
        "target": "Hijos y familiares (+12 años)",
        "schedule": "Sábados 2:00-4:00 PM",
        "location": "Cancha sintética",
        "image": "https://www.uninorte.edu.co/documents/15936117/33989154/cancha+de+futbol.jpg/15dcbb3c-d96f-9cb4-7156-a1a4c4a9b7b2",
        "enroll": "https://forms.office.com/pages/responsepage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUQlQ0WlRVWUU1UVRYNEw3VkVSR05XWVg4UC4u",
    },
    {
        "name": "Club de Caminantes",
        "icon": "🥾",
        "target": "Colaboradores de planta, docentes y familiares (+6 años)",
        "schedule": "Domingos según programación",
        "location": "Varía según ruta",
        "image": "https://www.uninorte.edu.co/documents/15936117/51497787/imagen-caminatas-ecologicas.jpg/6a1a6e47-76f3-8868-1f9b-60a7bf2b300b",
        "enroll": "https://forms.office.com/Pages/ResponsePage.aspx?id=ebawul-96E-1Fsa4sxfHglOtSOY5yDNNuoaa4MxUZZpUNFhGTUxPVkY5QVhPQjNXRkVLMVlOR0tXQS4u",
    },
    {
        "name": "Club de Cocina",
        "icon": "👨‍🍳",
        "target": "Colaboradores de planta y cónyuges beneficiarios",
        "schedule": "Sábados según programación",
        "location": "Varía según sesión",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/cocina.jpg/105730c6-2b0c-9596-5bb6-950ae0c9fb24",
        "enroll": "https://forms.office.com/r/PBPFXnyAUj",
    },
    {
        "name": "Club de Lectura LitInfan",
        "icon": "📚",
        "target": "Hijos y familiares",
        "schedule": "Una vez al mes, 10:30 AM",
        "location": "Biblioteca Karl C. Parrish Jr.",
        "image": "https://www.uninorte.edu.co/documents/15936117/32204167/galeria13956.jpg/4eedf4b0-9799-74f1-c436-47e7450fbc39",
        "enroll": "https://forms.office.com/r/kbWXpLFm8u",
    },
]


def get_catalogo_actividades(user_id: int, status: str) -> Dict:
    """
    Muestra el catálogo visual completo de todas las alternativas deportivas y artísticas
    de Bienestar Organizacional en formato carrusel con imágenes, horarios, ubicaciones
    y enlaces de inscripción.
    """
    set_status(user_id, status, 6)

    total = len(ACTIVIDADES_BIENESTAR)

    slides_html = ""
    indicators_html = ""
    for i, act in enumerate(ACTIVIDADES_BIENESTAR):
        slides_html += f'''
                    <div class="carousel-item" style="min-width: 100%; display: flex; flex-direction: column; align-items: center;">
                        <div style="width: 100%; height: 300px; overflow: hidden; border-radius: 8px;">
                            <img src="{act['image']}" alt="{act['name']}" style="width: 100%; height: 100%; object-fit: cover;" />
                        </div>
                        <div style="width: 100%; padding: 16px 4px 8px 4px; text-align: center;">
                            <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 8px;">
                                <span style="font-size: 22px;">{act['icon']}</span>
                                <h4 style="color: #124072; font-size: 16px; font-weight: 700; margin: 0;">{act['name']}</h4>
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; align-items: center;">
                                <span style="color: #4b5563; font-size: 13px;">👥 {act['target']}</span>
                                <span style="color: #4b5563; font-size: 13px;">📅 {act['schedule']}</span>
                                <span style="color: #4b5563; font-size: 13px;">📍 {act['location']}</span>
                            </div>
                            <a href="{act['enroll']}" target="_blank" rel="noopener noreferrer"
                               style="display: inline-block; background: linear-gradient(90deg, #124072 60%, #00aeda 100%); color: white; padding: 10px 28px; border-radius: 6px; font-size: 13px; font-weight: 600; text-decoration: none;">
                                Inscribirme
                            </a>
                        </div>
                    </div>
        '''
        active_class = "active" if i == 0 else ""
        indicators_html += f'<span class="carousel-indicator {active_class}" data-index="{i}" style="width: 8px; height: 8px; border-radius: 50%; background-color: {"#124072" if i == 0 else "#cbd5e1"}; cursor: pointer; transition: background-color 0.3s;"></span>'

    carousel_html = f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc; }}
            .carousel-container {{ width: 100%; max-width: 800px; margin: 0 auto; padding: 20px; background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
            .carousel-header {{ background: linear-gradient(135deg, #124072 0%, #00aeda 100%); padding: 16px; border-radius: 10px; text-align: center; margin-bottom: 16px; }}
            .carousel-header h2 {{ color: #fff; font-size: 1.15rem; font-weight: 700; margin: 0 0 4px 0; }}
            .carousel-header p {{ color: #d4edda; font-size: 0.8rem; margin: 0; }}
            .carousel {{ position: relative; overflow: hidden; border-radius: 8px; }}
            .carousel-inner {{ display: flex; transition: transform 0.5s ease; }}
            .carousel-controls {{ position: absolute; top: 40%; left: 0; right: 0; display: flex; justify-content: space-between; padding: 0 10px; pointer-events: none; }}
            .carousel-control {{ width: 40px; height: 40px; background: rgba(255,255,255,0.85); border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.12); pointer-events: auto; transition: all 0.2s; border: none; font-size: 18px; color: #124072; }}
            .carousel-control:hover {{ background: white; box-shadow: 0 4px 12px rgba(0,0,0,0.18); }}
            .carousel-indicators {{ display: flex; justify-content: center; gap: 6px; margin-top: 14px; flex-wrap: wrap; }}
            .carousel-counter {{ text-align: center; margin-top: 8px; font-size: 0.8rem; color: #64748b; }}
            .carousel-footer {{ background: #f8f9fa; border-radius: 8px; padding: 10px; margin-top: 14px; text-align: center; }}
            .carousel-footer p {{ color: #6b7280; font-size: 11px; margin: 0; }}
            .carousel-footer .contact {{ color: #124072; font-weight: 600; margin-top: 4px; }}
        </style>
    </head>
    <body>
        <div class="carousel-container">
            <div class="carousel-header">
                <h2>Alternativas Deportivas y Artisticas</h2>
                <p>{total} actividades disponibles</p>
            </div>
            <div class="carousel" id="actCarousel">
                <div class="carousel-inner" id="carouselInner">
                    {slides_html}
                </div>
                <div class="carousel-controls">
                    <button class="carousel-control" id="prevBtn">&#8249;</button>
                    <button class="carousel-control" id="nextBtn">&#8250;</button>
                </div>
            </div>
            <div class="carousel-indicators" id="indicators">
                {indicators_html}
            </div>
            <div class="carousel-counter" id="counter">1 / {total}</div>
            <div class="carousel-footer">
                <p>Sin costo &middot; Cupos limitados &middot; Febrero a noviembre &middot; Asistencia regular obligatoria</p>
                <p class="contact">Ext. 4597 | Cel 3114129772 | bienestarorg@uninorte.edu.co</p>
            </div>
        </div>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const inner = document.getElementById('carouselInner');
                const indicators = document.querySelectorAll('.carousel-indicator');
                const counter = document.getElementById('counter');
                const total = {total};
                let current = 0;

                function update() {{
                    inner.style.transform = 'translateX(-' + (current * 100) + '%)';
                    indicators.forEach((ind, i) => {{
                        ind.style.backgroundColor = i === current ? '#124072' : '#cbd5e1';
                        ind.style.transform = i === current ? 'scale(1.3)' : 'scale(1)';
                    }});
                    counter.textContent = (current + 1) + ' / ' + total;
                }}

                document.getElementById('nextBtn').addEventListener('click', function() {{
                    current = (current + 1) % total;
                    update();
                }});

                document.getElementById('prevBtn').addEventListener('click', function() {{
                    current = (current - 1 + total) % total;
                    update();
                }});

                indicators.forEach(function(ind) {{
                    ind.addEventListener('click', function() {{
                        current = parseInt(this.getAttribute('data-index'));
                        update();
                    }});
                }});

                let autoplay = setInterval(function() {{
                    current = (current + 1) % total;
                    update();
                }}, 5000);

                const container = document.querySelector('.carousel-container');
                container.addEventListener('mouseenter', function() {{ clearInterval(autoplay); }});
                container.addEventListener('mouseleave', function() {{
                    autoplay = setInterval(function() {{
                        current = (current + 1) % total;
                        update();
                    }}, 5000);
                }});

                document.addEventListener('keydown', function(e) {{
                    if (e.key === 'ArrowLeft') {{ current = (current - 1 + total) % total; update(); }}
                    if (e.key === 'ArrowRight') {{ current = (current + 1) % total; update(); }}
                }});

                update();
            }});
        </script>
    </body>
    </html>
    '''

    activity_names = ", ".join([a["name"] for a in ACTIVIDADES_BIENESTAR[:8]])
    content_for_answers = [
        f"Aqui tienes el catalogo completo de {len(ACTIVIDADES_BIENESTAR)} actividades deportivas y artisticas de Bienestar Organizacional. Entre las opciones: {activity_names}, y muchas mas. Todas son sin costo, con cupos limitados, disponibles de febrero a noviembre. Puedes inscribirte directamente desde cada tarjeta."
    ]

    return {
        "graph": carousel_html,
        "content_for_answers": content_for_answers
    }


def get_alternativas_deportivas(user_id: int, status: str) -> Dict:
    """
    Retorna información visual sobre el beneficio de Alternativas Deportivas y Artísticas
    de Bienestar Organizacional - Gestión Humana, Universidad del Norte.
    """
    set_status(user_id, status, 6)

    html_content = '''
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 100%; margin: 0 auto;">

        <!-- Header -->
        <div style="background: linear-gradient(135deg, #124072 0%, #00aeda 100%); padding: 20px; border-radius: 12px; margin-bottom: 16px; text-align: center;">
            <h3 style="color: #ffffff; font-size: 20px; font-weight: 700; margin: 0 0 6px 0;">
                Alternativas Deportivas y Artísticas
            </h3>
            <p style="color: #d4edda; font-size: 14px; margin: 0; font-style: italic;">
                Bienestar Organizacional - Gestión Humana
            </p>
        </div>

        <!-- Info General -->
        <div style="background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #124072; font-size: 15px; margin: 0 0 8px 0;">Información General</h4>
            <div style="display: flex; flex-direction: column; gap: 6px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 16px;">🏷️</span>
                    <span style="color: #2d2d2d; font-size: 13px;"><strong>Beneficio:</strong> Alternativas deportivas y artísticas</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 16px;">🏢</span>
                    <span style="color: #2d2d2d; font-size: 13px;"><strong>Área responsable:</strong> Bienestar Organizacional – Gestión Humana</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 16px;">📂</span>
                    <span style="color: #2d2d2d; font-size: 13px;"><strong>Categoría:</strong> Actividades Deportivas y Artísticas</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 16px;">🔗</span>
                    <a href="https://www.uninorte.edu.co/web/direccion-de-gestion-humana/actividades_bienestar" target="_blank" style="color: #00aeda; font-size: 13px; text-decoration: none;">Portal de Gestión Humana - Actividades</a>
                </div>
            </div>
        </div>

        <!-- Descripción -->
        <div style="background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #124072; font-size: 15px; margin: 0 0 8px 0;">¿Qué es?</h4>
            <p style="color: #2d2d2d; font-size: 13px; line-height: 1.6; margin: 0;">
                Conjunto de alternativas culturales, deportivas y artísticas orientadas a promover el bienestar integral, la creatividad y el aprovechamiento del tiempo libre de los colaboradores y sus familiares. Incluye clases y espacios formativos que fomentan la expresión artística, el desarrollo de habilidades culturales y la integración familiar.
            </p>
        </div>

        <!-- Público -->
        <div style="background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #124072; font-size: 15px; margin: 0 0 8px 0;">¿A quién aplica?</h4>
            <p style="color: #2d2d2d; font-size: 13px; line-height: 1.6; margin: 0;">
                Colaboradores(as) de planta, catedráticos y familiares beneficiarios de la Caja de Compensación Combarranquilla.
            </p>
        </div>

        <!-- Requisitos -->
        <div style="background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #124072; font-size: 15px; margin: 0 0 8px 0;">Requisitos</h4>
            <p style="color: #2d2d2d; font-size: 13px; line-height: 1.6; margin: 0;">
                Tener contrato laboral vigente en Uninorte y estar afiliado a Combarranquilla. Si no está afiliado, puede consultar con el asesor Jeremy Henao (Ext. 3557, Cel/WP 3174278674).
            </p>
        </div>

        <!-- Condiciones -->
        <div style="background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #124072; font-size: 15px; margin: 0 0 8px 0;">Condiciones</h4>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 16px;">📅</span>
                    <span style="color: #2d2d2d; font-size: 13px;"><strong>Vigencia:</strong> Febrero a noviembre</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 16px;">⏰</span>
                    <span style="color: #2d2d2d; font-size: 13px;"><strong>Horarios:</strong> Según cada actividad</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 16px;">🎟️</span>
                    <span style="color: #2d2d2d; font-size: 13px;"><strong>Cupos:</strong> Limitados</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 16px;">💰</span>
                    <span style="color: #2d2d2d; font-size: 13px;"><strong>Costo:</strong> Sin costo (asistencia regular obligatoria para mantener cupo)</span>
                </div>
            </div>
        </div>

        <!-- Inscripción -->
        <div style="background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #124072; font-size: 15px; margin: 0 0 8px 0;">¿Cómo inscribirse?</h4>
            <p style="color: #2d2d2d; font-size: 13px; line-height: 1.6; margin: 0;">
                Ingrese a la página de actividades del portal de Gestión Humana y diligencie el enlace de inscripción. Recibirá un correo de confirmación. Si no hay cupos, quedará en lista de espera. Puede inscribirse en cualquier momento entre febrero y noviembre.
            </p>
        </div>

        <!-- FAQs -->
        <div style="background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #124072; font-size: 15px; margin: 0 0 10px 0;">Preguntas Frecuentes</h4>
            <div style="margin-bottom: 10px;">
                <p style="color: #124072; font-size: 13px; font-weight: 600; margin: 0 0 4px 0;">¿Puedo inscribir a mi sobrino en las clases?</p>
                <p style="color: #2d2d2d; font-size: 13px; margin: 0;">La opción de inscribir sobrinos, nietos y hermanos solo aplica para quienes no tengan hijos inscritos en la actividad. En la página de cada actividad se describe a quiénes aplica.</p>
            </div>
            <div style="margin-bottom: 10px;">
                <p style="color: #124072; font-size: 13px; font-weight: 600; margin: 0 0 4px 0;">¿Debo traer algo para las clases deportivas?</p>
                <p style="color: #2d2d2d; font-size: 13px; margin: 0;">Ropa cómoda, hidratación y la mejor actitud.</p>
            </div>
            <div>
                <p style="color: #124072; font-size: 13px; font-weight: 600; margin: 0 0 4px 0;">¿Puedo inscribirme en varias actividades?</p>
                <p style="color: #2d2d2d; font-size: 13px; margin: 0;">Sí, los colaboradores pueden inscribirse en todas las actividades que prefieran.</p>
            </div>
        </div>

        <!-- Contacto -->
        <div style="background: linear-gradient(135deg, #124072 0%, #00aeda 100%); border-radius: 12px; padding: 18px; text-align: center;">
            <h4 style="color: #ffffff; font-size: 15px; margin: 0 0 12px 0;">Contacto - Bienestar Organizacional</h4>
            <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 8px;">
                <span style="background: rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 14px; color: #e2e8f0; font-size: 12px;">Ext. 4597</span>
                <span style="background: rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 14px; color: #e2e8f0; font-size: 12px;">Cel/WP: 3114129772</span>
                <span style="background: rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 14px; color: #e2e8f0; font-size: 12px;">bienestarorg@uninorte.edu.co</span>
            </div>
        </div>

    </div>
    '''

    return {
        "display": html_content,
        "content_for_answers": [
            "Alternativas Deportivas y Artísticas es un beneficio de Bienestar Organizacional para colaboradores de planta, catedráticos y familiares afiliados a Combarranquilla. Incluye actividades culturales, deportivas y artísticas sin costo, disponibles de febrero a noviembre. Se requiere contrato vigente y afiliación a Combarranquilla. Inscripción por la página de Gestión Humana. Contacto: Ext. 4597, Cel 3114129772, bienestarorg@uninorte.edu.co."
        ]
    }


def get_flexibilidad_info(user_id: int, status: str) -> Dict:
    """
    Retorna información visual completa sobre las medidas de Flexibilidad Laboral
    de Bienestar Organizacional - Gestión Humana, Universidad del Norte.
    Incluye Flexiacademia (docentes), Flexiespacio (administrativos) y Flexitiempo.
    """
    set_status(user_id, status, 6)

    html_content = '''
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 100%; margin: 0 auto;">

        <!-- Header -->
        <div style="background: linear-gradient(135deg, #124072 0%, #00aeda 100%); padding: 20px; border-radius: 12px; margin-bottom: 16px; text-align: center;">
            <h3 style="color: #ffffff; font-size: 20px; font-weight: 700; margin: 0 0 6px 0;">
                Medidas de Flexibilidad Laboral
            </h3>
            <p style="color: #d4edda; font-size: 14px; margin: 0; font-style: italic;">
                Bienestar Organizacional - Gestión Humana
            </p>
        </div>

        <!-- FLEXIACADEMIA -->
        <div style="background: #eef6ff; border: 2px solid #124072; border-radius: 12px; padding: 18px; margin-bottom: 16px;">
            <h4 style="color: #124072; font-size: 17px; margin: 0 0 10px 0; border-bottom: 2px solid #00aeda; padding-bottom: 8px;">📚 FLEXIACADEMIA (Docentes)</h4>
            <p style="color: #2d2d2d; font-size: 13px; line-height: 1.6; margin: 0 0 10px 0;">
                Beneficio para docentes con contrato a término indefinido o fijo superior a 3 meses, a partir del tercer mes de vinculación.
            </p>
            <div style="background: #ffffff; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                <p style="color: #124072; font-size: 13px; font-weight: 600; margin: 0 0 6px 0;">Docentes tiempo completo:</p>
                <p style="color: #2d2d2d; font-size: 13px; margin: 0;">Máximo 1 día y medio por semana fuera del campus, previa conciliación con el director de departamento. Preferiblemente para producción intelectual.</p>
            </div>
            <div style="background: #ffffff; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                <p style="color: #124072; font-size: 13px; font-weight: 600; margin: 0 0 6px 0;">Docentes medio tiempo:</p>
                <p style="color: #2d2d2d; font-size: 13px; margin: 0;">Media jornada (4 horas) fuera del campus durante la semana. Opción de dividir en dos jornadas de 2 horas. Preferiblemente para producción intelectual.</p>
            </div>
            <div style="background: #fff3cd; border-radius: 8px; padding: 12px;">
                <p style="color: #856404; font-size: 12px; margin: 0;">⚠️ No contempla realización de clases virtuales. No debe afectar presencialidad en clases, atención a estudiantes ni reuniones convocadas. Profesores extranjeros: durante intersemestral (junio-julio) pueden trabajar remoto hasta 1 semana desde su país de origen (no aplica para docentes colombianos).</p>
            </div>
        </div>

        <!-- FLEXIESPACIO -->
        <div style="background: #eef6ff; border: 2px solid #124072; border-radius: 12px; padding: 18px; margin-bottom: 16px;">
            <h4 style="color: #124072; font-size: 17px; margin: 0 0 10px 0; border-bottom: 2px solid #00aeda; padding-bottom: 8px;">🏠 FLEXIESPACIO (Administrativos)</h4>
            <p style="color: #2d2d2d; font-size: 13px; line-height: 1.6; margin: 0 0 10px 0;">
                Para colaboradores con contrato a término indefinido o fijo superior a 3 meses, a partir del tercer mes de vinculación. Registro en sistema Agatha.
            </p>
            <div style="background: #ffffff; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                <p style="color: #124072; font-size: 13px; font-weight: 600; margin: 0 0 6px 0;">4 días al mes:</p>
                <p style="color: #2d2d2d; font-size: 13px; margin: 0;">Rector, Vicerrector, Decanos, Directores Administrativos, Jefes</p>
            </div>
            <div style="background: #ffffff; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                <p style="color: #124072; font-size: 13px; font-weight: 600; margin: 0 0 6px 0;">3 días al mes:</p>
                <p style="color: #2d2d2d; font-size: 13px; margin: 0;">Coordinadores, Asistentes, Analistas, Rol Profesionales</p>
            </div>
            <div style="background: #fff3cd; border-radius: 8px; padding: 12px;">
                <p style="color: #856404; font-size: 12px; margin: 0;">⚠️ Variar los días (no siempre el mismo día). No se permiten 2 días laborales consecutivos. Opción de dividir 1 día en dos medias jornadas. Implica trabajar en la ciudad, no por fuera. No aplica para cargos técnicos, de soporte, estudiantes en práctica ni aprendices. Vigencia: febrero a noviembre.</p>
            </div>
        </div>

        <!-- FLEXITIEMPO -->
        <div style="background: #eef6ff; border: 2px solid #124072; border-radius: 12px; padding: 18px; margin-bottom: 16px;">
            <h4 style="color: #124072; font-size: 17px; margin: 0 0 10px 0; border-bottom: 2px solid #00aeda; padding-bottom: 8px;">⏰ FLEXITIEMPO (Administrativos)</h4>
            <p style="color: #2d2d2d; font-size: 13px; line-height: 1.6; margin: 0 0 10px 0;">
                Alternativas de horario flexible. Registro en sistema Agatha. Vigencia trimestral (cada 3 meses se concilia con el jefe). Disponible de febrero a noviembre.
            </p>

            <div style="background: #ffffff; border-radius: 8px; padding: 14px; margin-bottom: 8px;">
                <p style="color: #124072; font-size: 13px; font-weight: 600; margin: 0 0 4px 0;">Jornada L-V:</p>
                <div style="font-size: 12px; color: #2d2d2d; line-height: 1.8;">
                    <p style="margin: 2px 0;"><strong>Flexi1:</strong> L-J 7:30am-12:00pm y 1:30pm-5:30pm / V 8:00am-12:30pm y 2:00pm-5:30pm</p>
                    <p style="margin: 2px 0;"><strong>Flexi2:</strong> L-J 8:00am-12:30pm y 2:00pm-6:00pm / V 8:00am-12:30pm y 1:30pm-5:00pm</p>
                    <p style="margin: 2px 0;"><strong>Flexi3:</strong> L-J 8:00am-12:00pm y 2:00pm-6:30pm / V 8:00am-12:00pm y 1:30pm-5:30pm</p>
                    <p style="margin: 2px 0;"><strong>Flexi4:</strong> Bono de Tiempo (medio día libre al mes, mañana o tarde) - Solo cargos técnicos y soporte</p>
                </div>
            </div>

            <div style="background: #ffffff; border-radius: 8px; padding: 14px; margin-bottom: 8px;">
                <p style="color: #124072; font-size: 13px; font-weight: 600; margin: 0 0 4px 0;">Jornada L-S:</p>
                <div style="font-size: 12px; color: #2d2d2d; line-height: 1.8;">
                    <p style="margin: 2px 0;"><strong>Flexi4:</strong> Bono de Tiempo (medio día libre al mes)</p>
                    <p style="margin: 2px 0;"><strong>Flexi5:</strong> L-V 8:00am-12:30pm y 2:00pm-5:30pm / S 8:00am-10:00am</p>
                </div>
            </div>

            <div style="background: #fff3cd; border-radius: 8px; padding: 12px;">
                <p style="color: #856404; font-size: 12px; margin: 0;">⚠️ Flexi1, Flexi2, Flexi3 y Flexi5 son compatibles con Flexiespacio (solo para Rector, Vicerrector, Decanos, Dir. Admin, Jefes, Coordinadores, Asistentes, Analistas y Rol Profesional). Flexi4 (Bono de Tiempo) aplica exclusivamente para cargos técnicos, auxiliares y secretarios(as). No se permite acogerse a dos o más medidas de Flexitiempo simultáneamente. Solicitar con al menos 8 días de anticipación.</p>
            </div>
        </div>

        <!-- Roles -->
        <div style="background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
            <h4 style="color: #124072; font-size: 15px; margin: 0 0 10px 0;">Roles y Responsabilidades</h4>
            <div style="margin-bottom: 10px;">
                <p style="color: #124072; font-size: 13px; font-weight: 600; margin: 0 0 4px 0;">Jefe inmediato(a):</p>
                <p style="color: #2d2d2d; font-size: 13px; margin: 0;">Conciliar modalidad sin afectar servicio. Establecer acuerdos de desempeño. Aprobar solicitudes en Agatha. Recordar seguridad de la información remota.</p>
            </div>
            <div style="margin-bottom: 10px;">
                <p style="color: #124072; font-size: 13px; font-weight: 600; margin: 0 0 4px 0;">Colaborador(a):</p>
                <p style="color: #2d2d2d; font-size: 13px; margin: 0;">Conciliar con el equipo. Registrar en Agatha. Garantizar disponibilidad y localización durante flexiespacio (es trabajo, no tiempo libre). Garantizar seguridad de información remota.</p>
            </div>
            <div>
                <p style="color: #124072; font-size: 13px; font-weight: 600; margin: 0 0 4px 0;">Dirección de Gestión Humana:</p>
                <p style="color: #2d2d2d; font-size: 13px; margin: 0;">Establecer medidas viables operativa y financieramente con aprobación de Alta Dirección.</p>
            </div>
        </div>

        <!-- Nota importante -->
        <div style="background: #fef2f2; border-left: 4px solid #dc2626; border-radius: 0 8px 8px 0; padding: 14px; margin-bottom: 12px;">
            <p style="color: #991b1b; font-size: 13px; font-weight: 600; margin: 0 0 4px 0;">Importante</p>
            <p style="color: #2d2d2d; font-size: 12px; margin: 0;">El cumplimiento de responsabilidades siempre prevalece sobre los beneficios de flexibilidad, especialmente en eventos institucionales, reuniones o actividades emergentes. Todas las medidas pueden ser sujetas a cambio por la Institución.</p>
        </div>

        <!-- Contacto -->
        <div style="background: linear-gradient(135deg, #124072 0%, #00aeda 100%); border-radius: 12px; padding: 18px; text-align: center;">
            <h4 style="color: #ffffff; font-size: 15px; margin: 0 0 12px 0;">Contacto - Bienestar Organizacional</h4>
            <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 8px;">
                <span style="background: rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 14px; color: #e2e8f0; font-size: 12px;">Tel. 605-3509509</span>
                <span style="background: rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 14px; color: #e2e8f0; font-size: 12px;">Ext. 4597 - 3208</span>
                <span style="background: rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 14px; color: #e2e8f0; font-size: 12px;">Cel: 311 412 9772</span>
            </div>
        </div>

    </div>
    '''

    return {
        "display": html_content,
        "content_for_answers": [
            "Las medidas de flexibilidad laboral de Uninorte incluyen tres modalidades: FLEXIACADEMIA para docentes (hasta 1.5 días fuera del campus para tiempo completo, media jornada para medio tiempo, preferiblemente producción intelectual). FLEXIESPACIO para administrativos (4 días/mes para directivos, 3 días/mes para coordinadores y analistas, trabajo remoto en la ciudad). FLEXITIEMPO con horarios alternativos Flexi1 a Flexi5 y Bono de Tiempo para cargos técnicos. Todas requieren contrato de más de 3 meses, aplican de febrero a noviembre, registro en Agatha y conciliación con jefe inmediato. Contacto: Ext. 4597-3208, Cel 3114129772, Tel 605-3509509."
        ]
    }