from dotenv import load_dotenv
import os
from typing import Dict
from apps.status.services import set_status
from openai import OpenAI
import json
from apps.researcher.functions import generate_image_carousel_html
from apps.skills.models import TrainingReport
from apps.users.models import User
from datetime import datetime, timezone, timedelta
from apps.skills.services import SkillsTrainerDBService
from apps.skills.models import TrainingReport
from datetime import timezone, timedelta
from serpapi import GoogleSearch
load_dotenv()

openai_api_key = os.getenv("open_ai")

client = OpenAI(
    api_key=openai_api_key
)

def simulate_job_interview(job_position: str, company_type: str, user_instructions: str, user_id: int, status: str, language: str) -> Dict:
    """
    Generates a conversational job interview simulation for NAIA to conduct 
    a natural step-by-step interview, along with an informative HTML of the simulation.
    
    Args:
        job_position (str): Position for which the interview is simulated
        company_type (str): Type of company (startup, corporate, tech, etc.)
        user_instructions (str): Specific user preferences and customizations for the interview
        user_id (int): User ID
        status (str): Status message
        language (str): Language for the simulation
        
    Returns:
        dict: Dictionary with conversational guide and tracking HTML
    """
    try:
        set_status(user_id, status, 4) 
        
        is_spanish = language.lower().startswith('es') or 'spanish' in language.lower()
        
        system_prompt = """You are an HR specialist who creates STEP-BY-STEP interview scripts for an AI avatar called NAIA. Your job is to generate a detailed script with clear phases and numbered steps that NAIA must follow exactly to conduct a complete job interview from start to finish.

CRITICAL: The "interview_guide" must be a DETAILED STEP-BY-STEP SCRIPT with numbered phases that NAIA can follow sequentially. NAIA will follow this script exactly as written.

REQUIRED RESPONSE FORMAT:
You must return ONLY a valid JSON with this exact structure:

{
  "interview_guide": "DETAILED STEP-BY-STEP SCRIPT with numbered phases and exact dialogue",
  "questions": [
    {
      "question": "Specific question",
      "purpose": "Purpose of the question",
      "follow_up_suggestions": ["Follow-up 1", "Follow-up 2"]
    }
  ],
  "company_context": "Company context",
  "position_overview": "Position summary",
  "interview_tips": "Tips for the user"
}

INTERVIEW_GUIDE STRUCTURE (MUST BE DETAILED):
The interview_guide must contain these numbered phases:

PHASE 1 - OPENING:
- Exact greeting and introduction NAIA should say
- How to establish rapport and explain the process
- What NAIA should say about the interview structure

PHASE 2 - QUESTIONS (5-6 questions):
- Question 1: [Exact question text] - Wait for response
- Transition 1: [Exact transition text after response]
- Question 2: [Exact question text] - Wait for response
- Transition 2: [Exact transition text after response]
- [Continue for all questions]

PHASE 3 - CLOSING:
- Thank the candidate
- Explain next steps
- Professional goodbye

SCRIPT REQUIREMENTS:
- Each phase must be clearly numbered and detailed
- Include exact dialogue NAIA should say
- Specify when to wait for user responses
- Include natural transitions between questions
- Must have a clear beginning, middle, and end
- Total interview should last 10-15 minutes (5-6 questions max)
- Include encouraging remarks between questions

EXAMPLE FORMAT:
"PHASE 1 - OPENING:
Hello! I'm NAIA and I'll be conducting your interview today for the [POSITION] role. [Continue with exact dialogue...]

PHASE 2 - INTERVIEW QUESTIONS:
Question 1: Tell me about yourself and why you're interested in this position.
[Wait for response, then provide encouraging feedback]
Transition: Thank you for sharing that. Now I'd like to learn more about your experience.

Question 2: [Next specific question]
[Wait for response]
Transition: [Specific transition]

[Continue for all questions]

PHASE 3 - CLOSING:
Thank you for your time and thoughtful responses. [Continue with exact closing dialogue...]"

The script must be specific enough that NAIA knows exactly what to say and when."""

        if is_spanish:
            user_prompt = f"""Crea un guión de entrevista conversacional para NAIA para el siguiente contexto:

PUESTO: {job_position}
TIPO DE EMPRESA: {company_type}
IDIOMA: {language}

INSTRUCCIONES ESPECÍFICAS DEL USUARIO: {user_instructions}

IMPORTANTE: Debes seguir las instrucciones específicas del usuario al pie de la letra. Si el usuario especifica:
- Número de preguntas (mínimo/máximo): Respeta exactamente ese número
- Tipo de preguntas específicas: Incluye solo esas categorías
- Preguntas específicas que quiere practicar: Usa esas preguntas exactas
- Duración deseada: Ajusta el guión a ese tiempo
- Estilo de entrevista: Adapta el tono y enfoque según sus preferencias
- Cualquier otro requerimiento específico: Implementalo en el guión

El guión debe ser específico para esta posición y tipo de empresa, considerando:
- Competencias clave requeridas para el puesto
- Cultura organizacional del tipo de empresa mencionado
- Preguntas relevantes para el nivel de experiencia esperado
- Contexto del mercado laboral colombiano
- Y PRINCIPALMENTE: Las instrucciones específicas del usuario

Genera un guión que permita a NAIA ser una entrevistadora profesional, empática y efectiva, siguiendo exactamente lo que el usuario ha solicitado. Responde todo en español."""
        else:
            user_prompt = f"""Create a conversational interview script for NAIA for the following context:

POSITION: {job_position}
COMPANY TYPE: {company_type}
LANGUAGE: {language}

SPECIFIC USER INSTRUCTIONS: {user_instructions}

IMPORTANT: You must follow the user's specific instructions exactly. If the user specifies:
- Number of questions (minimum/maximum): Respect exactly that number
- Specific types of questions: Include only those categories
- Specific questions they want to practice: Use those exact questions
- Desired duration: Adjust the script to that timeframe
- Interview style: Adapt tone and approach according to their preferences
- Any other specific requirements: Implement them in the script

The script should be specific for this position and company type, considering:
- Key competencies required for the position
- Organizational culture of the mentioned company type
- Relevant questions for the expected experience level
- Colombian job market context
- And PRIMARILY: The user's specific instructions

Generate a script that allows NAIA to be a professional, empathetic and effective interviewer, following exactly what the user has requested. Respond everything in English."""

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        # Extract and validate JSON response
        response_content = response.choices[0].message.content
        
        try:
            interview_data = json.loads(response_content)
        except json.JSONDecodeError:
            # If not valid JSON, create basic structure
            default_tips = "Mantén la calma, sé auténtico y muestra tu entusiasmo." if is_spanish else "Stay calm, be authentic and show your enthusiasm."
            interview_data = {
                "interview_guide": response_content,
                "questions": [],
                "company_context": f"Interview for {job_position} at {company_type}",
                "position_overview": f"Position: {job_position}",
                "interview_tips": default_tips
            }
        
        # Generate informative HTML for the simulation
        if is_spanish:
            html_content = generate_spanish_html(job_position, company_type, interview_data)
        else:
            html_content = generate_english_html(job_position, company_type, interview_data)
        
        return {
            "interview_guide": interview_data.get("interview_guide", ""),
            "display": html_content
        }
        
    except Exception as e:
        print(f"Error generating job interview simulation: {str(e)}")
        return {"error": str(e)}


def generate_spanish_html(job_position: str, company_type: str, interview_data: dict) -> str:
    """Generate Spanish HTML for interview simulation"""
    return f"""
    <div class="simulation-container">
        <div class="header">
            <h1>
                <span class="emoji">🎯</span>
                Simulación de Entrevista
            </h1>
            <div class="status-badge">
                <span>🔴</span>
                EN VIVO - Entrevista Activa
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <h3>💼 Posición</h3>
                <p>{job_position}</p>
            </div>
            
            <div class="info-card">
                <h3>🏢 Empresa</h3>
                <p>{company_type}</p>
            </div>
            
            <div class="info-card">
                <h3>⏱️ Duración</h3>
                <p>10-15 minutos aproximadamente</p>
            </div>
            
            <div class="info-card">
                <h3>👥 Entrevistadora</h3>
                <p>NAIA - Especialista en RRHH</p>
            </div>
        </div>
        
        <div class="questions-preview">
            <h3>📋 Áreas a Evaluar</h3>
            {chr(10).join([f'<div class="question-item">• {q.get("purpose", "Evaluación general")}</div>' for q in interview_data.get("questions", [])[:5]])}
        </div>
        
        <div class="tips-section">
            <h3>💡 Consejos para la Entrevista</h3>
            <p>{interview_data.get("interview_tips", "Mantén la calma, sé auténtico y muestra tu entusiasmo por la oportunidad.")}</p>
        </div>
    </div>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        .simulation-container {{
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #667eea;
        }}
        
        .header h1 {{
            font-size: 2.2rem;
            color: #2d3748;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }}
        
        .header .emoji {{
            font-size: 2.5rem;
        }}
        
        .status-badge {{
            background: linear-gradient(45deg, #48bb78, #38a169);
            color: white;
            padding: 8px 20px;
            border-radius: 25px;
            font-weight: 600;
            font-size: 0.9rem;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .info-card {{
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            border-radius: 15px;
            padding: 20px;
            border: 2px solid rgba(102, 126, 234, 0.2);
            transition: all 0.3s ease;
        }}
        
        .info-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border-color: #667eea;
        }}
        
        .info-card h3 {{
            color: #4a5568;
            font-size: 1.1rem;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .info-card p {{
            color: #2d3748;
            line-height: 1.6;
            font-size: 0.95rem;
        }}
        
        .questions-preview {{
            background: rgba(255, 255, 255, 0.8);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
        }}
        
        .questions-preview h3 {{
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 1.3rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .question-item {{
            background: linear-gradient(90deg, #f7fafc, #edf2f7);
            padding: 12px 18px;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }}
        
        .question-item:hover {{
            background: linear-gradient(90deg, #edf2f7, #e2e8f0);
            transform: translateX(5px);
        }}
        
        .tips-section {{
            background: linear-gradient(135deg, #ffeaa7, #fdcb6e);
            border-radius: 15px;
            padding: 20px;
            border: 2px solid rgba(253, 203, 110, 0.3);
        }}
        
        .tips-section h3 {{
            color: #8b4513;
            margin-bottom: 15px;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .tips-section p {{
            color: #8b4513;
            line-height: 1.6;
            font-weight: 500;
        }}
        
        .progress-bar {{
            background: rgba(255, 255, 255, 0.3);
            height: 8px;
            border-radius: 4px;
            margin: 20px 0;
            overflow: hidden;
        }}
        
        .progress-fill {{
            background: linear-gradient(90deg, #48bb78, #38a169);
            height: 100%;
            width: 0%;
            border-radius: 4px;
            animation: fillProgress 3s ease-in-out;
        }}
        
        @keyframes fillProgress {{
            from {{ width: 0%; }}
            to {{ width: 100%; }}
        }}
        
        @media (max-width: 768px) {{
            .simulation-container {{
                padding: 20px;
                margin: 10px;
            }}
            
            .header h1 {{
                font-size: 1.8rem;
                flex-direction: column;
                gap: 10px;
            }}
            
            .info-grid {{
                grid-template-columns: 1fr;
                gap: 15px;
            }}
        }}
    </style>
    """


def generate_english_html(job_position: str, company_type: str, interview_data: dict) -> str:
    """Generate English HTML for interview simulation"""
    return f"""
    <div class="simulation-container">
        <div class="header">
            <h1>
                <span class="emoji">🎯</span>
                Interview Simulation
            </h1>
            <div class="status-badge">
                <span>🔴</span>
                LIVE - Active Interview
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <h3>💼 Position</h3>
                <p>{job_position}</p>
            </div>
            
            <div class="info-card">
                <h3>🏢 Company</h3>
                <p>{company_type}</p>
            </div>
            
            <div class="info-card">
                <h3>⏱️ Duration</h3>
                <p>Approximately 10-15 minutes</p>
            </div>
            
            <div class="info-card">
                <h3>👥 Interviewer</h3>
                <p>NAIA - HR Specialist</p>
            </div>
        </div>
        
        <div class="questions-preview">
            <h3>📋 Areas to Evaluate</h3>
            {chr(10).join([f'<div class="question-item">• {q.get("purpose", "General evaluation")}</div>' for q in interview_data.get("questions", [])[:5]])}
        </div>
        
        <div class="tips-section">
            <h3>💡 Interview Tips</h3>
            <p>{interview_data.get("interview_tips", "Stay calm, be authentic and show your enthusiasm for the opportunity.")}</p>
        </div>
    </div>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        .simulation-container {{
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #667eea;
        }}
        
        .header h1 {{
            font-size: 2.2rem;
            color: #2d3748;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }}
        
        .header .emoji {{
            font-size: 2.5rem;
        }}
        
        .status-badge {{
            background: linear-gradient(45deg, #48bb78, #38a169);
            color: white;
            padding: 8px 20px;
            border-radius: 25px;
            font-weight: 600;
            font-size: 0.9rem;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .info-card {{
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            border-radius: 15px;
            padding: 20px;
            border: 2px solid rgba(102, 126, 234, 0.2);
            transition: all 0.3s ease;
        }}
        
        .info-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border-color: #667eea;
        }}
        
        .info-card h3 {{
            color: #4a5568;
            font-size: 1.1rem;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .info-card p {{
            color: #2d3748;
            line-height: 1.6;
            font-size: 0.95rem;
        }}
        
        .questions-preview {{
            background: rgba(255, 255, 255, 0.8);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
        }}
        
        .questions-preview h3 {{
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 1.3rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .question-item {{
            background: linear-gradient(90deg, #f7fafc, #edf2f7);
            padding: 12px 18px;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }}
        
        .question-item:hover {{
            background: linear-gradient(90deg, #edf2f7, #e2e8f0);
            transform: translateX(5px);
        }}
        
        .tips-section {{
            background: linear-gradient(135deg, #ffeaa7, #fdcb6e);
            border-radius: 15px;
            padding: 20px;
            border: 2px solid rgba(253, 203, 110, 0.3);
        }}
        
        .tips-section h3 {{
            color: #8b4513;
            margin-bottom: 15px;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .tips-section p {{
            color: #8b4513;
            line-height: 1.6;
            font-weight: 500;
        }}
        
        .progress-bar {{
            background: rgba(255, 255, 255, 0.3);
            height: 8px;
            border-radius: 4px;
            margin: 20px 0;
            overflow: hidden;
        }}
        
        .progress-fill {{
            background: linear-gradient(90deg, #48bb78, #38a169);
            height: 100%;
            width: 0%;
            border-radius: 4px;
            animation: fillProgress 3s ease-in-out;
        }}
        
        @keyframes fillProgress {{
            from {{ width: 0%; }}
            to {{ width: 100%; }}
        }}
        
        @media (max-width: 768px) {{
            .simulation-container {{
                padding: 20px;
                margin: 10px;
            }}
            
            .header h1 {{
                font-size: 1.8rem;
                flex-direction: column;
                gap: 10px;
            }}
            
            .info-grid {{
                grid-template-columns: 1fr;
                gap: 15px;
            }}
        }}
    </style>
    """

def get_simulation_css() -> str:
    """Return the CSS styles for interview simulation"""
    return """
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .simulation-container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #667eea;
        }
        
        .header h1 {
            font-size: 2.2rem;
            color: #2d3748;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }
        
        .header .emoji {
            font-size: 2.5rem;
        }
        
        .status-badge {
            background: linear-gradient(45deg, #48bb78, #38a169);
            color: white;
            padding: 8px 20px;
            border-radius: 25px;
            font-weight: 600;
            font-size: 0.9rem;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .info-card {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            border-radius: 15px;
            padding: 20px;
            border: 2px solid rgba(102, 126, 234, 0.2);
            transition: all 0.3s ease;
        }
        
        .info-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border-color: #667eea;
        }
        
        .info-card h3 {
            color: #4a5568;
            font-size: 1.1rem;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .info-card p {
            color: #2d3748;
            line-height: 1.6;
            font-size: 0.95rem;
        }
        
        .questions-preview {
            background: rgba(255, 255, 255, 0.8);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
        }
        
        .questions-preview h3 {
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 1.3rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .question-item {
            background: linear-gradient(90deg, #f7fafc, #edf2f7);
            padding: 12px 18px;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }
        
        .question-item:hover {
            background: linear-gradient(90deg, #edf2f7, #e2e8f0);
            transform: translateX(5px);
        }
        
        .tips-section {
            background: linear-gradient(135deg, #ffeaa7, #fdcb6e);
            border-radius: 15px;
            padding: 20px;
            border: 2px solid rgba(253, 203, 110, 0.3);
        }
        
        .tips-section h3 {
            color: #8b4513;
            margin-bottom: 15px;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .tips-section p {
            color: #8b4513;
            line-height: 1.6;
            font-weight: 500;
        }
        
        .progress-bar {
            background: rgba(255, 255, 255, 0.3);
            height: 8px;
            border-radius: 4px;
            margin: 20px 0;
            overflow: hidden;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #48bb78, #38a169);
            height: 100%;
            width: 0%;
            border-radius: 4px;
            animation: fillProgress 3s ease-in-out;
        }
        
        @keyframes fillProgress {
            from { width: 0%; }
            to { width: 100%; }
        }
        
        @media (max-width: 768px) {
            .simulation-container {
                padding: 20px;
                margin: 10px;
            }
            
            .header h1 {
                font-size: 1.8rem;
                flex-direction: column;
                gap: 10px;
            }
            
            .info-grid {
                grid-template-columns: 1fr;
                gap: 15px;
            }
        }
    """


def analyze_professional_appearance(context: str, user_id: int, status: str, user_gender: str = None) -> Dict:
    """
    Analyzes the user's professional appearance and shows clothing suggestions via image carousel if needed.
    The image is handled automatically by the LLM system.
    
    Args:
        context (str): Analysis context (interview, presentation, cocktail, formal, etc.)
        user_id (int): User ID
        status (str): Status message for tracking
        user_gender (str, optional): User's declared gender ('male', 'female', 'non-binary', etc.)
                                   Takes absolute priority over visual analysis
        
    Returns:
        dict: Structured analysis with image carousel if suggestions are needed
    """
    try:
        set_status(user_id, status, 4) 

        # Construir parte del prompt sobre género con prioridad al usuario
        gender_instruction = ""
        if user_gender:
            gender_instruction = f"""
CRITICAL GENDER OVERRIDE: The user has explicitly declared their gender as '{user_gender}'. 
You MUST use this declared gender for all clothing recommendations and search queries, 
regardless of what you observe in the image. This user declaration has ABSOLUTE PRIORITY.
"""
        else:
            gender_instruction = """
GENDER IDENTIFICATION FROM IMAGE: Since no gender was declared by the user, 
identify the apparent gender presentation from the image to tailor recommendations appropriately.
"""

        analysis_prompt = f"""You are an expert professional image consultant. I need you to analyze the person's appearance in the image that has been provided, considering the following context: {context}

{gender_instruction}

Evaluate the following aspects:
1. **GENDER FOR RECOMMENDATIONS**: Use declared gender '{user_gender}' if provided, otherwise identify from image
2. **CLOTHING AND STYLE**: Appropriate for context, quality, colors, formality level
3. **PERSONAL GROOMING**: Hair, hygiene, makeup (if applicable)
4. **POSTURE AND BODY LANGUAGE**: Posture, expression, confidence
5. **ENVIRONMENT**: Background, lighting, professional framing

CRITICAL: Based on your analysis, determine if this person needs clothing/style improvements or if they are already well-dressed.

GENDER-AWARE SEARCH GUIDELINES:
{"- USER DECLARED GENDER: Use '" + user_gender + "' for all search terms and recommendations" if user_gender else "- VISUAL IDENTIFICATION: Determine from image appearance"}
- If male/masculine: Include "men", "male", "masculine" in search queries
- If female/feminine: Include "women", "female", "feminine" in search queries  
- If non-binary: Use "unisex", "gender neutral" terms
- CONTEXT OVERRIDE: If the context explicitly mentions different gender preferences, respect that
- EXAMPLES WITH DECLARED GENDER:
  * Declared male + boda → "elegant wedding guest attire men formal suit"
  * Declared female + interview → "professional business interview outfit women formal"
  * Declared male + presentación → "formal presentation attire men business professional"

You MUST respond with ONLY a valid JSON object in this EXACT format:
{{
    "overall_rating": 8.5,
    "needs_improvement": true,
    "analysis_summary": "Detailed professional analysis of the person's appearance...",
    "strengths": ["Specific strength 1", "Specific strength 2", "Specific strength 3"],
    "recommendations": ["Specific recommendation 1", "Specific recommendation 2"],
    "improvement_areas": ["area1", "area2"],
    "gender_identified": "{user_gender if user_gender else 'determined_from_image'}",
    "gender_source": "{'user_declared' if user_gender else 'visual_analysis'}",
    "search_query": "professional business attire interview formal men"
}}

RULES:
- ALWAYS prioritize declared gender over visual analysis
- If person is well-dressed and professional: set "needs_improvement": false and "search_query": ""
- If they need improvements: set "needs_improvement": true and create appropriate search query
- The search_query MUST reflect the correct gender (declared or identified)
- Make search_query specific to both context and gender
- For wedding contexts: "wedding guest attire [gender]" 
- For formal events: "formal [gender] attire [context]"
- Keep analysis_summary comprehensive but concise
- Be constructive and specific in all feedback
- Always respect user's gender declaration as absolute truth"""

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{
                "role": "user", 
                "content": analysis_prompt
            }],
            max_tokens=800
        )
        
        # Usar función similar a _clean_json_response
        analysis_text = response.choices[0].message.content
        analysis_data = clean_json_response(analysis_text)

        print(f"Analysis data: {analysis_data}")  # Debugging output
        
        # Construir respuesta base
        result = {
            "professional_analysis": analysis_data.get("analysis_summary", "Analysis completed"),
            "context_analyzed": context,
            "analysis_type": "professional_appearance", 
            "image_analyzed": True,
            "overall_rating": analysis_data.get("overall_rating", 7.0),
            "strengths": analysis_data.get("strengths", []),
            "recommendations": analysis_data.get("recommendations", []),
            "gender_used": analysis_data.get("gender_identified", user_gender or "not_specified"),
            "gender_source": analysis_data.get("gender_source", "user_declared" if user_gender else "visual_analysis")
        }
        
        # Verificar si necesita mejoras
        needs_improvement = analysis_data.get("needs_improvement", True)
        search_query = analysis_data.get("search_query", "").strip()
        
        if not needs_improvement or not search_query:
            result["status"] = "excellent"
            result["message"] = "¡Excelente! Tu apariencia es perfectamente apropiada para este contexto."
            return result
        
        # Buscar imágenes de vestimenta usando el query generado por el LLM
        api_key = os.getenv("SERPAPI_KEY")
        if not api_key:
            result["warning"] = "Cannot show clothing suggestions - API key not found"
            return result
        
        # Usar el query específico generado por el LLM
        image_params = {
            "engine": "google_images",
            "q": search_query,
            "api_key": api_key,
            "num": 8,
            "safe": "active"
        }
        
        try:
            search = GoogleSearch(image_params)
            image_results = search.get_dict()
            images = image_results.get("images_results", [])
            
            if images:
                carousel_html = generate_image_carousel_html(images, 8)
                result["graph"] = carousel_html
                result["search_query_used"] = search_query
                result["status"] = "suggestions_provided"
            else:
                result["warning"] = "No se pudieron encontrar sugerencias de vestimenta"
                
        except Exception as search_error:
            print(f"Error searching for clothing images: {str(search_error)}")
            result["warning"] = "Error al buscar sugerencias de vestimenta"
        
        return result
        
    except Exception as e:
        print(f"Error analyzing professional appearance: {str(e)}")
        return {"error": str(e)}


def clean_json_response(content: str) -> dict:
    """
    Limpia y parsea respuesta JSON del LLM, similar a _clean_json_response en llm.py
    """
    try:
        # Limpiar markdown si existe
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "", 1)
            if content.endswith("```"):
                content = content[:-3]
        
        content = content.strip()
        
        # Parsear JSON
        return json.loads(content)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {content}")
        return {
            "overall_rating": 7.0,
            "needs_improvement": True,
            "analysis_summary": content,  
            "strengths": [],
            "recommendations": [],
            "search_query": "professional business attire"
        }

def generate_training_report(training_type: str, training_data: str, user_id: int, status: str, use_synthetic_data: bool = False) -> Dict:
    """
    Generates a comprehensive training report in HTML format with visual elements,
    saves it to the database, and returns it for display/PDF conversion.
    
    Args:
        training_type (str): Type of training ("job_interview_simulation", "professional_appearance_analysis")
        training_data (str): JSON string or text with training session data
        user_id (int): User ID
        status (str): Status message for tracking
        use_synthetic_data (bool): Whether to generate synthetic data for testing
        
    Returns:
        dict: Dictionary with the generated report and success status
    """
    try:
        set_status(user_id, status, 4)  # 4 = skills trainer role
        
        # Get current time in Bogotá timezone (UTC-5)
        bogota_tz = timezone(timedelta(hours=-5))
        current_time = datetime.now(bogota_tz)
        
        # System prompt for the report generation agent
        system_prompt = """You are a professional training report specialist who creates comprehensive, visually appealing HTML reports for skill development sessions. Your reports are designed to be converted to PDF and must be professional, detailed, and actionable.

CRITICAL HTML REQUIREMENTS:
1. Generate ONLY clean HTML code with embedded CSS - no DOCTYPE, no explanations
2. Use professional color scheme: #2563eb (blue), #059669 (green), #dc2626 (red), #f59e0b (amber)
3. Create a modern, clean design suitable for PDF conversion
4. Include visual elements using CSS (progress bars, charts, icons)
5. Make it print-friendly with proper page breaks

REPORT STRUCTURE:
1. **Header Section**: Training type, date, participant info
2. **Executive Summary**: Overall performance overview with visual score
3. **Session Details**: Specific activities, questions, responses (if applicable)
4. **Performance Analysis**: Strengths and areas for improvement with visual indicators
5. **Detailed Feedback**: Specific observations and recommendations
6. **Action Plan**: Next steps and improvement suggestions
7. **Progress Tracking**: Visual indicators and goals

VISUAL ELEMENTS TO INCLUDE:
- Progress bars and score indicators using CSS
- Color-coded sections for different performance levels
- Professional SVG icons embedded inline (target, star, chart, lightbulb, user, check, arrow, etc.)
- Professional charts and graphs using CSS and SVG
- Skill matrices and competency grids with SVG indicators
- Timeline elements for improvement tracking with SVG elements

DESIGN PRINCIPLES:
- Clean, professional layout with proper spacing
- Consistent typography and visual hierarchy
- Use of white space for readability
- Color coding for quick visual understanding
- Print-friendly design (A4 page format)
- Professional branding appropriate for Universidad del Norte

CONTENT GUIDELINES:
- Use encouraging but honest language
- Provide specific, actionable feedback
- Include measurable goals and objectives
- Reference best practices and industry standards
- Maintain constructive tone throughout
- CRITICAL: Use only standard ASCII characters and CSS symbols (●, ▲, ★, ♦, →, ←, ↑, ↓) instead of Unicode emojis to avoid database encoding issues
- CRITICAL: Use only basic ASCII characters and CSS symbols (●, ▲, ★, ♦, →, ←, ↑, ↓) - NO Unicode emojis

OUTPUT: Return ONLY clean HTML code with embedded CSS styling. No explanations or additional text. IMPORTANT: Use only ASCII characters and basic symbols to ensure database compatibility. Ensure all content uses standard ASCII characters to avoid encoding issues.d objectives
- Reference best practices and industry standards
- Maintain constructive tone throughout
- Include both qualitative and quantitative assessments

OUTPUT: Return ONLY clean HTML code with embedded CSS styling. No explanations or additional text."""

        # Determine if we should use synthetic data or real data
        if use_synthetic_data:
            data_instruction = "Generate realistic synthetic training data for demonstration purposes. Create a comprehensive example session with realistic responses, feedback, and performance metrics."
        else:
            data_instruction = f"Use the following real training session data: {training_data}"

        # Create the user prompt based on training type
        if training_type == "job_interview_simulation":
            user_prompt = f"""Create a comprehensive job interview simulation report with the following details:

TRAINING TYPE: Job Interview Simulation
USER ID: {user_id}
SESSION DATE: {current_time.strftime('%B %d, %Y at %I:%M %p')} (Bogotá time)

DATA INSTRUCTION: {data_instruction}

Generate a professional HTML report that includes:
1. Interview session overview (position, duration, questions asked)
2. Performance analysis with visual scoring (1-10 scale)
3. Response quality assessment for each question
4. Communication skills evaluation
5. Professional presence assessment
6. Strengths and improvement areas with specific examples
7. Personalized action plan for skill development
8. Next steps and practice recommendations

Make the report visually engaging with:
- Overall interview score with visual progress bar
- Individual question performance charts
- Skill competency matrix
- Professional development roadmap
- Color-coded feedback sections

Ensure the report is comprehensive, actionable, and encouraging while maintaining professional standards."""

        elif training_type == "professional_appearance_analysis":
            user_prompt = f"""Create a comprehensive professional appearance analysis report with the following details:

TRAINING TYPE: Professional Appearance Analysis
USER ID: {user_id}
SESSION DATE: {current_time.strftime('%B %d, %Y at %I:%M %p')} (Bogotá time)

DATA INSTRUCTION: {data_instruction}

Generate a professional HTML report that includes:
1. Appearance assessment overview (context, occasion, analysis scope)
2. Overall professional image score with visual indicators
3. Detailed evaluation of clothing, grooming, posture, and environment
4. Strengths in professional presentation
5. Specific improvement recommendations
6. Context-appropriate styling suggestions
7. Professional image development plan
8. Follow-up recommendations and resources

Make the report visually engaging with:
- Overall appearance score with visual rating system
- Category-specific performance indicators (attire, grooming, posture)
- Before/after improvement visualization concepts
- Professional styling guide elements
- Color-coded recommendation priorities

Ensure the report is constructive, specific, and professionally encouraging."""

        else:
            # Generic training report
            user_prompt = f"""Create a comprehensive training session report with the following details:

TRAINING TYPE: {training_type}
USER ID: {user_id}
SESSION DATE: {current_time.strftime('%B %d, %Y at %I:%M %p')} (Bogotá time)

DATA INSTRUCTION: {data_instruction}

Generate a professional HTML report that includes:
1. Training session overview and objectives
2. Performance analysis with visual indicators
3. Skills assessment and competency evaluation
4. Detailed feedback and observations
5. Strengths and areas for development
6. Personalized improvement recommendations
7. Action plan and next steps
8. Progress tracking elements

Make the report comprehensive, actionable, and visually professional."""

        # Generate the report using OpenAI
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        report_html = response.choices[0].message.content
        
        # Clean any markdown code block markers from the response
        if report_html.startswith("```html"):
            report_html = report_html.replace("```html", "", 1)
        elif report_html.startswith("```"):
            report_html = report_html.replace("```", "", 1)
        
        if report_html.endswith("```"):
            report_html = report_html[:-3]
        
        report_html = report_html.strip()
        
        # Generate descriptive title for the report
        if training_type == "job_interview_simulation":
            title = f"Job Interview Simulation Report - {current_time.strftime('%B %d, %Y')}"
        elif training_type == "professional_appearance_analysis":
            title = f"Professional Appearance Analysis - {current_time.strftime('%B %d, %Y')}"
        else:
            title = f"{training_type.replace('_', ' ').title()} Report - {current_time.strftime('%B %d, %Y')}"
        
        # Save the report to the database
        try:
            user_instance = User.objects.get(id=user_id)
            training_report = TrainingReport.objects.create(
                user=user_instance,
                title=title,
                training_type=training_type,
                report_html=report_html,
                created_at=current_time
            )
            
            return {
                "pdf": report_html,
                "report_id": training_report.id,
                "title": title,
                "created_at": current_time.isoformat(),
                "message": f"Training report '{title}' generated and saved successfully"
            }
            
        except User.DoesNotExist:
            return {"error": f"User with ID {user_id} not found"}
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            # Still return the report even if DB save fails
            return {
                "pdf": report_html,
                "title": title,
                "created_at": current_time.isoformat(),
                "message": f"Training report generated successfully (DB save failed: {str(db_error)})"
            }
        
    except Exception as e:
        print(f"Error generating training report: {str(e)}")
        return {"error": str(e)}
    


def list_recent_training_reports(user_id: int, limit: int = 10, status: str = "") -> dict:
    """
    Lista los reportes de entrenamiento más recientes para un usuario específico.
    
    Args:
        user_id (int): ID del usuario cuyos reportes se quieren listar
        limit (int): Número máximo de reportes a retornar (por defecto 10)
        status (str): Mensaje de estado para tracking
        
    Returns:
        dict: Diccionario con HTML para mostrar en el frontend bajo la llave "display"
    """
    try:
        set_status(user_id, status, 4) 
        
        from apps.skills.services import SkillsTrainerDBService
        from datetime import timezone, timedelta
        db_service = SkillsTrainerDBService()
        

        all_reports = db_service.list_user_training_reports(user_id)
        
        recent_reports = list(all_reports[:limit])
        
        if not recent_reports:
            html_content = """
            <div style="padding: 20px; text-align: center; font-family: Arial, sans-serif;">
                <div style="background: linear-gradient(135deg, #f59e0b, #d97706); padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;">
                    <h2 style="margin: 0; font-size: 24px;">📋 Training Reports</h2>
                </div>
                <div style="background: #f9fafb; padding: 30px; border-radius: 10px; border: 2px dashed #d1d5db;">
                    <p style="font-size: 18px; color: #6b7280; margin: 0;">No training reports found yet.</p>
                    <p style="font-size: 14px; color: #9ca3af; margin-top: 10px;">Complete some training sessions to see your reports here!</p>
                </div>
            </div>
            """
        else:
            reports_html = ""
            bogota_tz = timezone(timedelta(hours=-5))
            
            for i, report in enumerate(recent_reports, 1):
                # Formatear fecha - convertir de UTC a Bogotá timezone
                created_at = report.get('created_at', '')
                if hasattr(created_at, 'strftime'):
                    # Si la fecha tiene timezone info, convertir a Bogotá
                    if hasattr(created_at, 'astimezone'):
                        bogota_time = created_at.astimezone(bogota_tz)
                        formatted_date = bogota_time.strftime('%B %d, %Y at %I:%M %p')
                    else:
                        # Si no tiene timezone info, asumir que es UTC y convertir
                        if created_at.tzinfo is None:
                            # Asumir UTC y convertir a Bogotá
                            utc_time = created_at.replace(tzinfo=timezone.utc)
                            bogota_time = utc_time.astimezone(bogota_tz)
                            formatted_date = bogota_time.strftime('%B %d, %Y at %I:%M %p')
                        else:
                            formatted_date = created_at.strftime('%B %d, %Y at %I:%M %p')
                else:
                    formatted_date = str(created_at)
                
                # Determinar el tipo de entrenamiento y su ícono
                training_type = report.get('training_type', 'Unknown')
                if 'interview' in training_type.lower():
                    icon = "💼"
                    type_color = "#2563eb"
                elif 'appearance' in training_type.lower():
                    icon = "👔"
                    type_color = "#059669"
                else:
                    icon = "📈"
                    type_color = "#d97706"
                
                reports_html += f"""
                <div style="background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-left: 4px solid {type_color};">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                        <div style="flex: 1;">
                            <h3 style="margin: 0 0 5px 0; color: #111827; font-size: 18px; font-weight: 600;">
                                {icon} {report.get('title', 'Training Report')}
                            </h3>
                            <p style="margin: 0; color: #6b7280; font-size: 14px;">
                                📅 {formatted_date}
                            </p>
                        </div>
                        <div style="background: {type_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;">
                            Report #{report.get('id', i)}
                        </div>
                    </div>
                    <div style="background: #f9fafb; padding: 10px; border-radius: 5px; margin-top: 10px;">
                        <p style="margin: 0; color: #374151; font-size: 13px;">
                            <strong>Type:</strong> {training_type.replace('_', ' ').title()}
                        </p>
                    </div>
                </div>
                """
            
            html_content = f"""
            <div style="padding: 20px; font-family: Arial, sans-serif; max-width: 800px;">
                <div style="background: linear-gradient(135deg, #d97706, #f59e0b); padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px; text-align: center;">
                    <h2 style="margin: 0; font-size: 24px;">📋 Your Training Reports</h2>
                    <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 14px;">
                        Showing {len(recent_reports)} of {len(all_reports)} total reports
                    </p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    {reports_html}
                </div>
                
                {f'<div style="text-align: center; padding: 15px; background: #eff6ff; border-radius: 8px; border: 1px solid #bfdbfe;"><p style="margin: 0; color: #1d4ed8; font-size: 14px;"><strong>Note:</strong> Showing the most recent {limit} reports. You have {len(all_reports)} total reports.</p></div>' if len(all_reports) > limit else ''}
            </div>
            """
        
        return {
            "display": html_content,
            "total_found": len(all_reports),
            "showing": len(recent_reports),
            "message": f"Successfully retrieved {len(recent_reports)} recent training reports"
        }
        
    except Exception as e:
        print(f"Error listing recent training reports: {str(e)}")
        error_html = f"""
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <div style="background: #fee2e2; border: 1px solid #fecaca; padding: 15px; border-radius: 8px; color: #dc2626;">
                <h3 style="margin: 0 0 10px 0; font-size: 16px;">❌ Error Loading Reports</h3>
                <p style="margin: 0; font-size: 14px;">Unable to retrieve your training reports at this time.</p>
            </div>
        </div>
        """
        return {"display": error_html, "error": str(e)}


def get_training_report_html(report_id: int, user_id: int, status: str = "") -> dict:
    """
    Obtiene el contenido HTML de un reporte de entrenamiento específico para descarga.
    
    Args:
        report_id (int): ID del reporte que se quiere obtener
        user_id (int): ID del usuario que solicita el reporte (para validación)
        status (str): Mensaje de estado para tracking
        
    Returns:
        dict: Diccionario con el HTML del reporte bajo la llave "pdf"
    """
    try:
        set_status(user_id, status, 4)
        
        db_service = SkillsTrainerDBService()
        
        # Obtener el reporte específico
        report_data = db_service.get_training_report_by_id(report_id)
        
        # Validar que el reporte pertenece al usuario (seguridad)
        try:
            report_instance = TrainingReport.objects.get(id=report_id)
            if report_instance.user.id != user_id:
                return {"error": "Access denied: This report does not belong to the current user"}
        except TrainingReport.DoesNotExist:
            return {"error": f"Training report with ID {report_id} not found"}
        
        # Extraer el HTML del reporte
        report_html = report_data.get('report_html', '')
        if not report_html:
            return {"error": "Report HTML content not found"}
        
        # Convertir la fecha a horario de Bogotá y formato string
        created_at = report_data.get('created_at', '')
        formatted_date = ''
        if created_at:
            try:
                bogota_tz = timezone(timedelta(hours=-5))
                
                if hasattr(created_at, 'strftime'):
                    if hasattr(created_at, 'astimezone'):
                        bogota_time = created_at.astimezone(bogota_tz)
                        formatted_date = bogota_time.strftime('%B %d, %Y at %I:%M %p')
                    else:
                        if created_at.tzinfo is None:
                            utc_time = created_at.replace(tzinfo=timezone.utc)
                            bogota_time = utc_time.astimezone(bogota_tz)
                            formatted_date = bogota_time.strftime('%B %d, %Y at %I:%M %p')
                        else:
                            formatted_date = created_at.strftime('%B %d, %Y at %I:%M %p')
                else:
                    formatted_date = str(created_at)
            except Exception as date_error:
                print(f"Error formatting date: {str(date_error)}")
                formatted_date = str(created_at)
        
        return {
            "pdf": report_html,
            "report_id": report_id,
            "title": report_data.get('title', 'Training Report'),
            "training_type": report_data.get('training_type', 'Unknown'),
            "created_at": formatted_date,  # Ahora es string, no datetime
            "message": f"Training report HTML retrieved successfully for download"
        }
        
    except Exception as e:
        print(f"Error retrieving training report HTML: {str(e)}")
        return {"error": str(e)}