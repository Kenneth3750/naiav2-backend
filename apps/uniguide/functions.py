from email.mime.text import MIMEText
from apps.status.services import set_status
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_FROM_EMAIL=os.getenv("DEFAULT_FROM_EMAIL")
EMAIL_HOST_PASSWORD=os.getenv("EMAIL_HOST_PASSWORD")


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