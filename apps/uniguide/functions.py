from email.mime.text import MIMEText
from apps.status.services import set_status
import smtplib
import os
from dotenv import load_dotenv
from openai import OpenAI
import re
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

        base_url = os.getenv('BACKEND_BASE_URL', 'http://localhost:8000')
        form_action_url = f"{base_url}/api/v1/uniguide/form/analysis/"

        # Agent specialized in mental health forms
        agent_prompt = """You are a specialized mental health form generator for Universidad del Norte students. Your task is to create personalized HTML questionnaires for mental health screening that will help connect students with the CAE (Centro de Acompañamiento Estudiantil).

        IMPORTANT: You are NOT the CAE. You are a SUPPORT SERVICE that helps students connect with CAE professionals.

        CRITICAL FORM REQUIREMENTS:
        1. Generate ONLY form field content (div, input, select, textarea elements)
        2. NO DOCTYPE, NO HTML tags, NO HEAD, NO BODY, NO FORM tags
        3. Start directly with the first div or fieldset
        4. End with the last input field - no closing tags for html/body/form
        5. NO submit button
        6. Think of it as generating ONLY the inside content that goes between <form> and </form>

        FORBIDDEN ELEMENTS:
        - <!DOCTYPE html>
        - <html>, <head>, <body>
        - <form> opening or closing tags
        - <button type="submit">
        - Any complete HTML document structure

        ⚠️ ABSOLUTELY NO IMAGES ALLOWED:
        - NO <img> tags
        - NO background images in CSS
        - NO image URLs or references
        - NO icons that require image files
        - Use only text, CSS shapes, and Unicode symbols (✓, ✗, ●, etc.)
        - Focus on clean typography and colors for visual appeal

        🔒 MANDATORY FIELD REQUIREMENTS:
        - ALL input fields MUST have the "required" attribute
        - ALL select fields MUST have the "required" attribute
        - ALL textarea fields MUST have the "required" attribute
        - NO optional fields allowed - every field must be mandatory
        - Use placeholder text to guide users on what to input

        🚫 SINGLE SUBMIT PREVENTION (Include this JavaScript):
        You MUST include this exact JavaScript code within a <script> tag at the end of your HTML:

        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.getElementById('mental-health-screening-form');
            let isSubmitting = false;
            
            if (form) {
                form.addEventListener('submit', function(event) {
                    event.preventDefault(); // Prevent form redirection
                    
                    // Check if already submitted
                    if (isSubmitting) {
                        return false;
                    }
                    
                    // Validate all required fields
                    const requiredFields = form.querySelectorAll('[required]');
                    let allValid = true;
                    
                    requiredFields.forEach(field => {
                        if (!field.value.trim()) {
                            allValid = false;
                            field.style.borderColor = '#dc3545';
                            field.style.boxShadow = '0 0 0 0.2rem rgba(220, 53, 69, 0.25)';
                        } else {
                            field.style.borderColor = '#28a745';
                            field.style.boxShadow = '0 0 0 0.2rem rgba(40, 167, 69, 0.25)';
                        }
                    });
                    
                    if (!allValid) {
                        alert('Por favor completa todos los campos obligatorios.');
                        return false;
                    }
                    
                    // Mark as submitting
                    isSubmitting = true;
                    
                    // Disable all form elements
                    const allInputs = form.querySelectorAll('input, select, textarea, button');
                    allInputs.forEach(element => {
                        element.disabled = true;
                        element.style.opacity = '0.6';
                    });
                    
                    // Change submit button text and style
                    const submitBtn = form.querySelector('button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.innerHTML = '✓ Enviado - Procesando...';
                        submitBtn.style.background = '#28a745';
                        submitBtn.style.cursor = 'not-allowed';
                    }
                    
                    // Show processing message
                    const processingDiv = document.createElement('div');
                    processingDiv.innerHTML = '<div style="text-align: center; padding: 20px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; margin: 20px 0; color: #155724;"><strong>✓ Formulario enviado exitosamente</strong><br>Tu evaluación está siendo procesada. Gracias por confiar en nuestro servicio de apoyo.</div>';
                    form.appendChild(processingDiv);
                    
                    // Prepare form data as URL-encoded string (compatible with Django request.POST)
                    const formData = new FormData(form);
                    const urlEncodedData = new URLSearchParams();
                    
                    for (const [key, value] of formData.entries()) {
                        urlEncodedData.append(key, value);
                    }
                    
                    // Submit form data via XMLHttpRequest (compatible with Django)
                    const xhr = new XMLHttpRequest();
                    xhr.open('POST', form.action, true);
                    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                    
                    xhr.onreadystatechange = function() {
                        if (xhr.readyState === 4) {
                            if (xhr.status === 200) {
                                try {
                                    const response = JSON.parse(xhr.responseText);
                                    console.log('Form submitted successfully:', response);
                                } catch (e) {
                                    console.log('Form submitted successfully (non-JSON response)');
                                }
                            } else {
                                console.error('Error submitting form. Status:', xhr.status);
                            }
                        }
                    };
                    
                    xhr.send(urlEncodedData.toString());
                    return false;
                });
            }
        });
        </script>

        OUTPUT EXAMPLE:
        <div class="container">
            <input type="hidden" name="user_id" value="1" required>
            <h3>Section Title</h3>
            <fieldset>
                <input type="text" name="example" required placeholder="Required field">
                <select name="example_select" required>
                    <option value="">Select an option</option>
                    <option value="option1">Option 1</option>
                </select>
            </fieldset>
            <script>[INCLUDE THE JAVASCRIPT CODE ABOVE]</script>
        </div>

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
        4. Use a mix of question types (scales, multiple choice, open text) - ALL REQUIRED
        5. Include severity assessment and risk level evaluation
        6. Organize questions logically by categories (emotional, behavioral, physical, social, academic)
        7. Use empathetic, non-judgmental language reflecting CAE's supportive approach
        8. Include proper styling for a professional, calming appearance
        9. Add emergency contact information if high-risk indicators are present
        10. Make it responsive and accessible
        11. MANDATORY: Include the JavaScript code for single-submit prevention

        STYLING GUIDELINES:
        - Use Universidad del Norte colors (blues, whites)
        - Clear, readable fonts (professional but warm)
        - Proper spacing and organization
        - Professional but empathetic appearance
        - Ensure mobile responsiveness
        - NO IMAGES - use CSS styling, colors, and Unicode symbols only
        - Visual feedback for required fields
        - Consistent styling for disabled state

        TECHNICAL REQUIREMENTS:
        - All fields must have "required" attribute
        - Include comprehensive JavaScript for form submission control
        - Prevent multiple submissions with client-side validation
        - Provide visual feedback for form states (valid, invalid, submitted)
        - Use fetch API for form submission without page refresh
        - Include proper error handling and user feedback

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

        OUTPUT: Return ONLY the complete HTML form content with embedded CSS styling and JavaScript. No explanations or additional text. Remember: NO images, ALL fields required, single-submit prevention included."""
                
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": agent_prompt},
                {"role": "user", "content": f"Create a html form questionnaire for mental health screening. This is a SUPPORT TOOL to help connect students with CAE professionals. The questionnaire should be personalized for: {user_specific_situation}. Form language: {language}. Put a hidden input field with the user_id: {user_id}."},
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

        html_form = html_form.replace('<!DOCTYPE html>', '')
        html_form = html_form.replace('<html', '').replace('</html>', '')
        html_form = html_form.replace('<head>', '').replace('</head>', '')
        html_form = html_form.replace('<body>', '').replace('</body>', '')
        html_form = re.sub(r'<form[^>]*>', '', html_form)
        html_form = html_form.replace('</form>', '')


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

