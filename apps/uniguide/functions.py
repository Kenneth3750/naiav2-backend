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
from bs4 import BeautifulSoup
import time
from services.files import B2FileService
from datetime import datetime, timezone, timedelta
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
            set_status(user_id, status or "Sending email...", 2)

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


def create_rag():
    """
    Save documents from B2 cloud storage into a vector database
    """
    try:
        # Get documents from B2
        b2_service = B2FileService()
        document_bytes_list = b2_service.download_uniguide_documents()
        
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

        return f"Successfully processed {len(document_bytes_list)} documents from B2 storage"

    except Exception as e:
        print(f"Error processing documents: {str(e)}")
        return {"error": str(e)}

def query_university_rag(user_id: int, question: str, k: int = 3, status:str = "") -> dict:
    """
    Query the information stored in the vector store and generate a response.
    """
    try:
        set_status(user_id, status, 2)
        persist_dir = "./chromadb_uniguide"

        if not os.path.exists(persist_dir):
            create_rag()
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


def get_current_month_uni_calendar(user_id: int, status: str) -> str:
    """ Scrape the current month's events from the Universidad del Norte calendar.
    Returns:
        str: Formatted string of events with their names and dates.
    """
    driver = None
    try: 
        set_status(user_id, status, 2)
        url = 'https://outlook.office365.com/calendar/published/82dc57e4303e46d490fec6d6df9e41c6@uninorte.edu.co/ca0af55ded00488eb89bac6079a9675a7730392440685253853/calendar.html'


        gmt_minus_5 = timezone(timedelta(hours=-5))

        current_bogota_time = datetime.now(gmt_minus_5)
        current_day = current_bogota_time.strftime('%Y-%m-%d')
        print(f"Current day in GMT-5: {current_day}")

        # Configuración más robusta de Chrome
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
        

        driver = webdriver.Chrome(options=options)
        

        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)

        driver.get(url)
        time.sleep(2)  

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        divs = soup.find_all('div', role='button')
        print(f"Found {len(divs)} events.")

        formatted_events = ""
        for div in divs:
            if div.get('aria-label') is not None:
                title = div.get("aria-label").strip().replace('\n', ' ').split(",")
                formatted_events += f"EVENT NAME: {title[0].strip()}, DATE: {title[2].strip()}\n"
            elif div.get('title') is not None:
                title = div.get("title").strip().replace('\n', ' ').split(",")
                formatted_events += f"EVENT NAME: {title[0].strip()}, DATE: {title[1].strip()}\n"
            else:
                print("No title or aria-label found for a div.")

        print("number of formatted events:", len(formatted_events.split('\n')) - 1)
        formatted_events += f"\n\nCurrent day in GMT-5: {current_day}, Use this date to compare with the events above.\n"
        
        return {"current_month_calendar": formatted_events}
    
    except Exception as e:
        print(f"Error scraping calendar: {str(e)}")
        return {"error": str(e)}
    
    finally:
        if driver is not None:
            try:
                driver.quit()
                print("WebDriver cerrado correctamente")
            except Exception as cleanup_error:
                print(f"Error cerrando WebDriver: {cleanup_error}")
                try:
                    import psutil
                    import os
                    
                    # Buscar y matar procesos de Chrome/ChromeDriver
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            if 'chrome' in proc.info['name'].lower() or 'chromedriver' in proc.info['name'].lower():
                                proc.kill()
                                print(f"Proceso {proc.info['name']} (PID: {proc.info['pid']}) terminado forzadamente")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except ImportError:
                    print("psutil no disponible para cleanup manual")
                except Exception as manual_cleanup_error:
                    print(f"Error en cleanup manual: {manual_cleanup_error}")
