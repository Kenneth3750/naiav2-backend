from email.mime.text import MIMEText
from apps.status.services import set_status
import smtplib
import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import tempfile
from typing import List
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
            set_status(user_id, status or "Sending email...", 1)

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


def mental_health_screening_tool(user_id: int, status: str, user_specific_situation: str, language: str ) -> dict:
    """
    This function generates a hmtl form questionnaire for mental health screening,
    which is designed to be filled out by the user. The questionnaire is based on the 
    the steps provided by CAE (Centro de Acompañamiento Estudiantil) from Universidad del Norte.

    Args:
        user_id (int): The ID of the user
        status (str): The status message for tracking
        user_specific_situtation (str): The user's specific situation to make a personalized questionnaire
    Returns:
        dict: A dictionary containing the HTML form for the questionnaire
    
    """
    try:
        set_status(user_id, status, 1)

        base_url = os.getenv('BACKEND_BASE_URL', 'http://localhost:3000')
        form_action_url = f"{base_url}/api/v1/uniguide/form/analysis/"

        # Agent specialized in mental health forms
        agent_prompt = f"""You are a specialized mental health form generator for Universidad del Norte students. Your task is to create personalized HTML questionnaires for mental health screening that will help connect students with the CAE (Centro de Acompañamiento Estudiantil).

        IMPORTANT: You are NOT the CAE. You are a SUPPORT SERVICE that helps students connect with CAE professionals.

        CRITICAL FORM REQUIREMENTS:
        1. The form MUST always have id="mental-health-screening-form" and name="mental-health-screening-form"
        2. DO NOT include any submit button - this will be handled separately
        3. All input fields must have unique names for easy data extraction
        4. Use appropriate input types (radio, checkbox, textarea, select, etc.)
        5. Include hidden field with user_id: <input type="hidden" name="user_id" value="{user_id}">

        MESSAGING GUIDELINES:
        - Make it clear this is a SUPPORT TOOL to help connect with CAE
        - Use phrases like "This assessment will help connect you with CAE professionals"
        - "This tool is designed to facilitate your connection with university mental health services"
        - "Your responses will help CAE professionals better understand your needs"
        - DO NOT speak as if you ARE the CAE
        - Position yourself as a bridge to professional help

        CAE INFORMATION TO INCLUDE (as reference, not as if you are them):
        - Schedule: Monday to Friday, 8:00 am to 12:30 pm and 2:00 pm to 6:30 pm
        - Team: Professional psychologists at CAE
        - Emergency Crisis Line (24 hours): 3793333 – 3399999 (outside campus)
        - CAE is the official support network for students

        CAE MENTAL HEALTH INDICATORS (Base your questions on these):
        When to seek help:
        - You don't like yourself, you have trouble accepting yourself
        - You find it very difficult to control yourself when you get angry
        - You have family problems that are affecting you too much
        - You have conflicts with someone close (Professor, classmate, friend, partner, family)
        - You are grieving the loss of someone or something
        - You have difficulty with alcohol and/or psychoactive substance consumption
        - You are living or have recently lived a situation of abuse or mistreatment (Physical, emotional, sexual, other)
        - You remain very worried, tense, anxious, stressed
        - It has become frequent that you don't sleep, sleep very little, your sleep is restless
        - You feel like not going to classes, studying and your academic performance has dropped
        - You have stopped enjoying what you liked or what was fun for you
        - You feel like you're losing the will to live
        - You feel a lot of discouragement, sadness, without energy or motivation for anything
        - You have become more irritable or have isolated yourself more than usual
        - You cry frequently and very easily
        - You have changed your eating habits (eat more or your appetite has decreased too much)
        - Restlessness, hyperactivity, you speak quickly or confusedly
        - You are physically hurting yourself (hitting, cutting, scratching or burning yourself)
        - Sometimes you want to die or think it would be best right now
        - You would like to end your life
        - You are planning or have attempted to take your life

        CAE CONTACT INFORMATION (Include this in the form):
        - Schedule: Monday to Friday, 8:00 am to 12:30 pm and 2:00 pm to 6:30 pm
        - Team: Professional psychologists available ALWAYS
        - Emergency Crisis Line (24 hours): 3793333 – 3399999 (outside campus)
        - Message: "We are your SUPPORT NETWORK - TALK to us"
        - Additional resources available for learning and access anytime, anywhere

        FORM STRUCTURE REQUIREMENTS:
        1. Create a welcoming introduction explaining the purpose and confidentiality
        2. Include CAE contact information prominently at the beginning
        3. Personalize questions based on the user's specific situation
        4. Use a mix of question types (scales, multiple choice, open text)
        5. Include severity assessment and risk level evaluation
        6. Organize questions logically by categories (emotional, behavioral, physical, social, academic)
        7. Use empathetic, non-judgmental language reflecting CAE's supportive approach
        8. Include proper styling for a professional, calming appearance
        9. Add emergency contact information if high-risk indicators are present
        10. Make it responsive and accessible

        STYLING GUIDELINES:
        - Use Universidad del Norte colors (blues, whites)
        - Clear, readable fonts (professional but warm)
        - Proper spacing and organization
        - Professional but empathetic appearance
        - Ensure mobile responsiveness
        - Include visual elements that reflect care and support

        PERSONALIZATION:
        - Adapt questions to directly address the user's specific situation
        - Include relevant follow-up questions based on their context
        - Maintain clinical relevance while being conversational
        - Focus on the most relevant CAE indicators for their situation
        - Emphasize that professional help is available and accessible

        IMPORTANT MESSAGING:
        - Emphasize that emotional wellbeing and mental health matter
        - Professional team ready to accompany and provide psychological attention
        - Always available support network
        - Normalize seeking help when needed

        OUTPUT: Return ONLY the complete HTML form with embedded CSS styling. No explanations or additional text."""

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": agent_prompt},
                {"role": "user", "content": f"Create a html form questionnaire for mental health screening. This is a SUPPORT TOOL to help connect students with CAE professionals. The questionnaire should be personalized for: {user_specific_situation}. Form language: {language}."},
            ],
        )
        html_form = response.choices[0].message.content

        # Clean up the response
        if html_form.startswith("```html"):
            html_form = html_form.replace("```html", "", 1)
        elif html_form.startswith("```"):
            html_form = html_form.replace("```", "", 1)
        
        html_form = html_form.rstrip()
        if html_form.endswith("```"):
            html_form = html_form[:-3].rstrip()
        
        html_form = html_form.strip()


        submit_button_text = "Enviar Evaluación" if language.lower() == "spanish" else "Submit Assessment"
        
        complete_form = f"""
        <form id="mental-health-screening-form" name="mental-health-screening-form" action="{form_action_url}" method="POST">
            {html_form}
            <div style="text-align: center; margin-top: 2rem; padding: 1rem;">
                <button type="submit" style="
                    background: linear-gradient(90deg, #124072 60%, #00aeda 100%);
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 8px rgba(18, 64, 114, 0.3);
                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(18, 64, 114, 0.4)'" 
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(18, 64, 114, 0.3)'">
                    {submit_button_text}
                </button>
            </div>
        </form>
        """

        with open("mental_health_screening_tool.html", "w", encoding="utf-8") as file:
            file.write(complete_form)
        return {"form": complete_form}
    except Exception as e:
        print(f"Error generating mental health screening tool: {str(e)}")
        return {"error": str(e)}


def create_rag(documents_dir: str):
    """
    Save documents from a directory into a vector database
    documents_dir: path to the directory containing PDF and TXT files
    """
    if not os.path.exists(documents_dir):
        raise ValueError(f"Directory {documents_dir} does not exist.")
    
    all_documents = []
    
    try:
        # Process PDF files
        pdf_files = [f for f in os.listdir(documents_dir) if f.lower().endswith('.pdf')]
        for pdf_file in pdf_files:
            pdf_path = os.path.join(documents_dir, pdf_file)
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            all_documents.extend(docs)
            print(f"Processed PDF: {pdf_file}")

        # Process TXT files
        txt_files = [f for f in os.listdir(documents_dir) if f.lower().endswith('.txt')]
        for txt_file in txt_files:
            txt_path = os.path.join(documents_dir, txt_file)
            loader = TextLoader(txt_path)
            docs = loader.load()
            all_documents.extend(docs)
            print(f"Processed TXT: {txt_file}")

        if not all_documents:
            raise ValueError("No PDF or TXT files found in the specified directory.")
        
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

        return f"Successfully processed {len(pdf_files)} PDF files and {len(txt_files)} TXT files"

    except Exception as e:
        print(f"Error processing documents: {str(e)}")
        return {"error": str(e)}

def query_rag(question: str, k: int = 3, status:str = "") -> dict:
    """
    Query the information stored in the vector store and generate a response.
    """
    try:
        set_status(status, 1)
        persist_dir = "./chromadb_uniguide"

        if not os.path.exists(persist_dir):
            create_rag("./rag_docs")
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
        return {"Resolved RAG": result_text}

    except Exception as e:
        print(f"Error retrieving documents: {str(e)}")
        return {"error": str(e)}


