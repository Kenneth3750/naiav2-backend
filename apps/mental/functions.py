from dotenv import load_dotenv
import os
from typing import Dict
from apps.status.services import set_status
from openai import OpenAI
from serpapi import GoogleSearch
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
        
        return {"graph": conversation_guide}
        
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
